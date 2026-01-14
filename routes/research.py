from flask import Blueprint, jsonify, request, g
from db.connection import connect_db
from systems.research.research_nodes import get_all_research_nodes
from auth_decorator.auth_decorator import require_auth

research = Blueprint('research', __name__)

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