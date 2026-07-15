from flask import Blueprint, jsonify, request

from auth.decorator import require_auth
from .service import get_player_experience, get_player_profile

player_bp = Blueprint("player", __name__, url_prefix="/player")


@player_bp.route("/profile")
@require_auth
def get_profile():
    profile = get_player_profile(request.user_id)

    if not profile:
        return jsonify({"error": "Player not found"}), 404

    return jsonify(vars(profile)), 200


@player_bp.route("/experience")
@require_auth
def get_experience():
    profile = get_player_profile(request.user_id)

    if not profile:
        return jsonify({"error": "Player not found"}), 404

    xp = get_player_experience(profile.id)

    if not xp:
        return jsonify({"error": "Experience data not found"}), 404

    return jsonify(vars(xp)), 200