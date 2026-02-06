from datetime import datetime, timedelta
from systems.experience.experience import check_level_up

MAX_CATCHUP_DAYS = 7
MAX_CATCHUP_SECONDS = MAX_CATCHUP_DAYS * 24 * 3600

def apply_resource_tick(settlement_id: int, cursor) -> None:
    """Apply resource tick to a settlement based on elapsed time and production rates."""
    cursor.execute("""
        SELECT 
            s.food, s.wood, s.stone, s.silver, s.gold,
            s.food_capacity, s.wood_capacity, s.stone_capacity, 
            s.silver_capacity, s.gold_capacity,
            s.last_resource_tick, s.player_id,
            s.current_food_rate, s.current_wood_rate, 
            s.current_stone_rate, s.current_silver_rate
        FROM settlements s
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

    elapsed_seconds = int((current_time - last_tick).total_seconds())

    elapsed_seconds = max(0, min(elapsed_seconds, MAX_CATCHUP_SECONDS)) # cap at 7 days worth of seconds

    if elapsed_seconds < 1:
        return

    hours = elapsed_seconds / 3600
    
    food_gained = hours * data['current_food_rate']
    wood_gained = hours * data['current_wood_rate']
    stone_gained = hours * data['current_stone_rate']
    silver_gained = hours * data['current_silver_rate']
    
    new_food = min(data['food'] + food_gained, data['food_capacity'])
    new_wood = min(data['wood'] + wood_gained, data['wood_capacity'])
    new_stone = min(data['stone'] + stone_gained, data['stone_capacity'])
    new_silver = min(data['silver'] + silver_gained, data['silver_capacity'])
    
    actual_food_gained = new_food - data['food']
    actual_wood_gained = new_wood - data['wood']
    actual_stone_gained = new_stone - data['stone']
    actual_silver_gained = new_silver - data['silver']
    
    xp_gained = int(
        actual_food_gained * 1.0 +
        actual_wood_gained * 1.0 +
        actual_stone_gained * 1.5 +
        actual_silver_gained * 2.0
    )
    
    print(f"Settlement {settlement_id} gained {food_gained} food, {wood_gained} wood, "
          f"{stone_gained} stone, {silver_gained} silver over {elapsed_seconds} seconds. "
          f"XP gained: {xp_gained}")

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