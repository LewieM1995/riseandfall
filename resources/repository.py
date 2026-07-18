def get_occupied_producing_plots(cursor, settlement_id: int) -> list:
    """Plots at this settlement whose structure produces a resource.
    Empty plots and non-production structures (walls, barracks) are
    excluded by the produces_resource IS NOT NULL filter."""
    cursor.execute(
        """
        SELECT
            sp.id AS plot_id,
            st.produces_resource,
            st.base_resource_per_hour,
            se.player_id
        FROM settlement_plots sp
        JOIN structures st ON sp.structure_id = st.id
        JOIN settlements se ON sp.settlement_id = se.id
        WHERE sp.settlement_id = ? AND st.produces_resource IS NOT NULL
        """,
        (settlement_id,),
    )
    return cursor.fetchall()


def get_settlement_geography_modifier(cursor, settlement_id: int, resource_type: str) -> float:
    """Permanent per-settlement multiplier (e.g. rich soil, a gold vein).
    Defaults to 1.0 if this settlement has no modifier for this resource."""
    cursor.execute(
        """
        SELECT multiplier FROM settlement_resource_modifiers
        WHERE settlement_id = ? AND resource_type = ?
        """,
        (settlement_id, resource_type),
    )
    row = cursor.fetchone()
    return row["multiplier"] if row else 1.0


def get_active_buff_bonus(cursor, settlement_id: int, resource_type: str, current_time) -> float:
    """Sum of active temporary-buff BONUS FRACTIONS (0.25 = +25%) for
    this resource type. Returns 0.0 if none active — caller adds this to
    the 1.0 baseline, never replaces it."""
    cursor.execute(
        """
        SELECT COALESCE(SUM(multiplier), 0.0) as total_bonus
        FROM resource_modifiers
        WHERE settlement_id = ? AND resource_type = ?
        AND (expires_at IS NULL OR expires_at > ?)
        """,
        (settlement_id, resource_type, current_time),
    )
    row = cursor.fetchone()
    return row["total_bonus"] if row else 0.0


def get_player_production_research_multiplier(cursor, player_id: int, resource_type: str) -> float:
    """Product of all unlocked player-scoped research production
    multipliers matching this resource type or 'all'. Starts at 1.0."""
    cursor.execute(
        """
        SELECT re.value
        FROM player_research pr
        JOIN research_effects re ON pr.node_id = re.node_id
        WHERE pr.player_id = ?
        AND re.effect_type = 'production_bonus'
        AND (re.target = ? OR re.target = 'all')
        """,
        (player_id, resource_type),
    )
    multiplier = 1.0
    for row in cursor.fetchall():
        multiplier *= row["value"]
    return multiplier


def upsert_settlement_resource(cursor, settlement_id: int, resource_type: str, amount: float, timestamp: str) -> None:
    cursor.execute(
        """
        INSERT INTO settlement_resources (settlement_id, resource_type, quantity, last_updated)
        VALUES (?, ?, ?, ?)
        ON CONFLICT(settlement_id, resource_type)
        DO UPDATE SET quantity = quantity + excluded.quantity, last_updated = CURRENT_TIMESTAMP
        """,
        (settlement_id, resource_type, amount, timestamp),
    )


def get_last_ticked_at(cursor, settlement_id: int):
    """Returns the ISO timestamp string, or None if this settlement has
    never been ticked (falls back to created_at in the service layer)."""
    cursor.execute(
        "SELECT last_ticked_at, created_at FROM settlements WHERE id = ?",
        (settlement_id,),
    )
    row = cursor.fetchone()
    if not row:
        return None
    return row["last_ticked_at"] or row["created_at"]


def update_last_ticked_at(cursor, settlement_id: int, timestamp: str) -> None:
    cursor.execute(
        "UPDATE settlements SET last_ticked_at = ? WHERE id = ?",
        (timestamp, settlement_id),
    )


def get_settlements_with_occupied_plots(cursor) -> list:
    """Player-owned (non-NPC) settlements that have at least one
    producing plot — used by the tick service to know what to process."""
    cursor.execute(
        """
        SELECT DISTINCT s.id
        FROM settlements s
        JOIN players p ON s.player_id = p.id
        JOIN settlement_plots sp ON s.id = sp.settlement_id
        JOIN structures st ON sp.structure_id = st.id
        WHERE p.is_npc = 0 AND st.produces_resource IS NOT NULL
        """
    )
    return cursor.fetchall()


def get_resource_totals_by_player_id(cursor, player_id: int) -> list:
    """Raw per-resource-type totals across all of a player's settlements."""
    cursor.execute(
        """
        SELECT
            resource_type,
            COALESCE(SUM(quantity), 0) as total_amount
        FROM settlement_resources sr
        JOIN settlements s ON sr.settlement_id = s.id
        WHERE s.player_id = ?
        GROUP BY sr.resource_type
        """,
        (player_id,),
    )
    return cursor.fetchall()