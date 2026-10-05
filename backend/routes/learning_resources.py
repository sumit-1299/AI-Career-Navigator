"""
Curated Learning Resources & Progress Tracking API Endpoints.

Provides:
- GET /api/learning-resources: Query and search learning resources.
- GET /api/learning-resources/<id>: Retrieve single resource details.
- POST /api/learning-resources: Add a curated learning resource.
- POST /api/learning-resources/<id>/start: Student starts a resource.
- PUT /api/learning-resources/<id>/progress: Update progress percentage & notes.
- POST /api/learning-resources/<id>/complete: Complete resource & update skill proficiency.
- GET /api/learning-resources/progress: Retrieve student's learning progress.
"""

from flask import Blueprint, jsonify, request
from flask_jwt_extended import get_jwt_identity, jwt_required
from extensions import db
from models.canonical_skill import CanonicalSkill
from models.learning_resource import LearningResource
from services.learning_progress_service import LearningProgressService
from services.learning_resource_service import LearningResourceService

learning_resources_bp = Blueprint("learning_resources", __name__, url_prefix="/api/learning-resources")


def resolve_user_id() -> Optional[int]:
    """Resolves student user_id from JWT token, query param, or JSON body."""
    uid = get_jwt_identity()
    if uid:
        return int(uid)

    param = request.args.get("user_id", type=int)
    if param:
        return param

    if request.is_json:
        body_uid = (request.get_json() or {}).get("user_id")
        if body_uid:
            return int(body_uid)

    return None


@learning_resources_bp.route("", methods=["GET"])
def list_learning_resources():
    """
    Query curated learning resources with optional filters:
    - canonical_skill_id
    - difficulty (Beginner, Intermediate, Advanced)
    - type / resource_type (Course, Documentation, Tutorial, Project, Book, Practice Platform)
    - q / search (keyword search)
    """
    canonical_skill_id = request.args.get("canonical_skill_id", type=int)
    difficulty = request.args.get("difficulty")
    resource_type = request.args.get("resource_type") or request.args.get("type")
    query_text = request.args.get("q") or request.args.get("search")
    limit = request.args.get("limit", default=20, type=int)

    if canonical_skill_id:
        resources = LearningResourceService.get_resources_for_canonical_skill(
            canonical_skill_id=canonical_skill_id,
            difficulty_level=difficulty,
            resource_type=resource_type
        )
    elif query_text:
        resources = LearningResourceService.search_resources(
            query_text=query_text,
            difficulty_level=difficulty,
            resource_type=resource_type,
            limit=limit
        )
    else:
        resources = LearningResourceService.search_resources(
            query_text=None,
            difficulty_level=difficulty,
            resource_type=resource_type,
            limit=limit
        )

    return jsonify({
        "status": "success",
        "count": len(resources),
        "resources": resources
    }), 200


@learning_resources_bp.route("/progress", methods=["GET"])
@jwt_required(optional=True)
def get_user_progress():
    """Retrieve learning progress records for the current student."""
    user_id = resolve_user_id()
    if not user_id:
        return jsonify({
            "status": "error",
            "message": "Authentication or user_id is required"
        }), 401

    status_filter = request.args.get("status")
    progress_list = LearningProgressService.get_user_progress(user_id=user_id, status=status_filter)

    return jsonify({
        "status": "success",
        "user_id": user_id,
        "count": len(progress_list),
        "progress": progress_list
    }), 200


@learning_resources_bp.route("/<int:resource_id>", methods=["GET"])
def get_resource_detail(resource_id):
    """Retrieve details for a specific learning resource."""
    resource = LearningResource.query.get(resource_id)
    if not resource:
        return jsonify({
            "status": "error",
            "message": f"Learning resource with id {resource_id} not found"
        }), 404

    return jsonify({
        "status": "success",
        "resource": resource.to_dict()
    }), 200


@learning_resources_bp.route("", methods=["POST"])
def create_learning_resource():
    """Create a new curated learning resource linked to a canonical skill."""
    data = request.get_json() or {}

    canonical_skill_id = data.get("canonical_skill_id")
    title = data.get("title")
    resource_type = data.get("resource_type")
    provider = data.get("provider")
    url = data.get("url")

    if not all([canonical_skill_id, title, resource_type, provider, url]):
        return jsonify({
            "status": "error",
            "message": "canonical_skill_id, title, resource_type, provider, and url are required"
        }), 400

    skill = CanonicalSkill.query.get(canonical_skill_id)
    if not skill:
        return jsonify({
            "status": "error",
            "message": f"Canonical skill with id {canonical_skill_id} not found"
        }), 404

    resource = LearningResourceService.create_resource(
        canonical_skill_id=canonical_skill_id,
        title=title,
        resource_type=resource_type,
        provider=provider,
        url=url,
        difficulty_level=data.get("difficulty_level", "Beginner"),
        estimated_duration=data.get("estimated_duration"),
        description=data.get("description"),
        certification_available=data.get("certification_available", False),
        status=data.get("status", "Active")
    )

    return jsonify({
        "status": "success",
        "message": "Learning resource created successfully",
        "resource": resource.to_dict()
    }), 201


@learning_resources_bp.route("/<int:resource_id>/start", methods=["POST"])
@jwt_required(optional=True)
def start_learning_resource(resource_id):
    """Student starts working on a learning resource."""
    user_id = resolve_user_id()
    if not user_id:
        return jsonify({
            "status": "error",
            "message": "Authentication or user_id is required"
        }), 401

    try:
        progress = LearningProgressService.start_resource(
            user_id=user_id,
            learning_resource_id=resource_id
        )
        return jsonify({
            "status": "success",
            "message": "Resource started",
            "progress": progress
        }), 200
    except ValueError as e:
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 404


@learning_resources_bp.route("/<int:resource_id>/progress", methods=["PUT", "PATCH"])
@jwt_required(optional=True)
def update_resource_progress(resource_id):
    """Update progress percentage and optional notes for a learning resource."""
    user_id = resolve_user_id()
    if not user_id:
        return jsonify({
            "status": "error",
            "message": "Authentication or user_id is required"
        }), 401

    data = request.get_json() or {}
    percentage = data.get("progress_percentage")
    notes = data.get("notes")

    if percentage is None:
        return jsonify({
            "status": "error",
            "message": "progress_percentage is required"
        }), 400

    try:
        progress = LearningProgressService.update_progress(
            user_id=user_id,
            learning_resource_id=resource_id,
            progress_percentage=float(percentage),
            notes=notes
        )
        return jsonify({
            "status": "success",
            "message": "Progress updated",
            "progress": progress
        }), 200
    except ValueError as e:
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 404


@learning_resources_bp.route("/<int:resource_id>/complete", methods=["POST"])
@jwt_required(optional=True)
def complete_learning_resource(resource_id):
    """Complete a learning resource and update the student's skill proficiency."""
    user_id = resolve_user_id()
    if not user_id:
        return jsonify({
            "status": "error",
            "message": "Authentication or user_id is required"
        }), 401

    try:
        progress = LearningProgressService.complete_resource(
            user_id=user_id,
            learning_resource_id=resource_id
        )
        return jsonify({
            "status": "success",
            "message": "Resource marked as completed and skill proficiency updated",
            "progress": progress
        }), 200
    except ValueError as e:
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 404
