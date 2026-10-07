"""
Practical Skill Assessment & Hands-On Task API Routes.
Phase 12 Module 12.3: Practical Skill Assessment & Hands-On Task Engine.

Provides:
- GET /api/practical-tasks: List and filter practical tasks with multi-factor prioritization.
- GET /api/practical-tasks/<task_id>: Retrieve specific practical task details.
- POST /api/practical-tasks/evaluate: Deterministically evaluate a student's technical submission.
"""

from flask import Blueprint, jsonify, request
from flask_jwt_extended import get_jwt_identity, verify_jwt_in_request

from services.practical_task_service import PracticalTaskService

practical_tasks_bp = Blueprint("practical_tasks", __name__, url_prefix="/api/practical-tasks")


def _get_current_user_id():
    """Extract authenticated user ID if JWT is present in request."""
    try:
        verify_jwt_in_request(optional=True)
        identity = get_jwt_identity()
        if identity:
            return int(identity)
    except Exception:
        pass
    return None


@practical_tasks_bp.route("", methods=["GET"])
@practical_tasks_bp.route("/", methods=["GET"])
def list_practical_tasks():
    """
    List practical tasks with optional filtering and deterministic prioritization.
    Query parameters:
    - career_id (int)
    - difficulty (str: BEGINNER, INTERMEDIATE, ADVANCED)
    - skill (str)
    - category (str)
    - job_source (str)
    - job_id (str)
    - limit (int, default 20)
    """
    career_id = request.args.get("career_id", type=int)
    difficulty = request.args.get("difficulty", type=str)
    skill = request.args.get("skill", type=str)
    category = request.args.get("category", type=str)
    job_source = request.args.get("job_source", type=str)
    job_id = request.args.get("job_id", type=str)
    limit = request.args.get("limit", default=20, type=int)

    user_id = _get_current_user_id()

    result = PracticalTaskService.list_tasks(
        career_id=career_id,
        difficulty=difficulty,
        skill=skill,
        category=category,
        job_source=job_source,
        job_id=job_id,
        user_id=user_id,
        limit=limit,
    )
    return jsonify(result), 200


@practical_tasks_bp.route("/<task_id>", methods=["GET"])
def get_practical_task(task_id):
    """Retrieve details for a specific practical task by ID."""
    task = PracticalTaskService.get_task_by_id(task_id)
    if not task:
        return jsonify({
            "status": "error",
            "message": f"Practical task '{task_id}' not found",
        }), 404

    return jsonify({
        "status": "success",
        "task": task,
        "disclaimer": PracticalTaskService.SAFETY_DISCLAIMER,
    }), 200


@practical_tasks_bp.route("/evaluate", methods=["POST"])
def evaluate_practical_task():
    """
    Deterministically evaluates a student's answer submission for a practical task.
    Payload:
    - task_id (str, required)
    - answer (str, required)
    """
    payload = request.get_json(silent=True)
    if not payload or not isinstance(payload, dict):
        return jsonify({
            "status": "error",
            "message": "Invalid or missing JSON payload",
        }), 400

    task_id = payload.get("task_id")
    if not task_id or not str(task_id).strip():
        return jsonify({
            "status": "error",
            "message": "task_id is required",
        }), 400

    answer = payload.get("answer")
    if answer is None or not isinstance(answer, str) or not answer.strip():
        return jsonify({
            "status": "error",
            "message": "answer is required and cannot be empty",
        }), 400

    user_id = _get_current_user_id()

    eval_result = PracticalTaskService.evaluate_task_attempt(
        task_id=str(task_id).strip(),
        answer=answer,
        user_id=user_id,
    )

    if eval_result.get("status") == "error":
        error_type = eval_result.get("error")
        if error_type == "NOT_FOUND":
            status_code = 404
        elif error_type == "PAYLOAD_TOO_LARGE":
            status_code = 413
        else:
            status_code = 400
        return jsonify(eval_result), status_code

    return jsonify(eval_result), 200
