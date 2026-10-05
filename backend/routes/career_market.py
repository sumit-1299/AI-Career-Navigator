"""
Career Market Outlook API Endpoints.

Provides:
- GET /api/careers/<career_id>/market-outlook: Specific career market outlook
- GET /api/careers/market-outlook: All careers market outlooks
- POST /api/careers/market-outlook/compare: Multi-career side-by-side comparison
"""

from flask import Blueprint, jsonify, request
from services.career_market_service import CareerMarketService

career_market_bp = Blueprint("career_market", __name__, url_prefix="/api/careers")


@career_market_bp.route("/market-outlook", methods=["GET"])
def get_all_market_outlooks():
    """Retrieve labor market intelligence for all canonical careers."""
    outlooks = CareerMarketService.get_all_market_outlooks()
    return jsonify({
        "status": "success",
        "count": len(outlooks),
        "market_outlooks": outlooks
    }), 200


@career_market_bp.route("/<int:career_id>/market-outlook", methods=["GET"])
def get_career_market_outlook(career_id):
    """Retrieve labor market intelligence for a specific career."""
    outlook = CareerMarketService.get_market_outlook_by_career_id(career_id)
    if not outlook:
        return jsonify({
            "status": "error",
            "message": f"Career with id {career_id} not found"
        }), 404

    return jsonify({
        "status": "success",
        "market_outlook": outlook
    }), 200


@career_market_bp.route("/market-outlook/compare", methods=["POST"])
def compare_market_outlooks():
    """Compare market outlooks for multiple career IDs."""
    data = request.get_json() or {}
    career_ids = data.get("career_ids", [])

    if not career_ids or not isinstance(career_ids, list):
        return jsonify({
            "status": "error",
            "message": "'career_ids' list is required in request body"
        }), 400

    comparisons = CareerMarketService.compare_market_outlooks([int(cid) for cid in career_ids])
    return jsonify({
        "status": "success",
        "count": len(comparisons),
        "comparisons": comparisons
    }), 200
