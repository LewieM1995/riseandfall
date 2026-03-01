from db.connection import connect_db

def get_all_npc_settlements() -> list[dict]:
    """Retrieve all NPC settlements with their resources and details"""

    conn = connect_db()
    cursor = conn.cursor()
    
    # Get all NPC settlements (where player.user_id IS NULL)
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
        JOIN players p ON s.player_id = p.id
        WHERE p.user_id IS NULL
        ORDER BY s.created_at ASC
    """)

    settlement_base_data = cursor.fetchall()
    settlements = []
    
    for settlement_row in settlement_base_data:
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
        
        settlement_dict.update(resources)
        
        # Get garrison strength
        cursor.execute("""
            SELECT SUM(quantity) as garrison_strength
            FROM garrison_units
            WHERE settlement_id = ?
        """, (settlement_id,))
        
        garrison_row = cursor.fetchone()
        settlement_dict['garrison_strength'] = garrison_row['garrison_strength'] or 0
        
        # Get total units
        cursor.execute("""
            SELECT SUM(quantity) as total_units
            FROM settlement_units
            WHERE settlement_id = ?
        """, (settlement_id,))
        
        unit_row = cursor.fetchone()
        settlement_dict['total_units'] = unit_row['total_units'] or 0
        
        settlements.append(settlement_dict)
    
    conn.close()

    return settlements