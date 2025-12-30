from datetime import datetime, timedelta

def apply_resource_tick(settlement_id, cursor):
    cursor.execute("""
        SELECT 
            s.food, s.wood, s.stone, s.silver, s.gold,
            s.last_resource_tick,
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
    
    #DEBUG LOGGING
    #print(f"Settlement {settlement_id}:")
    #print(f"Last tick: {last_tick}")
    #print(f"Current: {current_time}")
    #print(f"Elapsed: {elapsed_seconds} seconds")
    #print(f"Food before: {data['food']}")
    #print(f"Food rate: {data['food_rate']}")

    new_food = data['food'] + int(hours * data['food_rate'])
    new_wood = data['wood'] + int(hours * data['wood_rate'])
    new_stone = data['stone'] + int(hours * data['stone_rate'])
    new_silver = data['silver'] + int(hours * data['silver_rate'])

    #print(f"Food after: {new_food}")
    
    cursor.execute("""
        UPDATE settlements
        SET food = ?, wood = ?, stone = ?, silver = ?, last_resource_tick = ?
        WHERE id = ?
    """, (new_food, new_wood, new_stone, new_silver,
          current_time.isoformat(), settlement_id))