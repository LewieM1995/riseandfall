import sqlite3

conn = sqlite3.connect('./db/database/riseandfall.db')
cursor = conn.cursor()

# Get all table names
cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
tables = cursor.fetchall()

for table in tables:
    table_name = table[0]
    print(f"\n--- Table: {table_name} ---")
    
    # Get all rows from the table
    cursor.execute(f"SELECT * FROM {table_name}")
    rows = cursor.fetchall()
    
    # Get column names
    cursor.execute(f"PRAGMA table_info({table_name})")
    columns = cursor.fetchall()
    col_names = [col[1] for col in columns]
    
    print(f"Columns: {col_names}")
    for row in rows:
        print(row)

conn.close()