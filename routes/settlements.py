
from flask import Blueprint, jsonify, request
from systems.settlements.settlements import get_player_settlements_for_user
from database_operations.user_operations import get_player_id_for_user
from auth_decorator.auth_decorator import require_auth

settlement_bp = Blueprint('settlements', __name__)

@settlement_bp.route('/my_settlements', methods=['GET'])
@require_auth
def get_my_settlements():
    try:
        player_id = get_player_id_for_user(request.user_id)
        settlements = get_player_settlements_for_user(request.user_id)

        if not settlements:
            return jsonify({"settlements": []}), 200

        return jsonify({
            "player_id": player_id,
            "settlements": settlements
        }), 200

    except Exception as e:
        print("ERROR:", e)
        import traceback
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500
