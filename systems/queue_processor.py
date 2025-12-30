import json
from datetime import datetime
from db.connection import connect_db
from systems.resources import apply_resource_tick
from systems.combat import resolve_attack
from systems.units import finish_training
from systems.buildings import finish_build

def process_queue():
    conn = connect_db()
    cursor = conn.cursor()

    now = datetime.utcnow()

    cursor.execute("""
        SELECT * FROM action_queue
        WHERE status = 'pending'
          AND end_time <= ?
        ORDER BY end_time ASC
    """, (now,))

    actions = cursor.fetchall()

    for action in actions:
        payload = json.loads(action["payload"])

        # Always update resources first
        apply_resource_tick(action["settlement_id"], cursor)

        if action["action_type"] == "build":
            finish_build(action, payload, cursor)

        elif action["action_type"] == "train":
            finish_training(action, payload, cursor)

        elif action["action_type"] == "attack":
            resolve_attack(action, payload, cursor)

        cursor.execute("""
            UPDATE action_queue
            SET status = 'completed'
            WHERE id = ?
        """, (action["id"],))

    conn.commit()
    conn.close()
