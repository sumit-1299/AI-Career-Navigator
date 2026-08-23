from flask import Blueprint, request
from flask_jwt_extended import jwt_required, get_jwt_identity

from extensions import db
from models.student_profile import StudentProfile


profile_bp = Blueprint(
    "profile",
    __name__,
    url_prefix="/api/profile"
)


@profile_bp.route("", methods=["POST"])
@jwt_required()
def create_profile():

    user_id = get_jwt_identity()

    data = request.get_json()

    education = data.get("education")
    specialization = data.get("specialization")
    graduation_year = data.get("graduation_year")
    cgpa = data.get("cgpa")

    if not education:
        return {
            "status": "error",
            "message": "Education is required"
        }, 400

    existing_profile = StudentProfile.query.filter_by(
        user_id=user_id
    ).first()

    if existing_profile:
        return {
            "status": "error",
            "message": "Profile already exists"
        }, 409

    profile = StudentProfile(
        user_id=user_id,
        education=education,
        specialization=specialization,
        graduation_year=graduation_year,
        cgpa=cgpa
    )

    db.session.add(profile)
    db.session.commit()

    return {
        "status": "success",
        "message": "Student profile created successfully",
        "profile": {
            "id": profile.id,
            "user_id": profile.user_id,
            "education": profile.education,
            "specialization": profile.specialization,
            "graduation_year": profile.graduation_year,
            "cgpa": profile.cgpa
        }
    }, 201