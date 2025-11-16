"""
PennyWise Core Module
"""

from .config import Config
from .logger import logger

__all__ = ['Config', 'logger', 'initialize_pennywise']

def initialize_pennywise():
    """Initialize PennyWise application with configuration validation"""
    logger.info(f"🚀 Initializing {Config.APP_NAME} v{Config.VERSION}")

    # Validate configuration
    config_valid = Config.validate_config()

    # Log mode information
    mode_info = Config.get_mode_info()
    logger.info(f"📱 Mode: {'DEMO' if mode_info['demo_mode'] else 'LIVE'}")
    logger.info(f"🏦 Plaid: {'ENABLED' if mode_info['plaid_enabled'] else 'DISABLED'}")
    logger.info(f"🤖 AI: {'ENABLED' if mode_info['ai_enabled'] else 'DEMO MODE'}")

    if not config_valid and not Config.DEMO_MODE:
        logger.warning("⚠️  Running with partial configuration - some features may be limited")

    return config_valid