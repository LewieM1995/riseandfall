from db.connection import connect_db
from .repository import get_all_research_nodes, get_unlocked_research_nodes, get_player_research, get_player_level, get_research_node, get_settlement_count, get_player_resources, deduct_resources_from_settlements, insert_player_research

def get_all_research_nodes_service() -> list[dict]:
    """Service function to get all research nodes."""#
    conn = connect_db()
    try:
        cursor = conn.cursor()
        return get_all_research_nodes(cursor)
    finally:
        conn.close()

def get_unlocked_research_nodes_service(player_id: int) -> list[dict]:
    """Service function to fetch unlocked research nodes for a player."""
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

def unlock_research_node_service(player_id: int, node_id: int) -> None:
    conn = connect_db()
    try:
        cursor = conn.cursor()

        # Check if already unlocked
        if get_player_research(cursor, player_id, node_id):
            raise ValueError("Research node already unlocked.")

        # Get player level
        player_level = get_player_level(cursor, player_id)
        if player_level is None:
            raise ValueError("Player not found.")

        # Get research node requirements and costs
        node = get_research_node(cursor, node_id)
        if node is None:
            raise ValueError("Research node not found.")

        (
            required_level,
            cost_food,
            cost_wood,
            cost_stone,
            cost_silver,
            cost_gold,
        ) = node

        # Validate player level
        if player_level < required_level:
            raise ValueError(
                f"Player level {player_level} is insufficient. "
                f"Requires level {required_level}."
            )

        # Ensure player has settlements
        settlement_count = get_settlement_count(cursor, player_id)
        if settlement_count < 1:
            raise ValueError(
                "Player must have at least one settlement to unlock research."
            )

        # Get player's total resources across settlements
        resources = get_player_resources(cursor, player_id)

        resource_costs = {
            "food": cost_food,
            "wood": cost_wood,
            "stone": cost_stone,
            "silver": cost_silver,
            "gold": cost_gold,
        }

        # Validate resources
        for resource_type, required_amount in resource_costs.items():
            available_amount = resources.get(resource_type, 0)

            if available_amount < required_amount:
                raise ValueError(
                    f"Insufficient {resource_type}. "
                    f"Have {available_amount}, need {required_amount}"
                )

        # Deduct resources and unlock research
        deduct_resources_from_settlements(
            cursor,
            player_id,
            resource_costs
        )

        insert_player_research(
            cursor,
            player_id,
            node_id
        )

        conn.commit()

    except Exception:
        conn.rollback()
        raise

    finally:
        conn.close()