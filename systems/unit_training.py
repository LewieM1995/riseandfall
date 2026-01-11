from datetime import datetime, timedelta
import json

from db.connection import connect_db

def queue_unit_training(player_id: int, settlement_id: int, unit: str, quantity: int, duration_minutes: int) -> None:
    conn = connect_db()
    cursor = conn.cursor()

    start = datetime.utcnow()
    end = start + timedelta(minutes=duration_minutes)

    payload = {
        "unit": unit,
        "quantity": quantity
    }

    cursor.execute("""
        INSERT INTO action_queue (
            player_id, settlement_id, action_type,
            payload, start_time, end_time
        ) VALUES (?, ?, 'train', ?, ?, ?)
    """, (
        player_id,
        settlement_id,
        json.dumps(payload),
        start,
        end
    ))

    conn.commit()
    conn.close()
