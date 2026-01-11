from flask import Blueprint, jsonify, request
from systems.settlements.settlements import get_player_settlements_for_user
from systems.settlements.garrison import get_settlement_garrison
from database_operations.user_operations import get_player_id_for_user
from auth_decorator.auth_decorator import require_auth

settlement_bp = Blueprint('settlements', __name__)

@settlement_bp.route('/my_settlements', methods=['GET'])
@require_auth
def get_my_settlements() -> tuple[dict, int]:
    """Endpoint to retrieve settlements for the authenticated user."""
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

@settlement_bp.route('/settlement_garrison/<int:settlement_id>', methods=['GET'])
@require_auth
def get_settlement_garrison_route(settlement_id):
    try:
        garrison = get_settlement_garrison(settlement_id, request.user_id)
        
        if garrison is None:
            return jsonify({"error": "Settlement not found or access denied"}), 404

        return jsonify({"garrison": garrison}), 200

    except Exception as e:
        print("ERROR:", e)
        import traceback
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500
    
@settlement_bp.route('/garrison_units', methods=['GET'])
@require_auth
def get_garrison_units():
    try:
        player_id = get_player_id_for_user(request.user_id)
        settlements = get_player_settlements_for_user(request.user_id)

        garrisoned_units = []
        for settlement in settlements:
            garrisoned_units.extend(settlement.get('garrisoned_units', []))

        return jsonify({
            "player_id": player_id,
            "garrisoned_units": garrisoned_units
        }), 200

    except Exception as e:
        print("ERROR:", e)
        import traceback
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500