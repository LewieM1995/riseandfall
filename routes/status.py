from flask import Blueprint, jsonify, request

status_bp = Blueprint('/status', __name__)
@status_bp.route('/status', methods=['GET'])
def status():
    return jsonify({"status": "api running"}), 200

