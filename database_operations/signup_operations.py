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

    # Create starting settlement
    cursor.execute("""
        INSERT INTO settlements
        (player_id, name, x, y, settlement_type, food, wood, stone, silver, gold)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        player_id,
        f"{username}'s Village",
        100, 100,
        "village",
        800, 400, 200, 100, 5
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
    conn.close()

    return {
        "id": user_id,
        "username": username,
        "email": email,
        "player_id": player_id
    }