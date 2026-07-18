import json
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
    # base_plot_count / base_defense are placeholder balance numbers —
    # tune by hand. Global plot cap (10) is enforced in application code.
    # --------------------
    settlement_types = [
        ("fort", "A defensible frontier holding", "/fort.png", 5, 30),
        ("village", "A small village", "/village.png", 5, 10),
        ("town", "A bustling town", "/town.png", 6, 15),
        ("castle", "A fortified castle", "/castle.png", 7, 50),
        ("city", "A grand fortified city", "/city.png", 8, 40),
        ("monastery", "A religious sanctuary", "/monastery.png", 6, 10),
        ("outpost", "A remote outpost", "/outpost.png", 4, 5),
    ]

    cursor.executemany("""
        INSERT OR IGNORE INTO settlement_types
        (name, description, image_path, base_plot_count, base_defense)
        VALUES (?, ?, ?, ?, ?)
    """, settlement_types)

    cursor.execute("SELECT id, name FROM settlement_types")
    settlement_type_map = {name: id for id, name in cursor.fetchall()}

    # --------------------
    # NPC SETTLEMENT
    # --------------------
    cursor.execute("""
        INSERT OR IGNORE INTO settlements
        (player_id, name, settlement_type_id, x, y, last_ticked_at)
        VALUES (?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
    """, (
        npc_enemy_id,
        "Northumbria",
        settlement_type_map["castle"],
        400, 150
    ))

    cursor.execute(
        "SELECT id FROM settlements WHERE name = ?",
        ("Northumbria",)
    )
    northumbria_id = cursor.fetchone()[0]

    # --------------------
    # SETTLEMENT RESOURCE MODIFIERS (Geography)
    # Northumbria sits on rich stone deposits — a small permanent bonus,
    # hand-set rather than randomly rolled.
    # --------------------
    cursor.executemany("""
        INSERT OR IGNORE INTO settlement_resource_modifiers
        (settlement_id, resource_type, multiplier)
        VALUES (?, ?, ?)
    """, [
        (northumbria_id, "stone", 1.25),
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
    # produces_resource/base_resource_per_hour drive the plot-based tick
    # directly. Non-production structures (walls, watchtower, barracks)
    # leave these NULL/0 and instead carry structure_effects rows below.
    # --------------------
    structures = [
        # name, description, produces_resource, base_resource_per_hour, build_time_hours, requires_resources(json)
        ("farm", "Grows food", "food", 15.0, 1.0, json.dumps({"wood": 50})),
        ("hunting_lodge", "Hunts game for food and pelts", "food", 12.0, 1.5, json.dumps({"wood": 75})),
        ("lumber_camp", "Harvests wood from nearby forest", "wood", 10.0, 1.0, json.dumps({"wood": 30})),
        ("quarry", "Mines and cuts stone", "stone", 8.0, 2.0, json.dumps({"wood": 75, "stone": 25})),
        ("silver_mine", "Extracts silver ore", "silver", 4.0, 3.0, json.dumps({"wood": 100, "stone": 100})),
        ("gold_mine", "Extracts gold ore — rare and slow", "gold", 1.5, 5.0, json.dumps({"wood": 150, "stone": 150})),
        ("trapper_camp", "Traps furs for pelts", "pelt", 5.0, 1.5, json.dumps({"wood": 60})),

        ("wooden_fence", "A basic defensive structure", None, 0, 2.0, json.dumps({"wood": 100})),
        ("stone_wall", "A stronger defensive wall", None, 0, 6.0, json.dumps({"stone": 200, "wood": 50})),
        ("watchtower", "Provides vision and defense", None, 0, 8.0, json.dumps({"stone": 300, "wood": 100})),
        ("barracks", "Enables unit training", None, 0, 4.0, json.dumps({"wood": 200, "stone": 100})),
    ]

    cursor.executemany("""
        INSERT OR IGNORE INTO structures
        (name, description, produces_resource, base_resource_per_hour, build_time_hours, requires_resources)
        VALUES (?, ?, ?, ?, ?, ?)
    """, structures)

    cursor.execute("SELECT id, name FROM structures")
    structure_map = {name: id for id, name in cursor.fetchall()}

    # --------------------
    # STRUCTURE EFFECTS (Passive bonuses — defense, unlocks)
    # --------------------
    structure_effects = [
        (structure_map["wooden_fence"], "defense", None, 5, "+5 defense"),
        (structure_map["stone_wall"], "defense", None, 15, "+15 defense"),
        (structure_map["watchtower"], "defense", None, 25, "+25 defense"),
        (structure_map["barracks"], "unlock_feature", "unit_training", 1, "Enables unit training"),
    ]

    cursor.executemany("""
        INSERT OR IGNORE INTO structure_effects
        (structure_id, effect_type, target, value, description)
        VALUES (?, ?, ?, ?, ?)
    """, structure_effects)

    # --------------------
    # NORTHUMBRIA'S PLOTS
    # 7 plots (castle base_plot_count). A mix of production + defense,
    # left partially empty to demonstrate an unassigned plot.
    # --------------------
    plot_assignments = [
        (0, structure_map["farm"]),
        (1, structure_map["farm"]),
        (2, structure_map["quarry"]),
        (3, structure_map["lumber_camp"]),
        (4, structure_map["silver_mine"]),
        (5, structure_map["stone_wall"]),
        (6, None),  # empty plot
    ]

    for plot_index, structure_id in plot_assignments:
        cursor.execute("""
            INSERT OR IGNORE INTO settlement_plots
            (settlement_id, plot_index, structure_id, built_at)
            VALUES (?, ?, ?, ?)
        """, (
            northumbria_id,
            plot_index,
            structure_id,
            None,  # set below via CURRENT_TIMESTAMP for occupied plots only
        ))

    cursor.execute("""
        UPDATE settlement_plots
        SET built_at = CURRENT_TIMESTAMP
        WHERE settlement_id = ? AND structure_id IS NOT NULL AND built_at IS NULL
    """, (northumbria_id,))

    # --------------------
    # UNIT TYPES (Definitions of available units)
    # speed is arbitrary units/hour for army-travel-time calculations.
    # --------------------
    cursor.executemany("""
        INSERT OR IGNORE INTO unit_types
        (name, description, attack, defense, health, speed, cost_wood, cost_silver)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, [
        ("infantry", "Basic melee unit - reliable and cost-effective", 10, 5, 1, 5.0, 10, 5),
        ("archer", "Ranged unit - good for defense and ranged attacks", 7, 3, 1, 5.0, 15, 0),
        ("cavalry", "Heavy mounted unit - high attack and defense", 15, 10, 2, 10.0, 20, 10),
    ])

    cursor.execute("SELECT id, name FROM unit_types")
    unit_type_map = {name: id for id, name in cursor.fetchall()}

    # --------------------
    # SETTLEMENT UNITS - Primary storage (total army available)
    # --------------------
    cursor.executemany("""
        INSERT OR IGNORE INTO settlement_units
        (settlement_id, unit_type_id, quantity)
        VALUES (?, ?, ?)
    """, [
        (northumbria_id, unit_type_map["infantry"], 50),
        (northumbria_id, unit_type_map["archer"], 25),
        (northumbria_id, unit_type_map["cavalry"], 15),
    ])

    # --------------------
    # GARRISON UNITS - Subset currently defending
    # --------------------
    cursor.executemany("""
        INSERT OR IGNORE INTO garrison_units
        (settlement_id, unit_type_id, quantity)
        VALUES (?, ?, ?)
    """, [
        (northumbria_id, unit_type_map["infantry"], 40),
        (northumbria_id, unit_type_map["archer"], 15),
        (northumbria_id, unit_type_map["cavalry"], 10),
    ])

    # --------------------
    # RESEARCH NODES - PLOT EXPANSION (scope='settlement')
    # Five +1 nodes take a settlement from base_plot_count up to the
    # global cap of 10. A captured settlement keeps whatever of these
    # are already unlocked, since they're tied to the settlement.
    # --------------------
    plot_expansion_research = [
        ("plots", "Plot Expansion I", "Clear land for one more plot", "settlement", 1, 0, 200, 100, 0, 0, 1.0),
        ("plots", "Plot Expansion II", "Clear land for one more plot", "settlement", 2, 0, 350, 200, 0, 0, 1.5),
        ("plots", "Plot Expansion III", "Clear land for one more plot", "settlement", 3, 0, 500, 350, 100, 0, 2.0),
        ("plots", "Plot Expansion IV", "Clear land for one more plot", "settlement", 4, 0, 700, 500, 200, 0, 2.5),
        ("plots", "Plot Expansion V", "Clear land for one more plot", "settlement", 5, 0, 900, 700, 300, 0, 3.0),
    ]

    cursor.executemany("""
        INSERT OR IGNORE INTO research_nodes
        (sector, name, description, scope, required_player_level, cost_food, cost_wood, cost_stone, cost_silver, cost_gold, research_time_hours)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, plot_expansion_research)

    # --------------------
    # RESEARCH NODES - SETTLEMENTS (scope='player' — unlock new types)
    # --------------------
    settlement_research = [
        ("settlements", "Urban Planning", "Unlock town settlement type", "player", 3, 0, 300, 200, 100, 0, 0.5),
        ("settlements", "Basic Fortifications", "Unlock castle settlement type", "player", 5, 0, 500, 300, 0, 0, 1.0),
        ("settlements", "Frontier Expansion", "Unlock outpost settlement type", "player", 2, 0, 200, 100, 0, 0, 0.25),
        ("settlements", "Advanced Architecture", "Unlock city settlement type", "player", 10, 0, 1000, 800, 500, 0, 2.0),
    ]

    cursor.executemany("""
        INSERT OR IGNORE INTO research_nodes
        (sector, name, description, scope, required_player_level, cost_food, cost_wood, cost_stone, cost_silver, cost_gold, research_time_hours)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, settlement_research)

    # --------------------
    # RESEARCH NODES - ECONOMY (scope='player')
    # --------------------
    economy_research = [
        ("economy", "Improved Farming", "Increase food production by 25%", "player", 2, 0, 100, 0, 50, 0, 0.5),
        ("economy", "Logging Efficiency", "Increase wood production by 25%", "player", 2, 0, 150, 0, 50, 0, 0.5),
        ("economy", "Quarry Mastery", "Increase stone production by 25%", "player", 3, 0, 200, 100, 75, 0, 1.0),
        ("economy", "Trade Routes", "Increase silver production by 30%", "player", 4, 0, 0, 0, 200, 0, 1.0),
        ("economy", "Master Economics", "Increase all resource production by 15%", "player", 8, 0, 500, 300, 400, 0, 2.0),
    ]

    cursor.executemany("""
        INSERT OR IGNORE INTO research_nodes
        (sector, name, description, scope, required_player_level, cost_food, cost_wood, cost_stone, cost_silver, cost_gold, research_time_hours)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, economy_research)

    # --------------------
    # RESEARCH NODES - ARMY (scope='player')
    # --------------------
    army_research = [
        ("army", "Infantry Training", "Increase infantry attack by 20%", "player", 2, 100, 50, 0, 50, 0, 0.5),
        ("army", "Archery Range", "Increase archer attack by 20%", "player", 3, 100, 100, 0, 75, 0, 0.75),
        ("army", "Cavalry Tactics", "Increase cavalry attack by 20%", "player", 4, 150, 100, 0, 100, 0, 1.0),
        ("army", "Shield Wall", "Increase infantry defense by 25%", "player", 5, 200, 150, 50, 100, 0, 1.0),
        ("army", "Heavy Armor", "Increase all unit defense by 15%", "player", 7, 300, 200, 200, 200, 0, 2.0),
        ("army", "War Tactics", "Increase all unit attack by 15%", "player", 9, 400, 300, 100, 300, 0, 2.5),
    ]

    cursor.executemany("""
        INSERT OR IGNORE INTO research_nodes
        (sector, name, description, scope, required_player_level, cost_food, cost_wood, cost_stone, cost_silver, cost_gold, research_time_hours)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, army_research)

    # --------------------
    # RESEARCH NODES - DIPLOMACY (scope='player')
    # --------------------
    diplomacy_research = [
        ("diplomacy", "Basic Diplomacy", "Unlock alliance features", "player", 3, 0, 0, 0, 100, 0, 0.5),
        ("diplomacy", "Trade Agreements", "Reduce resource trade costs by 20%", "player", 5, 0, 200, 0, 200, 0, 1.0),
        ("diplomacy", "Espionage", "Unlock spy actions", "player", 6, 0, 100, 0, 300, 0, 1.5),
        ("diplomacy", "Grand Alliance", "Increase alliance member limit", "player", 10, 0, 500, 0, 500, 0, 2.0),
    ]

    cursor.executemany("""
        INSERT OR IGNORE INTO research_nodes
        (sector, name, description, scope, required_player_level, cost_food, cost_wood, cost_stone, cost_silver, cost_gold, research_time_hours)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, diplomacy_research)

    # --------------------
    # RESEARCH EFFECTS
    # --------------------
    cursor.execute("SELECT id, name FROM research_nodes")
    nodes = {name: node_id for node_id, name in cursor.fetchall()}

    research_effects = [
        # Plot expansion — one +1 per node
        (nodes["Plot Expansion I"], "plot_capacity", "settlement", 1, "+1 plot"),
        (nodes["Plot Expansion II"], "plot_capacity", "settlement", 1, "+1 plot"),
        (nodes["Plot Expansion III"], "plot_capacity", "settlement", 1, "+1 plot"),
        (nodes["Plot Expansion IV"], "plot_capacity", "settlement", 1, "+1 plot"),
        (nodes["Plot Expansion V"], "plot_capacity", "settlement", 1, "+1 plot"),

        # Settlement type unlocks
        (nodes["Urban Planning"], "unlock_settlement", "town", 1, "Unlocks town settlement type"),
        (nodes["Basic Fortifications"], "unlock_settlement", "castle", 1, "Unlocks castle settlement type"),
        (nodes["Frontier Expansion"], "unlock_settlement", "outpost", 1, "Unlocks outpost settlement type"),
        (nodes["Advanced Architecture"], "unlock_settlement", "city", 1, "Unlocks city settlement type"),

        # Economy bonuses (absolute multiplier — combined by multiplying together)
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

# python3 -m db.seed