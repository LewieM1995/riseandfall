from functools import wraps

import jwt
from flask import request, jsonify

from .tokens import SECRET_KEY, ALGORITHM


def require_auth(fn: callable) -> callable:
    @wraps(fn)
    def wrapper(*args: tuple, **kwargs: dict) -> callable:
        token = request.cookies.get("auth_token")

        if not token:
            return jsonify({"error": "Unauthorized"}), 401

        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            request.user_id = payload["user_id"]
        except jwt.ExpiredSignatureError:
            return jsonify({"error": "Token expired"}), 401
        except jwt.InvalidTokenError:
            return jsonify({"error": "Invalid token"}), 401

        return fn(*args, **kwargs)
    return wrapper