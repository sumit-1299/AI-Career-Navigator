from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required, get_jwt_identity

from extensions import db
from models.student_profile import StudentProfile


profile_bp = Blueprint(
    "profile",
    __name__,
    url_prefix="/api/profile"
)


def _format_profile_response(profile):
    """Format student profile with backward-compatible aliases."""
    return {
        "id": profile.id,
        "user_id": profile.user_id,
        "education": profile.education,
        "education_level": profile.education,
        "specialization": profile.specialization,
        "major": profile.specialization,
        "graduation_year": profile.graduation_year,
        "cgpa": profile.cgpa
    }


@profile_bp.route("", methods=["GET"])
@jwt_required(optional=True)
def get_profile():
    """Retrieve authenticated student's profile."""
    user_id = get_jwt_identity()
    if not user_id:
        param_user = request.args.get("user_id", type=int)
        if param_user:
            user_id = str(param_user)

    if not user_id:
        return jsonify({
            "status": "error",
            "message": "Missing Authorization Header"
        }), 401

    profile = StudentProfile.query.filter_by(user_id=int(user_id)).first()
    if not profile:
        return jsonify({
            "status": "success",
            "profile": None,
            "message": "Profile not found"
        }), 200

    return jsonify({
        "status": "success",
        "profile": _format_profile_response(profile)
    }), 200


@profile_bp.route("", methods=["POST"])
@jwt_required()
def create_profile():
    """Create initial student profile."""
    user_id = get_jwt_identity()
    data = request.get_json() or {}

    education = data.get("education") or data.get("education_level")
    specialization = data.get("specialization") or data.get("major")
    graduation_year = data.get("graduation_year")
    cgpa = data.get("cgpa")

    if not education:
        return jsonify({
            "status": "error",
            "message": "Education is required"
        }), 400

    existing_profile = StudentProfile.query.filter_by(
        user_id=int(user_id)
    ).first()

    if existing_profile:
        return jsonify({
            "status": "error",
            "message": "Profile already exists"
        }), 409

    profile = StudentProfile(
        user_id=int(user_id),
        education=education,
        specialization=specialization,
        graduation_year=int(graduation_year) if graduation_year else None,
        cgpa=float(cgpa) if cgpa is not None else None
    )

    db.session.add(profile)
    db.session.commit()

    return jsonify({
        "status": "success",
        "message": "Student profile created successfully",
        "profile": _format_profile_response(profile)
    }), 201


@profile_bp.route("", methods=["PUT"])
@jwt_required(optional=True)
def update_profile():
    """Create or update student profile."""
    user_id = get_jwt_identity()
    data = request.get_json() or {}

    if not user_id:
        param_user = data.get("user_id") or request.args.get("user_id", type=int)
        if param_user:
            user_id = str(param_user)

    if not user_id:
        return jsonify({
            "status": "error",
            "message": "Missing Authorization Header"
        }), 401

    education = data.get("education") or data.get("education_level")
    specialization = data.get("specialization") or data.get("major")
    graduation_year = data.get("graduation_year")
    cgpa = data.get("cgpa")

    profile = StudentProfile.query.filter_by(user_id=int(user_id)).first()

    if profile:
        if education is not None:
            profile.education = education
        if specialization is not None:
            profile.specialization = specialization
        if graduation_year is not None:
            profile.graduation_year = int(graduation_year) if graduation_year else None
        if cgpa is not None:
            profile.cgpa = float(cgpa) if cgpa is not None else None
        message = "Student profile updated successfully"
    else:
        profile = StudentProfile(
            user_id=int(user_id),
            education=education or "Not specified",
            specialization=specialization,
            graduation_year=int(graduation_year) if graduation_year else None,
            cgpa=float(cgpa) if cgpa is not None else None
        )
        db.session.add(profile)
        message = "Student profile created successfully"

    db.session.commit()

    return jsonify({
        "status": "success",
        "message": message,
        "profile": _format_profile_response(profile)
    }), 200
