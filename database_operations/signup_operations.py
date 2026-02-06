from werkzeug.security import generate_password_hash
from db.connection import connect_db
from datetime import datetime

def user_exists(email: str) -> bool:
    conn = connect_db()
    cursor = conn.cursor()

    cursor.execute("SELECT id FROM users WHERE email = ?", (email,))
    exists = cursor.fetchone() is not None

    conn.close()
    return exists

def create_user(username: str, email: str, password: str) -> dict:
    conn = connect_db()
    cursor = conn.cursor()

    try:
        # Create user
        password_hash = generate_password_hash(password)
        cursor.execute(
            "INSERT INTO users (username, email, password_hash) VALUES (?, ?, ?)",
            (username, email, password_hash)
        )
        user_id = cursor.lastrowid

        # Create player
        cursor.execute(
            "INSERT INTO players (user_id, username, is_npc) VALUES (?, ?, 0)",
            (user_id, username)
        )
        player_id = cursor.lastrowid

        # Get village settlement type to retrieve base rates
        cursor.execute(
            "SELECT id, base_food_rate, base_wood_rate, base_stone_rate, base_silver_rate FROM settlement_types WHERE name = ?",
            ("village",)
        )
        settlement_type = cursor.fetchone()
        
        if not settlement_type:
            raise UserCreationError("Village settlement type not found. Database may not be seeded.")
        
        settlement_type_id = settlement_type[0]
        base_food = settlement_type[1]
        base_wood = settlement_type[2]
        base_stone = settlement_type[3]
        base_silver = settlement_type[4]

        # Create starting settlement with proper settlement_type_id and rate columns
        cursor.execute("""
            INSERT INTO settlements
            (player_id, name, x, y, settlement_type_id, 
             food, wood, stone, silver, gold,
             base_food_rate, base_wood_rate, base_stone_rate, base_silver_rate,
             current_food_rate, current_wood_rate, current_stone_rate, current_silver_rate)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            player_id,
            f"{username}'s Village",
            100, 100,
            settlement_type_id,
            800, 400, 200, 100, 5,
            base_food, base_wood, base_stone, base_silver,      # base rates from settlement_type
            base_food, base_wood, base_stone, base_silver       # current rates (same as base initially)
        ))

        settlement_id = cursor.lastrowid

        # Give player starting units (total army)
        cursor.executemany("""
            INSERT INTO player_units (player_id, unit_type, quantity)
            VALUES (?, ?, ?)
        """, [
            (player_id, "infantry", 20),
            (player_id, "archer", 10)
        ])

        # garrison some units in the starting settlement
        cursor.executemany("""
            INSERT INTO settlement_garrisons (settlement_id, unit_type, quantity)
            VALUES (?, ?, ?)
        """, [
            (settlement_id, "infantry", 10),
            (settlement_id, "archer", 5)
        ])
        
        cursor.execute("""
           INSERT INTO player_research (player_id, node_id, unlocked_at)
           VALUES (?, ?, ?)
        """, (player_id, 1, datetime.now()))  # Starting research node for testing

        conn.commit()
        
        return {
            "id": user_id,
            "username": username,
            "email": email,
            "player_id": player_id
        }

    except sqlite3.IntegrityError as e:
        conn.rollback()
        # Check what constraint failed
        error_msg = str(e).lower()
        if 'email' in error_msg:
            raise UserCreationError("Email already exists")
        elif 'username' in error_msg:
            raise UserCreationError("Username already taken")
        else:
            raise UserCreationError(f"Database constraint violation: {str(e)}")
    
    except UserCreationError:
        conn.rollback()
        raise
    
    except Exception as e:
        conn.rollback()
        raise UserCreationError(f"Failed to create user: {str(e)}")
    
    finally:
        conn.close()