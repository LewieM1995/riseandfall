from flask import Blueprint, jsonify, request

from auth.decorator import require_auth
from .service import get_neighboring_settlements, get_player_settlements, get_settlement_garrison_service

settlements_bp = Blueprint("settlements", __name__)


@settlements_bp.route("/get_neighbors", methods=["GET"])
@require_auth
def get_neighbors():
    try:
        neighbors_list = get_neighboring_settlements()
        return jsonify({"neighbors": neighbors_list}), 200
    except Exception as e:
        print("ERROR:", e)
        import traceback
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500
    
    
@settlements_bp.route("/my_settlements", methods=["GET"])
@require_auth    
def get_settlements() -> list[dict]:
    user_id = request.user_id
    try:
        settlements = get_player_settlements(user_id)
        return jsonify({"settlements": settlements}), 200
    except Exception as e:
        print("ERROR:", e)
        import traceback
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500
    
    
@settlements_bp.route("/settlement_garrison/<int:settlement_id>", methods=["GET"])
@require_auth
def get_settlement_garrison(settlement_id: int) -> dict | None:
    user_id = request.user_id
    try:
        garrison = get_settlement_garrison_service(settlement_id, user_id)
        if garrison is None:
            return jsonify({"error": "Settlement not found or access denied"}), 404
        print(f"Retrieved garrison for settlement {settlement_id}: {garrison}")
        return jsonify({"garrison": garrison}), 200
    except Exception as e:
        print("ERROR:", e)
        import traceback
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500


# TODO — /my_settlements, /settlement_garrison/<id>, /garrison_units
# once settlements/service.py has get_player_settlements and
# get_settlement_garrison ported from the real source files.11