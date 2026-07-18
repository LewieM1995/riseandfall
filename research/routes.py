from flask import Blueprint, jsonify, request, g
from db.connection import connect_db
from .service import get_all_research_nodes_service, get_unlocked_research_nodes_service, unlock_research_node_service
from database_operations.user_operations import get_player_id_for_user
from auth.decorator import require_auth

research = Blueprint('research', __name__)

@research.route('/get_research_data', methods=['GET'])
@require_auth
def get_research_data() -> tuple[dict, int]:
    """
    Combined endpoint that returns all research nodes and player's unlocked research.
    """
    try:
        player_id = get_player_id_for_user(request.user_id)
        
        research_nodes_list = get_all_research_nodes_service()
        unlocked_research = get_unlocked_research_nodes_service(player_id)
        
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
        research_nodes_list = get_all_research_nodes_service()
        return jsonify({"research_nodes": research_nodes_list}), 200
    except Exception as e:
        print("ERROR:", e)
        import traceback
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500
    
@research.route('/get_research_unlocked', methods=['GET'])
@require_auth
def get_unlocked_research() -> tuple[dict, int]:
    try:
        player_id = get_player_id_for_user(request.user_id)
        unlocked_research = get_unlocked_research_nodes_service(player_id)
        return jsonify({"unlocked_research": unlocked_research}), 200
    except Exception as e:
        print("ERROR:", e)
        import traceback
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500
    
@research.route('/unlock_research_node', methods=['POST'])
@require_auth
def unlock_research_node() -> tuple[dict, int]:
    try:
        data = request.get_json()
        node_id = data.get('node_id')
        
        if node_id is None:
            return jsonify({"error": "node_id is required"}), 400
        
        player_id = get_player_id_for_user(request.user_id)
        unlock_research_node_service(player_id, node_id)
        
        return jsonify({"message": f"Research node {node_id} unlocked for player {player_id}"}), 200
    except Exception as e:
        print("ERROR:", e)
        import traceback
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500