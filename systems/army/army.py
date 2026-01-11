from db.connection import connect_db
from database_operations.user_operations import get_player_id_for_user

def get_player_armies_for_user(user_id: int) -> dict:
    """Retrieve detailed army information for a user, including standing and total armies."""
    player_id = get_player_id_for_user(user_id)
    
    conn = connect_db()
    cursor = conn.cursor()
    
    # Get player's army summary
    cursor.execute("""
        SELECT 
            pu.unit_type,
            pu.quantity as total,
            COALESCE(SUM(sg.quantity), 0) as garrisoned,
            (pu.quantity - COALESCE(SUM(sg.quantity), 0)) as available,
            ut.attack,
            ut.defense,
            ut.health,
            ut.cost_wood,
            ut.cost_silver
        FROM player_units pu
        LEFT JOIN settlements s ON s.player_id = ?
        LEFT JOIN settlement_garrisons sg ON sg.settlement_id = s.id 
            AND sg.unit_type = pu.unit_type
        LEFT JOIN unit_types ut ON ut.unit_type = pu.unit_type
        WHERE pu.player_id = ?
        GROUP BY pu.unit_type, pu.quantity
    """, (player_id, player_id))
    
    rows = cursor.fetchall()
    conn.close()
    
    # Calculate standing army totals
    standing_army = {
        "total_units": 0,
        "total_attack": 0,
        "total_defense": 0,
        "total_health": 0,
        "units": []
    }
    
    total_army = {
        "total_units": 0,
        "total_attack": 0,
        "total_defense": 0,
        "total_health": 0,
        "units": []
    }
    
    for row in rows:
        unit_data = dict(row)
        available = unit_data['available']
        total = unit_data['total']
        
        # Standing army (available units)
        standing_army["total_units"] += available
        standing_army["total_attack"] += available * unit_data['attack']
        standing_army["total_defense"] += available * unit_data['defense']
        standing_army["total_health"] += available * unit_data['health']
        standing_army["units"].append({
            "unit_type": unit_data['unit_type'],
            "quantity": available,
            "attack": unit_data['attack'],
            "defense": unit_data['defense'],
            "health": unit_data['health']
        })
        
        # Total army
        total_army["total_units"] += total
        total_army["total_attack"] += total * unit_data['attack']
        total_army["total_defense"] += total * unit_data['defense']
        total_army["total_health"] += total * unit_data['health']
        total_army["units"].append({
            "unit_type": unit_data['unit_type'],
            "quantity": total,
            "attack": unit_data['attack'],
            "defense": unit_data['defense'],
            "health": unit_data['health'],
            "garrisoned": unit_data['garrisoned']
        })
    
    return {
        "player_id": player_id,
        "standing_army": standing_army,
        "total_army": total_army
    }