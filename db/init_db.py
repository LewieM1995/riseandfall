from db.connection import connect_db

def init_db():
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
    # PLAYERS (Game Entities)
    # --------------------
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS players (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            username TEXT NOT NULL UNIQUE,
            is_npc INTEGER DEFAULT 0,
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
    # ARMIES
    # --------------------
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS armies (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            player_id INTEGER NOT NULL,
            location_settlement_id INTEGER,
            target_settlement_id INTEGER,
            eta DATETIME,

            FOREIGN KEY (player_id) REFERENCES players(id) ON DELETE CASCADE,
            FOREIGN KEY (location_settlement_id) REFERENCES settlements(id) ON DELETE SET NULL,
            FOREIGN KEY (target_settlement_id) REFERENCES settlements(id) ON DELETE SET NULL
        );
    """)

    # --------------------
    # ARMY UNITS
    # --------------------
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS army_units (
            army_id INTEGER NOT NULL,
            unit_type TEXT NOT NULL,
            quantity INTEGER NOT NULL DEFAULT 0,

            PRIMARY KEY (army_id, unit_type),
            FOREIGN KEY (army_id) REFERENCES armies(id) ON DELETE CASCADE,
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
            action_type TEXT NOT NULL,
            payload TEXT NOT NULL,
            start_time DATETIME NOT NULL,
            end_time DATETIME NOT NULL,
            status TEXT DEFAULT 'pending',
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,

            FOREIGN KEY (player_id) REFERENCES players(id) ON DELETE CASCADE,
            FOREIGN KEY (settlement_id) REFERENCES settlements(id) ON DELETE CASCADE
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

    conn.commit()
    conn.close()
    print("Game database initialized successfully.")


if __name__ == "__main__":
    init_db()