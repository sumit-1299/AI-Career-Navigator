"""
Skills API Endpoints.

Provides:
- GET /api/skills: Canonical search/autocomplete or student profile skills.
- GET /api/skills/search: Dedicated search endpoint.
- GET /api/skills/canonical/<id>: Canonical skill details.
- GET /api/skills/canonical/<id>/resources: Curated learning resources for canonical skill.
- POST /api/skills: Add skill to student profile with auto canonical linking.
- POST /api/skills/extract-resume: Extract, normalize, and canonically map skills from resume.
- POST /api/skills/extract-resume/apply: Apply extracted skills to student profile.
"""

from flask import Blueprint, jsonify, request
from flask_jwt_extended import get_jwt_identity, jwt_required
from sqlalchemy import or_

from extensions import db
from models.canonical_skill import CanonicalSkill
from models.skill import Skill
from models.skill_alias import SkillAlias
from services.learning_resource_service import LearningResourceService
from services.learning_progress_service import LearningProgressService
from services.resume_extraction_service import ResumeExtractionService
from utils.normalization import normalize_skill_name

skills_bp = Blueprint("skills", __name__, url_prefix="/api/skills")


def search_canonical_skills(query_text: str, limit: int = 10):
    """
    Search canonical skills by canonical_name, normalized_name, or aliases.
    Returns list of formatted skill dictionaries.
    """
    normalized_q = normalize_skill_name(query_text)
    if not normalized_q:
        return []

    # 1. Match directly on CanonicalSkill
    canonical_matches = (
        CanonicalSkill.query.filter(
            or_(
                CanonicalSkill.normalized_name.ilike(f"%{normalized_q}%"),
                CanonicalSkill.canonical_name.ilike(f"%{query_text}%"),
            )
        )
        .limit(limit)
        .all()
    )

    skill_dict = {s.id: s for s in canonical_matches}

    # 2. Match on SkillAlias
    if len(skill_dict) < limit:
        remaining = limit - len(skill_dict)
        alias_matches = (
            SkillAlias.query.filter(
                or_(
                    SkillAlias.normalized_alias.ilike(f"%{normalized_q}%"),
                    SkillAlias.alias_name.ilike(f"%{query_text}%"),
                )
            )
            .limit(remaining)
            .all()
        )

        for alias in alias_matches:
            if alias.canonical_skill and alias.canonical_skill_id not in skill_dict:
                skill_dict[alias.canonical_skill_id] = alias.canonical_skill
                if len(skill_dict) >= limit:
                    break

    # Format result records
    results = []
    for skill in skill_dict.values():
        aliases_info = [
            {
                "alias_name": a.alias_name,
                "source": a.data_source.source_name if a.data_source else None,
            }
            for a in skill.aliases
        ]

        results.append({
            "id": skill.id,
            "canonical_name": skill.canonical_name,
            "skill_name": skill.canonical_name,
            "skill_type": skill.skill_type,
            "description": skill.description,
            "aliases": aliases_info,
        })

    return results


@skills_bp.route("", methods=["GET"])
@jwt_required(optional=True)
def get_skills():
    """
    Get skills endpoint.
    - If query param 'q' or 'search' is provided: returns canonical skill search/autocomplete results (public).
    - If no query param: returns the authenticated student's profile skills (requires JWT).
    """
    query = request.args.get("q") or request.args.get("search")

    # 1. Search / Autocomplete flow
    if query is not None:
        limit = request.args.get("limit", default=10, type=int)
        if limit < 1:
            limit = 10
        elif limit > 50:
            limit = 50

        results = search_canonical_skills(query, limit=limit)
        return jsonify(results), 200

    # 2. Authenticated student profile skills flow
    user_id = get_jwt_identity()
    if not user_id:
        return jsonify({
            "status": "error",
            "message": "Missing Authorization Header",
        }), 401

    skills = Skill.query.filter_by(user_id=user_id).all()

    result = []
    for skill in skills:
        skill_data = {
            "id": skill.id,
            "skill_name": skill.skill_name,
            "proficiency": skill.proficiency,
            "canonical_skill_id": skill.canonical_skill_id,
        }
        if skill.canonical_skill:
            skill_data["canonical_name"] = skill.canonical_skill.canonical_name
            skill_data["skill_type"] = skill.canonical_skill.skill_type
        result.append(skill_data)

    return jsonify({
        "status": "success",
        "skills": result,
    }), 200


@skills_bp.route("/search", methods=["GET"])
def search_skills_endpoint():
    """Explicit endpoint for skill search and autocomplete."""
    query = request.args.get("q") or request.args.get("query") or ""
    limit = request.args.get("limit", default=10, type=int)

    if limit < 1:
        limit = 10
    elif limit > 50:
        limit = 50

    results = search_canonical_skills(query, limit=limit)
    return jsonify({
        "status": "success",
        "query": query,
        "count": len(results),
        "skills": results,
    }), 200


@skills_bp.route("/canonical/<int:skill_id>", methods=["GET"])
def get_canonical_skill_detail(skill_id):
    """Retrieve full details for a specific canonical skill."""
    skill = CanonicalSkill.query.get(skill_id)
    if not skill:
        return jsonify({
            "status": "error",
            "message": f"Canonical skill with id {skill_id} not found",
        }), 404

    aliases_info = [
        {
            "alias_name": a.alias_name,
            "source": a.data_source.source_name if a.data_source else None,
            "source_version": a.data_source.source_version if a.data_source else None,
        }
        for a in skill.aliases
    ]

    return jsonify({
        "status": "success",
        "canonical_skill": {
            "id": skill.id,
            "canonical_name": skill.canonical_name,
            "normalized_name": skill.normalized_name,
            "skill_type": skill.skill_type,
            "description": skill.description,
            "created_at": skill.created_at.isoformat() if skill.created_at else None,
            "aliases": aliases_info,
        },
    }), 200


@skills_bp.route("/canonical/<int:skill_id>/resources", methods=["GET"])
def get_canonical_skill_resources(skill_id):
    """Retrieve curated learning resources for a specific canonical skill."""
    skill = CanonicalSkill.query.get(skill_id)
    if not skill:
        return jsonify({
            "status": "error",
            "message": f"Canonical skill with id {skill_id} not found",
        }), 404

    difficulty = request.args.get("difficulty")
    resource_type = request.args.get("resource_type") or request.args.get("type")

    resources = LearningResourceService.get_resources_for_canonical_skill(
        canonical_skill_id=skill_id,
        difficulty_level=difficulty,
        resource_type=resource_type
    )

    return jsonify({
        "status": "success",
        "canonical_skill_id": skill_id,
        "canonical_name": skill.canonical_name,
        "count": len(resources),
        "resources": resources
    }), 200


@skills_bp.route("/canonical/<int:skill_id>/progress", methods=["GET"])
@jwt_required(optional=True)
def get_canonical_skill_progress(skill_id):
    """Retrieve student's learning progress for resources linked to a specific canonical skill."""
    user_id = get_jwt_identity()
    if not user_id:
        param_user = request.args.get("user_id", type=int)
        if param_user:
            user_id = str(param_user)

    if not user_id:
        return jsonify({
            "status": "error",
            "message": "Authentication or user_id is required"
        }), 401

    skill = CanonicalSkill.query.get(skill_id)
    if not skill:
        return jsonify({
            "status": "error",
            "message": f"Canonical skill with id {skill_id} not found"
        }), 404

    progress_list = LearningProgressService.get_progress_for_skill(
        user_id=int(user_id),
        canonical_skill_id=skill_id
    )

    return jsonify({
        "status": "success",
        "canonical_skill_id": skill_id,
        "canonical_name": skill.canonical_name,
        "count": len(progress_list),
        "progress": progress_list
    }), 200


@skills_bp.route("", methods=["POST"])
@jwt_required()
def add_skill():
    """
    Add a skill to the authenticated student's profile.
    Automatically resolves and links canonical_skill_id if an exact match exists.
    """
    user_id = get_jwt_identity()

    data = request.get_json()
    if not data:
        return jsonify({
            "status": "error",
            "message": "Request body must be valid JSON",
        }), 400

    skill_name = data.get("skill_name")
    proficiency = data.get("proficiency")

    if not skill_name or proficiency is None:
        return jsonify({
            "status": "error",
            "message": "skill_name and proficiency are required",
        }), 400

    if not isinstance(proficiency, int) or proficiency < 1 or proficiency > 10:
        return jsonify({
            "status": "error",
            "message": "proficiency must be between 1 and 10",
        }), 400

    # Auto-resolve canonical_skill_id
    normalized = normalize_skill_name(skill_name)
    canonical_skill = CanonicalSkill.query.filter_by(normalized_name=normalized).first()
    canonical_id = None

    if canonical_skill:
        canonical_id = canonical_skill.id
    else:
        # Check aliases
        alias_record = SkillAlias.query.filter_by(normalized_alias=normalized).first()
        if alias_record:
            canonical_id = alias_record.canonical_skill_id

    skill = Skill(
        user_id=user_id,
        skill_name=skill_name,
        proficiency=proficiency,
        canonical_skill_id=canonical_id,
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
            "proficiency": skill.proficiency,
            "canonical_skill_id": skill.canonical_skill_id,
        },
    }), 201


@skills_bp.route("/extract-resume", methods=["POST"])
def extract_resume_skills():
    """
    Extract, normalize, and canonically map skills from resume text or uploaded file.
    Accepts:
    - JSON: {"resume_text": "..."}
    - Multipart: request.files['file']
    """
    resume_text = ""
    if request.is_json:
        data = request.get_json() or {}
        resume_text = data.get("resume_text", "")
    elif "file" in request.files:
        file = request.files["file"]
        if file and file.filename:
            file_bytes = file.read()
            try:
                resume_text = ResumeExtractionService.validate_and_extract_file(
                    filename=file.filename,
                    file_bytes=file_bytes
                )
            except ValueError as e:
                return jsonify({
                    "status": "error",
                    "message": str(e)
                }), 400
            except Exception as e:
                return jsonify({
                    "status": "error",
                    "message": f"Failed to extract text from file: {str(e)}"
                }), 400
    else:
        resume_text = request.form.get("resume_text", "")

    if not resume_text or not resume_text.strip():
        return jsonify({
            "status": "error",
            "message": "resume_text string or file upload is required"
        }), 400

    min_conf = request.args.get("min_confidence", default=0.70, type=float)
    result = ResumeExtractionService.extract_skills_from_text(
        resume_text=resume_text,
        min_confidence=min_conf
    )

    return jsonify(result), 200


@skills_bp.route("/extract-resume/apply", methods=["POST"])
@jwt_required(optional=True)
def apply_extracted_skills():
    """
    Persist approved extracted skills directly to a student's profile.
    Accepts:
    - JSON: {"skills": [...], "user_id": 1}
    """
    user_id = get_jwt_identity()
    data = request.get_json() or {}

    if not user_id:
        param_user = data.get("user_id") or request.args.get("user_id", type=int)
        if param_user:
            user_id = param_user

    if not user_id:
        return jsonify({
            "status": "error",
            "message": "Authentication or user_id is required"
        }), 401

    skills_data = data.get("skills", [])
    if not isinstance(skills_data, list):
        return jsonify({
            "status": "error",
            "message": "'skills' must be a list of skill objects"
        }), 400

    result = ResumeExtractionService.apply_skills_to_student_profile(
        user_id=int(user_id),
        skills_data=skills_data
    )

    return jsonify(result), 200


@skills_bp.route("/extract-resume/score", methods=["POST"])
@jwt_required()
def score_resume_skills():
    """
    Score resume content against a target career's requirements.
    Calculates ATS score, matched keywords, missing keywords, and alignment level.
    Accepts:
    - Query param or JSON body: career_id
    - JSON: {"resume_text": "...", "career_id": 1}
    - Multipart: request.files['file'] + career_id
    """
    # 1. Parse career_id
    career_id = request.args.get("career_id", type=int)
    if not career_id:
        if request.is_json:
            career_id = (request.get_json() or {}).get("career_id")
        elif request.form.get("career_id"):
            try:
                career_id = int(request.form.get("career_id"))
            except (ValueError, TypeError):
                career_id = None

    if not career_id:
        return jsonify({
            "status": "error",
            "message": "career_id is required"
        }), 400

    try:
        career_id = int(career_id)
    except (ValueError, TypeError):
        return jsonify({
            "status": "error",
            "message": "Invalid career_id provided"
        }), 400

    # 2. Parse resume text
    resume_text = ""
    if request.is_json:
        data = request.get_json() or {}
        resume_text = data.get("resume_text", "")
    elif "file" in request.files:
        file = request.files["file"]
        if file and file.filename:
            file_bytes = file.read()
            try:
                resume_text = ResumeExtractionService.validate_and_extract_file(
                    filename=file.filename,
                    file_bytes=file_bytes
                )
            except ValueError as e:
                return jsonify({
                    "status": "error",
                    "message": str(e)
                }), 400
            except Exception as e:
                return jsonify({
                    "status": "error",
                    "message": f"Failed to extract text from file: {str(e)}"
                }), 400
    else:
        resume_text = request.form.get("resume_text", "")

    if not resume_text or not resume_text.strip():
        return jsonify({
            "status": "error",
            "message": "resume_text string or file upload is required"
        }), 400

    # 3. Calculate ATS score and keywords analysis
    try:
        result = ResumeExtractionService.score_resume_against_career(
            resume_text=resume_text,
            career_id=career_id
        )
    except ValueError as e:
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 400

    if result is None:
        return jsonify({
            "status": "error",
            "message": f"Career with id {career_id} not found"
        }), 404

    return jsonify(result), 200

