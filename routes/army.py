from flask import Blueprint, jsonify

army_bp = Blueprint('army', __name__)

@army_bp.route('/units', methods=['GET'])
def get_army_units():
    return jsonify({"status": "api running"}), 200
