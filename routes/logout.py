from flask import Blueprint, jsonify, make_response, request
from db.connection import connect_db
from auth_tokens.decode_token import decode_token 

logout_bp = Blueprint('logout', __name__)

@logout_bp.route('/logout', methods=['POST'])
def logout() -> tuple[dict, int]:
    """Endpoint to handle user logout."""
    try:
        conn = connect_db()
        cursor = conn.cursor()

        token = request.cookies.get("auth_token")
        if token:
            user_id = decode_token(token)
            cursor.execute("""
                UPDATE users
                SET is_active = 0
                WHERE id = ?
            """, (user_id,))
            conn.commit()

        response = make_response(jsonify({"message": "Logged out successfully"}))
        response.set_cookie(
            "auth_token",
            "",  # Clear cookie
            httponly=True,
            samesite="Lax",
            secure=False,
            max_age=0
        )
        return response, 200

    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({"error": "Logout failed"}), 500
