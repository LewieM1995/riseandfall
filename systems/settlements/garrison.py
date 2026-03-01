from db.connection import connect_db
from database_operations.user_operations import get_player_id_for_user


def get_settlement_garrison(settlement_id: int, user_id: int) -> dict | None:
    """
    Retrieve garrison (defending) units for a settlement owned by the user.
    
    Returns garrison strength and individual unit details.
    """
    player_id = get_player_id_for_user(user_id)
    
    conn = connect_db()
    cursor = conn.cursor()
    
    # Verify settlement belongs to player
    cursor.execute("""
        SELECT player_id FROM settlements WHERE id = ?
    """, (settlement_id,))
    
    result = cursor.fetchone()
    if not result or result['player_id'] != player_id:
        conn.close()
        return None
    
    # Get garrison units (units defending the settlement)
    cursor.execute("""
        SELECT 
            gu.unit_type_id,
            ut.name,
            gu.quantity,
            ut.attack,
            ut.defense,
            ut.health
        FROM garrison_units gu
        JOIN unit_types ut ON ut.id = gu.unit_type_id
        WHERE gu.settlement_id = ?
        ORDER BY ut.name
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
        
        units.append({
            'unit_type_id': unit_data['unit_type_id'],
            'name': unit_data['name'],
            'quantity': quantity,
            'attack': unit_data['attack'],
            'defense': unit_data['defense'],
            'health': unit_data['health'],
            'total_attack': quantity * unit_data['attack'],
            'total_defense': quantity * unit_data['defense'],
            'total_health': quantity * unit_data['health']
        })
    
    return {
        'settlement_id': settlement_id,
        'total_units': total_units,
        'total_attack': total_attack,
        'total_defense': total_defense,
        'total_health': total_health,
        'units': units
    }


def get_settlement_all_units(settlement_id: int, user_id: int) -> dict | None:
    """
    Retrieve ALL units at a settlement (not just garrison).
    
    This includes all units located at the settlement (garrison + staged for movement).
    """
    player_id = get_player_id_for_user(user_id)
    
    conn = connect_db()
    cursor = conn.cursor()
    
    # Verify settlement belongs to player
    cursor.execute("""
        SELECT player_id FROM settlements WHERE id = ?
    """, (settlement_id,))
    
    result = cursor.fetchone()
    if not result or result['player_id'] != player_id:
        conn.close()
        return None
    
    # Get all units at this settlement
    cursor.execute("""
        SELECT 
            su.unit_type_id,
            ut.name,
            su.quantity,
            ut.attack,
            ut.defense,
            ut.health
        FROM settlement_units su
        JOIN unit_types ut ON ut.id = su.unit_type_id
        WHERE su.settlement_id = ?
        ORDER BY ut.name
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
        
        units.append({
            'unit_type_id': unit_data['unit_type_id'],
            'name': unit_data['name'],
            'quantity': quantity,
            'attack': unit_data['attack'],
            'defense': unit_data['defense'],
            'health': unit_data['health'],
            'total_attack': quantity * unit_data['attack'],
            'total_defense': quantity * unit_data['defense'],
            'total_health': quantity * unit_data['health']
        })
    
    return {
        'settlement_id': settlement_id,
        'total_units': total_units,
        'total_attack': total_attack,
        'total_defense': total_defense,
        'total_health': total_health,
        'units': units
    }