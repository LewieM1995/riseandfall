import sqlite3
import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

# Get database path from environment, or use default
DB_PATH = os.getenv("DATABASE_PATH", "database/riseandfall.db")
DB_PATH = Path(DB_PATH)

# Ensure the directory exists
DB_PATH.parent.mkdir(parents=True, exist_ok=True)


def connect_db():
    """Establish a connection to the SQLite database with appropriate settings."""
    conn = sqlite3.connect(
        str(DB_PATH),
        detect_types=sqlite3.PARSE_DECLTYPES | sqlite3.PARSE_COLNAMES
    )

    # rows as dict-like objects
    conn.row_factory = sqlite3.Row

    # REQUIRED for this schema to enforce foreign keys
    conn.execute("PRAGMA foreign_keys = ON;")
    
    conn.execute("PRAGMA journal_mode = WAL;")
    conn.execute("PRAGMA synchronous = NORMAL;")

    return conn