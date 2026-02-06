from db.connection import connect_db
from database_operations.user_operations import get_player_id_for_user
from database_operations.database_operations import resolve_settlement_type_names, resolve_settlement_type_ids

def get_player_settlements_for_user(user_id: int) -> list[dict]:
    """Retrieve all settlements for a given user."""
    
    player_id = get_player_id_for_user(user_id)

    conn = connect_db()
    cursor = conn.cursor()

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
        WHERE player_id = ?
        ORDER BY created_at ASC
    """, (player_id,))
    
    settlement_type_names = resolve_settlement_type_names()
    
    settlements = []
    for row in cursor.fetchall():
        row_dict = dict(row)
        row_dict['settlement_type'] = settlement_type_names.get(
            row_dict['settlement_type_id'], 
            'unknown'
        )
        row_dict['food'] = int(row_dict['food'])
        row_dict['wood'] = int(row_dict['wood'])
        row_dict['stone'] = int(row_dict['stone'])
        row_dict['silver'] = int(row_dict['silver'])
        row_dict['gold'] = int(row_dict['gold'])
        
        settlements.append(row_dict)

    conn.close()

    return settlements