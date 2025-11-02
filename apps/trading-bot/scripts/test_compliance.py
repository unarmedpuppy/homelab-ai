#!/usr/bin/env python3
"""
Test script for Compliance Manager

Tests PDT compliance, settlement tracking, and trade frequency limits.

Usage:
    python scripts/test_compliance.py
"""

import sys
import os
from datetime import datetime, timedelta

# Add project root to path
project_root = os.path.join(os.path.dirname(__file__), '..')
sys.path.insert(0, project_root)

try:
    from src.core.risk.compliance import ComplianceManager, ComplianceResult
    from src.core.risk.account_monitor import AccountMonitor
    from src.data.database.models import Trade, TradeSide, OrderStatus, Account, CashAccountState
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
    print("  docker-compose exec trading-bot python scripts/test_compliance.py")
    print("="*60)
    sys.exit(1)


async def test_compliance():
    """Test compliance manager functionality"""
    print("="*60)
    print("Compliance Manager Test Suite")
    print("="*60)
    
    # Initialize database
    print("\n1. Initializing database...")
    try:
        init_db()
        print("   ✓ Database initialized")
    except Exception as e:
        print(f"   ✗ Database initialization failed: {e}")
        return False
    
    # Get or create test account
    print("\n2. Setting up test account...")
    session = SessionLocal()
    try:
        from src.data.database.models import User
        test_user = session.query(User).filter(User.username == "test_user").first()
        if not test_user:
            test_user = User(
                username="test_user",
                email="test@example.com",
                hashed_password="dummy_hash"
            )
            session.add(test_user)
            session.commit()
        
        test_account = session.query(Account).filter(Account.name == "Test Account").first()
        if not test_account:
            test_account = Account(
                user_id=test_user.id,
                name="Test Account",
                account_type="paper",
                broker="ibkr",
                broker_account_id="TEST123"
            )
            session.add(test_account)
            session.commit()
        
        # Set up cash account state (below threshold for testing)
        cash_state = session.query(CashAccountState).filter(
            CashAccountState.account_id == test_account.id
        ).first()
        
        if not cash_state:
            cash_state = CashAccountState(
                account_id=test_account.id,
                balance=20000.0,  # Below $25k threshold
                is_cash_account_mode=True,
                threshold=25000.0
            )
            session.add(cash_state)
        else:
            cash_state.balance = 20000.0
            cash_state.is_cash_account_mode = True
        
        session.commit()
        print(f"   ✓ Test account ready (ID: {test_account.id}, Cash Account Mode: {cash_state.is_cash_account_mode})")
        account_id = test_account.id
    except Exception as e:
        print(f"   ✗ Failed to setup test account: {e}")
        import traceback
        traceback.print_exc()
        session.rollback()
        session.close()
        return False
    finally:
        session.close()
    
    # Initialize compliance manager
    print("\n3. Initializing ComplianceManager...")
    account_monitor = AccountMonitor()
    compliance = ComplianceManager(account_monitor=account_monitor)
    print("   ✓ ComplianceManager initialized")
    
    # Test settlement date calculation
    print("\n4. Testing settlement date calculation (T+2)...")
    try:
        # Test Monday trade
        monday = datetime(2024, 12, 16, 10, 0, 0)  # Monday
        settlement = compliance.calculate_settlement_date(monday)
        expected = datetime(2024, 12, 18, 0, 0, 0)  # Wednesday (2 business days later)
        assert settlement.date() == expected.date(), f"Expected {expected.date()}, got {settlement.date()}"
        print(f"   ✓ Monday trade: {monday.date()} → settlement {settlement.date()} (Wednesday)")
        
        # Test Friday trade
        friday = datetime(2024, 12, 13, 10, 0, 0)  # Friday
        settlement = compliance.calculate_settlement_date(friday)
        expected = datetime(2024, 12, 17, 0, 0, 0)  # Tuesday (skip weekend)
        assert settlement.date() == expected.date(), f"Expected {expected.date()}, got {settlement.date()}"
        print(f"   ✓ Friday trade: {friday.date()} → settlement {settlement.date()} (Tuesday, skipped weekend)")
        
    except Exception as e:
        print(f"   ✗ Settlement date calculation failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    # Test PDT compliance
    print("\n5. Testing PDT compliance checks...")
    try:
        # Check initial PDT status
        check = await compliance.check_pdt_compliance(
            account_id=account_id,
            symbol="AAPL",
            side=TradeSide.BUY,
            will_create_day_trade=False
        )
        print(f"   Initial PDT check: {check.result.value} - {check.message}")
        assert check.can_proceed, "Should allow first trade"
        print("   ✓ Initial PDT check passed")
        
        # Simulate 3 day trades (would block)
        # Note: This is a simplified test - in real scenario, we'd create actual trades
        day_trade_count = compliance.get_day_trade_count(account_id, lookback_days=5)
        print(f"   Current day trade count: {day_trade_count}/3")
        print(f"   ✓ PDT tracking working")
        
    except Exception as e:
        print(f"   ✗ PDT compliance test failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    # Test trade frequency limits
    print("\n6. Testing trade frequency limits...")
    try:
        check = await compliance.check_trade_frequency(account_id)
        print(f"   Frequency check: {check.result.value} - {check.message}")
        assert check.can_proceed, "Should allow trades initially"
        print("   ✓ Trade frequency check passed")
        
        # Test incrementing frequency
        compliance.increment_trade_frequency(account_id, datetime.now())
        check = await compliance.check_trade_frequency(account_id)
        print(f"   After increment: {check.message}")
        print("   ✓ Trade frequency tracking working")
        
    except Exception as e:
        print(f"   ✗ Trade frequency test failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    # Test comprehensive compliance check
    print("\n7. Testing comprehensive compliance check...")
    try:
        check = await compliance.check_compliance(
            account_id=account_id,
            symbol="AAPL",
            side=TradeSide.BUY,
            amount=-1000.0,  # Negative for BUY (cash used)
            will_create_day_trade=False
        )
        print(f"   Comprehensive check: {check.result.value} - {check.message}")
        print(f"   Can proceed: {check.can_proceed}")
        print("   ✓ Comprehensive compliance check working")
        
    except Exception as e:
        print(f"   ✗ Comprehensive compliance check failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    # Test settlement recording
    print("\n8. Testing settlement tracking...")
    try:
        # Create a test trade first
        session = SessionLocal()
        try:
            test_trade = Trade(
                account_id=account_id,
                symbol="AAPL",
                side=TradeSide.BUY,
                quantity=10,
                price=150.0,
                order_type="market",
                status=OrderStatus.FILLED,
                executed_at=datetime.now()
            )
            session.add(test_trade)
            session.commit()
            session.refresh(test_trade)
            
            # Record settlement
            settlement = compliance.record_settlement(
                account_id=account_id,
                trade_id=test_trade.id,
                trade_date=test_trade.executed_at,
                amount=-1500.0  # Negative for BUY
            )
            
            assert settlement is not None, "Settlement should be recorded"
            assert settlement.settlement_date > settlement.trade_date, "Settlement date should be after trade date"
            print(f"   Trade date: {settlement.trade_date.date()}")
            print(f"   Settlement date: {settlement.settlement_date.date()}")
            print("   ✓ Settlement tracking working")
            
        finally:
            session.close()
        
    except Exception as e:
        print(f"   ✗ Settlement tracking test failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    print("\n" + "="*60)
    print("All compliance tests passed!")
    print("="*60)
    return True


def main():
    """Run tests"""
    try:
        success = asyncio.run(test_compliance())
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

