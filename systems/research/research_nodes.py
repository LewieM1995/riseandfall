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
        
def unlock_research_node(player_id: int, node_id: int) -> None:
    conn = connect_db()
    try:
        cursor = conn.cursor()
        
        # Check if already unlocked
        cursor.execute(
            """
            SELECT unlocked_at FROM player_research
            WHERE player_id = ? AND node_id = ?
            """,
            (player_id, node_id)
        )
        
        research_row = cursor.fetchone()
        if research_row is not None:
            raise ValueError("Research node already unlocked.")
        
        # Get player level
        cursor.execute(
            """
            SELECT level FROM players WHERE id = ?
            """,
            (player_id,)
        )
        
        player_level_row = cursor.fetchone()
        if not player_level_row:
            raise ValueError("Player not found.")
        
        player_level = player_level_row[0]
        
        # Get research node requirements and costs
        cursor.execute(
            """
            SELECT required_player_level, cost_food, cost_wood, cost_stone, cost_silver, cost_gold
            FROM research_nodes
            WHERE id = ?
            """,
            (node_id,)
        )
        
        node_row = cursor.fetchone()
        if not node_row:
            raise ValueError("Research node not found.")
        
        required_level, cost_food, cost_wood, cost_stone, cost_silver, cost_gold = node_row
        
        if player_level < required_level:
            raise ValueError(f"Player level {player_level} is insufficient. Requires level {required_level}.")
        
        # Count player's settlements
        cursor.execute(
            """
            SELECT COUNT(*) FROM settlements WHERE player_id = ?
            """,
            (player_id,)
        )
        
        num_settlements = cursor.fetchone()[0]
        if num_settlements < 1:
            raise ValueError("Player must have at least one settlement to unlock research.")
        
        # Check if player has enough resources
        cursor.execute(
            """
            SELECT SUM(food), SUM(wood), SUM(stone), SUM(silver), SUM(gold)
            FROM settlements
            WHERE player_id = ?
            """,
            (player_id,)
        )
        
        total_resources = cursor.fetchone()
        total_food, total_wood, total_stone, total_silver, total_gold = total_resources
        
        # Handle NULL values (no resources)
        total_food = total_food or 0
        total_wood = total_wood or 0
        total_stone = total_stone or 0
        total_silver = total_silver or 0
        total_gold = total_gold or 0
        
        # Validate sufficient resources
        if total_food < cost_food:
            raise ValueError(f"Insufficient food. Have {int(total_food)}, need {cost_food}")
        if total_wood < cost_wood:
            raise ValueError(f"Insufficient wood. Have {int(total_wood)}, need {cost_wood}")
        if total_stone < cost_stone:
            raise ValueError(f"Insufficient stone. Have {int(total_stone)}, need {cost_stone}")
        if total_silver < cost_silver:
            raise ValueError(f"Insufficient silver. Have {int(total_silver)}, need {cost_silver}")
        if total_gold < cost_gold:
            raise ValueError(f"Insufficient gold. Have {int(total_gold)}, need {cost_gold}")
        
        # Divide costs equally among settlements
        cost_per_settlement = tuple(cost // num_settlements for cost in (cost_food, cost_wood, cost_stone, cost_silver, cost_gold))
        
        # Deduct from all settlements
        cursor.execute(
            """
            UPDATE settlements
            SET food = food - ?, wood = wood - ?, stone = stone - ?, 
                silver = silver - ?, gold = gold - ?
            WHERE player_id = ?
            """,
            (*cost_per_settlement, player_id)
        )
        
        # Insert research
        cursor.execute(
            """
            INSERT INTO player_research (player_id, node_id, unlocked_at)
            VALUES (?, ?, CURRENT_TIMESTAMP)
            """,
            (player_id, node_id)
        )
        
        conn.commit()
    finally:
        conn.close()