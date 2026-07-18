from db.connection import connect_db
from .repository import get_npc_settlements, get_self_settlements, get_settlement_garrison_repository


def get_neighboring_settlements() -> list[dict]:
    """Entry-point read: all NPC settlements, for the neighbors panel."""
    conn = connect_db()
    try:
        cursor = conn.cursor()
        return get_npc_settlements(cursor)
    finally:
        conn.close()
        
def get_player_settlements(user_id: int) -> list[dict]:
    """Entry-point read: all settlements owned by a player, for the
    player's settlements panel.
    """
    conn = connect_db()
    try:
        cursor = conn.cursor()
        return get_self_settlements(cursor, user_id)
    finally:
        conn.close()
        
        
def get_settlement_garrison_service(settlement_id: int, user_id: int) -> dict | None:
    """Entry-point read: garrison details for a settlement, verifying
    ownership by the user_id. Returns None if the settlement does not
    belong to the user.
    """
    conn = connect_db()
    try:
        cursor = conn.cursor()
        return get_settlement_garrison_repository(cursor, settlement_id)
    finally:
        conn.close()


# TODO — need your real systems/settlements/settlements.py and
# systems/settlements/garrison.py to port these correctly rather than
# guess at ownership-check logic:
#
# def get_player_settlements(user_id: int) -> list[dict]:
#     """From systems.settlements.settlements.get_player_settlements_for_user"""
#     ...
#
# def get_settlement_garrison(settlement_id: int, user_id: int) -> dict | None:
#     """From systems.settlements.garrison.get_settlement_garrison —
#     must verify the settlement belongs to this user before returning
#     data, returning None (-> 404) on mismatch, same as the original."""
#     ...