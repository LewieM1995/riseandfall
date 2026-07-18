def get_all_research_nodes(cursor) -> list[dict]:
    """Retrieve all research nodes"""
    cursor.execute("SELECT * FROM research_nodes")
    return [dict(row) for row in cursor.fetchall()]


def get_unlocked_research_nodes(cursor, player_id: int) -> list[dict]:
    """Returns a list of research nodes that the player has unlocked."""
    cursor.execute(
        """
        SELECT rn.id, rn.name, rn.description, rn.cost, rn.prerequisites, rn.effect_type, rn.target, rn.value
        FROM research_nodes rn
        JOIN player_research pr ON rn.id = pr.node_id
        WHERE pr.player_id = ?
        """,
        (player_id,),
    )
    return [dict(row) for row in cursor.fetchall()]

def get_player_research(cursor, player_id, node_id):
    cursor.execute(
        """
        SELECT unlocked_at
        FROM player_research
        WHERE player_id = ? AND node_id = ?
        """,
        (player_id, node_id),
    )
    return cursor.fetchone()


def get_player_level(cursor, player_id):
    cursor.execute(
        "SELECT level FROM players WHERE id = ?",
        (player_id,),
    )
    row = cursor.fetchone()
    return row[0] if row else None


def get_research_node(cursor, node_id):
    cursor.execute(
        """
        SELECT required_player_level,
               cost_food,
               cost_wood,
               cost_stone,
               cost_silver,
               cost_gold
        FROM research_nodes
        WHERE id = ?
        """,
        (node_id,),
    )
    return cursor.fetchone()


def get_settlement_count(cursor, player_id):
    cursor.execute(
        "SELECT COUNT(*) FROM settlements WHERE player_id = ?",
        (player_id,),
    )
    return cursor.fetchone()[0]


def get_player_resources(cursor, player_id):
    cursor.execute(
        """
        SELECT sr.resource_type, SUM(sr.quantity)
        FROM settlement_resources sr
        JOIN settlements s ON s.id = sr.settlement_id
        WHERE s.player_id = ?
        GROUP BY sr.resource_type
        """,
        (player_id,),
    )

    rows = cursor.fetchall()

    return {
        resource_type: quantity or 0
        for resource_type, quantity in rows
    }


def deduct_resources_from_settlements(cursor, player_id, costs):
    for resource_type, amount in costs.items():
        cursor.execute(
            """
            UPDATE settlement_resources
            SET quantity = quantity - ?
            WHERE resource_type = ?
            AND settlement_id IN (
                SELECT id
                FROM settlements
                WHERE player_id = ?
            )
            """,
            (
                amount,
                resource_type,
                player_id,
            ),
        )


def insert_player_research(cursor, player_id, node_id):
    cursor.execute(
        """
        INSERT INTO player_research (player_id, node_id, unlocked_at)
        VALUES (?, ?, CURRENT_TIMESTAMP)
        """,
        (player_id, node_id),
    )