from flask import Blueprint, jsonify, request
from database_operations.user_operations import get_player_id_for_user
from systems.army.army import get_player_armies_for_user
from auth_decorator.auth_decorator import require_auth

army_bp = Blueprint('army', __name__)

@army_bp.route('/my_army_units', methods=['GET'])
@require_auth
def get_army_units() -> tuple[dict, int]:
    """Endpoint to retrieve the army units for the authenticated user."""
    try:
        player_id = get_player_id_for_user(request.user_id)
        army = get_player_armies_for_user(request.user_id)
        
        if not army:
            return jsonify({"army": []}), 200

        return jsonify({
            "player_id": player_id,
            "army": army
        }), 200

    except Exception as e:
        print("ERROR:", e)
        import traceback
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500

    

