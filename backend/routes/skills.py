from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity

from extensions import db
from models.skill import Skill

skills_bp = Blueprint("skills", __name__, url_prefix="/api/skills")


@skills_bp.route("", methods=["POST"])
@jwt_required()
def add_skill():
    user_id = get_jwt_identity()

    data = request.get_json()

    skill_name = data.get("skill_name")
    proficiency = data.get("proficiency")

    if not skill_name or proficiency is None:
        return jsonify({
            "status": "error",
            "message": "skill_name and proficiency are required"
        }), 400

    if not isinstance(proficiency, int) or proficiency < 1 or proficiency > 10:
        return jsonify({
            "status": "error",
            "message": "proficiency must be between 1 and 10"
        }), 400

    skill = Skill(
        user_id=user_id,
        skill_name=skill_name,
        proficiency=proficiency
    )

    db.session.add(skill)
    db.session.commit()

    return jsonify({
        "status": "success",
        "message": "Skill added successfully",
        "skill": {
            "id": skill.id,
            "user_id": skill.user_id,
            "skill_name": skill.skill_name,
            "proficiency": skill.proficiency
        }
    }), 201
@skills_bp.route("", methods=["GET"])
@jwt_required()
def get_skills():

    user_id = get_jwt_identity()

    skills = Skill.query.filter_by(user_id=user_id).all()

    result = []

    for skill in skills:
        result.append({
            "id": skill.id,
            "skill_name": skill.skill_name,
            "proficiency": skill.proficiency
        })

    return jsonify({
        "status": "success",
        "skills": result
    }), 200