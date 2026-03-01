from db.connection import connect_db
from database_operations.user_operations import get_player_id_for_user


def get_player_settlements_for_user(user_id: int) -> list[dict]:
    """
    Retrieve all settlements for a given user with their resources and status.
    
    Returns a list of settlements with:
    - Basic info: id, name, x, y, created_at
    - Resources: food, wood, stone, silver, gold, pelt
    - Active activities count
    - Worker summary
    """
    
    player_id = get_player_id_for_user(user_id)

    conn = connect_db()
    cursor = conn.cursor()

    # Get all settlements for this player with their locations
    cursor.execute("""
        SELECT
            s.id,
            s.name,
            s.settlement_type_id,
            st.name as settlement_type,
            s.x,
            s.y,
            s.created_at
        FROM settlements s
        LEFT JOIN settlement_types st ON s.settlement_type_id = st.id
        WHERE s.player_id = ?
        ORDER BY s.created_at ASC
    """, (player_id,))
    
    settlement_rows = cursor.fetchall()
    settlements = []
    
    for settlement_row in settlement_rows:
        settlement_id = settlement_row['id']
        settlement_dict = dict(settlement_row)
        
        # Get resources for this settlement
        cursor.execute("""
            SELECT resource_type, quantity
            FROM settlement_resources
            WHERE settlement_id = ?
        """, (settlement_id,))
        
        resources = {
            'food': 0,
            'wood': 0,
            'stone': 0,
            'silver': 0,
            'gold': 0,
            'pelt': 0
        }
        
        for resource_row in cursor.fetchall():
            resource_type = resource_row['resource_type']
            if resource_type in resources:
                resources[resource_type] = int(resource_row['quantity'])
        
        # Add resources to settlement dict
        settlement_dict.update(resources)
        
        # Get worker count for this settlement
        cursor.execute("""
            SELECT COUNT(DISTINCT worker_type_id) as worker_types, 
                   SUM(quantity) as total_workers
            FROM settlement_workers
            WHERE settlement_id = ?
        """, (settlement_id,))
        
        worker_row = cursor.fetchone()
        settlement_dict['worker_types'] = worker_row['worker_types'] or 0
        settlement_dict['total_workers'] = worker_row['total_workers'] or 0
        
        # Get count of active activities
        cursor.execute("""
            SELECT COUNT(*) as active_activities
            FROM settlement_activities
            WHERE settlement_id = ? AND status = 'in_progress'
        """, (settlement_id,))
        
        activity_row = cursor.fetchone()
        settlement_dict['active_activities'] = activity_row['active_activities'] or 0
        
        # Get total units at this settlement
        cursor.execute("""
            SELECT COUNT(DISTINCT unit_type_id) as unit_types,
                   SUM(quantity) as total_units
            FROM settlement_units
            WHERE settlement_id = ?
        """, (settlement_id,))
        
        unit_row = cursor.fetchone()
        settlement_dict['unit_types'] = unit_row['unit_types'] or 0
        settlement_dict['total_units'] = unit_row['total_units'] or 0
        
        # Get garrison strength (units defending)
        cursor.execute("""
            SELECT SUM(quantity) as garrison_strength
            FROM garrison_units
            WHERE settlement_id = ?
        """, (settlement_id,))
        
        garrison_row = cursor.fetchone()
        settlement_dict['garrison_strength'] = garrison_row['garrison_strength'] or 0
        
        settlements.append(settlement_dict)

    conn.close()

    return settlements