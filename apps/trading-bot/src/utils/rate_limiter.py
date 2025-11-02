"""
Rate Limiter
============

Rate limiting per data source/provider with Redis backing.
"""

import time
import logging
import threading
from typing import Optional, Dict, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass
from collections import OrderedDict

try:
    import redis
    from redis.exceptions import ConnectionError, RedisError
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False
    redis = None

from src.config.settings import settings

logger = logging.getLogger(__name__)


@dataclass
class RateLimitStatus:
    """Rate limit status information"""
    source: str
    allowed: int
    used: int
    remaining: int
    reset_at: datetime
    is_limited: bool


class RateLimiter:
    """
    Rate limiter using Redis (with in-memory fallback)
    
    Uses sliding window algorithm for rate limiting.
    """
    
    def __init__(self, source: str, redis_client: Optional[redis.Redis] = None, max_memory_windows: int = 100):
        """
        Initialize rate limiter for a data source
        
        Args:
            source: Data source identifier (e.g., "twitter", "reddit")
            redis_client: Optional Redis client (will create if not provided)
            max_memory_windows: Maximum number of in-memory rate limit windows to track (default: 100)
        """
        self.source = source
        self.redis_client = redis_client
        self.namespace = "rate_limit"
        self.max_memory_windows = max_memory_windows
        
        if not self.redis_client and REDIS_AVAILABLE:
            self._connect_redis()
        
        # In-memory fallback tracking (use OrderedDict for LRU eviction)
        self.in_memory_windows: OrderedDict[str, list] = OrderedDict()  # window_key -> list of timestamps
        self._connect_lock = threading.Lock()
    
    def _connect_redis(self):
        """Connect to Redis"""
        try:
            self.redis_client = redis.Redis(
                host=settings.redis.host,
                port=settings.redis.port,
                password=settings.redis.password if settings.redis.password else None,
                db=settings.redis.db,
                decode_responses=False,  # We use binary for timestamps
                socket_connect_timeout=2,
                socket_timeout=2
            )
            self.redis_client.ping()
            logger.debug(f"Rate limiter {self.source} connected to Redis")
        except (ConnectionError, RedisError, Exception) as e:
            logger.warning(f"Rate limiter {self.source} Redis unavailable: {e}")
            self.redis_client = None
    
    def _ensure_connected(self) -> bool:
        """
        Ensure Redis connection is active, reconnect if needed
        
        Returns:
            True if Redis is connected, False otherwise
        """
        if self.redis_client:
            try:
                self.redis_client.ping()
                return True
            except (RedisError, ConnectionError):
                # Connection lost, try to reconnect
                logger.warning(f"Rate limiter {self.source} connection lost, attempting to reconnect...")
                self.redis_client = None
        
        # Try to reconnect if Redis was available before
        if REDIS_AVAILABLE:
            with self._connect_lock:
                # Double-check after acquiring lock
                if not self.redis_client:
                    try:
                        self.redis_client = redis.Redis(
                            host=settings.redis.host,
                            port=settings.redis.port,
                            password=settings.redis.password if settings.redis.password else None,
                            db=settings.redis.db,
                            decode_responses=False,  # We use binary for timestamps
                            socket_connect_timeout=2,
                            socket_timeout=2
                        )
                        self.redis_client.ping()
                        logger.debug(f"Rate limiter {self.source} reconnected to Redis")
                        return True
                    except (ConnectionError, RedisError, Exception) as e:
                        logger.warning(f"Rate limiter {self.source} reconnection failed: {e}")
                        self.redis_client = None
        
        return False
    
    def _make_key(self, window_key: str) -> str:
        """Create namespaced Redis key"""
        return f"{self.namespace}:{self.source}:{window_key}"
    
    def check_rate_limit(
        self,
        limit: int,
        window_seconds: int,
        identifier: Optional[str] = None
    ) -> Tuple[bool, RateLimitStatus]:
        """
        Check if request is within rate limit
        
        Args:
            limit: Maximum number of requests allowed
            window_seconds: Time window in seconds
            identifier: Optional identifier (e.g., API key, user ID)
            
        Returns:
            Tuple of (is_allowed, RateLimitStatus)
        """
        window_key = identifier or "default"
        now = time.time()
        window_start = now - window_seconds
        
        # Clean up old timestamps
        cutoff_time = now - window_seconds
        
        # Validate parameters
        if limit < 1:
            raise ValueError("limit must be >= 1")
        if window_seconds < 1:
            raise ValueError("window_seconds must be >= 1")
        
        if self._ensure_connected():
            try:
                redis_key = self._make_key(window_key)
                
                # Use Redis sorted set for sliding window
                # Score = timestamp, member = request ID
                pipe = self.redis_client.pipeline()
                
                # Remove old entries (outside window)
                pipe.zremrangebyscore(redis_key, 0, cutoff_time)
                
                # Count current entries
                pipe.zcard(redis_key)
                
                # Add current request
                request_id = f"{now}:{id(self)}"
                pipe.zadd(redis_key, {request_id: now})
                
                # Set expiration
                pipe.expire(redis_key, window_seconds + 1)
                
                results = pipe.execute()
                current_count = results[1]  # Count before adding this request
                
                # Check limit
                is_allowed = current_count < limit
                used = current_count + (1 if is_allowed else 0)
                remaining = max(0, limit - used)
                
                # Get oldest timestamp for accurate reset time
                oldest_members = self.redis_client.zrange(redis_key, 0, 0, withscores=True)
                if oldest_members:
                    oldest_ts = oldest_members[0][1]
                    reset_at = datetime.fromtimestamp(oldest_ts + window_seconds)
                else:
                    reset_at = datetime.now() + timedelta(seconds=window_seconds)
                
                status = RateLimitStatus(
                    source=self.source,
                    allowed=limit,
                    used=used,
                    remaining=remaining,
                    reset_at=reset_at,
                    is_limited=not is_allowed
                )
                
                if not is_allowed:
                    logger.warning(
                        f"Rate limit exceeded for {self.source} "
                        f"({used}/{limit} in {window_seconds}s)"
                    )
                
                return is_allowed, status
                
            except (RedisError, ConnectionError) as e:
                logger.warning(f"Redis rate limit error for {self.source}: {e}")
                # Fall through to in-memory
        
        # In-memory fallback
        return self._check_rate_limit_memory(limit, window_seconds, window_key, now, cutoff_time)
    
    def _check_rate_limit_memory(
        self,
        limit: int,
        window_seconds: int,
        window_key: str,
        now: float,
        cutoff_time: float
    ) -> Tuple[bool, RateLimitStatus]:
        """Check rate limit using in-memory tracking"""
        # Move to end if exists (LRU)
        if window_key in self.in_memory_windows:
            self.in_memory_windows.move_to_end(window_key)
            timestamps = self.in_memory_windows[window_key]
        else:
            timestamps = []
            self.in_memory_windows[window_key] = timestamps
        
        # Remove old timestamps
        self.in_memory_windows[window_key] = [
            ts for ts in timestamps if ts > cutoff_time
        ]
        
        current_count = len(self.in_memory_windows[window_key])
        is_allowed = current_count < limit
        
        # Calculate reset time from oldest timestamp in window
        if self.in_memory_windows[window_key]:
            oldest_ts = min(self.in_memory_windows[window_key])
            reset_at = datetime.fromtimestamp(oldest_ts + window_seconds)
        else:
            reset_at = datetime.now() + timedelta(seconds=window_seconds)
        
        if is_allowed:
            self.in_memory_windows[window_key].append(now)
            used = current_count + 1
        else:
            used = current_count
            logger.warning(
                f"Rate limit exceeded for {self.source} "
                f"({used}/{limit} in {window_seconds}s) - in-memory tracking"
            )
        
        # Evict LRU windows if over limit
        while len(self.in_memory_windows) > self.max_memory_windows:
            self.in_memory_windows.popitem(last=False)
        
        remaining = max(0, limit - used)
        
        status = RateLimitStatus(
            source=self.source,
            allowed=limit,
            used=used,
            remaining=remaining,
            reset_at=reset_at,
            is_limited=not is_allowed
        )
        
        return is_allowed, status
    
    def wait_if_needed(
        self,
        limit: int,
        window_seconds: int,
        identifier: Optional[str] = None
    ) -> RateLimitStatus:
        """
        Wait if rate limit is exceeded
        
        Args:
            limit: Maximum requests allowed
            window_seconds: Time window in seconds
            identifier: Optional identifier
            
        Returns:
            RateLimitStatus after waiting
        """
        is_allowed, status = self.check_rate_limit(limit, window_seconds, identifier)
        
        if not is_allowed:
            # Calculate wait time
            wait_time = (status.reset_at - datetime.now()).total_seconds()
            if wait_time > 0:
                logger.info(f"Rate limit exceeded for {self.source}, waiting {wait_time:.1f}s")
                time.sleep(wait_time)
                # Check again after wait
                is_allowed, status = self.check_rate_limit(limit, window_seconds, identifier)
        
        return status
    
    def get_status(
        self,
        limit: int,
        window_seconds: int,
        identifier: Optional[str] = None
    ) -> RateLimitStatus:
        """
        Get current rate limit status without incrementing counter
        
        Args:
            limit: Maximum requests allowed
            window_seconds: Time window in seconds
            identifier: Optional identifier
            
        Returns:
            RateLimitStatus
        """
        window_key = identifier or "default"
        now = time.time()
        cutoff_time = now - window_seconds
        
        # Validate parameters
        if limit < 1:
            raise ValueError("limit must be >= 1")
        if window_seconds < 1:
            raise ValueError("window_seconds must be >= 1")
        
        if self._ensure_connected():
            try:
                redis_key = self._make_key(window_key)
                
                # Remove old entries and count
                pipe = self.redis_client.pipeline()
                pipe.zremrangebyscore(redis_key, 0, cutoff_time)
                pipe.zcard(redis_key)
                results = pipe.execute()
                
                used = results[1]
                remaining = max(0, limit - used)
                
                # Get oldest timestamp for accurate reset time
                oldest_members = self.redis_client.zrange(redis_key, 0, 0, withscores=True)
                if oldest_members:
                    oldest_ts = oldest_members[0][1]
                    reset_at = datetime.fromtimestamp(oldest_ts + window_seconds)
                else:
                    reset_at = datetime.now() + timedelta(seconds=window_seconds)
                
                return RateLimitStatus(
                    source=self.source,
                    allowed=limit,
                    used=used,
                    remaining=remaining,
                    reset_at=reset_at,
                    is_limited=used >= limit
                )
            except (RedisError, ConnectionError):
                pass
        
        # In-memory fallback
        if window_key not in self.in_memory_windows:
            used = 0
            reset_at = datetime.now() + timedelta(seconds=window_seconds)
        else:
            timestamps = [
                ts for ts in self.in_memory_windows[window_key]
                if ts > cutoff_time
            ]
            used = len(timestamps)
            
            # Calculate reset time from oldest timestamp
            if timestamps:
                oldest_ts = min(timestamps)
                reset_at = datetime.fromtimestamp(oldest_ts + window_seconds)
            else:
                reset_at = datetime.now() + timedelta(seconds=window_seconds)
        
        remaining = max(0, limit - used)
        
        return RateLimitStatus(
            source=self.source,
            allowed=limit,
            used=used,
            remaining=remaining,
            reset_at=reset_at,
            is_limited=used >= limit
        )
    
    def reset(self, identifier: Optional[str] = None):
        """Reset rate limit counter"""
        window_key = identifier or "default"
        
        if self._ensure_connected():
            try:
                redis_key = self._make_key(window_key)
                self.redis_client.delete(redis_key)
            except RedisError:
                pass
        
        if window_key in self.in_memory_windows:
            del self.in_memory_windows[window_key]


# Global rate limiters by source
_rate_limiters: Dict[str, RateLimiter] = {}
_rate_limiter_lock = threading.Lock()


def get_rate_limiter(source: str) -> RateLimiter:
    """Get or create rate limiter for a source (thread-safe)"""
    if source not in _rate_limiters:
        with _rate_limiter_lock:
            # Double-check pattern
            if source not in _rate_limiters:
                _rate_limiters[source] = RateLimiter(source)
    return _rate_limiters[source]

