from db.connection import connect_db
from database_operations.user_operations import get_player_id_for_user

def get_settlement_garrison(settlement_id: int, user_id: int) -> dict | None:
    """Retrieve garrison details for a settlement owned by the user."""
    player_id = get_player_id_for_user(user_id)
    
    conn = connect_db()
    cursor = conn.cursor()
    
    # Verify settlement belongs to player
    cursor.execute("""
        SELECT player_id FROM settlements WHERE id = ?
    """, (settlement_id,))
    
    result = cursor.fetchone()
    if not result or result[0] != player_id:
        conn.close()
        return None
    
    # Get garrison units
    cursor.execute("""
        SELECT 
            sg.unit_type,
            sg.quantity,
            ut.attack,
            ut.defense,
            ut.health
        FROM settlement_garrisons sg
        JOIN unit_types ut ON ut.unit_type = sg.unit_type
        WHERE sg.settlement_id = ?
    """, (settlement_id,))
    
    rows = cursor.fetchall()
    conn.close()
    
    total_units = 0
    total_attack = 0
    total_defense = 0
    total_health = 0
    units = []
    
    for row in rows:
        unit_data = dict(row)
        quantity = unit_data['quantity']
        
        total_units += quantity
        total_attack += quantity * unit_data['attack']
        total_defense += quantity * unit_data['defense']
        total_health += quantity * unit_data['health']
        
        units.append(unit_data)
    
    return {
        'total_units': total_units,
        'total_attack': total_attack,
        'total_defense': total_defense,
        'total_health': total_health,
        'units': units
    }