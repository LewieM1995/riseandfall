from db.connection import connect_db

def init_db():
    """Initialize the game database with required tables."""
    conn = connect_db()
    cursor = conn.cursor()

    # Enable foreign keys
    cursor.execute("PRAGMA foreign_keys = ON;")


    # --------------------
    # USERS (Authentication)
    # --------------------
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            last_login TIMESTAMP,
            is_active INTEGER DEFAULT 1,
            email_verified INTEGER DEFAULT 0
        );
    """)

    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
    """)


    # --------------------
    # PLAYERS (NPC and User Players)
    # --------------------
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS players (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            username TEXT NOT NULL UNIQUE,
            is_npc INTEGER DEFAULT 0,
            level INTEGER DEFAULT 1,
            experience INTEGER DEFAULT 0,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            last_login_at DATETIME,

            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
        );
    """)

    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_players_user_id ON players(user_id);
    """)

    # --------------------
    # SETTLEMENT TYPES
    # base_plot_count / base_defense are per-type baselines — hand-tuned,
    # not computed. Global plot cap (10) is enforced in application code,
    # not here, since it's a game-balance constant, not a schema constraint.
    # --------------------
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS settlement_types (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL,
            description TEXT,
            image_path TEXT,
            base_plot_count INTEGER NOT NULL DEFAULT 5,
            base_defense INTEGER NOT NULL DEFAULT 0
        );
    """)

    # --------------------
    # SETTLEMENTS
    # last_ticked_at drives the resource tick's elapsed-time calculation
    # now that production is plot-based rather than per-activity.
    # --------------------
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS settlements (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            player_id INTEGER NOT NULL,
            name TEXT NOT NULL,
            settlement_type_id INTEGER,
            x INTEGER NOT NULL,
            y INTEGER NOT NULL,
            last_ticked_at DATETIME,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,

            FOREIGN KEY (player_id) REFERENCES players(id) ON DELETE CASCADE,
            FOREIGN KEY (settlement_type_id) REFERENCES settlement_types(id) ON DELETE SET NULL
        );
    """)

    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_settlements_player ON settlements(player_id);
    """)

    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_settlements_coords ON settlements(x, y);
    """)

    # --------------------
    # SETTLEMENT RESOURCE MODIFIERS (Geography — permanent, per settlement)
    # e.g. Settlement A has rich soil (food: 1.5), Settlement B sits on a
    # gold vein (gold: 2.0). Only store rows that deviate from 1.0 —
    # missing rows default to 1.0 in the service layer.
    # --------------------
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS settlement_resource_modifiers (
            settlement_id INTEGER NOT NULL,
            resource_type TEXT NOT NULL,
            multiplier REAL NOT NULL DEFAULT 1.0,

            PRIMARY KEY (settlement_id, resource_type),
            FOREIGN KEY (settlement_id) REFERENCES settlements(id) ON DELETE CASCADE
        );
    """)

    # --------------------
    # RESOURCE MODIFIERS (Temporary buffs/debuffs — expiring)
    # Renamed from activity_modifiers now that production isn't tied to
    # activities. `multiplier` here is a BONUS FRACTION (0.25 = +25%),
    # summed and added to the 1.0 baseline — never replaces it. This
    # fixes a bug in the original design where "zero active buffs" would
    # have zeroed production instead of leaving it at normal (1.0).
    # --------------------
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS resource_modifiers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            settlement_id INTEGER NOT NULL,
            resource_type TEXT NOT NULL,
            modifier_type TEXT NOT NULL,
            multiplier REAL NOT NULL DEFAULT 0.0,
            expires_at DATETIME,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,

            FOREIGN KEY (settlement_id) REFERENCES settlements(id) ON DELETE CASCADE
        );
    """)

    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_resource_modifiers_settlement
            ON resource_modifiers(settlement_id);
    """)

    # --------------------
    # STRUCTURES (Buildable — definitions)
    # produces_resource/base_resource_per_hour live here now (moved from
    # the old activity_types table) since a plot's structure directly
    # determines production — no more worker-assigned activities.
    # NULL produces_resource = non-production structure (walls, barracks).
    # --------------------
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS structures (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL,
            description TEXT,
            produces_resource TEXT,
            base_resource_per_hour REAL DEFAULT 0,
            build_time_hours REAL NOT NULL,
            requires_resources TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        );
    """)

    # --------------------
    # STRUCTURE EFFECTS (Passive bonuses — defense, unlocks, multipliers)
    # Same pattern as research_effects, so structures and research
    # compose through identical service-layer logic.
    # --------------------
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS structure_effects (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            structure_id INTEGER NOT NULL,
            effect_type TEXT NOT NULL,
            target TEXT,
            value REAL NOT NULL,
            description TEXT,

            FOREIGN KEY (structure_id) REFERENCES structures(id) ON DELETE CASCADE
        );
    """)

    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_structure_effects_structure
            ON structure_effects(structure_id);
    """)

    # --------------------
    # SETTLEMENT PLOTS
    # Fixed slots per settlement (count comes from settlement_types,
    # expandable via settlement-scoped research up to a global cap of 10,
    # enforced in application code). Plots are unrestricted — any
    # structure can go on any plot. `level` is unused today but reserved
    # so a future building-levels system doesn't need another migration.
    # --------------------
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS settlement_plots (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            settlement_id INTEGER NOT NULL,
            plot_index INTEGER NOT NULL,
            structure_id INTEGER,
            level INTEGER DEFAULT 1,
            built_at DATETIME,

            UNIQUE(settlement_id, plot_index),
            FOREIGN KEY (settlement_id) REFERENCES settlements(id) ON DELETE CASCADE,
            FOREIGN KEY (structure_id) REFERENCES structures(id) ON DELETE SET NULL
        );
    """)

    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_settlement_plots_settlement
            ON settlement_plots(settlement_id);
    """)

    # --------------------
    # SETTLEMENT RESOURCES (Simplified)
    # --------------------
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS settlement_resources (
            settlement_id INTEGER NOT NULL,
            resource_type TEXT NOT NULL,
            quantity REAL DEFAULT 0,
            last_updated DATETIME DEFAULT CURRENT_TIMESTAMP,

            PRIMARY KEY (settlement_id, resource_type),
            FOREIGN KEY (settlement_id) REFERENCES settlements(id) ON DELETE CASCADE
        );
    """)

    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_settlement_resources_settlement
            ON settlement_resources(settlement_id);
    """)

    # --------------------
    # UNIT TYPES (Definitions)
    # speed added — determines army travel time between settlement
    # coordinates (slowest unit in a moving stack sets the pace).
    # --------------------
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS unit_types (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL,
            description TEXT,
            attack INTEGER NOT NULL,
            defense INTEGER NOT NULL,
            health INTEGER NOT NULL,
            speed REAL NOT NULL DEFAULT 1.0,
            cost_wood INTEGER NOT NULL,
            cost_silver INTEGER NOT NULL
        );
    """)

    # --------------------
    # SETTLEMENT UNITS (Total army stationed at a settlement)
    # --------------------
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS settlement_units (
            settlement_id INTEGER NOT NULL,
            unit_type_id INTEGER NOT NULL,
            quantity INTEGER NOT NULL DEFAULT 0,

            PRIMARY KEY (settlement_id, unit_type_id),
            FOREIGN KEY (settlement_id) REFERENCES settlements(id) ON DELETE CASCADE,
            FOREIGN KEY (unit_type_id) REFERENCES unit_types(id) ON DELETE CASCADE
        );
    """)

    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_settlement_units_settlement
            ON settlement_units(settlement_id);
    """)

    # --------------------
    # GARRISON UNITS (Subset of settlement_units currently defending)
    # Enforced in the service layer: garrison quantity must never exceed
    # settlement_units quantity for the same unit type.
    # --------------------
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS garrison_units (
            settlement_id INTEGER NOT NULL,
            unit_type_id INTEGER NOT NULL,
            quantity INTEGER NOT NULL DEFAULT 0,

            PRIMARY KEY (settlement_id, unit_type_id),
            FOREIGN KEY (settlement_id) REFERENCES settlements(id) ON DELETE CASCADE,
            FOREIGN KEY (unit_type_id) REFERENCES unit_types(id) ON DELETE CASCADE
        );
    """)

    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_garrison_units_settlement
            ON garrison_units(settlement_id);
    """)


    # --------------------
    # ACTION QUEUE
    # Generic queue for time-based actions: building, training, research,
    # army movement/attacks. action_type + JSON payload, one dispatcher.
    # --------------------
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS action_queue (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            player_id INTEGER NOT NULL,
            settlement_id INTEGER NOT NULL,
            target_settlement_id INTEGER,
            action_type TEXT NOT NULL,
            payload TEXT NOT NULL,
            start_time DATETIME NOT NULL,
            end_time DATETIME NOT NULL,
            status TEXT DEFAULT 'pending',
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,

            FOREIGN KEY (player_id) REFERENCES players(id) ON DELETE CASCADE,
            FOREIGN KEY (settlement_id) REFERENCES settlements(id) ON DELETE CASCADE,
            FOREIGN KEY (target_settlement_id) REFERENCES settlements(id) ON DELETE CASCADE
        );
    """)

    # --------------------
    # BATTLE REPORTS
    # --------------------
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS battle_reports (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            action_id INTEGER NOT NULL,
            attacker_settlement_id INTEGER NOT NULL,
            defender_settlement_id INTEGER NOT NULL,
            result_json TEXT NOT NULL,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,

            FOREIGN KEY (action_id) REFERENCES action_queue(id) ON DELETE CASCADE,
            FOREIGN KEY (attacker_settlement_id) REFERENCES settlements(id),
            FOREIGN KEY (defender_settlement_id) REFERENCES settlements(id)
        );
    """)

    # --------------------
    # RESEARCH NODES
    # scope='player': unlocked once, applies everywhere (unit bonuses,
    #   settlement-type unlocks, alliance features).
    # scope='settlement': unlocked per-settlement (plot expansion) — a
    #   captured settlement keeps whatever progress it already had,
    #   since the unlock lives on the settlement, not the player.
    # --------------------
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS research_nodes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            sector TEXT NOT NULL,
            name TEXT UNIQUE NOT NULL,
            description TEXT,
            scope TEXT NOT NULL DEFAULT 'player',
            required_player_level INTEGER DEFAULT 1,
            cost_food INTEGER DEFAULT 0,
            cost_wood INTEGER DEFAULT 0,
            cost_stone INTEGER DEFAULT 0,
            cost_silver INTEGER DEFAULT 0,
            cost_gold INTEGER DEFAULT 0,
            research_time_hours REAL DEFAULT 0,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        );
    """)

    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_research_nodes_sector ON research_nodes(sector);
    """)

    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_research_nodes_level ON research_nodes(required_player_level);
    """)

    # --------------------
    # PLAYER RESEARCH (scope='player' nodes)
    # --------------------
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS player_research (
            player_id INTEGER NOT NULL,
            node_id INTEGER NOT NULL,
            unlocked_at DATETIME DEFAULT CURRENT_TIMESTAMP,

            PRIMARY KEY (player_id, node_id),
            FOREIGN KEY (player_id) REFERENCES players(id) ON DELETE CASCADE,
            FOREIGN KEY (node_id) REFERENCES research_nodes(id) ON DELETE CASCADE
        );
    """)

    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_player_research_player ON player_research(player_id);
    """)

    # --------------------
    # SETTLEMENT RESEARCH (scope='settlement' nodes — e.g. plot expansion)
    # --------------------
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS settlement_research (
            settlement_id INTEGER NOT NULL,
            node_id INTEGER NOT NULL,
            unlocked_at DATETIME DEFAULT CURRENT_TIMESTAMP,

            PRIMARY KEY (settlement_id, node_id),
            FOREIGN KEY (settlement_id) REFERENCES settlements(id) ON DELETE CASCADE,
            FOREIGN KEY (node_id) REFERENCES research_nodes(id) ON DELETE CASCADE
        );
    """)

    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_settlement_research_settlement
            ON settlement_research(settlement_id);
    """)

    # --------------------
    # RESEARCH EFFECTS
    # --------------------
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS research_effects (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            node_id INTEGER NOT NULL,
            effect_type TEXT NOT NULL,
            target TEXT NOT NULL,
            value REAL NOT NULL,
            description TEXT,

            FOREIGN KEY (node_id) REFERENCES research_nodes(id) ON DELETE CASCADE
        );
    """)

    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_research_effects_node ON research_effects(node_id);
    """)

    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_research_effects_type ON research_effects(effect_type);
    """)

    conn.commit()
    conn.close()
    print("Game database initialized successfully.")


if __name__ == "__main__":
    init_db()

#python3 -m db.init_db