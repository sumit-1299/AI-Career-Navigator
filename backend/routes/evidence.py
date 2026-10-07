"""Owner-scoped evidence records with retry-safe creation and stale-edit protection."""

from flask import Blueprint, current_app, request
from flask_jwt_extended import jwt_required
from sqlalchemy import select, update
from sqlalchemy.exc import IntegrityError, SQLAlchemyError

from extensions import db
from models.assessment_attempt import utc_now
from models.candidate_evidence import CandidateEvidence
from routes.assessments import current_user_id, error
from services.candidate_evidence import submission_id, valid_version, validate_details


evidence_bp = Blueprint("evidence", __name__, url_prefix="/api/evidence")


@evidence_bp.after_request
def private_response(response):
    response.headers["Cache-Control"] = "no-store"
    return response


def owned_record(evidence_id, user_id):
    return db.session.execute(select(CandidateEvidence).where(
        CandidateEvidence.id == str(evidence_id), CandidateEvidence.user_id == user_id
    )).scalar_one_or_none()


def prior_submission(user_id, key):
    return db.session.execute(select(CandidateEvidence).where(
        CandidateEvidence.user_id == user_id, CandidateEvidence.submission_id == key
    )).scalar_one_or_none()


def creation_response(record, details):
    if record.details != details or record.archived:
        return error("This submission was already saved and later changed. Reopen My evidence to view it.", 409)
    return {"status": "success", "evidence": record.to_dict()}, 200


@evidence_bp.route("", methods=["GET", "POST"])
@jwt_required()
def evidence_collection():
    user_id = current_user_id()
    if user_id is None:
        return error("The candidate account is unavailable. Log in again.", 401)
    if request.method == "GET":
        records = db.session.execute(select(CandidateEvidence).where(
            CandidateEvidence.user_id == user_id
        ).order_by(CandidateEvidence.updated_at.desc(), CandidateEvidence.id.desc())).scalars().all()
        return {"status": "success", "evidence": [record.to_dict() for record in records]}
    body = request.get_json(silent=True)
    try:
        details = validate_details(body, "submission_id")
        key = submission_id(body["submission_id"])
    except ValueError as exception:
        return error(str(exception), 400)
    existing = prior_submission(user_id, key)
    if existing is not None:
        return creation_response(existing, details)
    record = CandidateEvidence(user_id=user_id, submission_id=key, details=details)
    try:
        db.session.add(record)
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        existing = prior_submission(user_id, key)
        if existing is not None:
            return creation_response(existing, details)
        current_app.logger.error("Evidence creation failed integrity checks")
        return error("Could not save evidence. Please try again.", 500)
    except SQLAlchemyError:
        db.session.rollback()
        current_app.logger.error("Evidence creation failed")
        return error("Could not save evidence. Please try again.", 500)
    return {"status": "success", "evidence": record.to_dict()}, 201


def save_change(record, user_id, version, changes):
    if not valid_version(version):
        return error("Send the positive integer version of the evidence you opened.", 400)
    try:
        changed = db.session.execute(update(CandidateEvidence).where(
            CandidateEvidence.id == record.id, CandidateEvidence.user_id == user_id,
            CandidateEvidence.version == version,
        ).values(**changes, version=version + 1, updated_at=utc_now()))
        if changed.rowcount != 1:
            db.session.rollback()
            return error("This evidence changed since you opened it. Copy any unsaved text, then reopen My evidence and try again.", 409)
        db.session.commit()
        db.session.refresh(record)
    except SQLAlchemyError:
        db.session.rollback()
        current_app.logger.error("Evidence update failed")
        return error("Could not update evidence. Please try again.", 500)
    return {"status": "success", "evidence": record.to_dict()}


@evidence_bp.route("/<uuid:evidence_id>", methods=["GET", "PUT"])
@jwt_required()
def evidence_item(evidence_id):
    user_id = current_user_id()
    if user_id is None:
        return error("The candidate account is unavailable. Log in again.", 401)
    record = owned_record(evidence_id, user_id)
    if record is None:
        return error("Evidence not found.", 404)
    if request.method == "GET":
        return {"status": "success", "evidence": record.to_dict()}
    body = request.get_json(silent=True)
    try:
        details = validate_details(body, "version")
    except ValueError as exception:
        return error(str(exception), 400)
    if details["kind"] != record.details["kind"]:
        return error("Evidence type cannot be changed. Add a separate submission.", 400)
    if record.archived:
        return error("Restore this evidence before editing it.", 409)
    return save_change(record, user_id, body["version"], {"details": details})


@evidence_bp.patch("/<uuid:evidence_id>/archive")
@jwt_required()
def archive_evidence(evidence_id):
    user_id = current_user_id()
    if user_id is None:
        return error("The candidate account is unavailable. Log in again.", 401)
    record = owned_record(evidence_id, user_id)
    if record is None:
        return error("Evidence not found.", 404)
    body = request.get_json(silent=True)
    if not isinstance(body, dict) or set(body) != {"version", "archived"} or type(body["archived"]) is not bool:
        return error("Send only version and a true/false archived value.", 400)
    return save_change(record, user_id, body["version"], {"archived": body["archived"]})
