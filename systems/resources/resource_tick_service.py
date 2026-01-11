
import threading
import time
from systems.resources.resource_tick import apply_resource_tick
from systems.resources.resources import connect_db
import logging

logger = logging.getLogger(__name__)

class ResourceTickService:
    def __init__(self) -> None:
        self.running = False
        self.thread = None
        logger.info("ResourceTickService initialized")
    
    def tick_all_settlements(self) -> None:
        """Apply resource ticks to all PLAYER settlements only"""
        conn = connect_db()
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                SELECT s.id 
                FROM settlements s
                JOIN players p ON s.player_id = p.id
                WHERE p.is_npc = 0
            """)
            settlements = cursor.fetchall()
            
            for settlement in settlements:
                apply_resource_tick(settlement['id'], cursor)
            
            conn.commit()
            logger.info(f"Successfully ticked {len(settlements)} player settlements")
            
        except Exception as e:
            conn.rollback()
            logger.error(f"Error ticking settlements: {e}", exc_info=True)
        finally:
            conn.close()
    
    def _run_loop(self, interval_seconds: float) -> None:
        """Background loop that ticks every interval"""
        while self.running:
            try:
                self.tick_all_settlements()
            except Exception as e:
                logger.error(f"Error in tick loop: {e}", exc_info=True)
            
            time.sleep(interval_seconds)
    
    def start(self, interval_seconds=60) -> None:
        """Start the periodic resource tick"""
        if self.running:
            return
        
        self.running = True
        self.thread = threading.Thread(target=self._run_loop, args=(interval_seconds,), daemon=True)
        self.thread.start()
        logger.info(f"Resource tick started (every {interval_seconds}s)")
    
    def stop(self) -> None:
        """Stop the ticker"""
        self.running = False
        if self.thread:
            self.thread.join(timeout=5)
        logger.info("ResourceTickService stopped")

_tick_service = None

def get_tick_service() -> ResourceTickService:
    """Single accessor for ResourceTickService"""
    global _tick_service
    if _tick_service is None:
        _tick_service = ResourceTickService()
    return _tick_service