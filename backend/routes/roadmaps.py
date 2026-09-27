"""Candidate-owned roadmaps with idempotent creation and explicit progress updates."""

from flask import Blueprint, current_app, request
from flask_jwt_extended import jwt_required
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError, SQLAlchemyError

from extensions import db
from models.assessment_attempt import utc_now
from models.learning_roadmap import LearningRoadmap
from routes.assessments import current_user_id, error, owned_attempt
from services.learning_roadmap import build_roadmap


roadmaps_bp = Blueprint("roadmaps", __name__, url_prefix="/api/roadmaps")


def roadmap_for_attempt(attempt_id, user_id):
    return db.session.execute(select(LearningRoadmap).where(
        LearningRoadmap.attempt_id == str(attempt_id), LearningRoadmap.user_id == user_id
    )).scalar_one_or_none()


@roadmaps_bp.route("/attempts/<uuid:attempt_id>", methods=["GET", "POST"])
@jwt_required()
def attempt_roadmap(attempt_id):
    user_id = current_user_id()
    if user_id is None:
        return error("The candidate account is unavailable. Log in again.", 401)
    attempt = owned_attempt(attempt_id, user_id)
    if attempt is None:
        return error("Assessment attempt not found.", 404)
    if request.method == "POST" and request.get_json(silent=True) != {}:
        return error("Send an empty JSON object {} to create or reopen a roadmap.", 400)
    roadmap = roadmap_for_attempt(attempt.id, user_id)
    if request.method == "GET":
        return {"status": "success", "roadmap": roadmap.to_dict() if roadmap else None}
    if roadmap:
        return {"status": "success", "roadmap": roadmap.to_dict()}, 200
    if attempt.submitted_at is None or attempt.result is None:
        return error("Submit the assessment before creating a learning roadmap.", 409)
    if attempt.skill_key != "sql":
        return error("A resource catalogue is not available for this assessment skill.", 409)
    roadmap = LearningRoadmap(
        attempt_id=attempt.id, user_id=user_id,
        snapshot=build_roadmap(
            attempt.result, attempt.assessment_version,
            attempt.question_snapshot["metadata"]["scoring_version"],
        ), progress={},
    )
    try:
        db.session.add(roadmap)
        db.session.commit()
    except IntegrityError:
        # The unique attempt_id also protects against two tabs creating at once.
        db.session.rollback()
        existing = roadmap_for_attempt(attempt_id, user_id)
        if existing:
            return {"status": "success", "roadmap": existing.to_dict()}, 200
        current_app.logger.exception("Could not create learning roadmap")
        return error("Could not save the learning roadmap.", 500)
    except SQLAlchemyError:
        db.session.rollback()
        current_app.logger.exception("Could not create learning roadmap")
        return error("Could not save the learning roadmap.", 500)
    return {"status": "success", "roadmap": roadmap.to_dict()}, 201


@roadmaps_bp.patch("/<uuid:roadmap_id>/progress")
@jwt_required()
def update_progress(roadmap_id):
    user_id = current_user_id()
    if user_id is None:
        return error("The candidate account is unavailable. Log in again.", 401)
    body = request.get_json(silent=True)
    if (not isinstance(body, dict) or set(body) != {"step_id", "completed"}
            or not isinstance(body["step_id"], str) or type(body["completed"]) is not bool):
        return error("Send only a string step_id and a boolean completed value.", 400)
    try:
        # PostgreSQL serializes changes to this row, preventing lost updates when
        # separate tabs update different steps. SQLite tests do not validate locks.
        roadmap = db.session.execute(select(LearningRoadmap).where(
            LearningRoadmap.id == str(roadmap_id), LearningRoadmap.user_id == user_id
        ).with_for_update()).scalar_one_or_none()
        if roadmap is None:
            return error("Learning roadmap not found.", 404)
        if body["step_id"] not in {step["id"] for step in roadmap.snapshot["steps"]}:
            return error("That step is not part of this saved roadmap.", 400)
        progress = dict(roadmap.progress)
        if progress.get(body["step_id"], {}).get("completed", False) != body["completed"]:
            progress[body["step_id"]] = {
                "completed": body["completed"], "updated_at": utc_now().isoformat(),
            }
            roadmap.progress = progress
        db.session.commit()
    except SQLAlchemyError:
        db.session.rollback()
        current_app.logger.exception("Could not update roadmap activity")
        return error("Could not save your learning activity.", 500)
    return {"status": "success", "roadmap": roadmap.to_dict()}
