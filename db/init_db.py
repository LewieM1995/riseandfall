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
    
    # ----------------
    # SETTLEMENT TYPES
    # --------------------
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS settlement_types (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL,
            
            -- base resource generation rates (per HOUR)
            food_rate REAL DEFAULT 60.0,
            wood_rate REAL DEFAULT 36.0,
            stone_rate REAL DEFAULT 24.0,
            silver_rate REAL DEFAULT 12.0,
            
            max_population INTEGER DEFAULT 100,
            description TEXT
        );
    """)

    # --------------------
    # SETTLEMENTS
    # --------------------
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS settlements (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            player_id INTEGER NOT NULL,
            name TEXT NOT NULL,
            x INTEGER NOT NULL,
            y INTEGER NOT NULL,
            settlement_type TEXT NOT NULL DEFAULT 'village',

            -- resources
            food INTEGER DEFAULT 0,
            wood INTEGER DEFAULT 0,
            stone INTEGER DEFAULT 0,
            silver INTEGER DEFAULT 0,
            gold INTEGER DEFAULT 0,
            last_resource_tick DATETIME DEFAULT CURRENT_TIMESTAMP,

            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,

            FOREIGN KEY (player_id) REFERENCES players(id) ON DELETE CASCADE,
            FOREIGN KEY (settlement_type) REFERENCES settlement_types(name) ON DELETE RESTRICT
        );
    """)

    # --------------------
    # UNIT TYPES
    # --------------------
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS unit_types (
            unit_type TEXT PRIMARY KEY,
            attack INTEGER NOT NULL,
            defense INTEGER NOT NULL,
            health INTEGER NOT NULL,
            cost_wood INTEGER NOT NULL,
            cost_silver INTEGER NOT NULL
        );
    """)

    # --------------------
    # PLAYER UNITS (Total Army)
    # --------------------
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS player_units (
            player_id INTEGER NOT NULL,
            unit_type TEXT NOT NULL,
            quantity INTEGER NOT NULL DEFAULT 0,
            
            PRIMARY KEY (player_id, unit_type),
            FOREIGN KEY (player_id) REFERENCES players(id) ON DELETE CASCADE,
            FOREIGN KEY (unit_type) REFERENCES unit_types(unit_type)
        );
    """)

    # --------------------
    # SETTLEMENT GARRISONS
    # --------------------
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS settlement_garrisons (
            settlement_id INTEGER NOT NULL,
            unit_type TEXT NOT NULL,
            quantity INTEGER NOT NULL DEFAULT 0,
            
            PRIMARY KEY (settlement_id, unit_type),
            FOREIGN KEY (settlement_id) REFERENCES settlements(id) ON DELETE CASCADE,
            FOREIGN KEY (unit_type) REFERENCES unit_types(unit_type)
        );
    """)
    
    
    # --------------------
    # ACTION QUEUE
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
    # --------------------
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS research_nodes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            sector TEXT NOT NULL,
            name TEXT UNIQUE NOT NULL,
            description TEXT,
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
    # PLAYER RESEARCH
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