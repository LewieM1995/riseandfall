from db.connection import connect_db

def get_all_research_nodes() -> list[dict]:
    """Retrieve all research nodes"""
    conn = connect_db()
    try:
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM research_nodes")
        return [dict(row) for row in cursor.fetchall()]
    finally:
        conn.close()