from datetime import datetime

from db.connection import connect_db
from .repository import (
    get_occupied_producing_plots,
    get_settlement_geography_modifier,
    get_active_buff_bonus,
    get_player_production_research_multiplier,
    upsert_settlement_resource,
    get_last_ticked_at,
    update_last_ticked_at,
    get_resource_totals_by_player_id,
)
from player.repository import get_player_id_for_user
from player.service import add_experience

MAX_CATCHUP_DAYS = 7
MAX_CATCHUP_SECONDS = MAX_CATCHUP_DAYS * 24 * 3600

XP_MULTIPLIERS = {
    "food": 1.0,
    "wood": 1.0,
    "stone": 1.5,
    "silver": 2.0,
    "gold": 5.0,
    "pelt": 1.5,
}


def calculate_xp_for_resource(resource_type: str, amount: float) -> int:
    """Pure formula — XP earned for a given amount of a resource type."""
    return int(amount * XP_MULTIPLIERS.get(resource_type, 1.0))


def apply_resource_tick(cursor, settlement_id: int) -> None:
    """Generate resources for every occupied, producing plot at a
    settlement since it was last ticked, and award XP for the total.

    Takes a cursor rather than opening its own connection because the
    background tick service processes many settlements in one
    transaction — this lets them all commit or roll back together.
    """
    plots = get_occupied_producing_plots(cursor, settlement_id)
    if not plots:
        return

    current_time = datetime.utcnow()
    last_ticked_raw = get_last_ticked_at(cursor, settlement_id)
    last_ticked_at = (
        datetime.fromisoformat(last_ticked_raw) if last_ticked_raw else current_time
    )

    elapsed_seconds = int((current_time - last_ticked_at).total_seconds())
    elapsed_seconds = max(0, min(elapsed_seconds, MAX_CATCHUP_SECONDS))

    if elapsed_seconds < 1:
        return

    hours = elapsed_seconds / 3600

    player_id = plots[0]["player_id"]
    total_xp_gained = 0

    # Aggregate production per resource type across all plots before
    # writing — a settlement might have 3 farms, we want one upsert for
    # "food", not three.
    production_by_resource: dict[str, float] = {}

    for plot in plots:
        resource_type = plot["produces_resource"]
        base_rate = plot["base_resource_per_hour"]

        geography_modifier = get_settlement_geography_modifier(cursor, settlement_id, resource_type)
        buff_bonus = get_active_buff_bonus(cursor, settlement_id, resource_type, current_time)
        research_multiplier = get_player_production_research_multiplier(cursor, player_id, resource_type)

        # 1.0 baseline + buff bonus, then multiplied by geography and research.
        # Buffs are additive to baseline so "no active buffs" never zeroes production.
        total_modifier = (1.0 + buff_bonus) * geography_modifier * research_multiplier

        resource_generated = base_rate * hours * total_modifier
        production_by_resource[resource_type] = (
            production_by_resource.get(resource_type, 0.0) + resource_generated
        )

    for resource_type, amount in production_by_resource.items():
        upsert_settlement_resource(cursor, settlement_id, resource_type, amount, current_time.isoformat())
        total_xp_gained += calculate_xp_for_resource(resource_type, amount)

        print(
            f"Settlement {settlement_id}: Generated {amount:.0f} {resource_type} "
            f"over {hours:.2f} hours."
        )

    update_last_ticked_at(cursor, settlement_id, current_time.isoformat())

    if total_xp_gained > 0 and player_id:
        add_experience(cursor, player_id, total_xp_gained)


def get_total_resources_for_player(user_id: int) -> dict | None:
    """Entry-point read: total resources across a user's settlements,
    shaped for the frontend resources panel."""
    conn = connect_db()
    try:
        cursor = conn.cursor()

        player_id = get_player_id_for_user(cursor, user_id)
        if player_id is None:
            return None

        rows = get_resource_totals_by_player_id(cursor, player_id)

        resources = {
            "total_food": 0,
            "total_wood": 0,
            "total_stone": 0,
            "total_silver": 0,
            "total_gold": 0,
            "total_pelt": 0,
        }
        resource_mapping = {
            "food": "total_food",
            "wood": "total_wood",
            "stone": "total_stone",
            "silver": "total_silver",
            "gold": "total_gold",
            "pelt": "total_pelt",
        }

        for row in rows:
            key = resource_mapping.get(row["resource_type"])
            if key:
                resources[key] = int(row["total_amount"])

        return resources
    finally:
        conn.close()