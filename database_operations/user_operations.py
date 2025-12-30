from werkzeug.security import check_password_hash
from db.connection import connect_db

def authenticate_user(email, password):
    """Authenticate user and return user data if valid"""
    conn = connect_db()
    cursor = conn.cursor()
    
    cursor.execute("SELECT id, username, email, password_hash FROM users WHERE email = ?", (email,))
    user = cursor.fetchone()
    
    if not user:
        return None
    
    if not check_password_hash(user['password_hash'], password):
        return None
    
    return {
        "id": user['id'],
        "username": user['username'],
        "email": user['email']
    }

def get_player_id_for_user(user_id):
    """Get the player_id from the players table for a given user_id"""
    conn = connect_db()
    cursor = conn.cursor()
    
    try:
        cursor.execute("""
            SELECT id 
            FROM players 
            WHERE user_id = ?
        """, (user_id,))
        
        result = cursor.fetchone()
        
        if result:
            return result[0]
            
        return None
        
    finally:
        cursor.close()
        conn.close()