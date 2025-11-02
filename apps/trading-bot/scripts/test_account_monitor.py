#!/usr/bin/env python3
"""
Test script for Account Monitor

Tests account balance detection and cash account mode functionality.

Usage:
    python scripts/test_account_monitor.py
"""

import sys
import os
from datetime import datetime

# Add project root to path
project_root = os.path.join(os.path.dirname(__file__), '..')
sys.path.insert(0, project_root)

try:
    from src.core.risk.account_monitor import AccountMonitor, AccountStatus
    from src.data.database.models import CashAccountState, Account
    from src.data.database import SessionLocal, init_db
    from src.config.settings import settings
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
    print("  docker-compose exec trading-bot python scripts/test_account_monitor.py")
    print("="*60)
    sys.exit(1)


async def test_account_monitor():
    """Test account monitor functionality"""
    print("="*60)
    print("Account Monitor Test Suite")
    print("="*60)
    
    # Initialize database
    print("\n1. Initializing database...")
    try:
        init_db()
        print("   ✓ Database initialized")
    except Exception as e:
        print(f"   ✗ Database initialization failed: {e}")
        return False
    
    # Create test account
    print("\n2. Creating test account...")
    session = SessionLocal()
    try:
        test_account = session.query(Account).filter(Account.name == "Test Account").first()
        if not test_account:
            from src.data.database.models import User
            # Create test user if needed
            test_user = session.query(User).filter(User.username == "test_user").first()
            if not test_user:
                test_user = User(
                    username="test_user",
                    email="test@example.com",
                    hashed_password="dummy_hash"
                )
                session.add(test_user)
                session.commit()
            
            test_account = Account(
                user_id=test_user.id,
                name="Test Account",
                account_type="paper",
                broker="ibkr",
                broker_account_id="TEST123"
            )
            session.add(test_account)
            session.commit()
            print(f"   ✓ Created test account (ID: {test_account.id})")
        else:
            print(f"   ✓ Using existing test account (ID: {test_account.id})")
    except Exception as e:
        print(f"   ✗ Failed to create test account: {e}")
        session.rollback()
        session.close()
        return False
    finally:
        session.close()
    
    account_id = test_account.id
    
    # Test AccountMonitor without IBKR client (simulated)
    print("\n3. Testing AccountMonitor (without IBKR connection)...")
    monitor = AccountMonitor(ibkr_client=None)
    
    try:
        # Test with simulated balance below threshold
        print("\n   Testing with balance below threshold...")
        
        # Manually create cash account state for testing
        session = SessionLocal()
        try:
            state = session.query(CashAccountState).filter(
                CashAccountState.account_id == account_id
            ).first()
            
            test_balance = 20000.0  # Below $25k threshold
            threshold = settings.risk.cash_account_threshold
            
            if not state:
                state = CashAccountState(
                    account_id=account_id,
                    balance=test_balance,
                    is_cash_account_mode=test_balance < threshold,
                    threshold=threshold
                )
                session.add(state)
            else:
                state.balance = test_balance
                state.is_cash_account_mode = test_balance < threshold
            
            session.commit()
            print(f"      ✓ Created state with balance ${test_balance:,.2f}")
        except Exception as e:
            print(f"      ✗ Failed to create state: {e}")
            session.rollback()
        finally:
            session.close()
        
        # Check account status
        status = await monitor.check_account_balance(account_id)
        print(f"      Balance: ${status.balance:,.2f}")
        print(f"      Threshold: ${status.threshold:,.2f}")
        print(f"      Cash Account Mode: {status.is_cash_account_mode}")
        
        assert status.balance == test_balance, "Balance mismatch"
        assert status.is_cash_account_mode == True, "Should be in cash account mode"
        print("      ✓ Cash account mode correctly enabled")
        
        # Test with balance above threshold
        print("\n   Testing with balance above threshold...")
        session = SessionLocal()
        try:
            state = session.query(CashAccountState).filter(
                CashAccountState.account_id == account_id
            ).first()
            
            test_balance = 30000.0  # Above $25k threshold
            state.balance = test_balance
            state.is_cash_account_mode = test_balance < threshold
            session.commit()
        finally:
            session.close()
        
        # Clear cache to force refresh
        monitor.clear_cache()
        status = await monitor.check_account_balance(account_id)
        
        assert status.balance == test_balance, "Balance mismatch"
        assert status.is_cash_account_mode == False, "Should NOT be in cash account mode"
        print("      ✓ Cash account mode correctly disabled")
        
        # Test cache
        print("\n   Testing cache functionality...")
        cached_status = monitor.get_cached_status(account_id)
        assert cached_status is not None, "Should have cached status"
        assert cached_status.account_id == account_id, "Cached status account ID mismatch"
        print("      ✓ Cache working correctly")
        
        print("\n   ✓ All AccountMonitor tests passed!")
        
    except Exception as e:
        print(f"   ✗ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    # Test balance extraction
    print("\n4. Testing balance extraction from account summary...")
    test_summaries = [
        {"NetLiquidation": {"value": "50000.00", "currency": "USD"}},
        {"TotalCashValue": {"value": "25000.50", "currency": "USD"}},
        {"AvailableFunds": {"value": "15000.75", "currency": "USD"}},
    ]
    
    for summary in test_summaries:
        balance = monitor._extract_balance_from_summary(summary)
        print(f"   Summary: {summary}")
        print(f"   Extracted balance: ${balance:,.2f}")
        assert balance > 0, "Should extract balance"
        print("   ✓ Balance extraction working")
    
    print("\n" + "="*60)
    print("All tests passed!")
    print("="*60)
    return True


def main():
    """Run tests"""
    try:
        success = asyncio.run(test_account_monitor())
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\nTests interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\nUnexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()

