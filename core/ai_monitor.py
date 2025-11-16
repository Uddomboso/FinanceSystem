"""
AI service monitoring and health checks for Penny
"""

import threading
import time
from datetime import datetime
from core.config import Config
from core.logger import logger

class AIMonitor:
    """Monitor Penny AI service health and performance"""

    def __init__(self):
        self.monitoring = False
        self.monitor_thread = None
        self.health_stats = {
            'total_requests': 0,
            'successful_requests': 0,
            'failed_requests': 0,
            'cache_hits': 0,
            'average_response_time': 0,
            'last_check': None
        }
        self.penny_brain = None

    def set_penny_brain(self, penny_brain):
        """Set the PennyBrain instance (called after both are initialized)"""
        self.penny_brain = penny_brain
        logger.info("✅ PennyBrain connected to AIMonitor")

    def start_monitoring(self):
        """Start background monitoring"""
        if self.monitoring:
            return

        self.monitoring = True
        self.monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self.monitor_thread.start()
        logger.info("🤖 Penny AI service monitoring started")

    def stop_monitoring(self):
        """Stop background monitoring"""
        self.monitoring = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=5)
        logger.info("🤖 Penny AI service monitoring stopped")

    def _monitor_loop(self):
        """Background monitoring loop"""
        while self.monitoring:
            try:
                self._check_service_health()
                time.sleep(300)  # Check every 5 minutes
            except Exception as e:
                logger.error(f"Penny monitor error: {e}")
                time.sleep(60)  # Wait 1 minute on error

    def _check_service_health(self):
        """Check Penny AI service health"""
        if not self.penny_brain:
            return

        status = self.penny_brain.get_service_status()

        self.health_stats.update({
            'last_check': datetime.now(),
            'circuit_status': 'OPEN' if status['circuit_open'] else 'CLOSED',
            'failure_count': status['failure_count'],
            'in_demo_mode': status['in_demo_mode']
        })

        # Log health status
        if status['circuit_open']:
            logger.warning(f"🔴 Penny Service Circuit OPEN - Failures: {status['failure_count']}")
        else:
            logger.info(f"🟢 Penny Service Healthy - Failures: {status['failure_count']}")
    
    def get_health_report(self):
        """Get current health report"""
        return {
            **self.health_stats,
            'monitoring_active': self.monitoring,
            'timestamp': datetime.now().isoformat()
        }
    
    def record_request(self, success=True, cache_hit=False, response_time=0):
        """Record request statistics"""
        self.health_stats['total_requests'] += 1
        
        if success:
            self.health_stats['successful_requests'] += 1
        else:
            self.health_stats['failed_requests'] += 1
        
        if cache_hit:
            self.health_stats['cache_hits'] += 1
        
        # Update average response time
        if response_time > 0:
            current_avg = self.health_stats['average_response_time']
            total_reqs = self.health_stats['successful_requests']
            self.health_stats['average_response_time'] = (
                (current_avg * (total_reqs - 1) + response_time) / total_reqs
            )

# Global monitor instance
ai_monitor = AIMonitor()