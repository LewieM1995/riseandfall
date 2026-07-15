def get_player_level_and_xp(cursor, player_id: int) -> dict | None:
    cursor.execute("SELECT experience, level FROM players WHERE id = ?", (player_id,))
    row = cursor.fetchone()
    return dict(row) if row else None

def update_player_level(cursor, player_id: int, new_level: int) -> None:
    cursor.execute("UPDATE players SET level = ? WHERE id = ?", (new_level, player_id))