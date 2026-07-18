def get_npc_settlements(cursor) -> list[dict]:
    """All NPC-owned settlements (player.user_id IS NULL) with their
    resources, garrison strength, and total unit count — used for the
    'neighbors' map/target list."""
    cursor.execute("""
        SELECT
            s.id,
            s.name,
            s.settlement_type_id,
            st.name as settlement_type,
            s.x,
            s.y,
            s.created_at
        FROM settlements s
        LEFT JOIN settlement_types st ON s.settlement_type_id = st.id
        JOIN players p ON s.player_id = p.id
        WHERE p.user_id IS NULL
        ORDER BY s.created_at ASC
    """)

    settlement_rows = cursor.fetchall()
    settlements = []

    for settlement_row in settlement_rows:
        settlement_id = settlement_row["id"]
        settlement_dict = dict(settlement_row)

        cursor.execute("""
            SELECT resource_type, quantity
            FROM settlement_resources
            WHERE settlement_id = ?
        """, (settlement_id,))

        resources = {
            "food": 0, "wood": 0, "stone": 0,
            "silver": 0, "gold": 0, "pelt": 0,
        }
        for resource_row in cursor.fetchall():
            resource_type = resource_row["resource_type"]
            if resource_type in resources:
                resources[resource_type] = int(resource_row["quantity"])

        settlement_dict.update(resources)

        cursor.execute("""
            SELECT SUM(quantity) as garrison_strength
            FROM garrison_units
            WHERE settlement_id = ?
        """, (settlement_id,))
        garrison_row = cursor.fetchone()
        settlement_dict["garrison_strength"] = garrison_row["garrison_strength"] or 0

        cursor.execute("""
            SELECT SUM(quantity) as total_units
            FROM settlement_units
            WHERE settlement_id = ?
        """, (settlement_id,))
        unit_row = cursor.fetchone()
        settlement_dict["total_units"] = unit_row["total_units"] or 0

        settlements.append(settlement_dict)

    return settlements


def get_self_settlements(cursor, user_id: int) -> list[dict]:
    """All settlements owned by a player, with their resources, garrison
    strength, and total unit count — used for the player's settlements
    panel."""
    cursor.execute("""
        SELECT
            s.id,
            s.name,
            s.settlement_type_id,
            st.name as settlement_type,
            s.x,
            s.y,
            s.created_at
        FROM settlements s
        LEFT JOIN settlement_types st ON s.settlement_type_id = st.id
        JOIN players p ON s.player_id = p.id
        WHERE p.user_id = ?
        ORDER BY s.created_at ASC
    """, (user_id,))

    settlement_rows = cursor.fetchall()
    settlements = []

    for settlement_row in settlement_rows:
        settlement_id = settlement_row["id"]
        settlement_dict = dict(settlement_row)

        cursor.execute("""
            SELECT resource_type, quantity
            FROM settlement_resources
            WHERE settlement_id = ?
        """, (settlement_id,))

        resources = {
            "food": 0, "wood": 0, "stone": 0,
            "silver": 0, "gold": 0, "pelt": 0,
        }
        for resource_row in cursor.fetchall():
            resource_type = resource_row["resource_type"]
            if resource_type in resources:
                resources[resource_type] = int(resource_row["quantity"])

        settlement_dict.update(resources)

        cursor.execute("""
            SELECT SUM(quantity) as garrison_strength
            FROM garrison_units
            WHERE settlement_id = ?
        """, (settlement_id,))
        garrison_row = cursor.fetchone()
        settlement_dict["garrison_strength"] = garrison_row["garrison_strength"] or 0

        cursor.execute("""
            SELECT SUM(quantity) as total_units
            FROM settlement_units
            WHERE settlement_id = ?
        """, (settlement_id,))
        unit_row = cursor.fetchone()
        settlement_dict["total_units"] = unit_row["total_units"] or 0

        settlements.append(settlement_dict)

    return settlements


def get_settlement_garrison_repository(cursor, settlement_id: int) -> dict:
    """Returns a dictionary with the total garrison strength and a breakdown
    of unit types for a given settlement."""
    cursor.execute("""
        SELECT SUM(quantity) as garrison_strength
        FROM garrison_units
        WHERE settlement_id = ?
    """, (settlement_id,))
    garrison_row = cursor.fetchone()
    garrison_strength = garrison_row["garrison_strength"] or 0

    cursor.execute("""
        SELECT ut.name as unit_type, gu.quantity
        FROM garrison_units gu
        JOIN unit_types ut ON gu.unit_type_id = ut.id
        WHERE gu.settlement_id = ?
    """, (settlement_id,))
    unit_breakdown = {row["unit_type"]: row["quantity"] for row in cursor.fetchall()}

    return {
        "unit_breakdown": unit_breakdown,
    }