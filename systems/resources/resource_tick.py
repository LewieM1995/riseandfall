from datetime import datetime, timedelta
from systems.experience.experience import check_level_up

MAX_CATCHUP_DAYS = 7
MAX_CATCHUP_SECONDS = MAX_CATCHUP_DAYS * 24 * 3600

def apply_resource_tick(settlement_id: int, cursor) -> None:
    """
    Process all active activities at a settlement and generate resources.
    
    For each in-progress activity:
    - Calculate hours elapsed since start
    - Generate resources: workers * base_rate * hours * modifiers
    - Add to settlement_resources
    - Update activity output
    """
    # Get all in-progress activities for this settlement
    cursor.execute("""
        SELECT 
            sa.id,
            sa.activity_type_id,
            sa.assigned_workers,
            sa.started_at,
            at.produces_resource,
            at.base_resource_per_hour,
            s.player_id
        FROM settlement_activities sa
        JOIN activity_types at ON sa.activity_type_id = at.id
        JOIN settlements s ON sa.settlement_id = s.id
        WHERE sa.settlement_id = ? AND sa.status = 'in_progress'
    """, (settlement_id,))
    
    activities = cursor.fetchall()
    if not activities:
        return
    
    current_time = datetime.utcnow()
    total_xp_gained = 0
    player_id = None
    
    for activity in activities:
        activity_id = activity['id']
        activity_type_id = activity['activity_type_id']
        assigned_workers = activity['assigned_workers']
        started_at = datetime.fromisoformat(activity['started_at'])
        resource_type = activity['produces_resource']
        base_rate = activity['base_resource_per_hour']
        player_id = activity['player_id']
        
        # Calculate elapsed time
        elapsed_seconds = int((current_time - started_at).total_seconds())
        elapsed_seconds = max(0, min(elapsed_seconds, MAX_CATCHUP_SECONDS))  # cap at 7 days
        
        if elapsed_seconds < 1:
            continue
        
        hours = elapsed_seconds / 3600
        
        # Get activity modifiers (buffs/debuffs)
        cursor.execute("""
            SELECT COALESCE(SUM(multiplier), 0.0) as total_modifier
            FROM activity_modifiers
            WHERE settlement_id = ? AND activity_type_id = ? 
            AND (expires_at IS NULL OR expires_at > ?)
        """, (settlement_id, activity_type_id, current_time))
        
        modifier_result = cursor.fetchone()
        modifier = modifier_result['total_modifier'] if modifier_result else 1.0
        
        # Calculate resource generation
        # Formula: workers * base_rate * hours * modifiers
        resource_generated = assigned_workers * base_rate * hours * modifier
        
        # Add to settlement resources
        cursor.execute("""
            INSERT INTO settlement_resources (settlement_id, resource_type, quantity, last_updated)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(settlement_id, resource_type)
            DO UPDATE SET quantity = quantity + excluded.quantity, last_updated = CURRENT_TIMESTAMP
        """, (settlement_id, resource_type, resource_generated, current_time.isoformat()))
        
        # Update activity's recorded output
        cursor.execute("""
            UPDATE settlement_activities 
            SET resource_output = resource_output + ?
            WHERE id = ?
        """, (resource_generated, activity_id))
        
        # Calculate XP gained
        # Different resources worth different XP
        xp_multipliers = {
            'food': 1.0,
            'wood': 1.0,
            'stone': 1.5,
            'silver': 2.0,
            'gold': 5.0,
            'pelt': 1.5,
            'defense': 2.0
        }
        
        xp_multiplier = xp_multipliers.get(resource_type, 1.0)
        xp_gained = int(resource_generated * xp_multiplier)
        total_xp_gained += xp_gained
        
        print(f"Settlement {settlement_id} Activity {activity_id}: "
              f"Generated {resource_generated:.0f} {resource_type} over {hours:.2f} hours "
              f"({assigned_workers} workers * {base_rate}/hr * {modifier:.2f} modifier). "
              f"XP gained: {xp_gained}")
    
    # Award total XP to player
    if total_xp_gained > 0 and player_id:
        cursor.execute("""
            UPDATE players
            SET experience = experience + ?
            WHERE id = ?
        """, (int(total_xp_gained), player_id))
        
        check_level_up(player_id, cursor)