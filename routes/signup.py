from flask import Blueprint, jsonify, request
from database_operations.signup_operations import create_user, user_exists
from validators.auth_validators import validate_password, validate_username

sign_up_bp = Blueprint('signup', __name__)

@sign_up_bp.route('/signup', methods=['POST'])
def signup():
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
        
        return jsonify({
            "message": "User created successfully",
            "user": {"username": user["username"], "email": user["email"], "id": user["id"]}
        }), 201
    except Exception as e:
        return jsonify({"error": "Failed to create user"}), 500