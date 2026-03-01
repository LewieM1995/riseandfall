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
    settlement_types = [
        ("village", "A small village", "/village.png"),
        ("town", "A bustling town", "/town.png"),
        ("castle", "A fortified castle", "/castle.png"),
        ("monastery", "A religious sanctuary", "/monastery.png"),
        ("outpost", "A remote outpost", "/outpost.png"),
    ]

    cursor.executemany("""
        INSERT OR IGNORE INTO settlement_types (name, description, image_path)
        VALUES (?, ?, ?)
    """, settlement_types)

    # Get settlement type ID for NPC settlement
    cursor.execute("SELECT id FROM settlement_types WHERE name = ?", ("castle",))
    castle_type_id = cursor.fetchone()[0]

    # --------------------
    # NPC SETTLEMENTS
    # --------------------
    cursor.execute("""
        INSERT OR IGNORE INTO settlements
        (player_id, name, settlement_type_id, x, y)
        VALUES (?, ?, ?, ?, ?)
    """, (
        npc_enemy_id,
        "Northumbria",
        castle_type_id,
        400, 150
    ))

    cursor.execute(
        "SELECT id FROM settlements WHERE name = ?",
        ("Northumbria",)
    )
    northumbria_id = cursor.fetchone()[0]

    # --------------------
    # WORKER TYPES
    # --------------------
    worker_types = [
        ("farmer", "Grows food and tends crops"),
        ("woodman", "Chops wood from forests"),
        ("stonemason", "Mines and quarries stone"),
        ("hunter", "Hunts animals for food and pelts"),
        ("builder", "Constructs structures and fortifications"),
        ("soldier", "Combat unit - melee"),
        ("archer", "Combat unit - ranged"),
    ]

    cursor.executemany("""
        INSERT OR IGNORE INTO worker_types (name, description)
        VALUES (?, ?)
    """, worker_types)

    # Get worker type IDs
    cursor.execute("SELECT id, name FROM worker_types")
    worker_type_map = {name: id for id, name in cursor.fetchall()}

    # --------------------
    # ACTIVITY TYPES
    # --------------------
    activity_types = [
        # Food production
        (worker_type_map["farmer"], "farm", "Tend crops and grow food", "food", 15.0),
        (worker_type_map["hunter"], "hunt", "Hunt animals for food", "food", 12.0),
        
        # Wood production
        (worker_type_map["woodman"], "chop_wood", "Harvest wood from forest", "wood", 10.0),
        
        # Stone production
        (worker_type_map["stonemason"], "mine_stone", "Quarry and mine stone", "stone", 8.0),
        
        # Construction activities
        (worker_type_map["builder"], "build_fence", "Build wooden fences", "defense", 5.0),
        (worker_type_map["builder"], "build_stone_wall", "Build stone walls", "defense", 10.0),
        (worker_type_map["builder"], "build_watchtower", "Build a watchtower", "defense", 15.0),
    ]

    cursor.executemany("""
        INSERT OR IGNORE INTO activity_types 
        (worker_type_id, name, description, produces_resource, base_resource_per_hour)
        VALUES (?, ?, ?, ?, ?)
    """, activity_types)

    # Get activity type IDs
    cursor.execute("SELECT id, name FROM activity_types")
    activity_type_map = {name: id for id, name in cursor.fetchall()}

    # --------------------
    # SETTLEMENT WORKERS (Initial population)
    # --------------------
    cursor.executemany("""
        INSERT OR IGNORE INTO settlement_workers
        (settlement_id, worker_type_id, quantity)
        VALUES (?, ?, ?)
    """, [
        (northumbria_id, worker_type_map["farmer"], 15),
        (northumbria_id, worker_type_map["woodman"], 10),
        (northumbria_id, worker_type_map["stonemason"], 8),
        (northumbria_id, worker_type_map["hunter"], 5),
        (northumbria_id, worker_type_map["builder"], 6),
        (northumbria_id, worker_type_map["soldier"], 20),
        (northumbria_id, worker_type_map["archer"], 10),
    ])

    # --------------------
    # SETTLEMENT RESOURCES (Initial resources)
    # --------------------
    cursor.executemany("""
        INSERT OR IGNORE INTO settlement_resources
        (settlement_id, resource_type, quantity)
        VALUES (?, ?, ?)
    """, [
        (northumbria_id, "food", 5000),
        (northumbria_id, "wood", 2000),
        (northumbria_id, "stone", 1000),
        (northumbria_id, "silver", 500),
        (northumbria_id, "gold", 100),
        (northumbria_id, "pelt", 0),
    ])

    # --------------------
    # STRUCTURES
    # --------------------
    structures = [
        ("wooden_fence", "A basic defensive structure", "defense: +5", 2.0, json.dumps({"wood": 100})),
        ("stone_wall", "A stronger defensive wall", "defense: +15", 6.0, json.dumps({"stone": 200, "wood": 50})),
        ("watchtower", "Provides vision and defense", "defense: +25, vision_range: 200", 8.0, json.dumps({"stone": 300, "wood": 100})),
        ("barracks", "Enables unit training", "unit_training: true", 4.0, json.dumps({"wood": 200, "stone": 100})),
        ("farm", "Increases food production", "food_production: +20", 1.0, json.dumps({"wood": 50})),
        ("lumber_mill", "Increases wood efficiency", "wood_production: +15", 3.0, json.dumps({"stone": 75, "wood": 100})),
        ("quarry", "Increases stone production", "stone_production: +15", 3.0, json.dumps({"wood": 75, "stone": 100})),
    ]

    cursor.executemany("""
        INSERT OR IGNORE INTO structures
        (name, description, provides, build_time_hours, requires_resources)
        VALUES (?, ?, ?, ?, ?)
    """, structures)

    # --------------------
    # UNIT TYPES (Definitions of available units)
    # --------------------
    cursor.executemany("""
        INSERT OR IGNORE INTO unit_types
        (name, description, attack, defense, health, cost_wood, cost_silver)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, [
        ("infantry", "Basic melee unit - reliable and cost-effective", 10, 5, 1, 10, 5),
        ("archer", "Ranged unit - good for defense and ranged attacks", 7, 3, 1, 15, 0),
        ("cavalry", "Heavy mounted unit - high attack and defense", 15, 10, 2, 20, 10),
    ])

    # Get unit type IDs
    cursor.execute("SELECT id, name FROM unit_types")
    unit_type_map = {name: id for id, name in cursor.fetchall()}

    # --------------------
    # SETTLEMENT UNITS - Primary storage
    # All units at a settlement (pool of available units)
    # --------------------
    cursor.executemany("""
        INSERT OR IGNORE INTO settlement_units
        (settlement_id, unit_type_id, quantity)
        VALUES (?, ?, ?)
    """, [
        # Northumbria (NPC settlement) - total units available
        (northumbria_id, unit_type_map["infantry"], 50),    # 50 infantry total
        (northumbria_id, unit_type_map["archer"], 25),      # 25 archers total
        (northumbria_id, unit_type_map["cavalry"], 15),     # 15 cavalry total
    ])

    # --------------------
    # GARRISON UNITS - Subset of settlement_units
    # Units currently assigned to defend the settlement
    # IMPORTANT: garrison quantity must be <= settlement_units quantity
    # --------------------
    cursor.executemany("""
        INSERT OR IGNORE INTO garrison_units
        (settlement_id, unit_type_id, quantity)
        VALUES (?, ?, ?)
    """, [
        # Northumbria - units currently defending (subset of total)
        (northumbria_id, unit_type_map["infantry"], 40),    # 40 of 50 defending
        (northumbria_id, unit_type_map["archer"], 15),      # 15 of 25 defending
        (northumbria_id, unit_type_map["cavalry"], 10),     # 10 of 15 defending
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