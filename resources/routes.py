

from flask import Blueprint, jsonify, request

from auth.decorator import require_auth
from .service import get_total_resources_for_player

resources_bp = Blueprint("resources", __name__)


@resources_bp.route("/total_resources")
@require_auth
def total_resources():
    resources = get_total_resources_for_player(request.user_id)

    if resources is None:
        return jsonify({"error": "Player not found"}), 404

    return jsonify(resources), 200