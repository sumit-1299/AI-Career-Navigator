"""Live tech-job search across public Greenhouse, Ashby and Lever sources."""

from concurrent.futures import ThreadPoolExecutor, as_completed

from flask import Blueprint, current_app, request
from flask_jwt_extended import jwt_required

from models.assessment_attempt import iso_utc, utc_now
from routes.assessments import current_user_id, error
from routes.job_matches import save_comparison
from services.candidate_evidence import submission_id
from services.live_jobs import (
    FeedUnavailable,
    SOURCE_REGISTRY,
    fetch_source,
    source_summary,
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


def _live_record(source_key, fetched, job, retrieved_at):
    return {
        "id": f"{source_key}:{job['provider_id']}",
        "source_key": source_key,
        "provider": fetched["provider"],
        "employer": fetched["employer"],
        "provider_id": job["provider_id"],
        "title": job["title"],
        "location": job["location"],
        "source_url": job["source_url"],
        "provider_updated_at": job.get("provider_updated_at"),
        "listed": True,
        "description": job["description"],
        "content_hash": job["content_hash"],
        "department": job.get("department", ""),
        "team": job.get("team", ""),
        "work_mode": job.get("work_mode", "Not specified"),
        "experience_level": job.get("experience_level", "Not specified"),
        "tech_tags": job.get("tech_tags", []),
        "retrieved_at": iso_utc(retrieved_at),
        "stale": False,
    }


def fetch_live_source(source_key, logger=None):
    """Fetch a source without touching Flask's application context in a worker."""
    fetched_at = utc_now()
    source = source_summary(source_key)

    try:
        fetched = fetch_source(source_key)
        records = [
            _live_record(source_key, fetched, job, fetched_at)
            for job in fetched["jobs"]
            if job.get("is_tech") is True
        ]

        return {
            **source,
            "status": "live",
            "available": True,
            "retrieved_at": iso_utc(fetched_at),
            "listed_count": len(records),
            "raw_count": len(fetched["jobs"]),
            "non_tech_excluded_count": len(fetched["jobs"]) - len(records),
            "last_error": None,
            "jobs": records,
        }
    except (FeedUnavailable, ValueError) as exc:
        # IMPORTANT: this function runs inside a ThreadPoolExecutor worker.
        # current_app is unavailable there, so use the logger passed by the
        # request thread instead of touching Flask's application context.
        if logger is not None:
            logger.warning(
                "Could not retrieve live source %s: %s",
                source_key,
                exc,
            )

        return {
            **source,
            "status": "unavailable",
            "available": False,
            "retrieved_at": iso_utc(fetched_at),
            "listed_count": 0,
            "raw_count": 0,
            "non_tech_excluded_count": 0,
            "last_error": str(exc),
            "jobs": [],
        }


def fetch_requested_sources(source_key=None):
    """Fetch selected public sources concurrently.

    The request thread captures the Flask logger first. Worker threads receive
    that logger as a plain object, avoiding the application-context error that
    caused the 500 response in the previous version.
    """
    source_keys = [source_key] if source_key else list(SOURCE_REGISTRY)
    if not source_keys:
        return {}

    logger = current_app.logger
    results = {}

    with ThreadPoolExecutor(max_workers=min(6, len(source_keys))) as executor:
        futures = {
            executor.submit(fetch_live_source, key, logger): key
            for key in source_keys
        }
        for future in as_completed(futures):
            key = futures[future]
            results[key] = future.result()

    return results


# Backwards-compatible alias for earlier code.
def fetch_requested_boards(board=None):
    mapping = {
        "canonical": "greenhouse-canonical",
        "razorpaysoftwareprivatelimited": "greenhouse-razorpay",
    }
    source_key = mapping.get(board) if board else None
    return fetch_requested_sources(source_key)


def _filter_jobs(records, query="", location="", work_mode="", experience="", technology="", provider=""):
    query = query.casefold().strip()
    location = location.casefold().strip()
    work_mode = work_mode.casefold().strip()
    experience = experience.casefold().strip()
    technology = technology.casefold().strip()
    provider = provider.casefold().strip()

    filtered = []
    for job in records:
        haystack = " ".join(
            [
                job["title"],
                job["description"],
                job.get("department", ""),
                job.get("team", ""),
                " ".join(job.get("tech_tags", [])),
            ]
        ).casefold()

        if query and query not in haystack:
            continue
        if location and location not in job["location"].casefold():
            continue
        if work_mode and work_mode != job.get("work_mode", "").casefold():
            continue
        if experience and experience != job.get("experience_level", "").casefold():
            continue
        if technology and technology not in [tag.casefold() for tag in job.get("tech_tags", [])]:
            continue
        if provider and provider != job.get("provider", "").casefold():
            continue

        relevance = 0
        if query and query in job["title"].casefold():
            relevance += 3
        if technology and technology in [tag.casefold() for tag in job.get("tech_tags", [])]:
            relevance += 2
        filtered.append((relevance, job))

    filtered.sort(
        key=lambda item: (
            -item[0],
            item[1]["title"].casefold(),
            item[1]["employer"].casefold(),
            item[1]["provider_id"],
        )
    )
    return [job for _, job in filtered]


def _facets(records):
    locations = sorted({job["location"] for job in records if job["location"]})
    technologies = sorted(
        {tag for job in records for tag in job.get("tech_tags", [])},
        key=str.casefold,
    )
    work_modes = sorted({job.get("work_mode", "Not specified") for job in records})
    experience_levels = sorted(
        {job.get("experience_level", "Not specified") for job in records},
        key=str.casefold,
    )
    providers = sorted({job.get("provider", "") for job in records if job.get("provider")})
    return {
        "locations": locations,
        "technologies": technologies,
        "work_modes": work_modes,
        "experience_levels": experience_levels,
        "providers": providers,
    }


@jobs_bp.get("")
def listings():
    source_key = request.args.get("source", "").strip()
    # Compatibility: old frontend used ?board=canonical.
    old_board = request.args.get("board", "").strip()
    if old_board:
        source_key = {
            "canonical": "greenhouse-canonical",
            "razorpaysoftwareprivatelimited": "greenhouse-razorpay",
        }.get(old_board, source_key)

    query = request.args.get("q", "").strip()
    location = request.args.get("location", "").strip()
    work_mode = request.args.get("work_mode", "").strip()
    experience = request.args.get("experience", "").strip()
    technology = request.args.get("technology", request.args.get("tech", "")).strip()
    provider = request.args.get("provider", "").strip()

    try:
        page = int(request.args.get("page", "1"))
    except ValueError:
        return error("Page must be a positive integer.", 400)

    if source_key and source_key not in SOURCE_REGISTRY:
        return error("Choose a configured live job source.", 400)

    if any(len(value) > 100 for value in [query, location, work_mode, experience, technology, provider]):
        return error("Search filters may contain at most 100 characters.", 400)
    if page < 1 or page > 10000:
        return error("Page must be a positive integer.", 400)

    source_results = fetch_requested_sources(source_key or None)
    all_jobs = []
    for result in source_results.values():
        all_jobs.extend(result["jobs"])

    filtered = _filter_jobs(
        all_jobs,
        query=query,
        location=location,
        work_mode=work_mode,
        experience=experience,
        technology=technology,
        provider=provider,
    )

    page_size = 20
    total = len(filtered)
    start = (page - 1) * page_size
    page_jobs = filtered[start:start + page_size]

    sources = [source_results[key] for key in source_results]
    sources.sort(key=lambda item: item["employer"].casefold())

    return {
        "status": "success",
        "source": "live_multi_provider",
        "tech_only": True,
        "search_scope_note": "Technology-focused vacancies only. Non-technical postings are excluded before results are returned.",
        "jobs": page_jobs,
        "total": total,
        "page": page,
        "page_size": page_size,
        "sources": sources,
        # Compatibility for earlier UI code.
        "boards": [
            {
                "board": item["source_key"],
                "employer": item["employer"],
                "source_url": item["source_url"],
                "status": item["status"],
                "available": item["available"],
                "retrieved_at": item["retrieved_at"],
                "listed_count": item["listed_count"],
                "prospect_count": item.get("non_tech_excluded_count", 0),
                "last_error": item["last_error"],
            }
            for item in sources
        ],
        "filters": {
            "q": query,
            "location": location,
            "work_mode": work_mode,
            "experience": experience,
            "technology": technology,
            "provider": provider,
        },
        "facets": _facets(all_jobs),
    }


@jobs_bp.get("/<source_key>/<path:provider_id>")
def item(source_key, provider_id):
    if source_key not in SOURCE_REGISTRY:
        return error("Live job source not configured.", 404)

    if not provider_id or len(provider_id) > 300:
        return error("Invalid provider posting identifier.", 400)

    result = fetch_requested_sources(source_key).get(source_key)
    if not result or not result["available"]:
        return error(
            (result or {}).get("last_error") or "The live employer source could not be reached.",
            503,
        )

    job = next(
        (item for item in result["jobs"] if item["provider_id"] == provider_id),
        None,
    )
    if job is None:
        return error(
            "This posting is no longer present on the live employer source. Return to Find Tech Jobs and refresh.",
            404,
        )

    return {
        "status": "success",
        "source": "live_multi_provider",
        "job": job,
        "source_info": {
            key: value
            for key, value in result.items()
            if key != "jobs"
        },
        "board": {
            "board": source_key,
            "employer": result["employer"],
            "source_url": result["source_url"],
            "status": result["status"],
            "available": result["available"],
            "retrieved_at": result["retrieved_at"],
            "listed_count": result["listed_count"],
            "prospect_count": result.get("non_tech_excluded_count", 0),
            "last_error": result["last_error"],
        },
    }


@jobs_bp.post("/<source_key>/<path:provider_id>/compare")
def compare(source_key, provider_id):
    if source_key not in SOURCE_REGISTRY:
        return error("Live job source not configured.", 404)
    if not provider_id or len(provider_id) > 300:
        return error("Invalid provider posting identifier.", 400)

    body = request.get_json(silent=True)
    if not isinstance(body, dict) or set(body) != {"submission_id", "mode"}:
        return error("Send only submission_id and mode.", 400)

    try:
        key = submission_id(body["submission_id"])
        if not isinstance(body["mode"], str) or body["mode"] not in {"keyword", "semantic"}:
            raise ValueError("Choose keyword or semantic comparison mode.")
    except ValueError as exc:
        return error(str(exc), 400)

    result = fetch_requested_sources(source_key).get(source_key)
    if not result or not result["available"]:
        return error(
            (result or {}).get("last_error") or "The live employer source could not be reached.",
            503,
        )

    current_job = next(
        (item for item in result["jobs"] if item["provider_id"] == provider_id),
        None,
    )
    if current_job is None:
        return error(
            "This posting is no longer present on the live employer source. Refresh and choose another role.",
            409,
        )

    job = {
        "title": current_job["title"],
        "description": current_job["description"],
        "source_url": current_job["source_url"],
        "source_type": current_job["provider"],
        "source_key": source_key,
        "live_job_id": current_job["provider_id"],
        "board": source_key,
        "employer": current_job["employer"],
        "provider_id": current_job["provider_id"],
        "location": current_job["location"],
        "work_mode": current_job.get("work_mode", "Not specified"),
        "experience_level": current_job.get("experience_level", "Not specified"),
        "tech_tags": current_job.get("tech_tags", []),
        "posting_version": 1,
        "content_hash": current_job["content_hash"],
        "provider_updated_at": current_job.get("provider_updated_at"),
        "last_seen_at": current_job["retrieved_at"],
        "stale_at_comparison": False,
        "source_captured_at": iso_utc(utc_now()),
    }

    return save_comparison(
        current_user_id(),
        key,
        job,
        body["mode"],
        max_fragments=300,
    )
