from db.connection import connect_db
from database_operations.database_operations import resolve_npc_ids, resolve_settlement_type_ids, resolve_settlement_type_names

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
            settlement_type_id,
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

    settlement_type_names = resolve_settlement_type_names()
    
    settlements = []
    for row in cursor.fetchall():
        row_dict = dict(row)
        row_dict['settlement_type'] = settlement_type_names.get(
            row_dict['settlement_type_id'], 
            'unknown'
        )
        settlements.append(row_dict)
    
    conn.close()

    return settlements