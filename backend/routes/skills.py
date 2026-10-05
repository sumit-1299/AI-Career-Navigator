from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity

from extensions import db
from models.skill import Skill
from routes.assessments import current_user_id, error

skills_bp = Blueprint("skills", __name__, url_prefix="/api/skills")


@skills_bp.route("", methods=["POST"])
@jwt_required()
def add_skill():
    user_id = current_user_id()
    if user_id is None:
        return error("The candidate account is unavailable. Log in again.", 401)
    data = request.get_json(silent=True)
    if not isinstance(data, dict) or set(data) != {"skill_name", "proficiency"}:
        return error("Send only skill_name and proficiency.", 400)

    skill_name = data.get("skill_name")
    proficiency = data.get("proficiency")

    if not isinstance(skill_name, str) or not 1 <= len(skill_name.strip()) <= 80:
        return jsonify({
            "status": "error",
            "message": "Enter a skill name of 1–80 characters."
        }), 400

    if type(proficiency) is not int or proficiency < 1 or proficiency > 10:
        return jsonify({
            "status": "error",
            "message": "proficiency must be between 1 and 10"
        }), 400

    skill = Skill(
        user_id=user_id,
        skill_name=skill_name.strip(),
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


@skills_bp.delete("/<int:skill_id>")
@jwt_required()
def remove_skill(skill_id):
    user_id = current_user_id()
    if user_id is None:
        return error("The candidate account is unavailable. Log in again.", 401)
    skill = db.session.get(Skill, skill_id)
    if skill is None or skill.user_id != user_id:
        return error("Skill rating not found.", 404)
    db.session.delete(skill)
    db.session.commit()
    return {"status": "success"}
