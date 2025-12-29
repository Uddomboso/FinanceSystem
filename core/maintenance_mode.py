"""
Maintenance Mode Manager for PennyWise
Centralized state management for emergency shutdown/maintenance mode
"""

import threading
from typing import Optional
from database.db_manager import fetch_one, execute_query
from core.logger import logger


class MaintenanceMode:
    """Centralized maintenance mode state manager"""
    
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls):
        """Singleton pattern to ensure single source of truth"""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        """Initialize maintenance mode state"""
        if self._initialized:
            return
        
        self._initialized = True
        self._ensure_table_exists()
        self._state_lock = threading.Lock()
        
        # Load current state from database
        self._is_enabled = self._load_state()
        logger.info(f"Maintenance mode initialized: {'ENABLED' if self._is_enabled else 'DISABLED'}")
    
    def _ensure_table_exists(self):
        """Create maintenance_mode table if it doesn't exist"""
        import time
        max_retries = 3
        retry_delay = 0.5
        
        for attempt in range(max_retries):
            try:
                execute_query("""
                    CREATE TABLE IF NOT EXISTS maintenance_mode (
                        id INTEGER PRIMARY KEY CHECK (id = 1),
                        enabled INTEGER DEFAULT 0,
                        message TEXT,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """, commit=True)
                
                # Insert default row if it doesn't exist
                existing = fetch_one("SELECT id FROM maintenance_mode WHERE id = 1")
                if not existing:
                    execute_query("""
                        INSERT INTO maintenance_mode (id, enabled, message)
                        VALUES (1, 0, 'PennyWise is temporarily unavailable due to maintenance.')
                    """, commit=True)
                
                # Success - break out of retry loop
                break
            except Exception as e:
                if attempt < max_retries - 1:
                    logger.warning(f"Database locked, retrying maintenance_mode table creation (attempt {attempt + 1}/{max_retries}): {e}")
                    time.sleep(retry_delay)
                    retry_delay *= 2  # Exponential backoff
                else:
                    logger.error(f"Failed to create maintenance_mode table after {max_retries} attempts: {e}")
    
    def _load_state(self) -> bool:
        """Load maintenance mode state from database"""
        import time
        max_retries = 3
        retry_delay = 0.5
        
        for attempt in range(max_retries):
            try:
                result = fetch_one("SELECT enabled FROM maintenance_mode WHERE id = 1")
                return bool(result['enabled']) if result else False
            except Exception as e:
                if attempt < max_retries - 1:
                    logger.warning(f"Database locked, retrying maintenance_mode state load (attempt {attempt + 1}/{max_retries}): {e}")
                    time.sleep(retry_delay)
                    retry_delay *= 2
                else:
                    logger.error(f"Failed to load maintenance mode state after {max_retries} attempts: {e}")
                    return False
    
    def is_enabled(self) -> bool:
        """Check if maintenance mode is currently enabled"""
        with self._state_lock:
            return self._is_enabled
    
    def enable(self, message: Optional[str] = None) -> bool:
        """
        Enable maintenance mode
        
        Args:
            message: Optional custom maintenance message
        
        Returns:
            True if successfully enabled
        """
        try:
            default_message = "PennyWise is temporarily unavailable due to maintenance."
            maintenance_message = message or default_message
            
            with self._state_lock:
                execute_query("""
                    UPDATE maintenance_mode 
                    SET enabled = 1, message = ?, updated_at = CURRENT_TIMESTAMP
                    WHERE id = 1
                """, (maintenance_message,), commit=True)
                self._is_enabled = True
            
            logger.warning(f"Maintenance mode ENABLED: {maintenance_message}")
            return True
        except Exception as e:
            logger.error(f"Failed to enable maintenance mode: {e}")
            return False
    
    def disable(self) -> bool:
        """
        Disable maintenance mode
        
        Returns:
            True if successfully disabled
        """
        try:
            with self._state_lock:
                execute_query("""
                    UPDATE maintenance_mode 
                    SET enabled = 0, updated_at = CURRENT_TIMESTAMP
                    WHERE id = 1
                """, commit=True)
                self._is_enabled = False
            
            logger.info("Maintenance mode DISABLED")
            return True
        except Exception as e:
            logger.error(f"Failed to disable maintenance mode: {e}")
            return False
    
    def get_message(self) -> str:
        """Get the current maintenance message"""
        try:
            result = fetch_one("SELECT message FROM maintenance_mode WHERE id = 1")
            return result['message'] if result and result['message'] else \
                "PennyWise is temporarily unavailable due to maintenance."
        except Exception as e:
            logger.error(f"Failed to get maintenance message: {e}")
            return "PennyWise is temporarily unavailable due to maintenance."


# Global singleton instance getter
_maintenance_mode = None

def get_maintenance_mode() -> MaintenanceMode:
    """Get the global maintenance mode instance"""
    global _maintenance_mode
    if _maintenance_mode is None:
        _maintenance_mode = MaintenanceMode()
    return _maintenance_mode

