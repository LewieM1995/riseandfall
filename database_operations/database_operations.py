from db.connection import connect_db

def get_all_test():
    connection = connect_db()
    cursor = connection.cursor()
    
    cursor.execute("SELECT * FROM armies")
    rows = cursor.fetchall()
    
    item = [dict(row) for row in rows]
    
    connection.close()
    return item

def get_all_players():
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

    