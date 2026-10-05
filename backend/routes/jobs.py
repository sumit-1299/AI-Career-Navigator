"""Live Greenhouse job browsing and immutable comparison snapshots."""

from concurrent.futures import ThreadPoolExecutor, as_completed

from flask import Blueprint, current_app, request
from flask_jwt_extended import jwt_required

from models.assessment_attempt import iso_utc, utc_now
from routes.assessments import current_user_id, error
from routes.job_matches import save_comparison
from services.candidate_evidence import submission_id
from services.live_jobs import (
    BOARDS,
    FeedUnavailable,
    fetch_board,
    normalize_feed,
)

jobs_bp = Blueprint("jobs", __name__, url_prefix="/api/jobs")


@jobs_bp.after_request
def private_response(response):
    response.headers["Cache-Control"] = "no-store"
    return response


@jobs_bp.before_request
@jwt_required()
def account_required():
    if current_user_id() is None:
        return error("The candidate account is unavailable. Log in again.", 401)


def board_source_url(board):
    return f"https://job-boards.greenhouse.io/{board}"


def fetch_live_board(board):
    """
    Fetch and normalize one employer board directly from Greenhouse.

    No database reads or writes occur here.
    """
    fetched_at = utc_now()

    try:
        payload = fetch_board(board)
        jobs, prospects = normalize_feed(payload)

        records = []
        for job in jobs:
            record = {
                "id": f"{board}:{job['provider_id']}",
                "provider": "greenhouse",
                "board": board,
                "employer": BOARDS[board],
                "provider_id": job["provider_id"],
                "title": job["title"],
                "location": job["location"],
                "source_url": job["source_url"],
                "provider_updated_at": job["provider_updated_at"],
                "listed": True,
                "description": job["description"],
                "content_hash": job["content_hash"],
                "retrieved_at": iso_utc(fetched_at),
                "stale": False,
            }
            records.append(record)

        return {
            "board": board,
            "employer": BOARDS[board],
            "source_url": board_source_url(board),
            "status": "live",
            "available": True,
            "retrieved_at": iso_utc(fetched_at),
            "listed_count": len(records),
            "prospect_count": prospects,
            "last_error": None,
            "jobs": records,
        }

    except (FeedUnavailable, ValueError) as exc:
        current_app.logger.warning(
            "Could not retrieve live Greenhouse board %s: %s",
            board,
            exc,
        )

        return {
            "board": board,
            "employer": BOARDS[board],
            "source_url": board_source_url(board),
            "status": "unavailable",
            "available": False,
            "retrieved_at": iso_utc(fetched_at),
            "listed_count": 0,
            "prospect_count": 0,
            "last_error": str(exc),
            "jobs": [],
        }


def fetch_requested_boards(board=None):
    """
    Fetch all selected boards concurrently.

    This keeps the two-employer view reasonably fast while ensuring
    every returned listing comes from the current provider response.
    """
    boards = [board] if board else list(BOARDS)

    results = {}

    with ThreadPoolExecutor(max_workers=len(boards)) as executor:
        futures = {
            executor.submit(fetch_live_board, token): token
            for token in boards
        }

        for future in as_completed(futures):
            token = futures[future]
            results[token] = future.result()

    return results


def filter_jobs(records, query="", location=""):
    query = query.casefold()
    location = location.casefold()

    filtered = []

    for job in records:
        haystack = f"{job['title']} {job['description']}".casefold()

        if query and query not in haystack:
            continue

        if location and location not in (job["location"] or "").casefold():
            continue

        filtered.append(job)

    filtered.sort(
        key=lambda item: (
            item["title"].casefold(),
            item["board"],
            item["provider_id"],
        )
    )

    return filtered


@jobs_bp.get("")
def listings():
    board = request.args.get("board", "").strip()
    query = request.args.get("q", "").strip()
    location = request.args.get("location", "").strip()

    try:
        page = int(request.args.get("page", "1"))
    except ValueError:
        return error("Page must be a positive integer.", 400)

    if (
        (board and board not in BOARDS)
        or len(query) > 100
        or len(location) > 100
        or page < 1
        or page > 10000
    ):
        return error(
            "Choose a configured board, search text up to 100 characters "
            "and a valid page.",
            400,
        )

    board_results = fetch_requested_boards(board or None)

    all_jobs = []
    for result in board_results.values():
        all_jobs.extend(result["jobs"])

    filtered = filter_jobs(
        all_jobs,
        query=query,
        location=location,
    )

    page_size = 20
    total = len(filtered)

    start = (page - 1) * page_size
    end = start + page_size

    page_jobs = filtered[start:end]

    boards = []
    for token in ([board] if board else BOARDS.keys()):
        result = board_results[token]

        boards.append(
            {
                "board": result["board"],
                "employer": result["employer"],
                "source_url": result["source_url"],
                "status": result["status"],
                "available": result["available"],
                "retrieved_at": result["retrieved_at"],
                "listed_count": result["listed_count"],
                "prospect_count": result["prospect_count"],
                "last_error": result["last_error"],
            }
        )

    return {
        "status": "success",
        "source": "greenhouse_live",
        "jobs": page_jobs,
        "total": total,
        "page": page,
        "page_size": page_size,
        "boards": boards,
    }


@jobs_bp.get("/<board>/<provider_id>")
def item(board, provider_id):
    if board not in BOARDS:
        return error("Employer board not configured.", 404)

    if not provider_id.isdigit():
        return error("Invalid Greenhouse posting identifier.", 400)

    result = fetch_live_board(board)

    if not result["available"]:
        return error(
            result["last_error"]
            or "The employer board could not be reached.",
            503,
        )

    job = next(
        (
            item
            for item in result["jobs"]
            if item["provider_id"] == provider_id
        ),
        None,
    )

    if job is None:
        return error(
            "This posting is no longer present on the live employer board. "
            "Return to Live jobs and refresh the listings.",
            404,
        )

    # Return the full current description only for a selected posting.
    full_job = dict(job)

    # The comparison endpoint needs these fields, while the list view
    # intentionally avoids sending the full description for every card.
    payload = {
        "status": "success",
        "source": "greenhouse_live",
        "job": full_job,
        "board": {
            "board": result["board"],
            "employer": result["employer"],
            "source_url": result["source_url"],
            "status": result["status"],
            "available": result["available"],
            "retrieved_at": result["retrieved_at"],
            "listed_count": result["listed_count"],
            "prospect_count": result["prospect_count"],
            "last_error": result["last_error"],
        },
    }

    return payload


@jobs_bp.post("/<board>/<provider_id>/compare")
def compare(board, provider_id):
    if board not in BOARDS:
        return error("Employer board not configured.", 404)

    if not provider_id.isdigit():
        return error("Invalid Greenhouse posting identifier.", 400)

    body = request.get_json(silent=True)

    if not isinstance(body, dict) or set(body) != {"submission_id", "mode"}:
        return error(
            "Send only submission_id and mode.",
            400,
        )

    try:
        key = submission_id(body["submission_id"])

        if not isinstance(body["mode"], str) or body["mode"] not in {
            "keyword",
            "semantic",
        }:
            raise ValueError(
                "Choose keyword or semantic comparison mode."
            )

    except ValueError as exc:
        return error(str(exc), 400)

    result = fetch_live_board(board)

    if not result["available"]:
        return error(
            result["last_error"]
            or "The employer board could not be reached.",
            503,
        )

    current_job = next(
        (
            item
            for item in result["jobs"]
            if item["provider_id"] == provider_id
        ),
        None,
    )

    if current_job is None:
        return error(
            "This posting is no longer present on the live employer board. "
            "Return to Live jobs and choose another posting.",
            409,
        )

    user_id = current_user_id()

    # JobComparison stores the exact live posting used for this comparison.
    # The live vacancy itself is NOT stored as a shared LiveJob record.
    job = {
        "title": current_job["title"],
        "description": current_job["description"],
        "source_url": current_job["source_url"],
        "source_type": "greenhouse",
        "live_job_id": current_job["provider_id"],
        "board": board,
        "employer": BOARDS[board],
        "provider_id": current_job["provider_id"],
        "location": current_job["location"],
        "posting_version": 1,
        "content_hash": current_job["content_hash"],
        "provider_updated_at": current_job["provider_updated_at"],
        "last_seen_at": current_job["retrieved_at"],
        "stale_at_comparison": False,
        "source_captured_at": iso_utc(utc_now()),
    }

    return save_comparison(
        user_id,
        key,
        job,
        body["mode"],
        max_fragments=300,
    )