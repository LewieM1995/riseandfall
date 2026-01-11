import json
from datetime import datetime
from db.connection import connect_db

def seed_db():
    """Seed the database with initial data for testing and development."""
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute("PRAGMA foreign_keys = ON;")

    # --------------------
    # NPC PLAYERS
    # --------------------
    cursor.execute("""
        INSERT OR IGNORE INTO players (username, is_npc)
        VALUES ('npc_enemy', 1);
    """)

    cursor.execute(
        "SELECT id FROM players WHERE username = ?",
        ("npc_enemy",)
    )
    npc_enemy_id = cursor.fetchone()[0]

    # --------------------
    # SETTLEMENT TYPES
    # --------------------
    cursor.execute("""
        INSERT OR IGNORE INTO settlement_types
        (name, food_rate, wood_rate, stone_rate, silver_rate, max_population, description)
        VALUES 
            ('village', 60.0, 36.0, 24.0, 12.0, 100, 'A small village'),
            ('town', 120.0, 72.0, 48.0, 30.0, 500, 'A bustling town'),
            ('city', 240.0, 150.0, 90.0, 60.0, 2000, 'A great city'),
            ('castle', 180.0, 90.0, 120.0, 90.0, 2000, 'A fortified castle'),
            ('outpost', 30.0, 90.0, 12.0, 6.0, 50, 'A remote outpost');
    """)
    
    # --------------------
    # NPC SETTLEMENTS
    # --------------------
    cursor.execute("""
        INSERT OR IGNORE INTO settlements
        (player_id, name, x, y, settlement_type, food, wood, stone, silver, gold)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        npc_enemy_id,
        "Northumbria",
        400, 150,
        "castle",
        1000, 500, 200, 100, 10
    ))

    cursor.execute(
        "SELECT id FROM settlements WHERE name = ?",
        ("Northumbria",)
    )
    northumbria_id = cursor.fetchone()[0]

    # --------------------
    # UNIT TYPES
    # --------------------
    unit_types = [
        ("infantry", 10, 5, 1, 10, 5),
        ("archer", 7, 3, 1, 15, 0),
        ("cavalry", 15, 10, 2, 20, 10)
    ]

    cursor.executemany("""
        INSERT OR IGNORE INTO unit_types
        (unit_type, attack, defense, health, cost_wood, cost_silver)
        VALUES (?, ?, ?, ?, ?, ?)
    """, unit_types)

    # --------------------
    # NPC PLAYER UNITS (Total Army)
    # --------------------
    cursor.executemany("""
        INSERT OR IGNORE INTO player_units
        (player_id, unit_type, quantity)
        VALUES (?, ?, ?)
    """, [
        (npc_enemy_id, "infantry", 100),
        (npc_enemy_id, "archer", 50),
        (npc_enemy_id, "cavalry", 30)
    ])

    # --------------------
    # NPC GARRISON
    # --------------------
    cursor.executemany("""
        INSERT OR IGNORE INTO settlement_garrisons
        (settlement_id, unit_type, quantity)
        VALUES (?, ?, ?)
    """, [
        (northumbria_id, "infantry", 40),
        (northumbria_id, "archer", 15),
        (northumbria_id, "cavalry", 10)
    ])

    conn.commit()
    conn.close()
    print("Seed data inserted successfully.")

if __name__ == "__main__":
    seed_db()