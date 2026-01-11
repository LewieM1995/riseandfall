
from db.connection import connect_db
from database_operations.user_operations import get_player_id_for_user

def get_player_settlements_for_user(user_id: int) -> list[dict]:
    """Retrieve all settlements for a given user."""
    player_id = get_player_id_for_user(user_id)

    conn = connect_db()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT
            id,
            name,
            settlement_type,
            x,
            y,
            food,
            wood,
            stone,
            silver,
            gold,
            created_at
        FROM settlements
        WHERE player_id = ?
        ORDER BY created_at ASC
    """, (player_id,))

    settlements = [dict(row) for row in cursor.fetchall()]
    conn.close()

    return settlements
