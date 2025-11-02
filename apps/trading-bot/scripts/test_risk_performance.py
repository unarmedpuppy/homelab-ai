#!/usr/bin/env python3
"""
Risk Management Performance Tests
==================================

Tests performance of risk management operations including caching,
database queries, and concurrent access.

Usage:
    python scripts/test_risk_performance.py
"""

import sys
import os
import time
import asyncio
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor

# Add project root to path
project_root = os.path.join(os.path.dirname(__file__), '..')
sys.path.insert(0, project_root)

try:
    from src.core.risk import RiskManager, AccountMonitor, ComplianceManager
    from src.data.database.models import Account, User, CashAccountState
    from src.data.database import SessionLocal, init_db
    import asyncio
except ImportError as e:
    print("="*60)
    print("ERROR: Failed to import required modules")
    print("="*60)
    print(f"\nMissing dependency: {e}")
    print("\nThis test script requires the project dependencies to be installed.")
    print("Please run this test from within the Docker container or ensure")
    print("all dependencies are installed in your Python environment.")
    print("\nTo run in Docker:")
    print("  docker-compose exec trading-bot python scripts/test_risk_performance.py")
    print("="*60)
    sys.exit(1)


async def test_cache_performance():
    """Test cache hit performance"""
    print("\n" + "="*60)
    print("Performance Test: Cache Effectiveness")
    print("="*60)
    
    session = SessionLocal()
    try:
        test_user = session.query(User).filter(User.username == "test_user_risk").first()
        if not test_user:
            print("  ⚠ Setup test account first")
            return
        
        test_account = session.query(Account).filter(Account.name == "Risk Test Account").first()
        if not test_account:
            print("  ⚠ Setup test account first")
            return
        
        account_id = test_account.id
    finally:
        session.close()
    
    monitor = AccountMonitor()
    
    # First call (cache miss)
    start = time.time()
    status1 = await monitor.check_account_balance(account_id)
    first_call_time = time.time() - start
    
    # Second call (cache hit)
    start = time.time()
    status2 = await monitor.check_account_balance(account_id)
    cached_call_time = time.time() - start
    
    speedup = first_call_time / cached_call_time if cached_call_time > 0 else 0
    
    print(f"  First call (cache miss): {first_call_time*1000:.2f}ms")
    print(f"  Cached call (cache hit): {cached_call_time*1000:.2f}ms")
    print(f"  Speedup: {speedup:.1f}x faster")
    
    if speedup > 2:
        print(f"  ✓ Cache provides significant speedup")
    else:
        print(f"  ⚠ Cache speedup less than expected")


async def test_concurrent_access():
    """Test concurrent access to risk manager"""
    print("\n" + "="*60)
    print("Performance Test: Concurrent Access")
    print("="*60)
    
    session = SessionLocal()
    try:
        test_account = session.query(Account).filter(Account.name == "Risk Test Account").first()
        if not test_account:
            print("  ⚠ Setup test account first")
            return
        account_id = test_account.id
    finally:
        session.close()
    
    risk_mgr = RiskManager()
    
    async def validate_trade_async(i):
        """Async validation call"""
        return await risk_mgr.validate_trade(
            account_id=account_id,
            symbol="AAPL",
            side="BUY",
            quantity=10,
            price_per_share=150.0,
            confidence_score=0.7
        )
    
    # Test concurrent validations
    num_concurrent = 10
    start = time.time()
    
    tasks = [validate_trade_async(i) for i in range(num_concurrent)]
    results = await asyncio.gather(*tasks)
    
    total_time = time.time() - start
    avg_time = total_time / num_concurrent
    
    print(f"  Concurrent validations: {num_concurrent}")
    print(f"  Total time: {total_time:.3f}s")
    print(f"  Average per validation: {avg_time*1000:.2f}ms")
    print(f"  Throughput: {num_concurrent/total_time:.1f} validations/sec")
    
    # Check all succeeded
    all_passed = all(r.can_proceed for r in results)
    print(f"  All validations passed: {all_passed}")
    
    if all_passed:
        print(f"  ✓ Thread-safe concurrent access working")
    else:
        print(f"  ✗ Some validations failed")


async def test_database_query_performance():
    """Test database query performance"""
    print("\n" + "="*60)
    print("Performance Test: Database Query Performance")
    print("="*60)
    
    session = SessionLocal()
    try:
        test_account = session.query(Account).filter(Account.name == "Risk Test Account").first()
        if not test_account:
            print("  ⚠ Setup test account first")
            return
        account_id = test_account.id
    finally:
        session.close()
    
    compliance = ComplianceManager()
    
    # Test day trade count query
    iterations = 100
    start = time.time()
    
    for _ in range(iterations):
        count = compliance.get_day_trade_count(account_id, lookback_days=5)
    
    total_time = time.time() - start
    avg_time = total_time / iterations
    
    print(f"  Day trade count queries: {iterations}")
    print(f"  Total time: {total_time:.3f}s")
    print(f"  Average per query: {avg_time*1000:.2f}ms")
    
    if avg_time < 0.050:  # 50ms
        print(f"  ✓ Query performance acceptable (< 50ms)")
    else:
        print(f"  ⚠ Query performance slow (> 50ms)")


def main():
    """Run performance tests"""
    print("="*60)
    print("Risk Management Performance Test Suite")
    print("="*60)
    
    # Initialize database
    print("\n1. Initializing database...")
    try:
        init_db()
        print("   ✓ Database initialized")
    except Exception as e:
        print(f"   ✗ Database initialization failed: {e}")
        return False
    
    # Run performance tests
    asyncio.run(test_cache_performance())
    asyncio.run(test_concurrent_access())
    asyncio.run(test_database_query_performance())
    
    print("\n" + "="*60)
    print("Performance tests complete")
    print("="*60)
    
    return True


if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\nTests interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\nUnexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

