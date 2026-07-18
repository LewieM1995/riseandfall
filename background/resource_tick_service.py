"""Background resource tick service.

This is the entry point for the periodic job: it owns the connection
and the loop/threading, and delegates the actual per-settlement work to
resources.service.apply_resource_tick — passing the SAME cursor to all
of them so one settlement's failure doesn't commit others' partial state
without the rest, and a full run commits or rolls back together.
"""

import threading
import time
import logging

from db.connection import connect_db
from resources.repository import get_settlements_with_occupied_plots
from resources.service import apply_resource_tick

logger = logging.getLogger(__name__)


class ResourceTickService:
    """
    Background service that processes all occupied plots at regular intervals.

    Each occupied plot's structure produces resources directly — no
    worker assignment, no in-progress "activities" to track.
    """

    def __init__(self) -> None:
        self.running = False
        self.thread = None
        logger.info("ResourceTickService initialized")

    def tick_all_settlements(self) -> None:
        """
        Process all activities for all player settlements.

        For each settlement with in-progress activities:
        - Calculate resources generated since last tick
        - Add to settlement_resources
        - Award XP to player
        """
        conn = connect_db()
        cursor = conn.cursor()

        try:
            settlements = get_settlements_with_occupied_plots(cursor)

            settlement_count = 0
            for settlement in settlements:
                apply_resource_tick(cursor, settlement["id"])
                settlement_count += 1

            conn.commit()
            logger.info(f"Successfully ticked {settlement_count} player settlements with occupied plots")

        except Exception as e:
            conn.rollback()
            logger.error(f"Error ticking settlements: {e}", exc_info=True)
        finally:
            conn.close()

    def _run_loop(self, interval_seconds: float) -> None:
        """Background loop that processes activities every interval"""
        while self.running:
            try:
                self.tick_all_settlements()
            except Exception as e:
                logger.error(f"Error in tick loop: {e}", exc_info=True)

            time.sleep(interval_seconds)

    def start(self, interval_seconds: int = 60) -> None:
        """
        Start the periodic activity processing service.

        Args:
            interval_seconds: How often to process activities (default 60 seconds)
                             For testing, use 10-30 seconds
                             For production, use 300-600 seconds (5-10 minutes)
        """
        if self.running:
            logger.warning("ResourceTickService already running")
            return

        self.running = True
        self.thread = threading.Thread(
            target=self._run_loop,
            args=(interval_seconds,),
            daemon=True
        )
        self.thread.start()
        logger.info(f"ResourceTickService started (processing every {interval_seconds}s)")

    def stop(self) -> None:
        """Stop the activity processing service"""
        self.running = False
        if self.thread:
            self.thread.join(timeout=5)
        logger.info("ResourceTickService stopped")


_tick_service = None


def get_tick_service() -> ResourceTickService:
    """Single accessor for ResourceTickService - returns singleton instance"""
    global _tick_service
    if _tick_service is None:
        _tick_service = ResourceTickService()
    return _tick_service