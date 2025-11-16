"""
AI service initialization to break circular imports
"""

from core.logger import logger

def initialize_ai_services():
    """Initialize AI services and connect them together"""
    try:
        logger.info("🔄 Initializing AI services...")

        # Import services
        from ai.penny_brain import penny_brain
        from core.ai_monitor import ai_monitor

        # Connect PennyBrain and AIMonitor
        if hasattr(penny_brain, 'set_monitor'):
            penny_brain.set_monitor(ai_monitor)
            logger.info("✅ PennyBrain monitor set")
        else:
            logger.error("❌ PennyBrain missing set_monitor method")
            return False

        if hasattr(ai_monitor, 'set_penny_brain'):
            ai_monitor.set_penny_brain(penny_brain)
            logger.info("✅ AIMonitor PennyBrain set")
        else:
            logger.error("❌ AIMonitor missing set_penny_brain method")
            return False
        
        logger.info("✅ AI services initialized and connected")
        return True
        
    except Exception as e:
        logger.error(f"❌ Failed to initialize AI services: {e}")
        return False