#!/usr/bin/env python3
"""
Test Caching & Rate Limiting
=============================

Test script for Redis caching and rate limiting functionality.
"""

import sys
import time
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.utils.cache import get_cache_manager, cached
from src.utils.rate_limiter import get_rate_limiter
from src.utils.monitoring import get_usage_monitor
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def test_cache_basic():
    """Test basic cache operations"""
    print("\n" + "=" * 60)
    print("Test 1: Basic Cache Operations")
    print("=" * 60)
    
    cache = get_cache_manager()
    
    # Test set/get
    cache.set("test:key1", {"value": "test_data", "number": 42}, ttl=60)
    result = cache.get("test:key1")
    print(f"✅ Set/Get test: {result}")
    assert result is not None
    assert result["value"] == "test_data"
    assert result["number"] == 42
    
    # Test exists
    exists = cache.exists("test:key1")
    print(f"✅ Exists test: {exists}")
    assert exists
    
    # Test TTL
    ttl = cache.get_ttl("test:key1")
    print(f"✅ TTL test: {ttl}s remaining")
    assert ttl is not None and ttl > 0
    
    # Test delete
    cache.delete("test:key1")
    result_after_delete = cache.get("test:key1")
    print(f"✅ Delete test: {result_after_delete is None}")
    assert result_after_delete is None
    
    print("✅ Basic cache tests passed!")


def test_cache_decorator():
    """Test @cached decorator"""
    print("\n" + "=" * 60)
    print("Test 2: Cache Decorator")
    print("=" * 60)
    
    call_count = [0]  # Use list to allow modification in nested function
    
    @cached(ttl=10, key_prefix="test")
    def expensive_function(x: int, y: int):
        call_count[0] += 1
        return {"result": x + y, "calls": call_count[0]}
    
    # First call - should execute function
    result1 = expensive_function(5, 3)
    print(f"✅ First call: {result1} (calls={call_count[0]})")
    assert result1["result"] == 8
    assert call_count[0] == 1
    
    # Second call - should use cache
    result2 = expensive_function(5, 3)
    print(f"✅ Second call (cached): {result2} (calls={call_count[0]})")
    assert result2["result"] == 8
    assert call_count[0] == 1  # Should not increment
    
    print("✅ Cache decorator tests passed!")


def test_rate_limiter():
    """Test rate limiting"""
    print("\n" + "=" * 60)
    print("Test 3: Rate Limiting")
    print("=" * 60)
    
    limiter = get_rate_limiter("test_source")
    
    limit = 5
    window = 10  # 10 second window
    
    # Test rate limit check
    print(f"\nTesting rate limit: {limit} requests per {window} seconds")
    
    allowed_count = 0
    blocked_count = 0
    
    for i in range(limit + 2):
        is_allowed, status = limiter.check_rate_limit(limit, window)
        
        if is_allowed:
            allowed_count += 1
            print(f"  Request {i+1}: ✅ Allowed ({status.remaining} remaining)")
        else:
            blocked_count += 1
            print(f"  Request {i+1}: ❌ Blocked ({status.remaining} remaining)")
    
    print(f"\n✅ Rate limit test: {allowed_count} allowed, {blocked_count} blocked")
    assert allowed_count == limit
    assert blocked_count == 2
    
    # Test status
    status = limiter.get_status(limit, window)
    print(f"\n✅ Status check: {status.used}/{status.allowed} used, {status.remaining} remaining")
    assert status.used == limit
    assert status.remaining == 0
    assert status.is_limited
    
    # Reset
    limiter.reset()
    status_after_reset = limiter.get_status(limit, window)
    print(f"✅ After reset: {status_after_reset.used} used")
    assert status_after_reset.used == 0
    
    print("✅ Rate limiter tests passed!")


def test_usage_monitoring():
    """Test usage monitoring"""
    print("\n" + "=" * 60)
    print("Test 4: Usage Monitoring")
    print("=" * 60)
    
    monitor = get_usage_monitor()
    
    # Record some requests
    sources = ["twitter", "reddit", "news"]
    for source in sources:
        for i in range(5):
            monitor.record_request(
                source=source,
                success=True,
                cached=(i % 2 == 0),  # Alternate cached/not cached
                cost=0.001 if i % 3 == 0 else 0.0
            )
    
    # Get metrics
    summary = monitor.get_usage_summary()
    print(f"\n✅ Usage Summary:")
    print(f"  Total requests: {summary['total_requests_today']}")
    print(f"  Total cost: ${summary['total_cost_today']:.4f}")
    print(f"  Average cache hit rate: {summary['average_cache_hit_rate']:.2%}")
    print(f"  Sources limited: {summary['sources_limited']}")
    
    assert summary['total_requests_today'] == 15  # 5 requests × 3 sources
    assert summary['average_cache_hit_rate'] > 0
    
    # Get source metrics
    twitter_metrics = monitor.get_source_metrics("twitter")
    if twitter_metrics:
        print(f"\n✅ Twitter Metrics:")
        print(f"  Requests today: {twitter_metrics.requests_today}")
        print(f"  Cache hit rate: {twitter_metrics.cache_hit_rate:.2%}")
        print(f"  Cost today: ${twitter_metrics.cost_today:.4f}")
        assert twitter_metrics.requests_today == 5
    
    print("✅ Usage monitoring tests passed!")


def test_integration():
    """Test cache + rate limiter integration"""
    print("\n" + "=" * 60)
    print("Test 5: Cache + Rate Limiter Integration")
    print("=" * 60)
    
    cache = get_cache_manager()
    limiter = get_rate_limiter("integration_test")
    monitor = get_usage_monitor()
    
    # Simulate a provider function with caching and rate limiting
    def fetch_data_with_rate_limit(symbol: str):
        # Check rate limit
        is_allowed, status = limiter.check_rate_limit(limit=10, window_seconds=60)
        if not is_allowed:
            monitor.record_request("integration_test", success=False)
            raise Exception(f"Rate limit exceeded: {status.remaining} remaining")
        
        # Check cache
        cache_key = f"data:{symbol}"
        cached_data = cache.get(cache_key)
        if cached_data:
            monitor.record_request("integration_test", success=True, cached=True)
            return cached_data
        
        # Fetch data (simulated)
        data = {"symbol": symbol, "price": 100.0, "timestamp": time.time()}
        
        # Store in cache
        cache.set(cache_key, data, ttl=300)
        
        monitor.record_request("integration_test", success=True, cached=False)
        return data
    
    # First call - should fetch and cache
    result1 = fetch_data_with_rate_limit("AAPL")
    print(f"✅ First call: {result1}")
    assert result1 is not None
    
    # Second call - should use cache
    result2 = fetch_data_with_rate_limit("AAPL")
    print(f"✅ Second call (cached): {result2}")
    assert result2 == result1
    
    print("✅ Integration tests passed!")


def main():
    """Run all tests"""
    print("\n" + "=" * 60)
    print("Caching & Rate Limiting Test Suite")
    print("=" * 60)
    
    try:
        test_cache_basic()
        test_cache_decorator()
        test_rate_limiter()
        test_usage_monitoring()
        test_integration()
        
        print("\n" + "=" * 60)
        print("✅ All Tests Passed!")
        print("=" * 60)
        
        # Show cache status
        cache = get_cache_manager()
        print(f"\nCache Status:")
        print(f"  Redis Available: {cache.is_available()}")
        print(f"  Using Redis: {cache.redis_client is not None}")
        print(f"  Fallback Mode: {cache.redis_client is None}")
        
        return 0
        
    except Exception as e:
        print(f"\n❌ Test Failed: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())

