"""Authenticated SQL assessment lifecycle, scoped to the current candidate."""

from flask import Blueprint, current_app, request
from flask_jwt_extended import get_jwt_identity, jwt_required
from sqlalchemy import func, select, update
from sqlalchemy.exc import SQLAlchemyError

from extensions import db
from models.assessment_attempt import AssessmentAttempt, utc_now
from models.skill import Skill
from models.user import User
from services.sql_assessment import ASSESSMENT, QUESTIONS, grade_answers, new_snapshot


assessments_bp = Blueprint("assessments", __name__, url_prefix="/api/assessments")


def error(message, code):
    return {"status": "error", "message": message}, code


def current_user_id():
    try:
        user_id = int(get_jwt_identity())
    except (TypeError, ValueError):
        return None
    return user_id if db.session.get(User, user_id) is not None else None


def owned_attempt(attempt_id, user_id):
    return db.session.execute(select(AssessmentAttempt).where(
        AssessmentAttempt.id == str(attempt_id), AssessmentAttempt.user_id == user_id
    )).scalar_one_or_none()


@assessments_bp.get("/sql")
@jwt_required()
def sql_description():
    if current_user_id() is None:
        return error("The candidate account is unavailable. Log in again.", 401)
    return {"status": "success", "assessment": {**ASSESSMENT, "question_count": len(QUESTIONS)}}


@assessments_bp.post("/sql/attempts")
@jwt_required()
def start_sql_attempt():
    user_id = current_user_id()
    if user_id is None:
        return error("The candidate account is unavailable. Log in again.", 401)
    if request.get_json(silent=True) != {}:
        return error("Send an empty JSON object {} to start an attempt.", 400)
    claims = db.session.execute(select(Skill).where(
        Skill.user_id == user_id, func.lower(func.trim(Skill.skill_name)) == "sql"
    )).scalars().all()
    attempt = AssessmentAttempt(
        user_id=user_id, skill_key=ASSESSMENT["skill_key"],
        assessment_version=ASSESSMENT["version"], question_snapshot=new_snapshot(),
        self_reported_claims=[
            {"skill_id": claim.id, "skill_name": claim.skill_name, "proficiency": claim.proficiency}
            for claim in claims
        ],
    )
    try:
        db.session.add(attempt)
        db.session.commit()
    except SQLAlchemyError:
        db.session.rollback()
        current_app.logger.exception("Could not start SQL assessment")
        return error("Could not save the assessment attempt.", 500)
    return {"status": "success", "attempt": attempt.to_dict()}, 201


@assessments_bp.get("/sql/attempts")
@jwt_required()
def list_sql_attempts():
    user_id = current_user_id()
    if user_id is None:
        return error("The candidate account is unavailable. Log in again.", 401)
    attempts = db.session.execute(select(AssessmentAttempt).where(
        AssessmentAttempt.user_id == user_id, AssessmentAttempt.skill_key == "sql"
    ).order_by(AssessmentAttempt.created_at.desc(), AssessmentAttempt.id.desc()).limit(50)).scalars().all()
    return {
        "status": "success", "limit": 50,
        "attempts": [attempt.to_dict(include_questions=False) for attempt in attempts],
    }


@assessments_bp.get("/attempts/<uuid:attempt_id>")
@jwt_required()
def get_attempt(attempt_id):
    user_id = current_user_id()
    if user_id is None:
        return error("The candidate account is unavailable. Log in again.", 401)
    attempt = owned_attempt(attempt_id, user_id)
    if attempt is None:
        return error("Assessment attempt not found.", 404)
    return {"status": "success", "attempt": attempt.to_dict()}


@assessments_bp.post("/attempts/<uuid:attempt_id>/submit")
@jwt_required()
def submit_attempt(attempt_id):
    user_id = current_user_id()
    if user_id is None:
        return error("The candidate account is unavailable. Log in again.", 401)
    attempt = owned_attempt(attempt_id, user_id)
    if attempt is None:
        return error("Assessment attempt not found.", 404)
    if attempt.submitted_at is not None:
        return error("This attempt has already been submitted. Start a new attempt to practise.", 409)
    body = request.get_json(silent=True)
    if not isinstance(body, dict) or set(body) != {"answers"}:
        return error("Send a JSON object containing only the answers list.", 400)
    try:
        result = grade_answers(attempt.question_snapshot["questions"], body["answers"])
    except ValueError as exception:
        return error(str(exception), 400)
    try:
        # Conditional update makes a completed attempt immutable, including retries.
        changed = db.session.execute(update(AssessmentAttempt).where(
            AssessmentAttempt.id == attempt.id, AssessmentAttempt.user_id == user_id,
            AssessmentAttempt.submitted_at.is_(None),
        ).values(answers=body["answers"], result=result, submitted_at=utc_now()))
        if changed.rowcount != 1:
            db.session.rollback()
            return error("This attempt has already been submitted.", 409)
        db.session.commit()
        db.session.refresh(attempt)
    except SQLAlchemyError:
        db.session.rollback()
        current_app.logger.exception("Could not submit SQL assessment")
        return error("Could not save the assessment result.", 500)
    return {"status": "success", "attempt": attempt.to_dict()}
