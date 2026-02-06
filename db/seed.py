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
        INSERT OR IGNORE INTO players (username, is_npc, level)
        VALUES ('npc_enemy', 1, 10);
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
        (name, base_food_rate, base_wood_rate, base_stone_rate, base_silver_rate, description)
        VALUES 
            ('village', 60.0, 36.0, 24.0, 12.0, 'A small village'),
            ('town', 120.0, 72.0, 48.0, 30.0, 'A bustling town'),
            ('city', 240.0, 150.0, 90.0, 60.0, 'A great city'),
            ('castle', 180.0, 90.0, 120.0, 90.0, 'A fortified castle'),
            ('outpost', 30.0, 90.0, 12.0, 6.0, 'A remote outpost');
    """)
    
    cursor.execute("SELECT id, name FROM settlement_types")
    settlement_type_ids = {name: id for id, name in cursor.fetchall()}
    
    # --------------------
    # NPC SETTLEMENTS
    # --------------------
    cursor.execute("""
        INSERT OR IGNORE INTO settlements
        (player_id, name, x, y, settlement_type_id, 
         food, wood, stone, silver, gold,
         base_food_rate, base_wood_rate, base_stone_rate, base_silver_rate,
         current_food_rate, current_wood_rate, current_stone_rate, current_silver_rate)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        npc_enemy_id,
        "Northumbria",
        400, 150,
        settlement_type_ids["castle"], 
        1000, 500, 200, 100, 10,
        180.0, 90.0, 120.0, 90.0,  # base rates from castle type
        180.0, 90.0, 120.0, 90.0   # current rates (same as base initially)
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

    # --------------------
    # RESEARCH NODES - SETTLEMENTS
    # --------------------
    settlement_research = [
        ("settlements", "Basic Fortifications", "Unlock castle settlement type", 5, 0, 500, 300, 0, 0, 1.0),
        ("settlements", "Urban Planning", "Unlock town settlement type", 3, 0, 300, 200, 100, 0, 0.5),
        ("settlements", "Advanced Architecture", "Unlock city settlement type", 10, 0, 1000, 800, 500, 0, 2.0),
        ("settlements", "Frontier Expansion", "Unlock outpost settlement type", 2, 0, 200, 100, 0, 0, 0.25),
    ]

    cursor.executemany("""
        INSERT OR IGNORE INTO research_nodes
        (sector, name, description, required_player_level, cost_food, cost_wood, cost_stone, cost_silver, cost_gold, research_time_hours)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, settlement_research)

    # --------------------
    # RESEARCH NODES - ECONOMY
    # --------------------
    economy_research = [
        ("economy", "Improved Farming", "Increase food production by 25%", 2, 0, 100, 0, 50, 0, 0.5),
        ("economy", "Logging Efficiency", "Increase wood production by 25%", 2, 0, 150, 0, 50, 0, 0.5),
        ("economy", "Quarry Mastery", "Increase stone production by 25%", 3, 0, 200, 100, 75, 0, 1.0),
        ("economy", "Trade Routes", "Increase silver production by 30%", 4, 0, 0, 0, 200, 0, 1.0),
        ("economy", "Master Economics", "Increase all resource production by 15%", 8, 0, 500, 300, 400, 0, 2.0),
    ]

    cursor.executemany("""
        INSERT OR IGNORE INTO research_nodes
        (sector, name, description, required_player_level, cost_food, cost_wood, cost_stone, cost_silver, cost_gold, research_time_hours)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, economy_research)

    # --------------------
    # RESEARCH NODES - ARMY
    # --------------------
    army_research = [
        ("army", "Infantry Training", "Increase infantry attack by 20%", 2, 100, 50, 0, 50, 0, 0.5),
        ("army", "Archery Range", "Increase archer attack by 20%", 3, 100, 100, 0, 75, 0, 0.75),
        ("army", "Cavalry Tactics", "Increase cavalry attack by 20%", 4, 150, 100, 0, 100, 0, 1.0),
        ("army", "Shield Wall", "Increase infantry defense by 25%", 5, 200, 150, 50, 100, 0, 1.0),
        ("army", "Heavy Armor", "Increase all unit defense by 15%", 7, 300, 200, 200, 200, 0, 2.0),
        ("army", "War Tactics", "Increase all unit attack by 15%", 9, 400, 300, 100, 300, 0, 2.5),
    ]

    cursor.executemany("""
        INSERT OR IGNORE INTO research_nodes
        (sector, name, description, required_player_level, cost_food, cost_wood, cost_stone, cost_silver, cost_gold, research_time_hours)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, army_research)

    # --------------------
    # RESEARCH NODES - DIPLOMACY
    # --------------------
    diplomacy_research = [
        ("diplomacy", "Basic Diplomacy", "Unlock alliance features", 3, 0, 0, 0, 100, 0, 0.5),
        ("diplomacy", "Trade Agreements", "Reduce resource trade costs by 20%", 5, 0, 200, 0, 200, 0, 1.0),
        ("diplomacy", "Espionage", "Unlock spy actions", 6, 0, 100, 0, 300, 0, 1.5),
        ("diplomacy", "Grand Alliance", "Increase alliance member limit", 10, 0, 500, 0, 500, 0, 2.0),
    ]

    cursor.executemany("""
        INSERT OR IGNORE INTO research_nodes
        (sector, name, description, required_player_level, cost_food, cost_wood, cost_stone, cost_silver, cost_gold, research_time_hours)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, diplomacy_research)

    # --------------------
    # RESEARCH EFFECTS
    # --------------------
    # Get node IDs for effect assignment
    cursor.execute("SELECT id, name FROM research_nodes")
    nodes = {name: node_id for node_id, name in cursor.fetchall()}

    research_effects = [
        # Settlement unlocks
        (nodes["Basic Fortifications"], "unlock_settlement", "castle", 1, "Unlocks castle settlement type"),
        (nodes["Urban Planning"], "unlock_settlement", "town", 1, "Unlocks town settlement type"),
        (nodes["Advanced Architecture"], "unlock_settlement", "city", 1, "Unlocks city settlement type"),
        (nodes["Frontier Expansion"], "unlock_settlement", "outpost", 1, "Unlocks outpost settlement type"),
        
        # Economy bonuses
        (nodes["Improved Farming"], "production_bonus", "food", 1.25, "+25% food production"),
        (nodes["Logging Efficiency"], "production_bonus", "wood", 1.25, "+25% wood production"),
        (nodes["Quarry Mastery"], "production_bonus", "stone", 1.25, "+25% stone production"),
        (nodes["Trade Routes"], "production_bonus", "silver", 1.30, "+30% silver production"),
        (nodes["Master Economics"], "production_bonus", "all", 1.15, "+15% all resource production"),
        
        # Army bonuses
        (nodes["Infantry Training"], "unit_attack_bonus", "infantry", 1.20, "+20% infantry attack"),
        (nodes["Archery Range"], "unit_attack_bonus", "archer", 1.20, "+20% archer attack"),
        (nodes["Cavalry Tactics"], "unit_attack_bonus", "cavalry", 1.20, "+20% cavalry attack"),
        (nodes["Shield Wall"], "unit_defense_bonus", "infantry", 1.25, "+25% infantry defense"),
        (nodes["Heavy Armor"], "unit_defense_bonus", "all", 1.15, "+15% all unit defense"),
        (nodes["War Tactics"], "unit_attack_bonus", "all", 1.15, "+15% all unit attack"),
        
        # Diplomacy features
        (nodes["Basic Diplomacy"], "unlock_feature", "alliance", 1, "Unlocks alliance system"),
        (nodes["Trade Agreements"], "trade_cost_reduction", "all", 0.80, "-20% trade costs"),
        (nodes["Espionage"], "unlock_feature", "spy", 1, "Unlocks espionage actions"),
        (nodes["Grand Alliance"], "alliance_member_increase", "all", 10, "+10 alliance member slots"),
    ]

    cursor.executemany("""
        INSERT OR IGNORE INTO research_effects
        (node_id, effect_type, target, value, description)
        VALUES (?, ?, ?, ?, ?)
    """, research_effects)

    conn.commit()
    conn.close()
    print("Seed data inserted successfully.")

if __name__ == "__main__":
    seed_db()
    
# python3 -m db.seed_db