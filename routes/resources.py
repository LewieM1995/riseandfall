from flask import Blueprint, jsonify, request
from systems.resources.resources import get_player_total_resources_for_user
from systems.experience.experience import get_player_experience, calculate_xp_for_level
from database_operations.user_operations import get_player_id_for_user
from auth_decorator.auth_decorator import require_auth

resource_bp = Blueprint('resources', __name__)

@resource_bp.route('/total_resources', methods=['GET'])
@require_auth
def get_my_total_resources() -> tuple[dict, int]:
    """Endpoint to retrieve total resources and experience for the authenticated user."""
    try:
        player_id = get_player_id_for_user(request.user_id)
        resources = get_player_total_resources_for_user(request.user_id)

        if not resources:
            return jsonify({"error": "Player not found or has no settlements"}), 404

        exp_data = get_player_experience(player_id)
        
        response = {
            "player_id": player_id,
            "food": resources["total_food"],
            "wood": resources["total_wood"],
            "stone": resources["total_stone"],
            "silver": resources["total_silver"],
            "gold": resources["total_gold"]
        }
    
        # Add experience data if available
        if exp_data:
            if exp_data["level"] == 1:
                current_level_xp = 0
            else:
                current_level_xp = calculate_xp_for_level(exp_data["level"])
            
            xp_for_next_level = calculate_xp_for_level(exp_data["level"] + 1)
            xp_progress = exp_data["experience"] - current_level_xp
            xp_needed_for_level = xp_for_next_level - current_level_xp
            
            response.update({
                "level": exp_data["level"],
                "experience": exp_data["experience"],
                "xp_for_next_level": xp_needed_for_level,
                "xp_progress": xp_progress
            })

        return jsonify(response), 200

    except Exception as e:
        print("ERROR:", e)
        import traceback
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500