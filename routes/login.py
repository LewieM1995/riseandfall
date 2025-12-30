from flask import Blueprint, jsonify, request
from database_operations.user_operations import authenticate_user
from validators.auth_validators import validate_email
from auth_tokens.auth_tokens import create_token

login_bp = Blueprint('login', __name__)

@login_bp.route('/login', methods=['POST'])
def login():
    try:
        data = request.get_json()
        email = data.get('email')
        password = data.get('password')

        if not email or not password:
            return jsonify({"error": "Email and password are required"}), 400

        # Only validate email format for login
        is_valid_email, email_error = validate_email(email)
        if not is_valid_email:
            return jsonify({"error": email_error}), 400

        # authenticate_user handles password checking internally
        user = authenticate_user(email, password)
        if not user:
            return jsonify({"error": "Invalid email or password"}), 401

        token = create_token(user["id"])

        response = jsonify({
            "message": "Login successful",
            "user": {
                "id": user["id"],
                "username": user["username"],
                "email": user["email"]
            }
        })

        response.set_cookie(
            "auth_token",
            token,
            httponly=True,
            samesite="Lax",
            secure=False,  # True in production
            max_age=3600 * 24 * 7  # 7 days
        )

        return response, 200

    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({"error": "Login failed"}), 500