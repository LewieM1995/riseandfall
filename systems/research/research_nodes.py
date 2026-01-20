from db.connection import connect_db
from database_operations.user_operations import get_player_id_for_user

def get_all_research_nodes() -> list[dict]:
    """Retrieve all research nodes"""
    conn = connect_db()
    try:
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM research_nodes")
        return [dict(row) for row in cursor.fetchall()]
    finally:
        conn.close()

def fetch_research_nodes_unlocked(player_id: int) -> list[int]:
    conn = connect_db()
    try:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT node_id
            FROM player_research
            WHERE player_id = ?
              AND unlocked_at IS NOT NULL
            """,
            (player_id,),
        )
        result = [row["node_id"] for row in cursor.fetchall()]
        #print("Unlocked research nodes:", result)
        return result
    finally:
        conn.close()