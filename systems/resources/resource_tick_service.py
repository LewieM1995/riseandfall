import threading
import time
from systems.resources.resource_tick import apply_resource_tick
from systems.resources.resources import connect_db
import logging

logger = logging.getLogger(__name__)


class ResourceTickService:
    """
    Background service that processes all active activities at regular intervals.
    
    Instead of auto-generating resources based on settlement type,
    this service processes activities (workers doing tasks) and generates resources.
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
            # Get all player settlements with active activities
            cursor.execute("""
                SELECT DISTINCT s.id 
                FROM settlements s
                JOIN players p ON s.player_id = p.id
                JOIN settlement_activities sa ON s.id = sa.settlement_id
                WHERE p.is_npc = 0 AND sa.status = 'in_progress'
            """)
            settlements = cursor.fetchall()
            
            settlement_count = 0
            for settlement in settlements:
                apply_resource_tick(settlement['id'], cursor)
                settlement_count += 1
            
            conn.commit()
            logger.info(f"Successfully ticked {settlement_count} player settlements with active activities")
            
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