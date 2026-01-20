from flask import Blueprint, jsonify, request, g
from db.connection import connect_db
from systems.research.research_nodes import fetch_research_nodes_unlocked, get_all_research_nodes
from database_operations.user_operations import get_player_id_for_user
from auth_decorator.auth_decorator import require_auth

research = Blueprint('research', __name__)

@research.route('/get_research_data', methods=['GET'])
@require_auth
def get_research_data() -> tuple[dict, int]:
    """
    Combined endpoint that returns all research nodes and player's unlocked research.
    """
    try:
        player_id = get_player_id_for_user(request.user_id)
        
        research_nodes_list = get_all_research_nodes()
        unlocked_research = fetch_research_nodes_unlocked(player_id)
        
        return jsonify({
            "research_nodes": research_nodes_list,
            "unlocked_research": unlocked_research
        }), 200

    except Exception as e:
        print("ERROR:", e)
        import traceback
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500

# Keep individual endpoints if needed for something else later
@research.route('/get_research_nodes', methods=['GET'])
@require_auth
def get_research_nodes() -> tuple[dict, int]:
    try:
        research_nodes_list = get_all_research_nodes()
        return jsonify({"research_nodes": research_nodes_list}), 200
    except Exception as e:
        print("ERROR:", e)
        import traceback
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500
    
@research.route('/get_research_unlocked', methods=['GET'])
@require_auth
def get_research_unlocked() -> tuple[dict, int]:
    try:
        player_id = get_player_id_for_user(request.user_id)
        unlocked_research = fetch_research_nodes_unlocked(player_id)
        return jsonify({"unlocked_research": unlocked_research}), 200
    except Exception as e:
        print("ERROR:", e)
        import traceback
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500