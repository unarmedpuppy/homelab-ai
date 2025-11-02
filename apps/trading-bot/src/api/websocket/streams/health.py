"""
Stream Health Monitoring
========================

Health monitoring and recovery for WebSocket streams.
"""

import logging
import asyncio
from typing import Dict, Optional
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class StreamHealthMonitor:
    """
    Monitors health of WebSocket streams and handles recovery
    
    Tracks:
    - Stream uptime
    - Last successful update time
    - Error counts
    - Recovery attempts
    """
    
    def __init__(self):
        """Initialize health monitor"""
        self.stream_status: Dict[str, Dict] = {}
        self.max_error_count = 10
        self.error_threshold = timedelta(minutes=5)  # 5 minutes without updates = unhealthy
        
    def register_stream(self, stream_name: str):
        """Register a stream for health monitoring"""
        self.stream_status[stream_name] = {
            "last_update": datetime.now(),
            "error_count": 0,
            "recovery_attempts": 0,
            "is_healthy": True,
            "started_at": datetime.now()
        }
        logger.info(f"Registered stream for health monitoring: {stream_name}")
    
    def record_update(self, stream_name: str):
        """Record a successful update from a stream"""
        if stream_name in self.stream_status:
            self.stream_status[stream_name]["last_update"] = datetime.now()
            self.stream_status[stream_name]["error_count"] = 0
            self.stream_status[stream_name]["is_healthy"] = True
    
    def record_error(self, stream_name: str):
        """Record an error from a stream"""
        if stream_name not in self.stream_status:
            self.register_stream(stream_name)
        
        status = self.stream_status[stream_name]
        status["error_count"] += 1
        
        # Mark as unhealthy if too many errors
        if status["error_count"] >= self.max_error_count:
            status["is_healthy"] = False
            logger.warning(
                f"Stream {stream_name} marked as unhealthy "
                f"(error_count: {status['error_count']})"
            )
    
    def check_health(self, stream_name: str) -> bool:
        """Check if a stream is healthy"""
        if stream_name not in self.stream_status:
            return False
        
        status = self.stream_status[stream_name]
        
        # Check if stream hasn't updated in too long
        time_since_update = datetime.now() - status["last_update"]
        if time_since_update > self.error_threshold:
            status["is_healthy"] = False
            return False
        
        return status["is_healthy"]
    
    def get_status(self, stream_name: str) -> Optional[Dict]:
        """Get health status for a stream"""
        return self.stream_status.get(stream_name)
    
    def get_all_status(self) -> Dict[str, Dict]:
        """Get health status for all streams"""
        return self.stream_status.copy()
    
    def increment_recovery_attempts(self, stream_name: str):
        """Increment recovery attempt counter"""
        if stream_name in self.stream_status:
            self.stream_status[stream_name]["recovery_attempts"] += 1


# Global health monitor instance
_health_monitor: Optional[StreamHealthMonitor] = None


def get_health_monitor() -> StreamHealthMonitor:
    """Get global stream health monitor instance (singleton)"""
    global _health_monitor
    if _health_monitor is None:
        _health_monitor = StreamHealthMonitor()
        logger.info("StreamHealthMonitor initialized")
    return _health_monitor

