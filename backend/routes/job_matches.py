"""Authenticated, immutable comparisons. No outbound job or model fetches."""

from copy import deepcopy
from flask import Blueprint, current_app, request
from flask_jwt_extended import jwt_required
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError, SQLAlchemyError

from extensions import db
from models.assessment_attempt import AssessmentAttempt, iso_utc, utc_now
from models.candidate_evidence import CandidateEvidence
from models.job_comparison import JobComparison
from models.skill import Skill
from routes.assessments import current_user_id, error
from services.candidate_evidence import source_url, submission_id, text_field
from services.job_matching import build_comparison
from services.semantic_encoder import SemanticUnavailable, model_status
from services.skill_catalog import CATALOG_VERSION, SKILLS

job_matches_bp = Blueprint("job_matches", __name__, url_prefix="/api/job-matches")


@job_matches_bp.after_request
def private_response(response):
    response.headers["Cache-Control"] = "no-store"
    return response


@job_matches_bp.get("/metadata")
@jwt_required()
def metadata():
    if current_user_id() is None:
        return error("The candidate account is unavailable. Log in again.", 401)
    return {"status": "success", "semantic_model": model_status(), "catalog_version": CATALOG_VERSION,
            "skills": [{"key": item["key"], "label": item["label"]} for item in SKILLS]}


def candidate_snapshot(user_id):
    skills = db.session.execute(select(Skill).where(Skill.user_id == user_id).order_by(Skill.id)).scalars().all()
    evidence = db.session.execute(select(CandidateEvidence).where(CandidateEvidence.user_id == user_id,
                                  CandidateEvidence.archived.is_(False)).order_by(CandidateEvidence.id)).scalars().all()
    # Latest submitted attempt, not the best score. An all-skipped latest attempt stays unassessed.
    attempt = db.session.execute(select(AssessmentAttempt).where(AssessmentAttempt.user_id == user_id,
                                 AssessmentAttempt.skill_key == "sql", AssessmentAttempt.submitted_at.is_not(None))
                                 .order_by(AssessmentAttempt.submitted_at.desc(), AssessmentAttempt.id.desc()).limit(1)).scalar_one_or_none()
    assessed = None
    if attempt:
        assessed = {"attempt_id": attempt.id, "assessment_version": attempt.assessment_version,
                    "submitted_at": iso_utc(attempt.submitted_at), "result": deepcopy(attempt.result)}
    return {"captured_at": iso_utc(utc_now()),
            "skills": [{"id": skill.id, "skill_name": skill.skill_name, "proficiency": skill.proficiency} for skill in skills],
            "evidence": [item.to_dict() for item in evidence], "sql_assessment": assessed}


def existing_submission(user_id, key):
    return db.session.execute(select(JobComparison).where(JobComparison.user_id == user_id,
                              JobComparison.submission_id == key)).scalar_one_or_none()


def repeat_response(record, job, mode):
    same_job = record.job == job
    if record.job.get("source_type") == job.get("source_type") == "greenhouse":
        # Retry identity is the immutable posting version, not the current fetch timestamp.
        same_job = all(record.job.get(key) == job.get(key) for key in ("live_job_id", "posting_version", "content_hash"))
    if not same_job or record.result["mode"] != mode:
        return error("This request was already saved with different input. Open a new comparison to change it.", 409)
    return {"status": "success", "comparison": record.to_dict()}, 200


@job_matches_bp.route("", methods=["GET", "POST"])
@jwt_required()
def comparisons():
    user_id = current_user_id()
    if user_id is None:
        return error("The candidate account is unavailable. Log in again.", 401)
    if request.method == "GET":
        records = db.session.execute(select(JobComparison).where(JobComparison.user_id == user_id)
                                     .order_by(JobComparison.created_at.desc(), JobComparison.id.desc()).limit(30)).scalars().all()
        return {"status": "success", "limit": 30, "comparisons": [record.to_dict(full=False) for record in records]}
    body = request.get_json(silent=True)
    if not isinstance(body, dict) or set(body) != {"submission_id", "title", "description", "source_url", "mode"}:
        return error("Send only submission_id, title, description, source_url and mode.", 400)
    try:
        key = submission_id(body["submission_id"])
        title = text_field(body["title"], "Job title", 160)
        description = text_field(body["description"], "Job description", 8000)
        if len(description) < 20:
            raise ValueError("Enter at least 20 characters of job description.")
        url = "" if body["source_url"] == "" else source_url(body["source_url"])
        mode = body["mode"]
        if not isinstance(mode, str) or mode not in {"keyword", "semantic"}:
            raise ValueError("Choose keyword or semantic comparison mode.")
    except ValueError as exception:
        return error(str(exception), 400)
    job = {"title": title, "description": description, "source_url": url, "source_type": "candidate_pasted"}
    return save_comparison(user_id, key, job, mode)


def save_comparison(user_id, key, job, mode, max_fragments=60):
    """Save the exact server-resolved job and candidate inputs for either source."""
    prior = existing_submission(user_id, key)
    if prior:
        return repeat_response(prior, job, mode)
    snapshot = candidate_snapshot(user_id)
    try:
        result = build_comparison(job["description"], snapshot, mode, max_fragments=max_fragments)
        if job["source_type"] == "greenhouse":
            result["policy_version"] = "live-job-comparison-v1"
            result["input_limits"] = {"max_fragments": max_fragments, "truncated": False}
    except SemanticUnavailable as exception:
        return error(str(exception), 503)
    except ValueError as exception:
        return error(str(exception), 400)
    except Exception:
        current_app.logger.error("Job comparison inference failed")
        return error("The comparison could not be completed. Your input has not been saved; try again or choose the keyword baseline.", 503)
    record = JobComparison(user_id=user_id, submission_id=key, job=job, candidate_snapshot=snapshot, result=result)
    try:
        db.session.add(record)
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        prior = existing_submission(user_id, key)
        if prior:
            return repeat_response(prior, job, mode)
        return error("Could not save the comparison. Please retry.", 500)
    except SQLAlchemyError:
        db.session.rollback()
        current_app.logger.error("Could not save job comparison")
        return error("Could not save the comparison. Please retry.", 500)
    return {"status": "success", "comparison": record.to_dict()}, 201


@job_matches_bp.get("/<uuid:comparison_id>")
@jwt_required()
def comparison_item(comparison_id):
    user_id = current_user_id()
    if user_id is None:
        return error("The candidate account is unavailable. Log in again.", 401)
    record = db.session.execute(select(JobComparison).where(JobComparison.id == str(comparison_id),
                                JobComparison.user_id == user_id)).scalar_one_or_none()
    if record is None:
        return error("Job comparison not found.", 404)
    return {"status": "success", "comparison": record.to_dict()}
