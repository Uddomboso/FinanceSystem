"""
System Logger - Database-backed logging for admin dashboard
"""
from datetime import datetime
from database.db_manager import execute_query
from core.logger import logger as console_logger

def log_to_database(level, action, user_id=None, details=None):
    """
    Log an event to the database system_logs table
    
    Args:
        level: Log level ('INFO', 'WARNING', 'ERROR', 'DEBUG')
        action: Action description (e.g., 'User Login', 'Transaction Created')
        user_id: Optional user ID (None for system-level logs)
        details: Optional additional details
    """
    try:
        # Validate level
        valid_levels = ['INFO', 'WARNING', 'ERROR', 'DEBUG']
        if level not in valid_levels:
            level = 'INFO'
        
        # Insert log entry
        execute_query("""
            INSERT INTO system_logs (level, action, user_id, details, timestamp)
            VALUES (?, ?, ?, ?, ?)
        """, (level, action, user_id, details, datetime.now()), commit=True)
        
        # Also log to console for debugging
        log_message = f"[{level}] {action}"
        if user_id:
            log_message += f" (User: {user_id})"
        if details:
            log_message += f" - {details}"
        
        if level == 'ERROR':
            console_logger.error(log_message)
        elif level == 'WARNING':
            console_logger.warning(log_message)
        elif level == 'DEBUG':
            console_logger.debug(log_message)
        else:
            console_logger.info(log_message)
            
    except Exception as e:
        # Fallback to console logging if database fails
        console_logger.error(f"Failed to log to database: {e}")

def log_info(action, user_id=None, details=None):
    """Log INFO level event"""
    log_to_database('INFO', action, user_id, details)

def log_warning(action, user_id=None, details=None):
    """Log WARNING level event"""
    log_to_database('WARNING', action, user_id, details)

def log_error(action, user_id=None, details=None):
    """Log ERROR level event"""
    log_to_database('ERROR', action, user_id, details)

def log_debug(action, user_id=None, details=None):
    """Log DEBUG level event"""
    log_to_database('DEBUG', action, user_id, details)

