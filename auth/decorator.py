import jwt
from functools import wraps
from flask import request, jsonify
from dotenv import load_dotenv
import os

load_dotenv()
SECRET_KEY = os.getenv("SECRET_KEY")

def require_auth(fn: callable) -> callable:
    @wraps(fn)
    def wrapper(*args: tuple, **kwargs: dict) -> callable:
        token = request.cookies.get("auth_token")

        if not token:
            return jsonify({"error": "Unauthorized"}), 401

        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
            request.user_id = payload["user_id"]
        except jwt.ExpiredSignatureError:
            return jsonify({"error": "Token expired"}), 401
        except jwt.InvalidTokenError:
            return jsonify({"error": "Invalid token"}), 401

        return fn(*args, **kwargs)
    return wrapper