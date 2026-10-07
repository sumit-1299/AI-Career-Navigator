"""Live tech jobs and skill alignment API routes.

Provides:
- GET /api/jobs: Query and filter live tech employer vacancies from Greenhouse, Ashby, and Lever feeds.
- GET /api/jobs/<source_key>/<path:provider_id>: Detailed posting view with normalized description.
- POST /api/jobs/<source_key>/<path:provider_id>/match: Compare vacancy requirements against candidate skills.
- POST /api/jobs/match-custom: Match candidate skills against any custom job description.
- GET /api/jobs/sources: Metadata and status of configured employer boards.
- GET /api/jobs/diagnostics/sql: 6-question SQL foundations diagnostic question bank.
- POST /api/jobs/diagnostics/sql/evaluate: Deterministic evaluation and topic breakdown of SQL answers.
"""

from typing import List, Optional
from flask import Blueprint, jsonify, request
from flask_jwt_extended import get_jwt_identity, verify_jwt_in_request

from extensions import db
from models.skill import Skill
from services.live_jobs_service import LiveJobsService
from services.sql_assessment_service import SqlAssessmentService

jobs_bp = Blueprint("jobs", __name__, url_prefix="/api/jobs")


def _resolve_user_skills(req_payload: Optional[dict] = None) -> List[str]:
    """Retrieve skills from authenticated user profile or from request payload."""
    skills = []
    # 1. Check if provided in payload
    if req_payload and isinstance(req_payload, dict):
        custom = req_payload.get("skills") or req_payload.get("custom_skills")
        if isinstance(custom, list):
            return [str(s).strip() for s in custom if str(s).strip()]

    # 2. Check JWT identity
    try:
        verify_jwt_in_request(optional=True)
        user_id = get_jwt_identity()
        if user_id:
            user_skill_records = Skill.query.filter_by(user_id=int(user_id)).all()
            for s in user_skill_records:
                if s.skill_name and s.skill_name.strip():
                    skills.append(s.skill_name.strip())
    except Exception:
        pass

    return skills


@jobs_bp.route("", methods=["GET"])
@jobs_bp.route("/", methods=["GET"])
def list_jobs():
    """List live technology vacancies with search filters and pagination."""
    query = request.args.get("q", request.args.get("query", "")).strip()
    location = request.args.get("location", "").strip()
    work_mode = request.args.get("work_mode", "").strip()
    experience = request.args.get("experience", "").strip()
    technology = request.args.get("technology", request.args.get("tech", "")).strip()
    provider = request.args.get("provider", "").strip()
    source_key = request.args.get("source_key", "").strip()

    try:
        page = int(request.args.get("page", 1))
        page_size = int(request.args.get("page_size", 10))
    except (ValueError, TypeError):
        return jsonify({"status": "error", "message": "page and page_size must be integers"}), 400

    if page < 1 or page_size < 1:
        return jsonify({"status": "error", "message": "page and page_size must be positive"}), 400

    results = LiveJobsService.search_jobs(
        query=query,
        location=location,
        work_mode=work_mode,
        experience=experience,
        technology=technology,
        provider=provider,
        source_key=source_key,
        page=page,
        page_size=page_size,
    )
    return jsonify(results), 200


@jobs_bp.route("/sources", methods=["GET"])
def list_sources():
    """Return configured employer board sources and registry."""
    registry = LiveJobsService.get_source_registry()
    sources_list = [
        {
            "source_key": k,
            "employer": v["label"],
            "provider": v["provider"],
            "board_url": v["board_url"],
        }
        for k, v in registry.items()
    ]
    return jsonify({
        "status": "success",
        "total_sources": len(sources_list),
        "sources": sorted(sources_list, key=lambda s: s["employer"]),
    }), 200


@jobs_bp.route("/<source_key>/<path:provider_id>", methods=["GET"])
def get_job_detail(source_key, provider_id):
    """Retrieve full details of a specific live job posting."""
    if source_key not in LiveJobsService.get_source_registry():
        return jsonify({"status": "error", "message": f"Source '{source_key}' not found"}), 404

    job_data = LiveJobsService.get_job(source_key, provider_id)
    if not job_data:
        return jsonify({"status": "error", "message": f"Job '{provider_id}' not found in source '{source_key}'"}), 404

    return jsonify(job_data), 200


@jobs_bp.route("/<source_key>/<path:provider_id>/match", methods=["POST"])
def match_job(source_key, provider_id):
    """Match candidate skills against a specific live employer posting."""
    if source_key not in LiveJobsService.get_source_registry():
        return jsonify({"status": "error", "message": f"Source '{source_key}' not found"}), 404

    job_data = LiveJobsService.get_job(source_key, provider_id)
    if not job_data or not job_data.get("job"):
        return jsonify({"status": "error", "message": "Job posting could not be found"}), 404

    payload = request.get_json(silent=True) or {}
    skills = _resolve_user_skills(payload)

    match_result = LiveJobsService.match_job_to_skills(job_data["job"], skills)
    return jsonify(match_result), 200


@jobs_bp.route("/<source_key>/<path:provider_id>/action-center", methods=["GET", "POST"])
def get_job_action_center(source_key, provider_id):
    """Retrieve synthesized Career Action Center intelligence for a specific live job."""
    if source_key not in LiveJobsService.get_source_registry():
        return jsonify({"status": "error", "message": f"Source '{source_key}' not found"}), 404

    payload = request.get_json(silent=True) if request.method == "POST" else {}
    if not payload and request.args:
        payload = request.args.to_dict()

    skills = _resolve_user_skills(payload)

    # Resolve user identity if authenticated
    user_id = None
    try:
        verify_jwt_in_request(optional=True)
        identity = get_jwt_identity()
        if identity:
            user_id = int(identity)
    except Exception:
        pass

    from_career_id = request.args.get("from_career_id", type=int)
    if not from_career_id and payload:
        try:
            from_career_id = int(payload.get("from_career_id"))
        except (ValueError, TypeError):
            from_career_id = None

    from services.job_action_center_service import JobActionCenterService
    result = JobActionCenterService.get_action_center(
        source_key=source_key,
        provider_id=provider_id,
        user_id=user_id,
        custom_skills=skills if skills else None,
        from_career_id=from_career_id,
    )

    if result.get("status") == "error":
        status_code = 404 if result.get("error") == "NOT_FOUND" else 400
        return jsonify(result), status_code

    return jsonify(result), 200


@jobs_bp.route("/match-custom", methods=["POST"])
def match_custom_job():
    """Match candidate skills against any custom/pasted job description."""
    payload = request.get_json(silent=True) or {}
    title = str(payload.get("job_title", "Custom Job")).strip()
    description = str(payload.get("job_description", "")).strip()

    if not description:
        return jsonify({"status": "error", "message": "job_description is required"}), 400

    from services.live_jobs_service import classify_tech_job
    classification = classify_tech_job(title, description)

    job_obj = {
        "provider_id": "custom-input",
        "title": title,
        "employer": str(payload.get("employer", "Custom Employer")),
        "description": description,
        "work_mode": classification["work_mode"],
        "experience_level": classification["experience_level"],
        "tech_tags": classification["tech_tags"],
    }

    skills = _resolve_user_skills(payload)
    match_result = LiveJobsService.match_job_to_skills(job_obj, skills)
    return jsonify(match_result), 200


# Technical Diagnostics Endpoints
@jobs_bp.route("/diagnostics/sql", methods=["GET"])
def get_sql_diagnostic():
    """Return SQL foundations diagnostic questions."""
    assessment = SqlAssessmentService.get_assessment(include_solutions=False)
    return jsonify(assessment), 200


@jobs_bp.route("/diagnostics/sql/evaluate", methods=["POST"])
def evaluate_sql_diagnostic():
    """Evaluate submitted SQL answers."""
    payload = request.get_json(silent=True) or {}
    answers = payload.get("answers", {})
    if not isinstance(answers, dict):
        return jsonify({"status": "error", "message": "answers must be a JSON object mapping question_id to option_id"}), 400

    result = SqlAssessmentService.evaluate(answers)
    return jsonify(result), 200
