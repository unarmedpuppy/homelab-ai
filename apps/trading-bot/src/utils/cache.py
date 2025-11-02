"""
Redis Cache Manager
===================

Centralized caching layer using Redis for sentiment and market data.
"""

import json
import logging
import threading
from typing import Optional, Any, Dict
from datetime import datetime, timedelta
from decimal import Decimal
from functools import wraps
import hashlib
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


class CacheEncoder(json.JSONEncoder):
    """Custom JSON encoder for cache serialization"""
    def default(self, obj):
        if isinstance(obj, datetime):
            return obj.isoformat()
        if isinstance(obj, Decimal):
            return float(obj)
        if hasattr(obj, '__dict__'):
            return obj.__dict__
        return str(obj)


class CacheManager:
    """
    Redis-based cache manager for sentiment and market data
    
    Features:
    - TTL-based expiration
    - Automatic serialization/deserialization
    - Connection error handling
    - Fallback to in-memory cache if Redis unavailable
    """
    
    def __init__(self, namespace: str = "trading_bot", max_memory_size: int = 1000):
        """
        Initialize cache manager
        
        Args:
            namespace: Redis key namespace prefix
            max_memory_size: Maximum number of entries in in-memory cache (default: 1000)
        """
        self.namespace = namespace
        self.redis_client = None
        # Use OrderedDict for LRU eviction
        self.in_memory_cache: OrderedDict[str, tuple] = OrderedDict()  # Fallback cache
        self.max_memory_size = max_memory_size
        self._connect_lock = threading.Lock()
        self._connect()
    
    def _connect(self):
        """Connect to Redis"""
        if not REDIS_AVAILABLE:
            logger.warning("Redis not available, using in-memory cache")
            return
        
        try:
            self.redis_client = redis.Redis(
                host=settings.redis.host,
                port=settings.redis.port,
                password=settings.redis.password if settings.redis.password else None,
                db=settings.redis.db,
                decode_responses=True,
                socket_connect_timeout=2,
                socket_timeout=2
            )
            # Test connection
            self.redis_client.ping()
            logger.info(f"Redis cache connected: {settings.redis.host}:{settings.redis.port}")
        except (ConnectionError, RedisError, Exception) as e:
            logger.warning(f"Redis connection failed, using in-memory cache: {e}")
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
                logger.warning("Redis connection lost, attempting to reconnect...")
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
                            decode_responses=True,
                            socket_connect_timeout=2,
                            socket_timeout=2
                        )
                        self.redis_client.ping()
                        logger.info(f"Redis cache reconnected: {settings.redis.host}:{settings.redis.port}")
                        return True
                    except (ConnectionError, RedisError, Exception) as e:
                        logger.warning(f"Redis reconnection failed: {e}")
                        self.redis_client = None
        
        return False
    
    def _make_key(self, key: str) -> str:
        """Create namespaced key"""
        return f"{self.namespace}:{key}"
    
    def get(self, key: str) -> Optional[Any]:
        """
        Get value from cache
        
        Args:
            key: Cache key
            
        Returns:
            Cached value or None
        """
        full_key = self._make_key(key)
        
        # Try Redis first
        if self._ensure_connected():
            try:
                value = self.redis_client.get(full_key)
                if value:
                    return json.loads(value)
            except (RedisError, json.JSONDecodeError) as e:
                logger.warning(f"Redis get error for {key}: {e}")
        
        # Fallback to in-memory cache
        if key in self.in_memory_cache:
            data, timestamp, ttl = self.in_memory_cache[key]
            if (datetime.now() - timestamp).total_seconds() < ttl:
                # Move to end (LRU)
                self.in_memory_cache.move_to_end(key)
                return data
            else:
                del self.in_memory_cache[key]
        
        return None
    
    def set(self, key: str, value: Any, ttl: int = 300):
        """
        Set value in cache with TTL
        
        Args:
            key: Cache key
            value: Value to cache (must be JSON serializable)
            ttl: Time-to-live in seconds (default: 5 minutes)
        """
        full_key = self._make_key(key)
        
        # Try Redis first
        if self._ensure_connected():
            try:
                serialized = json.dumps(value, cls=CacheEncoder)
                self.redis_client.setex(full_key, ttl, serialized)
                return
            except (RedisError, TypeError, ValueError) as e:
                logger.warning(f"Redis set error for {key}: {e}")
        
        # Fallback to in-memory cache
        # Remove old entry if exists (will be re-added at end)
        if key in self.in_memory_cache:
            del self.in_memory_cache[key]
        
        # Add new entry at end (most recently used)
        self.in_memory_cache[key] = (value, datetime.now(), ttl)
        
        # Evict LRU entries if over limit
        while len(self.in_memory_cache) > self.max_memory_size:
            # Remove oldest entry (first in OrderedDict)
            self.in_memory_cache.popitem(last=False)
    
    def delete(self, key: str):
        """Delete key from cache"""
        full_key = self._make_key(key)
        
        if self._ensure_connected():
            try:
                self.redis_client.delete(full_key)
            except RedisError as e:
                logger.warning(f"Redis delete error for {key}: {e}")
        
        if key in self.in_memory_cache:
            del self.in_memory_cache[key]
    
    def clear_pattern(self, pattern: str):
        """
        Delete all keys matching pattern
        
        Args:
            pattern: Redis pattern (e.g., "sentiment:*")
        """
        full_pattern = self._make_key(pattern)
        
        if self._ensure_connected():
            try:
                # Use SCAN instead of KEYS for better performance
                keys_to_delete = []
                cursor = 0
                while True:
                    cursor, keys = self.redis_client.scan(cursor, match=full_pattern, count=100)
                    keys_to_delete.extend(keys)
                    if cursor == 0:
                        break
                
                if keys_to_delete:
                    # Delete in batches to avoid blocking
                    for i in range(0, len(keys_to_delete), 100):
                        batch = keys_to_delete[i:i+100]
                        self.redis_client.delete(*batch)
                    logger.info(f"Cleared {len(keys_to_delete)} keys matching {pattern}")
            except RedisError as e:
                logger.warning(f"Redis clear_pattern error: {e}")
        
        # Clear in-memory cache matching pattern
        keys_to_delete = [k for k in list(self.in_memory_cache.keys()) if pattern.replace('*', '') in k]
        for key in keys_to_delete:
            del self.in_memory_cache[key]
    
    def _cleanup_in_memory_cache(self):
        """Remove expired entries from in-memory cache (LRU eviction handled in set())"""
        now = datetime.now()
        expired_keys = [
            key for key, (_, timestamp, ttl) in list(self.in_memory_cache.items())
            if (now - timestamp).total_seconds() >= ttl
        ]
        for key in expired_keys:
            del self.in_memory_cache[key]
    
    def exists(self, key: str) -> bool:
        """Check if key exists in cache"""
        full_key = self._make_key(key)
        
        if self._ensure_connected():
            try:
                return self.redis_client.exists(full_key) > 0
            except RedisError:
                pass
        
        if key in self.in_memory_cache:
            data, timestamp, ttl = self.in_memory_cache[key]
            if (datetime.now() - timestamp).total_seconds() < ttl:
                # Move to end (LRU)
                self.in_memory_cache.move_to_end(key)
                return True
            else:
                del self.in_memory_cache[key]
        
        return False
    
    def get_ttl(self, key: str) -> Optional[int]:
        """Get remaining TTL for a key (in seconds)"""
        full_key = self._make_key(key)
        
        if self._ensure_connected():
            try:
                ttl = self.redis_client.ttl(full_key)
                return ttl if ttl > 0 else None
            except RedisError:
                pass
        
        # For in-memory cache
        if key in self.in_memory_cache:
            data, timestamp, ttl = self.in_memory_cache[key]
            remaining = ttl - (datetime.now() - timestamp).total_seconds()
            return int(remaining) if remaining > 0 else None
        
        return None
    
    def is_available(self) -> bool:
        """Check if Redis is available"""
        return self._ensure_connected()


# Global cache manager instance
_cache_manager: Optional[CacheManager] = None
_cache_lock = threading.Lock()


def get_cache_manager() -> CacheManager:
    """Get global cache manager instance (thread-safe)"""
    global _cache_manager
    if _cache_manager is None:
        with _cache_lock:
            # Double-check pattern
            if _cache_manager is None:
                _cache_manager = CacheManager()
    return _cache_manager


def cache_key(*args, **kwargs) -> str:
    """
    Generate cache key from function arguments
    
    Args:
        *args: Positional arguments
        **kwargs: Keyword arguments
        
    Returns:
        Cache key string
    """
    # Sort kwargs for consistent keys
    sorted_kwargs = sorted(kwargs.items())
    key_parts = [str(arg) for arg in args] + [f"{k}={v}" for k, v in sorted_kwargs]
    key_string = ":".join(key_parts)
    
    # Create hash for long keys
    if len(key_string) > 200:
        key_string = hashlib.md5(key_string.encode()).hexdigest()
    
    return key_string


def cached(ttl: int = 300, key_prefix: str = ""):
    """
    Decorator to cache function results
    
    Args:
        ttl: Cache TTL in seconds
        key_prefix: Prefix for cache keys
        
    Usage:
        @cached(ttl=600, key_prefix="sentiment")
        def get_sentiment(symbol: str):
            ...
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            cache = get_cache_manager()
            
            # Generate cache key (include function name to avoid collisions)
            func_name = func.__name__
            cache_key_str = cache_key(*args, **kwargs)
            if key_prefix:
                cache_key_str = f"{key_prefix}:{func_name}:{cache_key_str}"
            else:
                cache_key_str = f"{func_name}:{cache_key_str}"
            
            # Try to get from cache
            cached_value = cache.get(cache_key_str)
            if cached_value is not None:
                logger.debug(f"Cache hit: {cache_key_str}")
                return cached_value
            
            # Execute function
            logger.debug(f"Cache miss: {cache_key_str}")
            result = func(*args, **kwargs)
            
            # Store in cache
            if result is not None:
                cache.set(cache_key_str, result, ttl=ttl)
            
            return result
        
        return wrapper
    return decorator

