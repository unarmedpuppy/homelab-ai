#!/usr/bin/env python3
"""
Good Faith Violation (GFV) Prevention Test Script
==================================================

Tests GFV detection and prevention logic.

Usage:
    python scripts/test_gfv_prevention.py
"""

import sys
import os
from datetime import datetime, timedelta

# Add project root to path
project_root = os.path.join(os.path.dirname(__file__), '..')
sys.path.insert(0, project_root)

try:
    from src.core.risk import ComplianceManager, AccountMonitor
    from src.data.database.models import (
        Account, User, Trade, TradeSide, OrderStatus,
        CashAccountState, SettlementTracking
    )
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
    print("  docker-compose exec trading-bot python scripts/test_gfv_prevention.py")
    print("="*60)
    sys.exit(1)


class GFVTestSuite:
    """Test suite for GFV prevention"""
    
    def __init__(self):
        self.results = {
            "passed": 0,
            "failed": 0,
            "tests": []
        }
        self.account_id = None
        self.compliance = None
    
    def setup_test_account(self):
        """Set up test account"""
        session = SessionLocal()
        try:
            # Get or create test user
            test_user = session.query(User).filter(User.username == "test_user_gfv").first()
            if not test_user:
                test_user = User(
                    username="test_user_gfv",
                    email="test_gfv@example.com",
                    hashed_password="dummy_hash"
                )
                session.add(test_user)
                session.commit()
            
            # Get or create test account
            test_account = session.query(Account).filter(Account.name == "GFV Test Account").first()
            if not test_account:
                test_account = Account(
                    user_id=test_user.id,
                    name="GFV Test Account",
                    account_type="paper",
                    broker="ibkr",
                    broker_account_id="GFV_TEST123"
                )
                session.add(test_account)
                session.commit()
            
            self.account_id = test_account.id
            
            # Set up cash account state
            cash_state = session.query(CashAccountState).filter(
                CashAccountState.account_id == self.account_id
            ).first()
            
            if not cash_state:
                cash_state = CashAccountState(
                    account_id=self.account_id,
                    balance=20000.0,
                    is_cash_account_mode=True,
                    threshold=25000.0
                )
                session.add(cash_state)
            else:
                cash_state.balance = 20000.0
                cash_state.is_cash_account_mode = True
            
            session.commit()
            print(f"✓ Test account ready: ID={self.account_id}, Balance=${cash_state.balance:,.2f}")
            
        except Exception as e:
            session.rollback()
            print(f"✗ Failed to setup test account: {e}")
            raise
        finally:
            session.close()
    
    def assert_test(self, name: str, condition: bool, message: str = ""):
        """Assert a test condition"""
        if condition:
            self.results["passed"] += 1
            self.results["tests"].append({"name": name, "status": "PASS", "message": message})
            print(f"  ✓ {name}: {message}")
            return True
        else:
            self.results["failed"] += 1
            self.results["tests"].append({"name": name, "status": "FAIL", "message": message})
            print(f"  ✗ {name}: {message}")
            return False
    
    async def test_buy_with_settled_cash(self):
        """Test buying with settled cash (should pass)"""
        print("\n" + "="*60)
        print("Test: Buy with Settled Cash")
        print("="*60)
        
        try:
            check = await self.compliance.check_gfv_prevention(
                account_id=self.account_id,
                symbol="AAPL",
                side=TradeSide.BUY,
                amount=-1000.0  # Negative for buy
            )
            
            self.assert_test(
                "Buy with settled cash",
                check.can_proceed == True and check.result.value in ["allowed", "warning"],
                f"Result: {check.result.value}, Message: {check.message[:80]}"
            )
            
        except Exception as e:
            self.assert_test("Buy with settled cash", False, f"Error: {e}")
    
    async def test_buy_with_unsettled_funds_no_position(self):
        """Test buying with unsettled funds but no existing position (should warn)"""
        print("\n" + "="*60)
        print("Test: Buy with Unsettled Funds (No Existing Position)")
        print("="*60)
        
        try:
            # First, create a SELL trade that hasn't settled yet
            session = SessionLocal()
            try:
                sell_trade = Trade(
                    account_id=self.account_id,
                    symbol="TSLA",
                    side=TradeSide.SELL,
                    quantity=10,
                    price=200.0,
                    order_type="market",
                    status=OrderStatus.FILLED,
                    filled_quantity=10,
                    timestamp=datetime.now()
                )
                session.add(sell_trade)
                session.flush()
                
                # Record settlement (settlement date in future)
                settlement_date = self.compliance.calculate_settlement_date(datetime.now())
                settlement = SettlementTracking(
                    account_id=self.account_id,
                    trade_id=sell_trade.id,
                    trade_date=datetime.now(),
                    settlement_date=settlement_date,
                    amount=2000.0,  # Positive for SELL
                    is_settled=False
                )
                session.add(settlement)
                session.commit()
                
                # Now try to buy with those unsettled funds
                check = await self.compliance.check_gfv_prevention(
                    account_id=self.account_id,
                    symbol="AAPL",  # Different symbol
                    side=TradeSide.BUY,
                    amount=-1500.0
                )
                
                self.assert_test(
                    "Buy with unsettled funds (different symbol)",
                    check.can_proceed == True,
                    f"Result: {check.result.value}, Message: {check.message[:80]}"
                )
                
                # Cleanup
                session.delete(settlement)
                session.delete(sell_trade)
                session.commit()
                
            except Exception as e:
                session.rollback()
                raise
            finally:
                session.close()
                
        except Exception as e:
            self.assert_test("Buy with unsettled funds", False, f"Error: {e}")
    
    async def test_sell_with_settled_position(self):
        """Test selling a position that was bought with settled funds (should pass)"""
        print("\n" + "="*60)
        print("Test: Sell Settled Position")
        print("="*60)
        
        try:
            check = await self.compliance.check_gfv_prevention(
                account_id=self.account_id,
                symbol="MSFT",
                side=TradeSide.SELL,
                amount=1500.0  # Positive for sell
            )
            
            self.assert_test(
                "Sell settled position",
                check.can_proceed == True,
                f"Result: {check.result.value}, Message: {check.message[:80]}"
            )
            
        except Exception as e:
            self.assert_test("Sell settled position", False, f"Error: {e}")
    
    async def test_sell_unsettled_position_warning_mode(self):
        """Test selling a position bought with unsettled funds in warning mode"""
        print("\n" + "="*60)
        print("Test: Sell Unsettled Position (Warning Mode)")
        print("="*60)
        
        try:
            # Set to warning mode
            original_mode = self.compliance.gfv_enforcement_mode
            self.compliance.gfv_enforcement_mode = "warning"
            
            # Create a BUY trade that hasn't settled
            session = SessionLocal()
            try:
                buy_trade = Trade(
                    account_id=self.account_id,
                    symbol="NVDA",
                    side=TradeSide.BUY,
                    quantity=5,
                    price=400.0,
                    order_type="market",
                    status=OrderStatus.FILLED,
                    filled_quantity=5,
                    timestamp=datetime.now()
                )
                session.add(buy_trade)
                session.flush()
                
                # Record settlement (settlement date in future)
                settlement_date = self.compliance.calculate_settlement_date(datetime.now())
                settlement = SettlementTracking(
                    account_id=self.account_id,
                    trade_id=buy_trade.id,
                    trade_date=datetime.now(),
                    settlement_date=settlement_date,
                    amount=-2000.0,  # Negative for BUY
                    is_settled=False
                )
                session.add(settlement)
                session.commit()
                
                # Now try to sell (should warn but allow)
                check = await self.compliance.check_gfv_prevention(
                    account_id=self.account_id,
                    symbol="NVDA",
                    side=TradeSide.SELL,
                    amount=2100.0
                )
                
                self.assert_test(
                    "Sell unsettled position (warning mode)",
                    check.can_proceed == True and check.result.value == "warning",
                    f"Result: {check.result.value}, Message: {check.message[:80]}"
                )
                
                # Cleanup
                session.delete(settlement)
                session.delete(buy_trade)
                session.commit()
                
            except Exception as e:
                session.rollback()
                raise
            finally:
                session.close()
                self.compliance.gfv_enforcement_mode = original_mode
                
        except Exception as e:
            self.assert_test("Sell unsettled position (warning)", False, f"Error: {e}")
    
    async def test_sell_unsettled_position_strict_mode(self):
        """Test selling a position bought with unsettled funds in strict mode"""
        print("\n" + "="*60)
        print("Test: Sell Unsettled Position (Strict Mode)")
        print("="*60)
        
        try:
            # Set to strict mode
            original_mode = self.compliance.gfv_enforcement_mode
            self.compliance.gfv_enforcement_mode = "strict"
            
            # Create a BUY trade that hasn't settled
            session = SessionLocal()
            try:
                buy_trade = Trade(
                    account_id=self.account_id,
                    symbol="AMD",
                    side=TradeSide.BUY,
                    quantity=10,
                    price=100.0,
                    order_type="market",
                    status=OrderStatus.FILLED,
                    filled_quantity=10,
                    timestamp=datetime.now()
                )
                session.add(buy_trade)
                session.flush()
                
                # Record settlement (settlement date in future)
                settlement_date = self.compliance.calculate_settlement_date(datetime.now())
                settlement = SettlementTracking(
                    account_id=self.account_id,
                    trade_id=buy_trade.id,
                    trade_date=datetime.now(),
                    settlement_date=settlement_date,
                    amount=-1000.0,  # Negative for BUY
                    is_settled=False
                )
                session.add(settlement)
                session.commit()
                
                # Now try to sell (should block)
                check = await self.compliance.check_gfv_prevention(
                    account_id=self.account_id,
                    symbol="AMD",
                    side=TradeSide.SELL,
                    amount=1100.0
                )
                
                self.assert_test(
                    "Sell unsettled position (strict mode)",
                    check.can_proceed == False and check.result.value == "blocked_gfv",
                    f"Result: {check.result.value}, Message: {check.message[:80]}"
                )
                
                # Cleanup
                session.delete(settlement)
                session.delete(buy_trade)
                session.commit()
                
            except Exception as e:
                session.rollback()
                raise
            finally:
                session.close()
                self.compliance.gfv_enforcement_mode = original_mode
                
        except Exception as e:
            self.assert_test("Sell unsettled position (strict)", False, f"Error: {e}")
    
    def print_summary(self):
        """Print test summary"""
        print("\n" + "="*60)
        print("Test Summary")
        print("="*60)
        print(f"Total Tests: {self.results['passed'] + self.results['failed']}")
        print(f"Passed: {self.results['passed']}")
        print(f"Failed: {self.results['failed']}")
        
        if self.results['failed'] > 0:
            print("\nFailed Tests:")
            for test in self.results['tests']:
                if test['status'] == 'FAIL':
                    print(f"  ✗ {test['name']}: {test['message']}")
        
        print("\n" + "="*60)
        if self.results['failed'] == 0:
            print("🎉 All tests passed!")
        else:
            print(f"⚠️  {self.results['failed']} test(s) failed")
        print("="*60)


async def main():
    """Run all tests"""
    print("="*60)
    print("GFV Prevention Test Suite")
    print("="*60)
    
    # Initialize database
    print("\n1. Initializing database...")
    try:
        init_db()
        print("   ✓ Database initialized")
    except Exception as e:
        print(f"   ✗ Database initialization failed: {e}")
        return False
    
    # Create test suite
    suite = GFVTestSuite()
    
    # Setup test account
    print("\n2. Setting up test account...")
    try:
        suite.setup_test_account()
    except Exception as e:
        print(f"   ✗ Setup failed: {e}")
        return False
    
    # Initialize compliance manager
    suite.compliance = ComplianceManager()
    
    # Run all tests
    await suite.test_buy_with_settled_cash()
    await suite.test_buy_with_unsettled_funds_no_position()
    await suite.test_sell_with_settled_position()
    await suite.test_sell_unsettled_position_warning_mode()
    await suite.test_sell_unsettled_position_strict_mode()
    
    # Print summary
    suite.print_summary()
    
    return suite.results['failed'] == 0


if __name__ == "__main__":
    try:
        success = asyncio.run(main())
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\nTests interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\nUnexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

