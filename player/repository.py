def get_player_level_and_xp(cursor, player_id: int) -> dict | None:
    """Fetch a player's raw level/xp row."""
    cursor.execute(
        "SELECT experience, level FROM players WHERE id = ?",
        (player_id,),
    )
    row = cursor.fetchone()
    return dict(row) if row else None


def update_player_level(cursor, player_id: int, new_level: int) -> None:
    """Persist a new level for a player."""
    cursor.execute(
        "UPDATE players SET level = ? WHERE id = ?",
        (new_level, player_id),
    )


def get_player_by_id(cursor, player_id: int) -> dict | None:
    """Fetch a full player row by internal player id."""
    cursor.execute(
        "SELECT id, username, user_id, level, experience FROM players WHERE id = ?",
        (player_id,),
    )
    row = cursor.fetchone()
    return dict(row) if row else None


def insert_player(cursor, user_id: int, username: str, is_npc: bool = False) -> int:
    """Create a player row for a new user, return the new player's id."""
    cursor.execute(
        "INSERT INTO players (user_id, username, is_npc) VALUES (?, ?, ?)",
        (user_id, username, int(is_npc)),
    )
    return cursor.lastrowid


def grant_experience(cursor, player_id: int, amount: int) -> None:
    """Add XP to a player. Does not check for level-up — that's the
    service layer's job (see player.service.add_experience)."""
    cursor.execute(
        "UPDATE players SET experience = experience + ? WHERE id = ?",
        (amount, player_id),
    )


def get_player_id_for_user(cursor, user_id: int) -> int | None:
    """Resolve a player's internal id from their auth user_id.

    Routes/services only ever have `user_id` from the auth token —
    this is the one place that bridges "logged-in user" to "player row".
    """
    cursor.execute(
        "SELECT id FROM players WHERE user_id = ?",
        (user_id,),
    )
    row = cursor.fetchone()
    return row["id"] if row else None