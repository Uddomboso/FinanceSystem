import logging
import sys
from datetime import datetime
from core.config import Config

class PennyLogger:
    """Custom logger for PennyWise application"""
    
    def __init__(self, name="PennyWise"):
        self.logger = logging.getLogger(name)
        self.logger.setLevel(logging.INFO)
        
        # Create formatter
        formatter = logging.Formatter(
            '%(asctime)s | %(name)s | %(levelname)s | %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        
        # Console handler
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(formatter)
        self.logger.addHandler(console_handler)
        
        # File handler (optional)
        try:
            file_handler = logging.FileHandler('pennywise.log', encoding='utf-8')
            file_handler.setFormatter(formatter)
            self.logger.addHandler(file_handler)
        except Exception:
            pass  # Skip file logging if not possible
    
    def info(self, message):
        self.logger.info(message)
    
    def warning(self, message):
        self.logger.warning(message)
    
    def error(self, message):
        self.logger.error(message)
    
    def debug(self, message):
        self.logger.debug(message)
    
    def critical(self, message):
        self.logger.critical(message)

# Global logger instance
logger = PennyLogger()

def log_demo_event(event_type, details=""):
    """Special logging for demo mode events"""
    if Config.DEMO_MODE:
        logger.info(f"🎭 DEMO {event_type}: {details}")