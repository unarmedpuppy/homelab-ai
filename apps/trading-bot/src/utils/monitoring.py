"""
API Usage & Rate Limit Monitoring
==================================

Monitor API usage, costs, and rate limits across all data sources.
"""

import logging
import threading
from typing import Dict, List, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict

from src.utils.rate_limiter import get_rate_limiter, RateLimitStatus
from src.utils.cache import get_cache_manager

logger = logging.getLogger(__name__)


@dataclass
class SourceMetrics:
    """Metrics for a data source"""
    source: str
    requests_today: int
    requests_this_hour: int
    rate_limit_status: RateLimitStatus
    cache_hits: int = 0
    cache_misses: int = 0
    cache_hit_rate: float = 0.0
    errors: int = 0
    last_request: Optional[datetime] = None
    cost_today: float = 0.0  # Estimated cost if applicable


class UsageMonitor:
    """
    Monitor API usage and rate limits across data sources
    """
    
    def __init__(self, max_history_size: int = 1000, history_ttl_hours: int = 24):
        """
        Initialize usage monitor
        
        Args:
            max_history_size: Maximum number of request history entries (default: 1000)
            history_ttl_hours: TTL for history entries in hours (default: 24)
        """
        self.source_metrics: Dict[str, SourceMetrics] = {}
        self.request_history: List[Dict] = []  # Store recent requests for analysis
        self.max_history_size = max_history_size
        self.history_ttl_hours = history_ttl_hours
        self.cache = get_cache_manager()
        self._lock = threading.Lock()  # Lock for thread-safe operations
    
    def record_request(
        self,
        source: str,
        success: bool = True,
        cached: bool = False,
        cost: float = 0.0
    ):
        """
        Record an API request
        
        Args:
            source: Data source name
            success: Whether request was successful
            cached: Whether result came from cache
            cost: Estimated cost of request
        """
        now = datetime.now()
        
        with self._lock:
            if source not in self.source_metrics:
                self.source_metrics[source] = SourceMetrics(
                    source=source,
                    requests_today=0,
                    requests_this_hour=0,
                    rate_limit_status=RateLimitStatus(
                        source=source,
                        allowed=0,
                        used=0,
                        remaining=0,
                        reset_at=now,
                        is_limited=False
                    )
                )
            
            metrics = self.source_metrics[source]
            metrics.requests_today += 1
            metrics.requests_this_hour += 1
            metrics.last_request = now
            
            if cached:
                metrics.cache_hits += 1
            else:
                metrics.cache_misses += 1
            
            if not success:
                metrics.errors += 1
            
            if cost > 0:
                metrics.cost_today += cost
            
            # Calculate cache hit rate
            total = metrics.cache_hits + metrics.cache_misses
            if total > 0:
                metrics.cache_hit_rate = metrics.cache_hits / total
            
            # Record in history with TTL cleanup
            cutoff_time = now - timedelta(hours=self.history_ttl_hours)
            self.request_history = [
                entry for entry in self.request_history
                if entry.get("timestamp", now) > cutoff_time
            ]
            
            self.request_history.append({
                "source": source,
                "timestamp": now,
                "success": success,
                "cached": cached,
                "cost": cost
            })
            
            # Limit history size
            if len(self.request_history) > self.max_history_size:
                self.request_history = self.request_history[-self.max_history_size:]
            
            # Reset hourly counter if needed
            if metrics.last_request and metrics.last_request.hour != now.hour:
                metrics.requests_this_hour = 1
    
    def get_source_metrics(self, source: str) -> Optional[SourceMetrics]:
        """Get metrics for a data source"""
        with self._lock:
            return self.source_metrics.get(source)
    
    def get_all_metrics(self) -> Dict[str, SourceMetrics]:
        """Get metrics for all sources"""
        with self._lock:
            return self.source_metrics.copy()
    
    def update_rate_limit_status(
        self,
        source: str,
        limit: int,
        window_seconds: int
    ):
        """Update rate limit status for a source"""
        limiter = get_rate_limiter(source)
        status = limiter.get_status(limit, window_seconds)
        
        if source not in self.source_metrics:
            self.source_metrics[source] = SourceMetrics(
                source=source,
                requests_today=0,
                requests_this_hour=0,
                rate_limit_status=status
            )
        else:
            self.source_metrics[source].rate_limit_status = status
    
    def get_usage_summary(self) -> Dict:
        """Get summary of API usage"""
        total_requests = sum(m.requests_today for m in self.source_metrics.values())
        total_cost = sum(m.cost_today for m in self.source_metrics.values())
        total_errors = sum(m.errors for m in self.source_metrics.values())
        
        sources_limited = [
            source for source, metrics in self.source_metrics.items()
            if metrics.rate_limit_status.is_limited
        ]
        
        avg_cache_hit_rate = (
            sum(m.cache_hit_rate for m in self.source_metrics.values()) /
            len(self.source_metrics) if self.source_metrics else 0
        )
        
        return {
            "total_requests_today": total_requests,
            "total_cost_today": total_cost,
            "total_errors": total_errors,
            "sources_limited": sources_limited,
            "average_cache_hit_rate": avg_cache_hit_rate,
            "sources": {
                source: {
                    "requests_today": m.requests_today,
                    "requests_this_hour": m.requests_this_hour,
                    "cache_hit_rate": m.cache_hit_rate,
                    "errors": m.errors,
                    "cost_today": m.cost_today,
                    "rate_limit_remaining": m.rate_limit_status.remaining,
                    "rate_limit_used": m.rate_limit_status.used,
                    "rate_limit_allowed": m.rate_limit_status.allowed,
                    "is_limited": m.rate_limit_status.is_limited
                }
                for source, m in self.source_metrics.items()
            }
        }
    
    def reset_daily_counters(self):
        """Reset daily counters (should be called at midnight)"""
        with self._lock:
            for metrics in self.source_metrics.values():
                metrics.requests_today = 0
                metrics.cost_today = 0
                metrics.errors = 0
    
    def cleanup_unused_sources(self, days_unused: int = 7):
        """
        Remove metrics for sources not used in specified days
        
        Args:
            days_unused: Number of days of inactivity before removal (default: 7)
        """
        cutoff_time = datetime.now() - timedelta(days=days_unused)
        
        with self._lock:
            sources_to_remove = [
                source for source, metrics in self.source_metrics.items()
                if metrics.last_request and metrics.last_request < cutoff_time
            ]
            for source in sources_to_remove:
                del self.source_metrics[source]
                logger.debug(f"Removed unused source metrics: {source}")


# Global monitor instance
_usage_monitor: Optional[UsageMonitor] = None
_usage_monitor_lock = threading.Lock()


def get_usage_monitor() -> UsageMonitor:
    """Get global usage monitor instance (thread-safe)"""
    global _usage_monitor
    if _usage_monitor is None:
        with _usage_monitor_lock:
            # Double-check pattern
            if _usage_monitor is None:
                _usage_monitor = UsageMonitor()
    return _usage_monitor

