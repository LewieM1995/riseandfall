from flask import Blueprint, jsonify, request, g
from database_operations.user_operations import authenticate_user
from validators.auth_validators import validate_email
from auth_tokens.auth_tokens import create_token
from db.connection import connect_db

login_bp = Blueprint('login', __name__)

@login_bp.route('/login', methods=['POST'])
def login() -> tuple[dict, int]:
    """Endpoint to handle user login."""
    try:
        data = request.get_json()
        email = data.get('email')
        password = data.get('password')

        if not email or not password:
            return jsonify({"error": "Email and password are required"}), 400

        is_valid_email, email_error = validate_email(email)
        if not is_valid_email:
            return jsonify({"error": email_error}), 400

        user = authenticate_user(email, password)
        if not user:
            return jsonify({"error": "Invalid email or password"}), 401

        conn = connect_db()
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE users 
            SET is_active = 1, last_login = CURRENT_TIMESTAMP 
            WHERE id = ?
        """, (user["id"],))
        conn.commit()

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
