def check_level_up(player_id: int, cursor) -> None:
    """Check and apply level ups."""
    cursor.execute("SELECT experience, level FROM players WHERE id = ?", (player_id,))
    data = cursor.fetchone()
    
    if not data:
        return
    
    xp_needed = calculate_xp_for_level(data['level'] + 1)
    
    if data['experience'] >= xp_needed:
        new_level = data['level'] + 1
        cursor.execute("""
            UPDATE players
            SET level = ?
            WHERE id = ?
        """, (new_level, player_id))
        
        # Recursively check for further level ups
        check_level_up(player_id, cursor)

def calculate_xp_for_level(level: int) -> int:
    """Calculate XP needed to reach a level."""
    return int(100 * pow(1.5, level - 1))

def get_player_experience(player_id: int) -> dict:
    """Get player's current level and experience."""
    from db.connection import connect_db
    
    conn = connect_db()
    cursor = conn.cursor()
    
    try:
        cursor.execute("""
            SELECT level, experience
            FROM players
            WHERE id = ?
        """, (player_id,))
        
        data = cursor.fetchone()
        
        if not data:
            return None
        
        return {
            "level": data["level"],
            "experience": data["experience"]
        }
    finally:
        conn.close()