

from datetime import datetime

from db.connection import connect_db
from .repository import (
    get_in_progress_activities,
    get_activity_modifier,
    upsert_settlement_resource,
    add_activity_output,
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
    "defense": 2.0,
}


def calculate_xp_for_resource(resource_type: str, amount: float) -> int:
    """Pure formula — XP earned for a given amount of a resource type."""
    return int(amount * XP_MULTIPLIERS.get(resource_type, 1.0))


def apply_resource_tick(cursor, settlement_id: int) -> None:
    """Process all in-progress activities at a settlement: generate
    resources since each activity started, record output, and award XP.

    Takes a cursor rather than opening its own connection because the
    background tick service processes many settlements in one
    transaction (see background/resource_tick_service.py) — this lets
    all of them commit or roll back together.
    """
    activities = get_in_progress_activities(cursor, settlement_id)
    if not activities:
        return

    current_time = datetime.utcnow()
    total_xp_gained = 0
    player_id = None

    for activity in activities:
        activity_id = activity["id"]
        activity_type_id = activity["activity_type_id"]
        assigned_workers = activity["assigned_workers"]
        started_at = datetime.fromisoformat(activity["started_at"])
        resource_type = activity["produces_resource"]
        base_rate = activity["base_resource_per_hour"]
        player_id = activity["player_id"]

        elapsed_seconds = int((current_time - started_at).total_seconds())
        elapsed_seconds = max(0, min(elapsed_seconds, MAX_CATCHUP_SECONDS))

        if elapsed_seconds < 1:
            continue

        hours = elapsed_seconds / 3600
        modifier = get_activity_modifier(cursor, settlement_id, activity_type_id, current_time)

        resource_generated = assigned_workers * base_rate * hours * modifier

        upsert_settlement_resource(
            cursor, settlement_id, resource_type, resource_generated, current_time.isoformat()
        )
        add_activity_output(cursor, activity_id, resource_generated)

        xp_gained = calculate_xp_for_resource(resource_type, resource_generated)
        total_xp_gained += xp_gained

        print(
            f"Settlement {settlement_id} Activity {activity_id}: "
            f"Generated {resource_generated:.0f} {resource_type} over {hours:.2f} hours "
            f"({assigned_workers} workers * {base_rate}/hr * {modifier:.2f} modifier). "
            f"XP gained: {xp_gained}"
        )

    if total_xp_gained > 0 and player_id:
        # Single cross-domain call — resources doesn't touch XP columns
        # or level-up logic directly, player.service owns both.
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