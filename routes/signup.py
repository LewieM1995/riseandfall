from flask import Blueprint, jsonify, request
from database_operations.signup_operations import create_user, user_exists
from validators.auth_validators import validate_password, validate_username
from auth_tokens.auth_tokens import create_token

sign_up_bp = Blueprint('signup', __name__)

@sign_up_bp.route('/signup', methods=['POST'])
def signup() -> tuple[dict, int]:
    """Endpoint to handle user signup."""
    data = request.get_json()
    username = data.get('username')
    email = data.get('email')
    password = data.get('password')
    
    print("DEBUG Signup Data:", data)
    
    # Basic validation
    if not username or not email or not password:
        return jsonify({"error": "Username, email, and password are required"}), 400
    
    # Validate username
    is_valid_username, username_error = validate_username(username)
    if not is_valid_username:
        return jsonify({"error": username_error}), 400
    
    # Validate password
    is_valid_password, password_error = validate_password(password)
    if not is_valid_password:
        return jsonify({"error": password_error}), 400
    
    # Check if user already exists
    if user_exists(email):
        return jsonify({"error": "Email already registered"}), 409
    
    # Create user
    try:
        user = create_user(username, email, password)
        
        # Create token
        token = create_token(user["id"])
        
        # Build response
        response = jsonify({
            "message": "User created successfully",
            "user": {
                "id": user["id"],
                "username": user["username"],
                "email": user["email"]
            }
        })
        
        # Set auth cookie
        response.set_cookie(
            "auth_token",
            token,
            httponly=True,
            samesite="Lax",
            secure=False,  # True in production
            max_age=3600 * 24 * 7  # 7 days
        )
        
        return response, 201
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({"error": "Failed to create user"}), 500