from db.connection import connect_db
from database_operations.database_operations import resolve_npc_ids

def get_all_npc_settlements() -> list[dict]:
    """Retrieve all NPC settlements"""

    conn = connect_db()
    cursor = conn.cursor()
    
    npc_ids = resolve_npc_ids()
    npc_player_ids = [npc['id'] for npc in npc_ids]
    
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
        WHERE player_id IN ({})
        ORDER BY created_at ASC
    """.format(','.join('?' * len(npc_player_ids))), npc_player_ids)

    settlements = [dict(row) for row in cursor.fetchall()]
    conn.close()

    return settlements
