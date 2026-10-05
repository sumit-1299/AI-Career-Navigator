"""
Career, Skill-Gap Analysis, Recommendation & Transition API Endpoints.

Provides:
- GET /api/careers: List all available career tracks.
- GET /api/careers/<id>: Retrieve single career details and requirements.
- GET /api/careers/<id>/skill-gap: Evaluate student profile vs career skill requirements.
- GET /api/careers/<id>/roadmap: Generate sequential learning roadmap and recommendations.
- GET /api/careers/recommendations: Multi-career recommendations ranked for student.
- GET /api/careers/<from_id>/transition/<to_id>: Comparative career transition analysis.
- POST /api/careers/transition: Comparative career transition analysis via POST body.
"""

from flask import Blueprint, jsonify, request
from flask_jwt_extended import get_jwt_identity, jwt_required

from extensions import db
from models.career import Career
from models.career_skill import CareerSkill
from models.skill import Skill
from services.career_recommendation_service import CareerRecommendationService
from services.career_transition_service import CareerTransitionService
from services.career_comparison_service import CareerComparisonService
from services.student_analytics_service import StudentAnalyticsService
from services.roadmap_service import generate_learning_roadmap
from services.skill_gap_service import assess_career_skill_gap

careers_bp = Blueprint("careers", __name__, url_prefix="/api/careers")


@careers_bp.route("", methods=["GET"])
def list_careers():
    """List all available standardized career tracks."""
    careers = Career.query.order_by(Career.title).all()

    result = []
    for c in careers:
        skills_count = len(c.skills) if hasattr(c, "skills") and c.skills else (
            CareerSkill.query.filter_by(career_id=c.id).count()
        )
        result.append({
            "id": c.id,
            "title": c.title,
            "domain": c.domain,
            "description": c.description,
            "total_required_skills": skills_count,
        })

    return jsonify({
        "status": "success",
        "count": len(result),
        "careers": result,
    }), 200


@careers_bp.route("/recommendations", methods=["GET"])
@jwt_required(optional=True)
def get_career_recommendations():
    """
    Generate ranked multi-career recommendations for a student.
    - If user is authenticated with JWT: uses student profile skills.
    - If user_id is provided in query params: uses that student's skills.
    - Otherwise evaluates with baseline/empty skill profile.
    - Optional filters: domain, limit.
    """
    user_id = get_jwt_identity()
    if not user_id:
        param_user = request.args.get("user_id", type=int)
        if param_user:
            user_id = str(param_user)

    student_skills = []
    if user_id:
        student_skills = Skill.query.filter_by(user_id=int(user_id)).all()

    domain = request.args.get("domain")
    limit = request.args.get("limit", type=int)

    recommendations = CareerRecommendationService.recommend_careers(
        student_skills=student_skills,
        domain_filter=domain,
        limit=limit
    )

    return jsonify({
        "status": "success",
        "user_id": int(user_id) if user_id else None,
        "count": len(recommendations),
        "recommendations": recommendations
    }), 200


@careers_bp.route("/<int:career_id>", methods=["GET"])
def get_career_detail(career_id):
    """Retrieve details for a specific career track, including its required skills."""
    career = Career.query.get(career_id)
    if not career:
        return jsonify({
            "status": "error",
            "message": f"Career with id {career_id} not found",
        }), 404

    career_skills = career.skills if hasattr(career, "skills") and career.skills else (
        CareerSkill.query.filter_by(career_id=career.id).all()
    )

    skills_data = [
        {
            "id": cs.id,
            "skill_name": cs.skill_name,
            "canonical_skill_id": cs.canonical_skill_id,
            "required_level": cs.required_level,
            "importance": cs.importance,
        }
        for cs in sorted(career_skills, key=lambda x: (-x.importance, -x.required_level, x.skill_name))
    ]

    return jsonify({
        "status": "success",
        "career": {
            "id": career.id,
            "title": career.title,
            "domain": career.domain,
            "description": career.description,
            "required_skills": skills_data,
        },
    }), 200


@careers_bp.route("/<int:career_id>/skill-gap", methods=["GET"])
@jwt_required(optional=True)
def get_career_skill_gap(career_id):
    """
    Evaluate student skills against a target career's requirements.
    - If user is authenticated with JWT: evaluates that student's skills.
    - If user_id is provided in query params: evaluates that user's skills.
    - Otherwise evaluates with an empty skill profile (baseline role analysis).
    """
    user_id = get_jwt_identity()
    if not user_id:
        param_user = request.args.get("user_id", type=int)
        if param_user:
            user_id = str(param_user)

    student_skills = []
    if user_id:
        student_skills = Skill.query.filter_by(user_id=int(user_id)).all()

    gap_analysis = assess_career_skill_gap(career_id, student_skills)
    if not gap_analysis:
        return jsonify({
            "status": "error",
            "message": f"Career with id {career_id} not found",
        }), 404

    pct = gap_analysis["summary"]["readiness_percentage"]
    category = "Advanced" if pct >= 80 else ("Proficient" if pct >= 60 else ("Developing" if pct >= 30 else "Novice"))

    response_payload = {
        "status": "success",
        "career": gap_analysis["career"]["title"],
        "career_name": gap_analysis["career"]["title"],
        "career_id": gap_analysis["career"]["id"],
        "domain": gap_analysis["career"]["domain"],
        "description": gap_analysis["career"]["description"],
        "total_required_skills": gap_analysis["summary"]["total_required_skills"],
        "total_career_skills": gap_analysis["summary"]["total_required_skills"],
        "matched": gap_analysis["summary"]["matched_skills"],
        "matched_count": gap_analysis["summary"]["matched_skills"],
        "weak": gap_analysis["summary"]["weak_skills"],
        "weak_count": gap_analysis["summary"]["weak_skills"],
        "missing": gap_analysis["summary"]["missing_skills"],
        "missing_count": gap_analysis["summary"]["missing_skills"],
        "readiness_percentage": pct,
        "readiness_score": pct,
        "readiness_category": category,
        "skill_gaps": gap_analysis["prioritized_skill_gaps"],
        "matched_skills": [
            {
                "name": s["skill_name"],
                "canonical_id": s.get("canonical_skill_id"),
                "student_level": s.get("current_proficiency", 0),
                "required_level": s.get("required_level", 0),
                "category": s.get("priority_level", "Core")
            }
            for s in gap_analysis["prioritized_skill_gaps"] if s.get("status") == "MATCHED"
        ],
        "weak_skills": [
            {
                "name": s["skill_name"],
                "canonical_id": s.get("canonical_skill_id"),
                "student_level": s.get("current_proficiency", 0),
                "required_level": s.get("required_level", 0),
                "category": s.get("priority_level", "Core")
            }
            for s in gap_analysis["prioritized_skill_gaps"] if s.get("status") == "WEAK"
        ],
        "missing_skills": [
            {
                "name": s["skill_name"],
                "canonical_id": s.get("canonical_skill_id"),
                "student_level": s.get("current_proficiency", 0),
                "required_level": s.get("required_level", 0),
                "category": s.get("priority_level", "Core")
            }
            for s in gap_analysis["prioritized_skill_gaps"] if s.get("status") == "MISSING"
        ],
    }

    return jsonify(response_payload), 200


@careers_bp.route("/<int:career_id>/roadmap", methods=["GET"])
@jwt_required(optional=True)
def get_career_roadmap(career_id):
    """
    Generate an explainable learning roadmap based on identified skill gaps,
    optionally incorporating weekly study intensity (5, 10, or 20 hours/week).
    """
    # 1. Study intensity validation
    hours_per_week_raw = request.args.get("hours_per_week")
    hours_per_week = None
    if hours_per_week_raw is not None:
        try:
            hours_per_week = int(hours_per_week_raw)
        except (ValueError, TypeError):
            return jsonify({
                "status": "error",
                "message": "Invalid study intensity. Supported values are 5, 10, or 20 hours per week."
            }), 400

        if hours_per_week not in [5, 10, 20]:
            return jsonify({
                "status": "error",
                "message": "Invalid study intensity. Supported values are 5, 10, or 20 hours per week."
            }), 400

    user_id = get_jwt_identity()
    if not user_id:
        param_user = request.args.get("user_id", type=int)
        if param_user:
            user_id = str(param_user)

    student_skills = []
    if user_id:
        student_skills = Skill.query.filter_by(user_id=int(user_id)).all()

    gap_analysis = assess_career_skill_gap(career_id, student_skills)
    if not gap_analysis:
        return jsonify({
            "status": "error",
            "message": f"Career with id {career_id} not found",
        }), 404

    roadmap = generate_learning_roadmap(
        gap_analysis["career"]["title"],
        gap_analysis["prioritized_skill_gaps"],
        hours_per_week=hours_per_week
    )

    response_payload = {
        "status": "success",
        "career_id": career_id,
        "readiness_percentage": gap_analysis["summary"]["readiness_percentage"],
        "roadmap": roadmap,
    }

    if hours_per_week is not None:
        response_payload["hours_per_week"] = roadmap.get("hours_per_week", hours_per_week)
        response_payload["estimated_total_hours"] = roadmap.get("estimated_total_hours", 0)
        response_payload["estimated_weeks"] = roadmap.get("estimated_weeks", 0)
        response_payload["estimated_completion_date"] = roadmap.get("estimated_completion_date")
        response_payload["weekly_milestones"] = roadmap.get("weekly_milestones", [])

    return jsonify(response_payload), 200


@careers_bp.route("/<int:from_id>/transition/<int:to_id>", methods=["GET"])
def get_career_transition(from_id, to_id):
    """
    Comparative career transition analysis between two careers.
    """
    result = CareerTransitionService.analyze_transition(from_id, to_id)
    if not result:
        return jsonify({
            "status": "error",
            "message": f"One or both career IDs ({from_id}, {to_id}) not found"
        }), 404

    return jsonify({
        "status": "success",
        "transition": result
    }), 200


@careers_bp.route("/compare", methods=["GET", "POST"])
@jwt_required(optional=True)
def compare_careers():
    """
    Side-by-side career comparison between two careers.
    Evaluates:
    - Common Skills
    - Career A Only
    - Career B Only
    - Student Already Has
    - Student Missing
    - Overlap percentage, readiness percentages, and acquisition distances.
    Accepts:
    - GET params: career_a_id, career_b_id, user_id (or via JWT)
    - POST body: {"career_a_id": 1, "career_b_id": 2, "user_id": 3}
    """
    user_id = get_jwt_identity()

    if request.method == "POST":
        data = request.get_json() or {}
        a_id = data.get("career_a_id") or data.get("career_a")
        b_id = data.get("career_b_id") or data.get("career_b")
        if not user_id and data.get("user_id"):
            user_id = str(data.get("user_id"))
    else:
        a_id = request.args.get("career_a_id", type=int) or request.args.get("career_a", type=int)
        b_id = request.args.get("career_b_id", type=int) or request.args.get("career_b", type=int)
        if not user_id:
            param_user = request.args.get("user_id", type=int)
            if param_user:
                user_id = str(param_user)

    if not a_id or not b_id:
        return jsonify({
            "status": "error",
            "message": "Both career_a_id and career_b_id are required"
        }), 400

    student_skills = []
    if user_id:
        student_skills = Skill.query.filter_by(user_id=int(user_id)).all()

    comparison = CareerComparisonService.compare_careers(
        career_a_id=int(a_id),
        career_b_id=int(b_id),
        student_skills=student_skills
    )

    if not comparison:
        return jsonify({
            "status": "error",
            "message": f"One or both career IDs ({a_id}, {b_id}) not found"
        }), 404

    return jsonify({
        "status": "success",
        "user_id": int(user_id) if user_id else None,
        "comparison": comparison
    }), 200


@careers_bp.route("/<int:career_id>/analytics", methods=["GET"])
@jwt_required(optional=True)
def get_career_analytics(career_id):
    """
    Retrieve student career readiness velocity and learning analytics for a target career.
    - Requires user identification via JWT or query parameter ?user_id=<id>.
    - Returns baseline vs current readiness, improvement, velocity, timeline, and remaining gaps.
    """
    user_id = get_jwt_identity()
    if not user_id:
        param_user = request.args.get("user_id", type=int)
        if param_user:
            user_id = str(param_user)

    if not user_id:
        return jsonify({
            "status": "error",
            "message": "user_id is required for student analytics (provide JWT or ?user_id=<id>)"
        }), 400

    analytics = StudentAnalyticsService.get_student_career_analytics(
        user_id=int(user_id),
        career_id=career_id
    )

    if not analytics:
        return jsonify({
            "status": "error",
            "message": f"Career with id {career_id} or user {user_id} not found"
        }), 404

    return jsonify({
        "status": "success",
        "analytics": analytics
    }), 200


@careers_bp.route("/analytics", methods=["GET"])
@jwt_required(optional=True)
def get_general_career_analytics():
    """
    Alternative endpoint for student career readiness analytics via query params.
    Accepts: ?career_id=<id>&user_id=<id>
    """
    career_id = request.args.get("career_id", type=int)
    if not career_id:
        return jsonify({
            "status": "error",
            "message": "career_id query parameter is required"
        }), 400

    return get_career_analytics(career_id)


@careers_bp.route("/transition", methods=["POST"])
def post_career_transition():
    """
    Comparative career transition analysis via POST body.
    Expects: {"from_career_id": 1, "to_career_id": 6}
    """
    data = request.get_json() or {}
    from_id = data.get("from_career_id") or data.get("source_career_id")
    to_id = data.get("to_career_id") or data.get("target_career_id")

    if not from_id or not to_id:
        return jsonify({
            "status": "error",
            "message": "Both from_career_id and to_career_id are required"
        }), 400

    result = CareerTransitionService.analyze_transition(int(from_id), int(to_id))
    if not result:
        return jsonify({
            "status": "error",
            "message": f"One or both career IDs ({from_id}, {to_id}) not found"
        }), 404

    return jsonify({
        "status": "success",
        "transition": result
    }), 200
