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
            resource_type,
            COALESCE(SUM(quantity), 0) as total_amount
        FROM settlement_resources sr
        JOIN settlements s ON sr.settlement_id = s.id
        WHERE s.player_id = ?
        GROUP BY sr.resource_type
    """, (player_id,))

    results = cursor.fetchall()
    conn.close()

    # Init all resource
    resources = {
        'total_food': 0,
        'total_wood': 0,
        'total_stone': 0,
        'total_silver': 0,
        'total_gold': 0,
        'total_pelt': 0
    }

    resource_mapping = {
        'food': 'total_food',
        'wood': 'total_wood',
        'stone': 'total_stone',
        'silver': 'total_silver',
        'gold': 'total_gold',
        'pelt': 'total_pelt'
    }

    for resource_type, total_amount in results:
        key = resource_mapping.get(resource_type)
        if key:
            resources[key] = int(total_amount)

    return resources