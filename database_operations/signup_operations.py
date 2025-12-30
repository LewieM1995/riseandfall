from werkzeug.security import generate_password_hash
from db.connection import connect_db

def user_exists(email):
    conn = connect_db()
    cursor = conn.cursor()

    cursor.execute("SELECT id FROM users WHERE email = ?", (email,))
    exists = cursor.fetchone() is not None

    conn.close()
    return exists

def create_user(username, email, password):
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

    # Create starting settlement(s)
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

    # Create starter army
    cursor.execute("""
        INSERT INTO armies (player_id, location_settlement_id)
        VALUES (?, ?)
    """, (player_id, settlement_id))

    army_id = cursor.lastrowid

    cursor.executemany("""
        INSERT INTO army_units (army_id, unit_type, quantity)
        VALUES (?, ?, ?)
    """, [
        (army_id, "infantry", 20),
        (army_id, "archer", 10)
    ])

    conn.commit()
    conn.close()

    return {
        "id": user_id,
        "username": username,
        "email": email,
        "player_id": player_id
    }
