from flask import Blueprint, request
from flask_jwt_extended import jwt_required, get_jwt_identity

from extensions import db
from models.career_preference import CareerPreference

career_preferences_bp = Blueprint(
    "career_preferences",
    __name__,
    url_prefix="/api/career-preferences"
)


@career_preferences_bp.route("", methods=["POST"])
@jwt_required()
def create_or_update_preferences():

    user_id = get_jwt_identity()

    data = request.get_json()

    if not data:
        return {
            "status": "error",
            "message": "Request body is required"
        }, 400

    target_role = data.get("target_role")
    preferred_domain = data.get("preferred_domain")
    experience_level = data.get("experience_level")

    if not target_role or not preferred_domain or not experience_level:
        return {
            "status": "error",
            "message": "target_role, preferred_domain and experience_level are required"
        }, 400

    preference = CareerPreference.query.filter_by(
        user_id=user_id
    ).first()

    if preference:
        preference.target_role = target_role
        preference.preferred_domain = preferred_domain
        preference.experience_level = experience_level
        message = "Career preferences updated successfully"

    else:
        preference = CareerPreference(
            user_id=user_id,
            target_role=target_role,
            preferred_domain=preferred_domain,
            experience_level=experience_level
        )

        db.session.add(preference)
        message = "Career preferences saved successfully"

    db.session.commit()

    return {
        "status": "success",
        "message": message,
        "career_preferences": {
            "id": preference.id,
            "user_id": preference.user_id,
            "target_role": preference.target_role,
            "preferred_domain": preference.preferred_domain,
            "experience_level": preference.experience_level
        }
    }, 200


@career_preferences_bp.route("", methods=["GET"])
@jwt_required()
def get_preferences():

    user_id = get_jwt_identity()

    preference = CareerPreference.query.filter_by(
        user_id=user_id
    ).first()

    if not preference:
        return {
            "status": "error",
            "message": "Career preferences not found"
        }, 404

    return {
        "status": "success",
        "career_preferences": {
            "id": preference.id,
            "user_id": preference.user_id,
            "target_role": preference.target_role,
            "preferred_domain": preference.preferred_domain,
            "experience_level": preference.experience_level
        }
    }, 200