from db.connection import connect_db

def get_all_players() -> list[dict]:
    """
    Retrieve all players from the database.

    Returns:
        List[dict]: A list of players as dictionaries.
    """
    conn = connect_db()
    cursor = conn.cursor()

    try:
        cursor.execute("SELECT * FROM players")

        rows = cursor.fetchall()

        # If `conn.row_factory = sqlite3.Row` in connect_db, this works
        result = [dict(row) for row in rows]

    finally:
        conn.close()

    return result

    