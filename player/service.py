import sqlite3
from datetime import datetime

from db.connection import connect_db
from .repository import (
    get_player_level_and_xp,
    update_player_level,
    get_player_by_id,
    get_player_id_for_user,
    insert_player,
    grant_experience,
)
from .models import Player, PlayerExperience


class PlayerSetupError(Exception):
    """Raised when a new player's starting kingdom can't be bootstrapped
    (missing seed data, DB constraint violation, etc). Callers like
    auth.service.signup catch this and turn it into their own error type."""
    pass


def calculate_xp_for_level(level: int) -> int:
    """XP required to reach the given level. Pure formula, no DB."""
    return int(100 * pow(1.60, level - 1))


def check_level_up(cursor, player_id: int) -> None:
    """Check and apply level ups, recursing in case of multi-level jumps.

    Takes a cursor (not a connection) because this is designed to be
    called from inside another domain's transaction — e.g. right after
    a resource-gathering action grants XP, without opening a second
    connection or risking a half-committed state.
    """
    data = get_player_level_and_xp(cursor, player_id)
    if not data:
        return

    xp_needed = calculate_xp_for_level(data["level"] + 1)

    if data["experience"] >= xp_needed:
        new_level = data["level"] + 1
        update_player_level(cursor, player_id, new_level)
        check_level_up(cursor, player_id)


def add_experience(cursor, player_id: int, amount: int) -> None:
    """Grant XP and check for level-up in one call, same cursor/transaction.

    This is the ONE function other domains should call when a player
    earns XP (resource gathering, combat, research, etc) — they should
    never write to players.experience or call check_level_up themselves.
    One call, one place that knows how XP + leveling work together.
    """
    if amount <= 0:
        return
    grant_experience(cursor, player_id, amount)
    check_level_up(cursor, player_id)


def get_player_experience(player_id: int) -> PlayerExperience | None:
    """Entry-point read: get a player's level/xp/next-level threshold."""
    conn = connect_db()
    try:
        cursor = conn.cursor()
        data = get_player_level_and_xp(cursor, player_id)
        if not data:
            return None
        return PlayerExperience(
            level=data["level"],
            experience=data["experience"],
            xp_for_next_level=calculate_xp_for_level(data["level"] + 1),
        )
    finally:
        conn.close()


def get_player_profile(user_id: int) -> Player | None:
    """Entry-point read: resolve a full player profile from a user_id.

    This is what routes call — routes only ever have `user_id` from the
    auth token, never the internal `player_id`.
    """
    conn = connect_db()
    try:
        cursor = conn.cursor()
        player_id = get_player_id_for_user(cursor, user_id)
        if player_id is None:
            return None
        data = get_player_by_id(cursor, player_id)
        if not data:
            return None
        return Player(**data)
    finally:
        conn.close()


def create_new_player_with_starting_kingdom(cursor, user_id: int, username: str) -> dict:
    """Bootstrap a brand-new player: player row, starting settlement,
    workers, resources, units, garrison, and first research node.

    Takes a cursor (not a connection) because this is called from
    auth.service.signup as part of ONE transaction with the user-row
    insert — if any step here fails, the user row must roll back too.

    NOTE: the settlement/resources/army/research SQL below is
    intentionally inline rather than split into those domains'
    repository.py files. This is one-time account-setup logic, not
    reused gameplay logic, and those domains don't have real
    repository.py files yet. Revisit this when they do — most of these
    queries (insert_settlement, insert_settlement_resources, etc.) are
    natural candidates to move to settlements/repository.py,
    resources/repository.py, army/repository.py, and
    research/repository.py at that point.
    """
    try:
        player_id = insert_player(cursor, user_id, username)

        cursor.execute("SELECT id FROM settlement_types WHERE name = ?", ("village",))
        village_type = cursor.fetchone()
        if not village_type:
            raise PlayerSetupError(
                "Settlement types not found. Please run 'python3 -m db.seed_db' to initialize database."
            )
        village_type_id = village_type[0]

        cursor.execute(
            """
            INSERT INTO settlements (player_id, name, settlement_type_id, x, y)
            VALUES (?, ?, ?, ?, ?)
            """,
            (player_id, f"{username}'s Village", village_type_id, 100, 100),
        )
        settlement_id = cursor.lastrowid

        cursor.execute(
            "SELECT id, name FROM worker_types WHERE name IN ('farmer', 'woodman', 'stonemason', 'hunter')"
        )
        worker_types = {name: wid for wid, name in cursor.fetchall()}
        if not worker_types or len(worker_types) < 4:
            raise PlayerSetupError(
                "Worker types not found. Please run 'python3 -m db.seed_db' to initialize database."
            )

        cursor.executemany(
            "INSERT INTO settlement_workers (settlement_id, worker_type_id, quantity) VALUES (?, ?, ?)",
            [
                (settlement_id, worker_types["farmer"], 10),
                (settlement_id, worker_types["woodman"], 5),
                (settlement_id, worker_types["stonemason"], 3),
                (settlement_id, worker_types["hunter"], 2),
            ],
        )

        starting_amounts = {"food": 1000, "wood": 500, "pelt": 50, "stone": 300, "silver": 100, "gold": 10}
        cursor.executemany(
            "INSERT INTO settlement_resources (settlement_id, resource_type, quantity) VALUES (?, ?, ?)",
            [(settlement_id, resource, amount) for resource, amount in starting_amounts.items()],
        )

        cursor.execute("SELECT id, name FROM unit_types WHERE name IN ('infantry', 'archer')")
        unit_types = {name: uid for uid, name in cursor.fetchall()}
        if not unit_types:
            raise PlayerSetupError(
                "Unit types not found. Please run 'python3 -m db.seed_db' to initialize database."
            )

        cursor.executemany(
            "INSERT INTO settlement_units (settlement_id, unit_type_id, quantity) VALUES (?, ?, ?)",
            [
                (settlement_id, unit_types["infantry"], 20),
                (settlement_id, unit_types["archer"], 10),
            ],
        )

        cursor.executemany(
            "INSERT INTO garrison_units (settlement_id, unit_type_id, quantity) VALUES (?, ?, ?)",
            [
                (settlement_id, unit_types["infantry"], 10),
                (settlement_id, unit_types["archer"], 5),
            ],
        )

        cursor.execute("SELECT id FROM research_nodes WHERE sector = 'settlements' LIMIT 1")
        first_research = cursor.fetchone()
        if first_research:
            cursor.execute(
                "INSERT INTO player_research (player_id, node_id, unlocked_at) VALUES (?, ?, ?)",
                (player_id, first_research[0], datetime.now()),
            )

        return {"player_id": player_id, "settlement_id": settlement_id}

    except sqlite3.IntegrityError as e:
        raise PlayerSetupError(f"Database constraint violation: {e}")
    except PlayerSetupError:
        raise
    except Exception as e:
        raise PlayerSetupError(f"Failed to set up new player: {e}")


