def get_in_progress_activities(cursor, settlement_id: int) -> list:
    """All activities currently running at a settlement, joined with
    their type info and owning player_id."""
    cursor.execute(
        """
        SELECT
            sa.id,
            sa.activity_type_id,
            sa.assigned_workers,
            sa.started_at,
            at.produces_resource,
            at.base_resource_per_hour,
            s.player_id
        FROM settlement_activities sa
        JOIN activity_types at ON sa.activity_type_id = at.id
        JOIN settlements s ON sa.settlement_id = s.id
        WHERE sa.settlement_id = ? AND sa.status = 'in_progress'
        """,
        (settlement_id,),
    )
    return cursor.fetchall()


def get_activity_modifier(cursor, settlement_id: int, activity_type_id: int, current_time) -> float:
    """Sum of active buff/debuff multipliers for this activity type."""
    cursor.execute(
        """
        SELECT COALESCE(SUM(multiplier), 0.0) as total_modifier
        FROM activity_modifiers
        WHERE settlement_id = ? AND activity_type_id = ?
        AND (expires_at IS NULL OR expires_at > ?)
        """,
        (settlement_id, activity_type_id, current_time),
    )
    row = cursor.fetchone()
    return row["total_modifier"] if row else 1.0


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


def add_activity_output(cursor, activity_id: int, resource_generated: float) -> None:
    cursor.execute(
        "UPDATE settlement_activities SET resource_output = resource_output + ? WHERE id = ?",
        (resource_generated, activity_id),
    )


def get_settlements_with_active_activities(cursor) -> list:
    """Player-owned (non-NPC) settlements that have at least one
    in-progress activity — used by the tick service to know what to process."""
    cursor.execute(
        """
        SELECT DISTINCT s.id
        FROM settlements s
        JOIN players p ON s.player_id = p.id
        JOIN settlement_activities sa ON s.id = sa.settlement_id
        WHERE p.is_npc = 0 AND sa.status = 'in_progress'
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