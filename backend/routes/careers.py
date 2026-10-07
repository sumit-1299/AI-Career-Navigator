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
from services.readiness_summary_service import ReadinessSummaryService
from services.career_pathway_service import CareerPathwayService
from services.career_simulator_service import CareerSimulatorService
from services.skill_roi_service import SkillRoiService
from services.portfolio_project_service import PortfolioProjectService
from services.academic_benchmark_service import AcademicBenchmarkService
from services.industry_demand_service import IndustryDemandService
from services.career_trajectory_service import CareerTrajectoryService
from services.interview_simulation_service import InterviewSimulationService
from services.recommendation_evaluation_service import RecommendationEvaluationService

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
    - If user is authenticated with JWT: uses student profile skills, career preferences,
      academic background, and market outlook for personalized multi-factor scoring (Module 9.1).
    - If user_id is provided in query params without JWT: falls back to skill-only recommendations (backward compatible).
    - Otherwise evaluates with baseline/empty skill profile.
    - Query parameters (limit, user_id) are strictly validated, returning HTTP 400 on malformed input.
    - Optional filters: domain, limit.
    """
    # 1. Validate query parameters
    raw_limit = request.args.get("limit")
    limit = None
    if raw_limit is not None:
        try:
            limit = int(raw_limit)
            if limit <= 0:
                return jsonify({
                    "status": "error",
                    "message": "limit must be a positive integer"
                }), 400
        except (ValueError, TypeError):
            return jsonify({
                "status": "error",
                "message": "limit must be a positive integer"
            }), 400

    raw_user_id = request.args.get("user_id")
    param_user_id = None
    if raw_user_id is not None:
        try:
            param_user_id = int(raw_user_id)
            if param_user_id <= 0:
                return jsonify({
                    "status": "error",
                    "message": "user_id must be a valid integer"
                }), 400
        except (ValueError, TypeError):
            return jsonify({
                "status": "error",
                "message": "user_id must be a valid integer"
            }), 400

    # 2. Authoritative identity resolution
    auth_identity = get_jwt_identity()
    if auth_identity:
        # Authenticated: JWT identity is strictly authoritative
        user_id = int(auth_identity)
        is_personalized = True
    elif param_user_id:
        # Unauthenticated: preserve backward compatibility for legacy queries
        user_id = param_user_id
        is_personalized = False
    else:
        user_id = None
        is_personalized = False

    student_skills = []
    if user_id:
        student_skills = Skill.query.filter_by(user_id=user_id).all()

    domain = request.args.get("domain")
    include_roi = request.args.get("include_roi", "").lower() in ["1", "true", "yes"]

    recommendations = CareerRecommendationService.recommend_careers(
        student_skills=student_skills,
        domain_filter=domain,
        limit=limit,
        user_id=user_id if is_personalized else None,
        is_personalized=is_personalized,
        include_roi=include_roi
    )

    response_data = {
        "status": "success",
        "user_id": user_id,
        "is_personalized": is_personalized,
        "count": len(recommendations),
        "recommendations": recommendations
    }
    if include_roi:
        response_data["include_roi"] = True

    return jsonify(response_data), 200



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


    # Additive Module 11.1 Skill ROI ranking
    include_roi = request.args.get("include_roi", "true").lower() in ["1", "true", "yes"]
    if include_roi:
        roi_res = SkillRoiService.rank_career_skill_rois(career_id, user_id=int(user_id) if user_id else None)
        response_payload["skill_roi_ranking"] = roi_res.get("ranked_skills", [])
        response_payload["quickest_win"] = roi_res.get("quickest_win")
        response_payload["highest_gain"] = roi_res.get("highest_gain")

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
    - Common Skills, Career A Only, Career B Only, Student Already Has, Student Missing
    - Overlap percentage, readiness percentages, and acquisition distances
    - Module 9.2: Market demand comparison, salary differential, study timeline delta,
      career transition difficulty classification, and O*NET transferable skills matrix.
    Accepts:
    - GET params: career_a_id, career_b_id, hours_per_week (5, 10, 20), user_id (or via JWT)
    - POST body: {"career_a_id": 1, "career_b_id": 2, "hours_per_week": 10, "user_id": 3}
    """
    auth_user_id = get_jwt_identity()
    user_id = auth_user_id

    if request.method == "POST":
        data = request.get_json() or {}
        a_id_raw = data.get("career_a_id") or data.get("career_a")
        b_id_raw = data.get("career_b_id") or data.get("career_b")
        if not user_id and data.get("user_id"):
            user_id = str(data.get("user_id"))
        hours_per_week_raw = data.get("hours_per_week")
    else:
        a_id_raw = request.args.get("career_a_id") or request.args.get("career_a")
        b_id_raw = request.args.get("career_b_id") or request.args.get("career_b")
        if not user_id:
            param_user = request.args.get("user_id")
            if param_user:
                user_id = str(param_user)
        hours_per_week_raw = request.args.get("hours_per_week")

    # 1. Validate career IDs
    if not a_id_raw or not b_id_raw:
        return jsonify({
            "status": "error",
            "message": "Both career_a_id and career_b_id are required"
        }), 400

    try:
        a_id = int(a_id_raw)
        b_id = int(b_id_raw)
        if a_id <= 0 or b_id <= 0:
            return jsonify({
                "status": "error",
                "message": "Both career_a_id and career_b_id must be valid positive integers"
            }), 400
    except (ValueError, TypeError):
        return jsonify({
            "status": "error",
            "message": "Both career_a_id and career_b_id must be valid positive integers"
        }), 400

    # 2. Validate study intensity (hours_per_week)
    hours_per_week = 10
    if hours_per_week_raw is not None:
        try:
            hpw_val = int(hours_per_week_raw)
            if hpw_val not in [5, 10, 20]:
                return jsonify({
                    "status": "error",
                    "message": "Invalid study intensity. Supported values are 5, 10, or 20 hours per week."
                }), 400
            hours_per_week = hpw_val
        except (ValueError, TypeError):
            return jsonify({
                "status": "error",
                "message": "Invalid study intensity. Supported values are 5, 10, or 20 hours per week."
            }), 400

    student_skills = []
    if user_id:
        try:
            student_skills = Skill.query.filter_by(user_id=int(user_id)).all()
        except Exception:
            student_skills = []

    comparison = CareerComparisonService.compare_careers(
        career_a_id=a_id,
        career_b_id=b_id,
        student_skills=student_skills,
        hours_per_week=hours_per_week
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
    jwt_user = get_jwt_identity()
    user_id = str(jwt_user) if jwt_user is not None else None
    param_user = request.args.get("user_id", type=int)

    if jwt_user is not None and param_user is not None:
        # Prevent IDOR: Authenticated user cannot request another user's analytics
        if str(jwt_user) != str(param_user):
            return jsonify({
                "status": "error",
                "message": "Forbidden: user_id parameter does not match authenticated token"
            }), 403

    if not user_id and param_user:
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


@careers_bp.route("/<int:career_id>/readiness-summary", methods=["GET", "POST"])
@jwt_required(optional=True)
def get_career_readiness_summary(career_id):
    """
    Placement-Ready Career Readiness Summary & Report View (Phase 8 Module 8.4).
    Accepts:
    - hours_per_week: query param or POST JSON (5, 10, or 20, default 10)
    - resume_text: query param or POST JSON (optional)
    """
    hours_per_week = 10
    resume_text = None

    if request.method == "POST":
        data = request.get_json() or {}
        if "hours_per_week" in data:
            try:
                hours_per_week = int(data["hours_per_week"])
            except (ValueError, TypeError):
                return jsonify({
                    "status": "error",
                    "message": "Invalid study intensity. Supported values are 5, 10, or 20 hours per week."
                }), 400
        resume_text = data.get("resume_text")
    else:
        hours_raw = request.args.get("hours_per_week")
        if hours_raw is not None:
            try:
                hours_per_week = int(hours_raw)
            except (ValueError, TypeError):
                return jsonify({
                    "status": "error",
                    "message": "Invalid study intensity. Supported values are 5, 10, or 20 hours per week."
                }), 400
        resume_text = request.args.get("resume_text")

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

    summary = ReadinessSummaryService.generate_readiness_summary(
        career_id=career_id,
        user_id=int(user_id) if user_id else None,
        hours_per_week=hours_per_week,
        resume_text=resume_text
    )

    if not summary:
        return jsonify({
            "status": "error",
            "message": f"Career with ID {career_id} not found"
        }), 404

    return jsonify(summary), 200


@careers_bp.route("/<int:career_id>/pathways", methods=["GET", "POST"])
@jwt_required(optional=True)
def get_career_pathways(career_id):
    """
    Module 9.3: Interactive Career Pathway Branching & Elective Specialization Tree.
    Evaluates available pathways, core vs elective competencies, student matches and gaps,
    learning effort under configurable study intensities (5, 10, 20 hrs/week),
    and ranked pathway recommendations.
    Accepts:
    - GET params: hours_per_week (5, 10, 20), user_id (optional, overridden by JWT identity if authenticated)
    - POST body: {"hours_per_week": 10, "user_id": 1}
    """
    # 1. Validate career ID
    if career_id <= 0:
        return jsonify({
            "status": "error",
            "message": "career_id must be a valid positive integer"
        }), 400

    # 2. Extract study intensity (hours_per_week)
    hours_per_week = 10
    if request.method == "POST":
        data = request.get_json() or {}
        if "hours_per_week" in data:
            try:
                hours_per_week = int(data["hours_per_week"])
            except (ValueError, TypeError):
                return jsonify({
                    "status": "error",
                    "message": "Invalid study intensity. Supported values are 5, 10, or 20 hours per week."
                }), 400
    else:
        hours_raw = request.args.get("hours_per_week")
        if hours_raw is not None:
            try:
                hours_per_week = int(hours_raw)
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

    # 3. Resolve user identity: prioritize JWT, fallback to query param or POST body
    auth_user_id = get_jwt_identity()
    user_id = None
    if auth_user_id:
        try:
            user_id = int(auth_user_id)
        except (ValueError, TypeError):
            user_id = None
    else:
        if request.method == "POST":
            data = request.get_json() or {}
            param_user = data.get("user_id")
        else:
            param_user = request.args.get("user_id")
        if param_user:
            try:
                user_id = int(param_user)
            except (ValueError, TypeError):
                return jsonify({
                    "status": "error",
                    "message": "user_id must be a valid integer"
                }), 400

    # 4. Evaluate career pathways
    result = CareerPathwayService.evaluate_career_pathways(
        career_id=career_id,
        user_id=user_id,
        hours_per_week=hours_per_week
    )

    if not result:
        return jsonify({
            "status": "error",
            "message": f"Career with ID {career_id} not found"
        }), 404

    return jsonify({
        "status": "success",
        **result
    }), 200


@careers_bp.route("/<int:career_id>/academic-benchmark", methods=["GET"])
@jwt_required(optional=True)
def get_career_academic_benchmark(career_id):
    """
    Module 11.3: Academic Recommendation Benchmarking.
    Compares student's academic curriculum evidence against career requirements
    and student demonstrated proficiency.
    """
    career = Career.query.get(career_id)
    if not career:
        return jsonify({
            "status": "error",
            "message": f"Career with id {career_id} not found"
        }), 404

    auth_identity = get_jwt_identity()
    user_id = int(auth_identity) if auth_identity else request.args.get("user_id", type=int)

    program_id = request.args.get("program")

    result = AcademicBenchmarkService.benchmark_career_curriculum(
        career_id=career_id,
        user_id=user_id,
        program_id=program_id
    )

    if "error" in result:
        return jsonify({
            "status": "error",
            "message": result.get("message", "Failed to calculate academic benchmark")
        }), 404

    return jsonify({
        "status": "success",
        **result
    }), 200


@careers_bp.route("/<int:career_id>/industry-demand", methods=["GET"])
@jwt_required(optional=True)
def get_career_industry_demand(career_id):
    """
    Module 11.4: Real-Time Industry Trends & Dynamic Skill Demand Weighting.
    Evaluates market evidence and computes dynamic skill priority weights.
    """
    career = Career.query.get(career_id)
    if not career:
        return jsonify({
            "status": "error",
            "message": f"Career with id {career_id} not found"
        }), 404

    auth_identity = get_jwt_identity()
    user_id = int(auth_identity) if auth_identity else request.args.get("user_id", type=int)

    trend_filter = request.args.get("trend")
    demand_level_filter = request.args.get("demand_level")
    limit = request.args.get("limit", default=None, type=int)

    result = IndustryDemandService.evaluate_career_industry_demand(
        career_id=career_id,
        user_id=user_id,
        trend_filter=trend_filter,
        demand_level_filter=demand_level_filter,
        limit=limit
    )

    if "error" in result:
        return jsonify({
            "status": "error",
            "message": result.get("message", "Failed to evaluate career industry demand")
        }), 404

    return jsonify({
        "status": "success",
        **result
    }), 200


@careers_bp.route("/<int:career_id>/trajectory", methods=["GET"])
@jwt_required(optional=True)
def get_career_trajectory(career_id):
    """
    Module 11.5: Multi-Hop Career Trajectory Intelligence.
    Calculates multi-step career paths from source career to target career,
    evaluating transition compatibility, costs, effort, and progressive skill reuse.
    """
    career = Career.query.get(career_id)
    if not career:
        return jsonify({
            "status": "error",
            "message": f"Target career with id {career_id} not found"
        }), 404

    auth_identity = get_jwt_identity()
    user_id = int(auth_identity) if auth_identity else request.args.get("user_id", type=int)

    from_career_id = request.args.get("from_career_id", type=int)
    objective = request.args.get("objective", "BEST_FIT")
    max_hops = request.args.get("max_hops", default=3, type=int)
    limit = request.args.get("limit", default=3, type=int)

    result = CareerTrajectoryService.find_trajectory(
        target_career_id=career_id,
        from_career_id=from_career_id,
        objective=objective,
        max_hops=max_hops,
        user_id=user_id,
        limit=limit
    )

    if "error" in result:
        status_code = 404 if "NOT_FOUND" in result.get("error", "") else 400
        return jsonify({
            "status": "error",
            "message": result.get("message", "Failed to calculate career trajectory")
        }), status_code

    return jsonify({
        "status": "success",
        **result
    }), 200


@careers_bp.route("/<int:career_id>/simulate-skill", methods=["GET", "POST"])
@jwt_required(optional=True)
def simulate_career_skill(career_id):
    """
    Module 9.4: "What If I Learn Skill X?" Interactive Career Simulator.
    Calculates in-memory impact of hypothetical skill acquisition/improvement on career readiness,
    remaining skill gaps, study timeline, and specialization pathways.
    Strictly read-only and immutable.
    """
    # 1. Validate career ID
    if career_id <= 0:
        return jsonify({
            "status": "error",
            "message": "career_id must be a valid positive integer"
        }), 400

    # 2. Extract inputs from POST body or GET query params
    if request.method == "POST":
        data = request.get_json() or {}
        skill_id = data.get("skill_id")
        skill_name = data.get("skill_name")
        simulated_level = data.get("simulated_level")
        hours_per_week_raw = data.get("hours_per_week")
        user_id_param = data.get("user_id")
    else:
        skill_id = request.args.get("skill_id")
        skill_name = request.args.get("skill_name")
        simulated_level = request.args.get("simulated_level")
        hours_per_week_raw = request.args.get("hours_per_week")
        user_id_param = request.args.get("user_id")

    # Validate that at least one of skill_id or skill_name is provided
    if not skill_id and not skill_name:
        return jsonify({
            "status": "error",
            "message": "Either skill_id or skill_name is required"
        }), 400

    if simulated_level is None:
        return jsonify({
            "status": "error",
            "message": "simulated_level is required"
        }), 400

    # 3. Validate study intensity (hours_per_week)
    hours_per_week = 10
    if hours_per_week_raw is not None:
        try:
            hpw_val = int(hours_per_week_raw)
            if hpw_val not in [5, 10, 20]:
                return jsonify({
                    "status": "error",
                    "message": "Invalid study intensity. Supported values are 5, 10, or 20 hours per week."
                }), 400
            hours_per_week = hpw_val
        except (ValueError, TypeError):
            return jsonify({
                "status": "error",
                "message": "Invalid study intensity. Supported values are 5, 10, or 20 hours per week."
            }), 400

    # 4. Resolve user identity: prioritize JWT, fallback to param
    auth_user_id = get_jwt_identity()
    user_id = None
    if auth_user_id:
        try:
            user_id = int(auth_user_id)
        except (ValueError, TypeError):
            user_id = None
    elif user_id_param:
        try:
            user_id = int(user_id_param)
        except (ValueError, TypeError):
            return jsonify({
                "status": "error",
                "message": "user_id must be a valid integer"
            }), 400

    # 5. Run simulation
    result = CareerSimulatorService.simulate_skill_impact(
        career_id=career_id,
        skill_id=skill_id,
        skill_name=skill_name,
        simulated_level=simulated_level,
        user_id=user_id,
        hours_per_week=hours_per_week
    )

    if "error" in result:
        err_code = result["error"]
        status_code = 404 if err_code in ["CAREER_NOT_FOUND", "SKILL_NOT_FOUND"] else 400
        return jsonify({
            "status": "error",
            "code": err_code,
            "message": result.get("message", "Simulation failed")
        }), status_code

    return jsonify({
        "status": "success",
        "simulation": result,
        **result
    }), 200


@careers_bp.route("/<int:career_id>/skill-roi", methods=["GET"])
@jwt_required(optional=True)
def get_career_skill_roi(career_id):
    """
    Module 11.1: Return deterministic Skill ROI ranking for missing and weak skills.
    Calculates marginal readiness gain, estimated study weeks, and ROI score.
    """
    career = Career.query.get(career_id)
    if not career:
        return jsonify({
            "status": "error",
            "message": f"Career with id {career_id} not found"
        }), 404

    auth_identity = get_jwt_identity()
    user_id = int(auth_identity) if auth_identity else request.args.get("user_id", type=int)

    raw_hours = request.args.get("hours_per_week", 10)
    try:
        hours_per_week = int(raw_hours)
        if hours_per_week <= 0:
            return jsonify({
                "status": "error",
                "message": "hours_per_week must be a positive integer"
            }), 400
    except (ValueError, TypeError):
        return jsonify({
            "status": "error",
            "message": "hours_per_week must be a positive integer"
        }), 400

    roi_data = SkillRoiService.rank_career_skill_rois(
        career_id=career_id,
        user_id=user_id,
        hours_per_week=hours_per_week
    )

    if "error" in roi_data:
        return jsonify({
            "status": "error",
            "message": roi_data.get("message", "Failed to calculate skill ROI")
        }), 404

    return jsonify({
        "status": "success",
        **roi_data
    }), 200


@careers_bp.route("/<int:career_id>/counterfactual", methods=["POST"])
@jwt_required(optional=True)
def run_skill_counterfactual(career_id):
    """
    Module 11.1: In-memory counterfactual analysis for improving a specific skill.
    Calculates before vs after score, gap delta, hours, weeks, ROI, and explainable justification.
    """
    career = Career.query.get(career_id)
    if not career:
        return jsonify({
            "status": "error",
            "message": f"Career with id {career_id} not found"
        }), 404

    data = request.get_json(silent=True) or {}
    skill_id = data.get("skill_id")
    skill_name = data.get("skill_name")
    target_level = data.get("target_level")
    raw_hours = data.get("hours_per_week", 10)

    try:
        hours_per_week = int(raw_hours)
        if hours_per_week <= 0:
            return jsonify({
                "status": "error",
                "message": "hours_per_week must be a positive integer"
            }), 400
    except (ValueError, TypeError):
        return jsonify({
            "status": "error",
            "message": "hours_per_week must be a positive integer"
        }), 400

    if not skill_id and not skill_name:
        return jsonify({
            "status": "error",
            "message": "Either skill_id or skill_name must be provided"
        }), 400

    auth_identity = get_jwt_identity()
    user_id = int(auth_identity) if auth_identity else data.get("user_id")
    if user_id:
        try:
            user_id = int(user_id)
        except (ValueError, TypeError):
            user_id = None

    result = SkillRoiService.calculate_counterfactual(
        career_id=career_id,
        skill_id=skill_id,
        skill_name=skill_name,
        target_level=target_level,
        user_id=user_id,
        hours_per_week=hours_per_week
    )

    if "error" in result:
        status_code = 404 if result.get("error") in ["CAREER_NOT_FOUND", "SKILL_NOT_FOUND"] else 400
        return jsonify({
            "status": "error",
            "code": result.get("error"),
            "message": result.get("message", "Counterfactual evaluation failed")
        }), status_code

    return jsonify({
        "status": "success",
        **result
    }), 200


@careers_bp.route("/<int:career_id>/portfolio-recommendations", methods=["GET"])
@jwt_required(optional=True)
def get_career_portfolio_recommendations(career_id):
    """
    Module 11.2: Actionable Portfolio & Capstone Project Recommendations.
    Returns tailored projects based on career requirements, student missing/weak skills,
    readiness level, and Phase 11.1 Skill ROI quick wins.
    """
    career = Career.query.get(career_id)
    if not career:
        return jsonify({
            "status": "error",
            "message": f"Career with id {career_id} not found"
        }), 404

    auth_identity = get_jwt_identity()
    user_id = int(auth_identity) if auth_identity else request.args.get("user_id", type=int)

    difficulty_filter = request.args.get("difficulty")
    limit = request.args.get("limit", default=None, type=int)

    result = PortfolioProjectService.recommend_projects_for_career(
        career_id=career_id,
        user_id=user_id,
        difficulty_filter=difficulty_filter,
        limit=limit
    )

    if "error" in result:
        return jsonify({
            "status": "error",
            "message": result.get("message", "Failed to retrieve portfolio recommendations")
        }), 404

    return jsonify({
        "status": "success",
        **result
    }), 200

@careers_bp.route("/<int:career_id>/interview-simulation", methods=["GET", "POST"])
@jwt_required(optional=True)
def get_or_create_interview_simulation(career_id):
    """
    Module 11.6: AI Interview Simulation & Career Readiness Assessment.
    Generates a deterministic session with curated questions for the target career.
    """
    career = Career.query.get(career_id)
    if not career:
        return jsonify({
            "status": "error",
            "message": f"Career with id {career_id} not found"
        }), 404

    auth_identity = get_jwt_identity()
    user_id = int(auth_identity) if auth_identity else request.args.get("user_id", type=int)

    data = request.get_json(silent=True) or {}
    difficulty = request.args.get("difficulty") or data.get("difficulty") or "INTERMEDIATE"
    question_count = request.args.get("question_count", type=int) or data.get("question_count", 5)

    result = InterviewSimulationService.generate_session(
        career_id=career_id,
        difficulty=difficulty,
        question_count=question_count,
        user_id=user_id
    )

    if "error" in result:
        status_code = 404 if "NOT_FOUND" in result.get("error", "") else 400
        return jsonify({
            "status": "error",
            "message": result.get("message", "Failed to generate interview simulation session")
        }), status_code

    return jsonify({
        "status": "success",
        **result
    }), 200


@careers_bp.route("/<int:career_id>/interview-simulation/evaluate", methods=["POST"])
@jwt_required(optional=True)
def evaluate_interview_simulation(career_id):
    """
    Module 11.6: AI Interview Simulation & Career Readiness Assessment.
    Evaluates student answers against expected competencies, calculates category scores,
    overall readiness, improvement recommendations, and cross-module intelligence.
    """
    career = Career.query.get(career_id)
    if not career:
        return jsonify({
            "status": "error",
            "message": f"Career with id {career_id} not found"
        }), 404

    auth_identity = get_jwt_identity()
    user_id = int(auth_identity) if auth_identity else request.args.get("user_id", type=int)

    data = request.get_json(silent=True) or {}
    answers = data.get("answers")
    if not answers or not isinstance(answers, list):
        return jsonify({
            "status": "error",
            "message": "Payload must include a non-empty 'answers' list of {question_id, answer}"
        }), 400

    difficulty = data.get("difficulty") or request.args.get("difficulty") or "INTERMEDIATE"

    result = InterviewSimulationService.evaluate_session(
        career_id=career_id,
        answers=answers,
        difficulty=difficulty,
        user_id=user_id
    )

    if "error" in result:
        status_code = 404 if "NOT_FOUND" in result.get("error", "") else 400
        return jsonify({
            "status": "error",
            "message": result.get("message", "Failed to evaluate interview simulation")
        }), status_code

    return jsonify({
        "status": "success",
        **result
    }), 200


@careers_bp.route("/evaluation/benchmark", methods=["GET", "POST"])
@jwt_required(optional=True)
def get_recommendation_benchmark():
    """
    Phase 12 Module 12.1: End-to-End Recommendation Evaluation & Research Validation.
    Executes and returns structured benchmark evaluation measuring ranking quality,
    skill-gap detection, robustness, cross-module consistency, and safety guardrails.
    """
    data = request.get_json(silent=True) or {}
    case_id = request.args.get("case_id") or data.get("case_id")
    limit = request.args.get("limit", type=int) or data.get("limit")

    include_robustness_param = request.args.get("include_robustness")
    if include_robustness_param is not None:
        include_robustness = include_robustness_param.lower() in ("true", "1", "yes")
    else:
        include_robustness = data.get("include_robustness", True)

    include_cross_module_param = request.args.get("include_cross_module")
    if include_cross_module_param is not None:
        include_cross_module = include_cross_module_param.lower() in ("true", "1", "yes")
    else:
        include_cross_module = data.get("include_cross_module", True)

    report = RecommendationEvaluationService.run_full_benchmark_evaluation(
        case_id_filter=case_id,
        include_robustness=include_robustness,
        include_cross_module=include_cross_module,
        limit_cases=limit
    )

    if "error" in report:
        return jsonify({
            "status": "error",
            "message": report.get("message", "Benchmark evaluation error")
        }), 404

    return jsonify({
        "status": "success",
        "benchmark": report
    }), 200


@careers_bp.route("/<int:career_id>/practical-tasks", methods=["GET"])
@jwt_required(optional=True)
def get_career_practical_tasks(career_id):
    """
    Phase 12 Module 12.3: Practical Skill Assessment & Hands-On Task Engine.
    Lists practical tasks specifically prioritized for this career track.
    """
    career = Career.query.get(career_id)
    if not career:
        return jsonify({
            "status": "error",
            "message": f"Career with id {career_id} not found"
        }), 404

    auth_identity = get_jwt_identity()
    user_id = int(auth_identity) if auth_identity else request.args.get("user_id", type=int)

    difficulty = request.args.get("difficulty", type=str)
    skill = request.args.get("skill", type=str)
    category = request.args.get("category", type=str)
    job_source = request.args.get("job_source", type=str)
    job_id = request.args.get("job_id", type=str)
    limit = request.args.get("limit", default=20, type=int)

    from services.practical_task_service import PracticalTaskService
    result = PracticalTaskService.list_tasks(
        career_id=career_id,
        difficulty=difficulty,
        skill=skill,
        category=category,
        job_source=job_source,
        job_id=job_id,
        user_id=user_id,
        limit=limit
    )

    return jsonify(result), 200


