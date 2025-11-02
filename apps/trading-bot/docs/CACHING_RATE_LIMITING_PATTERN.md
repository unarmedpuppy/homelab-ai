# Caching & Rate Limiting Pattern Guide

## Overview

This document describes the standardized pattern for implementing Redis-backed caching and centralized rate limiting in data providers. All sentiment providers and data sources should follow this pattern for consistency, performance, and observability.

**Last Updated**: 2024-12-19  
**Status**: ✅ Production Ready

---

## Table of Contents

1. [Architecture](#architecture)
2. [Implementation Pattern](#implementation-pattern)
3. [Cache Manager](#cache-manager)
4. [Rate Limiter](#rate-limiter)
5. [Usage Monitoring](#usage-monitoring)
6. [Best Practices](#best-practices)
7. [Examples](#examples)
8. [Troubleshooting](#troubleshooting)

---

## Architecture

### Components

```
┌─────────────────────────────────────────────────────────┐
│              Data Provider (e.g., Twitter)              │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐ │
│  │   Cache      │  │ Rate Limiter │  │   Monitor    │ │
│  │   Manager    │  │              │  │              │ │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘ │
│         │                  │                  │         │
│         └──────────────────┼──────────────────┘         │
│                            │                            │
└────────────────────────────┼────────────────────────────┘
                             │
                    ┌────────┴────────┐
                    │                 │
            ┌───────▼───────┐ ┌───────▼───────┐
            │    Redis      │ │ In-Memory     │
            │  (Primary)    │ │ (Fallback)    │
            └───────────────┘ └───────────────┘
```

### Key Features

- **Redis-backed caching** with automatic in-memory fallback
- **Centralized rate limiting** per data source
- **Usage monitoring** for API calls, costs, and cache hit rates
- **Automatic TTL management** for cache expiration
- **Sliding window** rate limiting algorithm
- **Graceful degradation** when Redis is unavailable

---

## Implementation Pattern

### Step 1: Initialize Utilities in `__init__`

```python
from ...utils.cache import get_cache_manager
from ...utils.rate_limiter import get_rate_limiter
from ...utils.monitoring import get_usage_monitor

class MySentimentProvider:
    def __init__(self, persist_to_db: bool = True):
        self.client = MyClient()
        self.analyzer = SentimentAnalyzer()
        
        # Initialize caching, rate limiting, and monitoring
        self.cache = get_cache_manager()
        self.cache_ttl = settings.my_provider.cache_ttl  # From config
        self.rate_limiter = get_rate_limiter("my_provider")  # Source name
        self.usage_monitor = get_usage_monitor()
        
        self.persist_to_db = persist_to_db
        self.repository = SentimentRepository() if persist_to_db else None
```

### Step 2: Replace In-Memory Cache Methods

**Old Pattern (In-Memory)**:
```python
def _get_from_cache(self, key: str) -> Optional[Any]:
    if key not in self.cache:
        return None
    data, timestamp = self.cache[key]
    if (datetime.now() - timestamp).total_seconds() > self.cache_ttl:
        del self.cache[key]
        return None
    return data

def _set_cache(self, key: str, data: Any):
    self.cache[key] = (data, datetime.now())
```

**New Pattern (Redis-Backed)**:
```python
def _get_from_cache(self, key: str) -> Optional[Any]:
    """Get data from cache using Redis-backed cache manager"""
    cache_key = f"my_provider:{key}"  # Use source prefix
    return self.cache.get(cache_key)

def _set_cache(self, key: str, data: Any):
    """Store data in cache using Redis-backed cache manager"""
    cache_key = f"my_provider:{key}"  # Use source prefix
    self.cache.set(cache_key, data, ttl=self.cache_ttl)
```

### Step 3: Add Rate Limiting to Data Fetching Methods

```python
def get_sentiment(self, symbol: str, hours: int = 24) -> Optional[SymbolSentiment]:
    """Get sentiment with rate limiting and caching"""
    
    # 1. Check rate limit FIRST (before cache to track usage)
    is_allowed, rate_status = self.rate_limiter.check_rate_limit(
        limit=100,          # Max requests
        window_seconds=60   # Per 60 seconds
    )
    
    if not is_allowed:
        logger.warning(f"Rate limit exceeded for {symbol}, waiting...")
        rate_status = self.rate_limiter.wait_if_needed(limit=100, window_seconds=60)
        if rate_status.is_limited:
            logger.error(f"Rate limit still exceeded after wait")
            self.usage_monitor.record_request("my_provider", success=False)
            return None
    
    # 2. Check cache (after rate limit check)
    cache_key = f"sentiment_{symbol}_{hours}"
    cached = self._get_from_cache(cache_key)
    if cached:
        logger.debug(f"Returning cached sentiment for {symbol}")
        self.usage_monitor.record_request("my_provider", success=True, cached=True)
        return cached
    
    # 3. Fetch data from API
    try:
        data = self._fetch_from_api(symbol, hours)
    except Exception as e:
        logger.error(f"Error fetching data: {e}")
        self.usage_monitor.record_request("my_provider", success=False)
        return None
    
    # 4. Process and cache result
    sentiment = self._process_data(data)
    self._set_cache(cache_key, sentiment)
    self.usage_monitor.record_request("my_provider", success=True, cached=False)
    
    return sentiment
```

---

## Cache Manager

### Usage

```python
from ...utils.cache import get_cache_manager

cache = get_cache_manager()

# Set value with TTL
cache.set("key", {"data": "value"}, ttl=300)  # 5 minutes

# Get value
value = cache.get("key")

# Check if exists
exists = cache.exists("key")

# Delete key
cache.delete("key")

# Clear by pattern
cache.clear_pattern("sentiment:*")

# Check TTL
ttl_seconds = cache.get_ttl("key")
```

### Features

- **Automatic serialization**: JSON serialization for complex objects
- **TTL support**: Time-to-live expiration
- **Pattern matching**: Clear multiple keys by pattern
- **Fallback**: Automatic in-memory fallback if Redis unavailable
- **Namespace**: Automatic key namespacing (`trading_bot:` prefix)

### Cache Decorator

For simple functions, use the `@cached` decorator:

```python
from ...utils.cache import cached

@cached(ttl=600, key_prefix="sentiment")
def compute_sentiment(symbol: str, hours: int):
    # Expensive computation
    return result
```

---

## Rate Limiter

### Usage

```python
from ...utils.rate_limiter import get_rate_limiter

limiter = get_rate_limiter("my_source")  # Source identifier

# Check rate limit
is_allowed, status = limiter.check_rate_limit(
    limit=100,          # Max requests
    window_seconds=60   # Per 60 seconds
)

if not is_allowed:
    # Handle rate limit exceeded
    print(f"Rate limit: {status.used}/{status.allowed}")
    print(f"Reset at: {status.reset_at}")

# Wait if needed
status = limiter.wait_if_needed(limit=100, window_seconds=60)

# Get current status (without incrementing)
status = limiter.get_status(limit=100, window_seconds=60)

# Reset counter
limiter.reset()
```

### Rate Limit Status

```python
@dataclass
class RateLimitStatus:
    source: str              # Source identifier
    allowed: int            # Total allowed
    used: int               # Currently used
    remaining: int          # Remaining requests
    reset_at: datetime      # When limit resets
    is_limited: bool        # Whether currently limited
```

### Common Rate Limits

| Source | Limit | Window | Notes |
|--------|-------|--------|-------|
| Twitter | 300 | 900s (15 min) | API v2 limits |
| Reddit | 60 | 60s (1 min) | PRAW default |
| News | 100 | 60s (1 min) | NewsAPI free tier |
| Options | 100 | 60s (1 min) | Unusual Whales |

---

## Usage Monitoring

### Recording Requests

```python
from ...utils.monitoring import get_usage_monitor

monitor = get_usage_monitor()

# Record successful cached request
monitor.record_request("my_source", success=True, cached=True)

# Record successful API request
monitor.record_request("my_source", success=True, cached=False, cost=0.001)

# Record failed request
monitor.record_request("my_source", success=False)
```

### Getting Metrics

```python
# Get metrics for a source
metrics = monitor.get_source_metrics("twitter")
print(f"Requests today: {metrics.requests_today}")
print(f"Cache hit rate: {metrics.cache_hit_rate:.2%}")
print(f"Cost today: ${metrics.cost_today:.4f}")

# Get summary for all sources
summary = monitor.get_usage_summary()
print(f"Total requests: {summary['total_requests_today']}")
print(f"Average cache hit rate: {summary['average_cache_hit_rate']:.2%}")
```

---

## Best Practices

### 1. Cache Key Naming

Use consistent prefixes for each provider:
- `twitter:sentiment_{symbol}_{hours}`
- `reddit:sentiment_{symbol}_{hours}`
- `news:article_{id}`
- `options:sentiment_{symbol}_{hours}`

### 2. Rate Limit Placement

Always check rate limits **before** cache checks:
1. Check rate limit
2. If exceeded, wait or return error
3. Check cache
4. If cache miss, fetch from API

This ensures accurate usage tracking.

### 3. Error Handling

```python
try:
    data = fetch_from_api()
    self.usage_monitor.record_request("source", success=True, cached=False)
except RateLimitError:
    self.usage_monitor.record_request("source", success=False)
    raise
except Exception as e:
    self.usage_monitor.record_request("source", success=False)
    logger.error(f"API error: {e}")
    return None
```

### 4. TTL Selection

| Data Type | Recommended TTL | Rationale |
|-----------|----------------|-----------|
| Real-time sentiment | 300s (5 min) | Balance freshness vs API calls |
| Historical data | 3600s (1 hour) | Changes less frequently |
| Aggregated results | 600s (10 min) | Expensive to compute |
| Static reference data | 86400s (24 hours) | Rarely changes |

### 5. Monitoring Integration

Always record requests:
- Success/failure status
- Cache hit/miss
- Estimated costs (if applicable)

This enables:
- Performance monitoring
- Cost tracking
- Debugging
- Alerting

---

## Examples

### Complete Provider Example

```python
from ...utils.cache import get_cache_manager
from ...utils.rate_limiter import get_rate_limiter
from ...utils.monitoring import get_usage_monitor

class StocktwitsSentimentProvider:
    def __init__(self, persist_to_db: bool = True):
        self.client = StocktwitsClient()
        self.analyzer = SentimentAnalyzer()
        
        # Initialize utilities
        self.cache = get_cache_manager()
        self.cache_ttl = 300  # 5 minutes
        self.rate_limiter = get_rate_limiter("stocktwits")
        self.usage_monitor = get_usage_monitor()
        
        self.persist_to_db = persist_to_db
        self.repository = SentimentRepository() if persist_to_db else None
    
    def _get_from_cache(self, key: str) -> Optional[Any]:
        """Get data from cache using Redis-backed cache manager"""
        cache_key = f"stocktwits:{key}"
        return self.cache.get(cache_key)
    
    def _set_cache(self, key: str, data: Any):
        """Store data in cache using Redis-backed cache manager"""
        cache_key = f"stocktwits:{key}"
        self.cache.set(cache_key, data, ttl=self.cache_ttl)
    
    def get_sentiment(self, symbol: str, hours: int = 24) -> Optional[SymbolSentiment]:
        """Get sentiment with rate limiting and caching"""
        
        # Rate limit: 60 requests per minute
        is_allowed, rate_status = self.rate_limiter.check_rate_limit(limit=60, window_seconds=60)
        if not is_allowed:
            logger.warning(f"Stocktwits rate limit exceeded for {symbol}")
            rate_status = self.rate_limiter.wait_if_needed(limit=60, window_seconds=60)
            if rate_status.is_limited:
                self.usage_monitor.record_request("stocktwits", success=False)
                return None
        
        # Check cache
        cache_key = f"sentiment_{symbol}_{hours}"
        cached = self._get_from_cache(cache_key)
        if cached:
            self.usage_monitor.record_request("stocktwits", success=True, cached=True)
            return cached
        
        # Fetch from API
        try:
            messages = self.client.get_messages(symbol, hours=hours)
        except Exception as e:
            logger.error(f"Error fetching Stocktwits data: {e}")
            self.usage_monitor.record_request("stocktwits", success=False)
            return None
        
        # Process and cache
        sentiment = self._analyze_sentiment(messages, symbol)
        self._set_cache(cache_key, sentiment)
        self.usage_monitor.record_request("stocktwits", success=True, cached=False)
        
        return sentiment
```

### Using Cache Decorator

```python
from ...utils.cache import cached

class DataProcessor:
    @cached(ttl=600, key_prefix="processed")
    def expensive_computation(self, symbol: str, params: dict):
        # This result will be cached for 10 minutes
        return self._compute(symbol, params)
```

---

## Troubleshooting

### Redis Connection Issues

**Problem**: Redis unavailable, falling back to in-memory cache

**Solution**: 
- Check Redis is running: `redis-cli ping`
- Verify connection settings in `REDIS_HOST`, `REDIS_PORT`
- Cache will automatically use in-memory fallback

**Impact**: 
- Cache is process-local (not shared across instances)
- Rate limiting is process-local
- Monitoring works but data not persistent

### Rate Limits Too Strict

**Problem**: Getting rate-limited frequently

**Solution**:
- Adjust limits in provider initialization
- Check actual API limits from provider documentation
- Consider implementing exponential backoff

### Cache Hit Rate Low

**Problem**: Low cache hit rate (< 50%)

**Solutions**:
- Increase TTL for stable data
- Check cache keys are consistent
- Verify Redis is working (not always falling back)
- Consider pre-warming cache for common symbols

### High Memory Usage

**Problem**: In-memory cache growing too large

**Solution**:
- Redis automatically manages memory with TTL
- In-memory fallback auto-cleans expired entries
- For large datasets, consider Redis persistence

---

## API Endpoints

### Monitoring Endpoints

- `GET /api/monitoring/cache/status` - Cache health
- `GET /api/monitoring/rate-limits` - Rate limit status
- `GET /api/monitoring/usage` - Usage metrics
- `POST /api/monitoring/cache/clear` - Clear cache

---

## Migration Checklist

When migrating an existing provider:

- [ ] Import utilities (`get_cache_manager`, `get_rate_limiter`, `get_usage_monitor`)
- [ ] Initialize in `__init__`
- [ ] Replace `_get_from_cache` to use Redis-backed cache
- [ ] Replace `_set_cache` to use Redis-backed cache
- [ ] Add rate limiting check before cache check
- [ ] Add usage monitoring for all requests
- [ ] Update cache key prefixes
- [ ] Test with Redis available and unavailable
- [ ] Verify cache hit rates improve
- [ ] Monitor rate limit compliance

---

## Summary

This pattern provides:

✅ **Consistent caching** across all providers  
✅ **Centralized rate limiting** with automatic tracking  
✅ **Usage monitoring** for observability  
✅ **Graceful degradation** when Redis unavailable  
✅ **Easy integration** with existing providers  

**All new data providers should follow this pattern for consistency and best practices.**

---

**For questions or issues**, see:
- [Cache Implementation](../src/utils/cache.py)
- [Rate Limiter Implementation](../src/utils/rate_limiter.py)
- [Monitoring Implementation](../src/utils/monitoring.py)

