def get_user_by_email(cursor, email: str) -> dict | None:
    """Fetch a full user row (including password hash) by email."""
    cursor.execute(
        "SELECT id, username, email, password_hash FROM users WHERE email = ?",
        (email,),
    )
    row = cursor.fetchone()
    return dict(row) if row else None


def user_exists(cursor, email: str) -> bool:
    cursor.execute("SELECT 1 FROM users WHERE email = ?", (email,))
    return cursor.fetchone() is not None


def insert_user(cursor, username: str, email: str, password_hash: str) -> int:
    """Insert a new user row, return the new user's id."""
    cursor.execute(
        """
        INSERT INTO users (username, email, password_hash)
        VALUES (?, ?, ?)
        """,
        (username, email, password_hash),
    )
    return cursor.lastrowid


def set_user_active(cursor, user_id: int, active: bool, update_last_login: bool = False) -> None:
    if update_last_login:
        cursor.execute(
            "UPDATE users SET is_active = ?, last_login = CURRENT_TIMESTAMP WHERE id = ?",
            (int(active), user_id),
        )
    else:
        cursor.execute(
            "UPDATE users SET is_active = ? WHERE id = ?",
            (int(active), user_id),
        )