"""Browse selected public boards and compare a server-resolved posting snapshot."""

from flask import Blueprint, current_app, request
from flask_jwt_extended import jwt_required
from sqlalchemy import func, or_, select
from sqlalchemy.exc import SQLAlchemyError

from extensions import db
from models.assessment_attempt import iso_utc, utc_now
from models.live_job import JobBoardSync, LiveJob
from routes.assessments import current_user_id, error
from routes.job_matches import existing_submission, save_comparison
from services.candidate_evidence import submission_id
from services.live_jobs import BOARDS, RefreshBusy, refresh_board, sync_status

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


@jobs_bp.get("")
def listings():
    board = request.args.get("board", "")
    query = request.args.get("q", "").strip()
    location = request.args.get("location", "").strip()
    try:
        page = int(request.args.get("page", "1"))
    except ValueError:
        return error("Page must be a positive integer.", 400)
    if (board and board not in BOARDS) or len(query) > 100 or len(location) > 100 or page < 1 or page > 10000:
        return error("Choose a configured board, search text up to 100 characters and a valid page.", 400)
    conditions = [LiveJob.listed.is_(True), LiveJob.board.in_(BOARDS)]
    if board:
        conditions.append(LiveJob.board == board)
    if query:
        conditions.append(or_(LiveJob.title.icontains(query, autoescape=True), LiveJob.description.icontains(query, autoescape=True)))
    if location:
        conditions.append(LiveJob.location.icontains(location, autoescape=True))
    total = db.session.scalar(select(func.count()).select_from(LiveJob).where(*conditions))
    records = db.session.execute(select(LiveJob).where(*conditions).order_by(func.lower(LiveJob.title), LiveJob.board, LiveJob.id)
                                 .offset((page - 1) * 20).limit(20)).scalars().all()
    return {"status": "success", "jobs": [item.to_dict() for item in records], "total": total, "page": page,
            "page_size": 20, "boards": [sync_status(token, db.session.get(JobBoardSync, token)) for token in BOARDS]}


@jobs_bp.post("/boards/<board>/refresh")
def refresh(board):
    if board not in BOARDS:
        return error("Employer board not configured.", 404)
    if request.get_json(silent=True) != {}:
        return error("Send an empty JSON object; employer sources are configured on the server.", 400)
    try:
        result = refresh_board(board)
    except RefreshBusy as exc:
        return error(str(exc), 409)
    except SQLAlchemyError:
        db.session.rollback()
        current_app.logger.error("Could not save live job refresh")
        return error("Could not save this refresh. The previous cache is retained.", 503)
    # A handled provider failure returns a status object so the UI can show retained data.
    return {"status": "success", **result}


@jobs_bp.get("/<uuid:job_id>")
def item(job_id):
    record = db.session.get(LiveJob, str(job_id))
    if record is None or record.board not in BOARDS:
        return error("Posting not found.", 404)
    return {"status": "success", "job": record.to_dict(full=True),
            "board": sync_status(record.board, db.session.get(JobBoardSync, record.board))}


@jobs_bp.post("/<uuid:job_id>/compare")
def compare(job_id):
    body = request.get_json(silent=True)
    if not isinstance(body, dict) or set(body) != {"submission_id", "job_version", "mode"}:
        return error("Send only submission_id, job_version and mode.", 400)
    try:
        key = submission_id(body["submission_id"])
        if type(body["job_version"]) is not int or body["job_version"] < 1:
            raise ValueError("Choose a valid posting version.")
        if not isinstance(body["mode"], str) or body["mode"] not in {"keyword", "semantic"}:
            raise ValueError("Choose keyword or semantic comparison mode.")
    except ValueError as exc:
        return error(str(exc), 400)
    user_id = current_user_id()
    prior = existing_submission(user_id, key)
    if prior:
        source = prior.job
        if (source.get("source_type") != "greenhouse" or source.get("live_job_id") != str(job_id)
                or source.get("posting_version") != body["job_version"] or prior.result["mode"] != body["mode"]):
            return error("This request was already saved with different input. Open a new comparison.", 409)
        return {"status": "success", "comparison": prior.to_dict()}, 200
    record = db.session.get(LiveJob, str(job_id))
    if record is None or record.board not in BOARDS:
        return error("Posting not found.", 404)
    if not record.listed or record.version != body["job_version"]:
        return error("This posting changed or is no longer listed. Return to Live jobs and reopen it.", 409)
    listing = record.to_dict(full=True)
    job = {"title": record.title, "description": record.description, "source_url": record.source_url,
           "source_type": "greenhouse", "live_job_id": record.id, "board": record.board,
           "employer": listing["employer"], "provider_id": record.provider_id, "location": record.location,
           "posting_version": record.version, "content_hash": record.content_hash,
           "provider_updated_at": record.provider_updated_at, "last_seen_at": listing["last_seen_at"],
           "stale_at_comparison": listing["stale"], "source_captured_at": iso_utc(utc_now())}
    return save_comparison(user_id, key, job, body["mode"], max_fragments=300)
