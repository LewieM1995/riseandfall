from flask import Blueprint, jsonify, request, make_response

from .service import signup as signup_service, login as login_service, logout as logout_service, AuthError
from .tokens import decode_token

auth_bp = Blueprint("auth", __name__)

COOKIE_MAX_AGE = 3600 * 24 * 7  # 7 days


def _set_auth_cookie(response, token: str):
    response.set_cookie(
        "auth_token",
        token,
        httponly=True,
        samesite="Lax",
        secure=False,  # True in production
        max_age=COOKIE_MAX_AGE,
    )


@auth_bp.route("/signup", methods=["POST"])
def signup():
    data = request.get_json()

    try:
        user, token = signup_service(
            data.get("username"), data.get("email"), data.get("password")
        )
    except AuthError as e:
        return jsonify({"error": e.message}), e.status

    response = jsonify({"message": "User created successfully", "user": user})
    _set_auth_cookie(response, token)
    return response, 201


@auth_bp.route("/login", methods=["POST"])
def login():
    data = request.get_json()

    try:
        user, token = login_service(data.get("email"), data.get("password"))
    except AuthError as e:
        return jsonify({"error": e.message}), e.status

    response = jsonify({"message": "Login successful", "user": user})
    _set_auth_cookie(response, token)
    return response, 200


@auth_bp.route("/logout", methods=["POST"])
def logout():
    token = request.cookies.get("auth_token")
    user_id = decode_token(token) if token else None

    logout_service(user_id)

    response = make_response(jsonify({"message": "Logged out successfully"}))
    response.set_cookie("auth_token", "", httponly=True, samesite="Lax", secure=False, max_age=0)
    return response, 200