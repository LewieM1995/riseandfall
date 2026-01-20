from datetime import datetime, timedelta
from systems.experience.experience import check_level_up

def apply_resource_tick(settlement_id: int, cursor) -> None:
    """Apply resource tick to a settlement based on elapsed time and production rates."""
    cursor.execute("""
        SELECT 
            s.food, s.wood, s.stone, s.silver, s.gold,
            s.last_resource_tick, s.player_id,
            st.food_rate, st.wood_rate, st.stone_rate, st.silver_rate
        FROM settlements s
        JOIN settlement_types st ON s.settlement_type = st.name
        WHERE s.id = ?
    """, (settlement_id,))
    
    data = cursor.fetchone()
    if not data:
        return
    
    current_time = datetime.utcnow()
    
    if not data['last_resource_tick']:
        last_tick = current_time
    else:
        last_tick = datetime.fromisoformat(data['last_resource_tick'])

    elapsed_seconds = max(0, min(int((current_time - last_tick).total_seconds()), 60 * 60 * 24))

    if elapsed_seconds < 1:
        return

    hours = elapsed_seconds / 3600
    
    food_gained = int(hours * data['food_rate'])
    wood_gained = int(hours * data['wood_rate'])
    stone_gained = int(hours * data['stone_rate'])
    silver_gained = int(hours * data['silver_rate'])
    
    new_food = data['food'] + food_gained
    new_wood = data['wood'] + wood_gained
    new_stone = data['stone'] + stone_gained
    new_silver = data['silver'] + silver_gained
    
    xp_gained = (
        food_gained * 1.0 +
        wood_gained * 1.0 +
        stone_gained * 1.5 +
        silver_gained * 2.0
    )
    
    cursor.execute("""
        UPDATE settlements
        SET food = ?, wood = ?, stone = ?, silver = ?, last_resource_tick = ?
        WHERE id = ?
    """, (new_food, new_wood, new_stone, new_silver,
          current_time.isoformat(), settlement_id))

    if xp_gained > 0:
        cursor.execute("""
            UPDATE players
            SET experience = experience + ?
            WHERE id = ?
        """, (int(xp_gained), data['player_id']))
        
        check_level_up(data['player_id'], cursor)