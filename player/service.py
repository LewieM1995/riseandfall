# player/service.py
from db.connection import connect_db
from .repository import get_player_level_and_xp, update_player_level

def calculate_xp_for_level(level: int) -> int:
    return int(100 * pow(1.60, level - 1))

def check_level_up(cursor, player_id: int) -> None:
    data = get_player_level_and_xp(cursor, player_id)
    if not data:
        return
    if data["experience"] >= calculate_xp_for_level(data["level"] + 1):
        update_player_level(cursor, player_id, data["level"] + 1)
        check_level_up(cursor, player_id)  # recurse for multi-level jumps

def get_player_experience(player_id: int) -> dict | None:
    conn = connect_db()
    try:
        cursor = conn.cursor()
        return get_player_level_and_xp(cursor, player_id)
    finally:
        conn.close()