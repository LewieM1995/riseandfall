from flask import Blueprint, jsonify, request, g
from db.connection import connect_db
from systems.neighbors.neighbors import get_all_npc_settlements
from auth_decorator.auth_decorator import require_auth

neighbors = Blueprint('neighbors', __name__)

@neighbors.route('/get_neighbors', methods=['GET'])
@require_auth
def get_neighbors() -> tuple[dict, int]:
    try:
        neighbors_list = get_all_npc_settlements()

        return jsonify({"neighbors": neighbors_list}), 200

    except Exception as e:
        print("ERROR:", e)
        import traceback
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500