import json

from db.connection import connect_db
from database_operations.user_operations import get_player_id_for_user

def get_player_total_resources_for_user(user_id: int) -> dict:
    """Calculate total resources for a user across all their settlements."""
    player_id = get_player_id_for_user(user_id)

    conn = connect_db()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT 
            COALESCE(SUM(s.food), 0) as total_food,
            COALESCE(SUM(s.wood), 0) as total_wood,
            COALESCE(SUM(s.stone), 0) as total_stone,
            COALESCE(SUM(s.silver), 0) as total_silver,
            COALESCE(SUM(s.gold), 0) as total_gold
        FROM settlements s
        WHERE s.player_id = ?
    """, (player_id,))

    result = cursor.fetchone()
    conn.close()

    return {
        'total_food': int(result['total_food']),
        'total_wood': int(result['total_wood']),
        'total_stone': int(result['total_stone']),
        'total_silver': int(result['total_silver']),
        'total_gold': int(result['total_gold'])
    }

