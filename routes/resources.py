from flask import Blueprint, jsonify, request
from systems.resources.resources import get_player_total_resources_for_user
from database_operations.user_operations import get_player_id_for_user
from auth_decorator.auth_decorator import require_auth

# print(f" resources.py loaded, get_player_id_for_user = {get_player_id_for_user}")

resource_bp = Blueprint('resources', __name__)

@resource_bp.route('/total_resources', methods=['GET'])
@require_auth
def get_my_total_resources():
    try:
        #print(f" Authenticated user_id: {request.user_id}")
        #print(f" About to call get_player_id_for_user: {get_player_id_for_user}")
        
        player_id = get_player_id_for_user(request.user_id)

        resources = get_player_total_resources_for_user(request.user_id)

        if not resources:
            return jsonify({"error": "Player not found or has no settlements"}), 404

        return jsonify({
            "player_id": player_id,
            "food": resources["total_food"],
            "wood": resources["total_wood"],
            "stone": resources["total_stone"],
            "silver": resources["total_silver"],
            "gold": resources["total_gold"]
        }), 200

    except Exception as e:
        print("ERROR:", e)
        import traceback
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500