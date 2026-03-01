import sqlite3
from werkzeug.security import generate_password_hash
from db.connection import connect_db
from datetime import datetime


class UserCreationError(Exception):
    """Custom exception for user creation errors"""
    pass


def user_exists(email: str) -> bool:
    """Check if a user with the given email already exists."""
    conn = connect_db()
    cursor = conn.cursor()

    cursor.execute("SELECT id FROM users WHERE email = ?", (email,))
    exists = cursor.fetchone() is not None

    conn.close()
    return exists


def create_user(username: str, email: str, password: str) -> dict:
    """
    Create a new user with a player and starting settlement.
    
    Args:
        username: User's chosen username
        email: User's email address
        password: User's password (will be hashed)
    
    Returns:
        Dictionary with user_id, username, email, player_id, settlement_id
    
    Raises:
        UserCreationError: If user creation fails
    """
    conn = connect_db()
    cursor = conn.cursor()

    try:
        # create user account
        password_hash = generate_password_hash(password)
        cursor.execute(
            "INSERT INTO users (username, email, password_hash) VALUES (?, ?, ?)",
            (username, email, password_hash)
        )
        user_id = cursor.lastrowid

        # Create player associated with user
        cursor.execute(
            "INSERT INTO players (user_id, username, is_npc) VALUES (?, ?, 0)",
            (user_id, username)
        )
        player_id = cursor.lastrowid

        # Get default settlement type (village)
        cursor.execute(
            "SELECT id FROM settlement_types WHERE name = ?",
            ("village",)
        )
        village_type = cursor.fetchone()
        if not village_type:
            raise UserCreationError(
                "Settlement types not found. Please run 'python3 -m db.seed_db' to initialize database."
            )
        village_type_id = village_type[0]

        # Create starting settlement
        cursor.execute("""
            INSERT INTO settlements (player_id, name, settlement_type_id, x, y)
            VALUES (?, ?, ?, ?, ?)
        """, (
            player_id,
            f"{username}'s Village",
            village_type_id,
            100, 100
        ))
        settlement_id = cursor.lastrowid

        # Init settlement with starting workers
        # Get worker type IDs
        cursor.execute("SELECT id, name FROM worker_types WHERE name IN ('farmer', 'woodman', 'stonemason', 'hunter')")
        worker_types = {name: wid for wid, name in cursor.fetchall()}
        
        if not worker_types or len(worker_types) < 4:
            raise UserCreationError(
                "Worker types not found. Please run 'python3 -m db.seed_db' to initialize database."
            )
        
        # Assign starting workers to settlement
        cursor.executemany("""
            INSERT INTO settlement_workers (settlement_id, worker_type_id, quantity)
            VALUES (?, ?, ?)
        """, [
            (settlement_id, worker_types["farmer"], 10),
            (settlement_id, worker_types["woodman"], 5),
            (settlement_id, worker_types["stonemason"], 3),
            (settlement_id, worker_types["hunter"], 2),
        ])

        # Init settlement resources
        starting_amounts = {
            "food": 1000,
            "wood": 500,
            "stone": 300,
            "silver": 100,
            "gold": 10
        }
        
        cursor.executemany("""
            INSERT INTO settlement_resources (settlement_id, resource_type, quantity)
            VALUES (?, ?, ?)
        """, [
            (settlement_id, resource, amount)
            for resource, amount in starting_amounts.items()
        ])

        # get unit type IDs
        cursor.execute("SELECT id, name FROM unit_types WHERE name IN ('infantry', 'archer')")
        unit_types = {name: uid for uid, name in cursor.fetchall()}
        
        if not unit_types:
            raise UserCreationError(
                "Unit types not found. Please run 'python3 -m db.seed_db' to initialize database."
            )
        
        # Assign starting units to settlement
        cursor.executemany("""
            INSERT INTO settlement_units (settlement_id, unit_type_id, quantity)
            VALUES (?, ?, ?)
        """, [
            (settlement_id, unit_types["infantry"], 20),
            (settlement_id, unit_types["archer"], 10)
        ])

        # Set up garrison (units defending the settlement)
        cursor.executemany("""
            INSERT INTO garrison_units (settlement_id, unit_type_id, quantity)
            VALUES (?, ?, ?)
        """, [
            (settlement_id, unit_types["infantry"], 10),
            (settlement_id, unit_types["archer"], 5)
        ])
        
        # Give player starting research (optional - for testing/onboarding)
        # Get first settlement research node
        cursor.execute(
            "SELECT id FROM research_nodes WHERE sector = 'settlements' LIMIT 1"
        )
        first_research = cursor.fetchone()
        
        if first_research:
            cursor.execute("""
                INSERT INTO player_research (player_id, node_id, unlocked_at)
                VALUES (?, ?, ?)
            """, (player_id, first_research[0], datetime.now()))

        conn.commit()
        
        return {
            "id": user_id,
            "username": username,
            "email": email,
            "player_id": player_id,
            "settlement_id": settlement_id
        }

    except sqlite3.IntegrityError as e:
        conn.rollback()
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