import sqlite3

from werkzeug.security import generate_password_hash, check_password_hash

from db.connection import connect_db
from .repository import get_user_by_email, user_exists, insert_user, set_user_active
from .validators import validate_username, validate_password, validate_email
from .tokens import create_token
from player.service import create_new_player_with_starting_kingdom, PlayerSetupError


class AuthError(Exception):
    """Raised for any expected auth failure (bad input, wrong password,
    duplicate email). Routes catch this and turn it into a 4xx response."""
    def __init__(self, message: str, status: int = 400):
        self.message = message
        self.status = status


def signup(username: str, email: str, password: str) -> tuple[dict, str]:
    """Validate, create the user + their starting player/kingdom, return
    (user_dict, auth_token).

    User-row creation and player/kingdom bootstrap happen in ONE
    transaction (same cursor, one commit) so a failure partway through
    setup can't leave a user with no player, or vice versa — matching
    the original create_user's all-or-nothing behavior.
    """
    if not username or not email or not password:
        raise AuthError("Username, email, and password are required")

    is_valid, error = validate_username(username)
    if not is_valid:
        raise AuthError(error)

    is_valid, error = validate_password(password)
    if not is_valid:
        raise AuthError(error)

    conn = connect_db()
    try:
        cursor = conn.cursor()

        if user_exists(cursor, email):
            raise AuthError("Email already registered", status=409)

        try:
            password_hash = generate_password_hash(password)
            user_id = insert_user(cursor, username, email, password_hash)

            kingdom = create_new_player_with_starting_kingdom(cursor, user_id, username)

            conn.commit()
        except sqlite3.IntegrityError as e:
            conn.rollback()
            error_msg = str(e).lower()
            if "email" in error_msg:
                raise AuthError("Email already exists", status=409)
            elif "username" in error_msg:
                raise AuthError("Username already taken", status=409)
            raise AuthError(f"Database constraint violation: {e}", status=500)
        except PlayerSetupError as e:
            conn.rollback()
            raise AuthError(str(e), status=500)

        token = create_token(user_id)
        return {
            "id": user_id,
            "username": username,
            "email": email,
            "player_id": kingdom["player_id"],
            "settlement_id": kingdom["settlement_id"],
        }, token
    finally:
        conn.close()


def login(email: str, password: str) -> tuple[dict, str]:
    """Validate credentials, mark user active, return (user_dict, auth_token)."""
    if not email or not password:
        raise AuthError("Email and password are required")

    is_valid, error = validate_email(email)
    if not is_valid:
        raise AuthError(error)

    conn = connect_db()
    try:
        cursor = conn.cursor()

        user = get_user_by_email(cursor, email)
        if not user or not check_password_hash(user["password_hash"], password):
            raise AuthError("Invalid email or password", status=401)

        set_user_active(cursor, user["id"], active=True, update_last_login=True)
        conn.commit()

        token = create_token(user["id"])
        return {"id": user["id"], "username": user["username"], "email": user["email"]}, token
    finally:
        conn.close()


def logout(user_id: int | None) -> None:
    """Mark the user inactive, if we could identify one from the token."""
    if user_id is None:
        return

    conn = connect_db()
    try:
        cursor = conn.cursor()
        set_user_active(cursor, user_id, active=False)
        conn.commit()
    finally:
        conn.close()