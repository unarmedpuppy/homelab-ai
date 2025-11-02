#!/usr/bin/env python3
"""
End-to-End Risk Management Test Suite
======================================

Comprehensive integration tests for all cash account rules and risk management.

Usage:
    python scripts/test_risk_management_e2e.py
"""

import sys
import os
from datetime import datetime, timedelta

# Add project root to path
project_root = os.path.join(os.path.dirname(__file__), '..')
sys.path.insert(0, project_root)

try:
    from src.core.risk import (
        RiskManager, AccountMonitor, ComplianceManager,
        PositionSizingManager, ProfitTakingManager
    )
    from src.data.database.models import (
        Account, User, Trade, TradeSide, OrderStatus,
        CashAccountState, DayTrade, SettlementTracking, TradeFrequencyTracking
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
    print("  docker-compose exec trading-bot python scripts/test_risk_management_e2e.py")
    print("="*60)
    sys.exit(1)


class RiskManagementTestSuite:
    """Comprehensive test suite for risk management"""
    
    def __init__(self):
        self.results = {
            "passed": 0,
            "failed": 0,
            "tests": []
        }
        self.account_id = None
        self.risk_manager = None
    
    def setup_test_account(self):
        """Set up test account and cash account state"""
        session = SessionLocal()
        try:
            # Create test user
            test_user = session.query(User).filter(User.username == "test_user_risk").first()
            if not test_user:
                test_user = User(
                    username="test_user_risk",
                    email="test_risk@example.com",
                    hashed_password="dummy_hash"
                )
                session.add(test_user)
                session.commit()
            
            # Create test account
            test_account = session.query(Account).filter(Account.name == "Risk Test Account").first()
            if not test_account:
                test_account = Account(
                    user_id=test_user.id,
                    name="Risk Test Account",
                    account_type="paper",
                    broker="ibkr",
                    broker_account_id="RISK_TEST123"
                )
                session.add(test_account)
                session.commit()
            
            self.account_id = test_account.id
            
            # Set up cash account state (below threshold)
            cash_state = session.query(CashAccountState).filter(
                CashAccountState.account_id == self.account_id
            ).first()
            
            if not cash_state:
                cash_state = CashAccountState(
                    account_id=self.account_id,
                    balance=20000.0,  # Below $25k threshold
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
    
    async def test_account_monitoring(self):
        """Test account balance monitoring and cash account mode"""
        print("\n" + "="*60)
        print("Test: Account Monitoring")
        print("="*60)
        
        try:
            monitor = AccountMonitor()
            
            # Test balance check
            status = await monitor.check_account_balance(self.account_id)
            self.assert_test(
                "Account balance check",
                status.balance > 0,
                f"Balance: ${status.balance:,.2f}"
            )
            
            # Test cash account mode detection
            self.assert_test(
                "Cash account mode detection",
                status.is_cash_account_mode == True,
                f"Mode: {'Cash Account' if status.is_cash_account_mode else 'Margin Account'}"
            )
            
            # Test cache
            cached = monitor.get_cached_status(self.account_id)
            self.assert_test(
                "Cache functionality",
                cached is not None and cached.account_id == self.account_id,
                "Status cached successfully"
            )
            
        except Exception as e:
            self.assert_test("Account monitoring", False, f"Error: {e}")
    
    async def test_settlement_calculation(self):
        """Test T+2 settlement date calculation"""
        print("\n" + "="*60)
        print("Test: Settlement Date Calculation")
        print("="*60)
        
        try:
            compliance = ComplianceManager()
            
            # Test Monday trade
            monday = datetime(2024, 12, 16, 10, 0, 0)  # Monday
            settlement = compliance.calculate_settlement_date(monday)
            expected = datetime(2024, 12, 18, 0, 0, 0)  # Wednesday
            self.assert_test(
                "Monday trade settlement",
                settlement.date() == expected.date(),
                f"Monday → {settlement.date()} (expected Wednesday)"
            )
            
            # Test Friday trade (should skip weekend)
            friday = datetime(2024, 12, 13, 10, 0, 0)  # Friday
            settlement = compliance.calculate_settlement_date(friday)
            expected = datetime(2024, 12, 17, 0, 0, 0)  # Tuesday
            self.assert_test(
                "Friday trade settlement (skip weekend)",
                settlement.date() == expected.date(),
                f"Friday → {settlement.date()} (expected Tuesday, skipped weekend)"
            )
            
            # Test business day detection
            is_monday = compliance.is_business_day(datetime(2024, 12, 16).date())
            is_saturday = compliance.is_business_day(datetime(2024, 12, 14).date())
            self.assert_test(
                "Business day detection",
                is_monday == True and is_saturday == False,
                "Monday is business day, Saturday is not"
            )
            
        except Exception as e:
            self.assert_test("Settlement calculation", False, f"Error: {e}")
    
    async def test_pdt_compliance(self):
        """Test PDT violation prevention"""
        print("\n" + "="*60)
        print("Test: PDT Compliance")
        print("="*60)
        
        try:
            compliance = ComplianceManager()
            
            # Check initial PDT status
            check = await compliance.check_pdt_compliance(
                account_id=self.account_id,
                symbol="AAPL",
                side=TradeSide.BUY,
                will_create_day_trade=False
            )
            self.assert_test(
                "Initial PDT check",
                check.can_proceed == True,
                f"Can proceed: {check.message}"
            )
            
            # Get day trade count
            count = compliance.get_day_trade_count(self.account_id, lookback_days=5)
            self.assert_test(
                "Day trade count",
                count >= 0,
                f"Current day trades: {count}/3"
            )
            
            # Test warning mode
            old_mode = compliance.pdt_enforcement
            compliance.pdt_enforcement = "warning"
            check = await compliance.check_pdt_compliance(
                account_id=self.account_id,
                symbol="AAPL",
                side=TradeSide.BUY,
                will_create_day_trade=True
            )
            self.assert_test(
                "PDT warning mode",
                check.result.value in ["allowed", "warning"],
                f"Warning mode allows with warning: {check.message}"
            )
            compliance.pdt_enforcement = old_mode
            
        except Exception as e:
            self.assert_test("PDT compliance", False, f"Error: {e}")
    
    async def test_trade_frequency_limits(self):
        """Test trade frequency limits"""
        print("\n" + "="*60)
        print("Test: Trade Frequency Limits")
        print("="*60)
        
        try:
            compliance = ComplianceManager()
            
            # Check initial frequency
            check = await compliance.check_trade_frequency(self.account_id)
            self.assert_test(
                "Initial frequency check",
                check.can_proceed == True,
                f"{check.message}"
            )
            
            # Increment frequency
            compliance.increment_trade_frequency(self.account_id, datetime.now())
            
            # Check again
            check = await compliance.check_trade_frequency(self.account_id)
            self.assert_test(
                "After increment",
                check.can_proceed == True,
                f"{check.message}"
            )
            
        except Exception as e:
            self.assert_test("Trade frequency limits", False, f"Error: {e}")
    
    async def test_position_sizing(self):
        """Test position sizing with different confidence levels"""
        print("\n" + "="*60)
        print("Test: Position Sizing")
        print("="*60)
        
        try:
            sizing = PositionSizingManager()
            
            # Test low confidence
            result = await sizing.calculate_position_size(
                account_id=self.account_id,
                confidence_score=0.3,  # Low confidence
                price_per_share=150.0
            )
            self.assert_test(
                "Low confidence sizing",
                result.confidence_level.value == "low",
                f"{result.size_shares} shares (${result.size_usd:,.2f}) at {result.confidence_level.value} confidence"
            )
            
            # Test medium confidence
            result = await sizing.calculate_position_size(
                account_id=self.account_id,
                confidence_score=0.6,  # Medium confidence
                price_per_share=150.0
            )
            self.assert_test(
                "Medium confidence sizing",
                result.confidence_level.value == "medium",
                f"{result.size_shares} shares (${result.size_usd:,.2f}) at {result.confidence_level.value} confidence"
            )
            
            # Test high confidence
            result = await sizing.calculate_position_size(
                account_id=self.account_id,
                confidence_score=0.9,  # High confidence
                price_per_share=150.0
            )
            self.assert_test(
                "High confidence sizing",
                result.confidence_level.value == "high",
                f"{result.size_shares} shares (${result.size_usd:,.2f}) at {result.confidence_level.value} confidence"
            )
            
            # Verify high > medium > low
            low_size = await sizing.calculate_position_size(
                account_id=self.account_id,
                confidence_score=0.3,
                price_per_share=150.0
            )
            high_size = await sizing.calculate_position_size(
                account_id=self.account_id,
                confidence_score=0.9,
                price_per_share=150.0
            )
            self.assert_test(
                "Size increases with confidence",
                high_size.size_usd > low_size.size_usd,
                f"High: ${high_size.size_usd:,.2f} > Low: ${low_size.size_usd:,.2f}"
            )
            
        except Exception as e:
            self.assert_test("Position sizing", False, f"Error: {e}")
    
    async def test_profit_taking(self):
        """Test profit taking levels and partial exits"""
        print("\n" + "="*60)
        print("Test: Profit Taking")
        print("="*60)
        
        try:
            profit_mgr = ProfitTakingManager()
            
            # Create exit plan
            entry_price = 100.0
            quantity = 100
            exit_plan = profit_mgr.create_exit_plan(entry_price, quantity)
            
            self.assert_test(
                "Exit plan creation",
                exit_plan.level_1_price > entry_price,
                f"Level 1: ${exit_plan.level_1_price:.2f} ({((exit_plan.level_1_price/entry_price - 1) * 100):.1f}%)"
            )
            
            from src.core.risk.profit_taking import ProfitLevel
            
            # Test level 1 (5% profit)
            level_1_price = entry_price * 1.05
            result = profit_mgr.check_profit_levels(level_1_price, exit_plan, quantity)
            self.assert_test(
                "Level 1 profit detection",
                result.should_exit == True and result.profit_level == ProfitLevel.LEVEL_1,
                f"Exit: {result.exit_quantity} shares at {result.profit_pct*100:.1f}% profit"
            )
            
            # Test level 2 (10% profit)
            exit_plan2 = profit_mgr.create_exit_plan(entry_price, quantity)
            level_2_price = entry_price * 1.10
            result = profit_mgr.check_profit_levels(level_2_price, exit_plan2, quantity)
            self.assert_test(
                "Level 2 profit detection",
                result.should_exit == True and result.profit_level == ProfitLevel.LEVEL_2,
                f"Exit: {result.exit_quantity} shares at {result.profit_pct*100:.1f}% profit"
            )
            
            # Test level 3 (20% profit)
            exit_plan3 = profit_mgr.create_exit_plan(entry_price, quantity)
            level_3_price = entry_price * 1.20
            result = profit_mgr.check_profit_levels(level_3_price, exit_plan3, quantity)
            self.assert_test(
                "Level 3 profit detection",
                result.should_exit == True and result.profit_level == ProfitLevel.LEVEL_3,
                f"Exit: {result.exit_quantity} shares at {result.profit_pct*100:.1f}% profit"
            )
            
            # Test partial exit
            if profit_mgr.partial_exit_enabled:
                exit_plan4 = profit_mgr.create_exit_plan(entry_price, quantity)
                result = profit_mgr.check_profit_levels(level_1_price, exit_plan4, quantity)
                self.assert_test(
                    "Partial exit at level 1",
                    result.exit_quantity < quantity and result.remaining_shares > 0,
                    f"Exit {result.exit_quantity}/{quantity} shares, {result.remaining_shares} remaining"
                )
            
        except Exception as e:
            self.assert_test("Profit taking", False, f"Error: {e}")
    
    async def test_comprehensive_validation(self):
        """Test comprehensive pre-trade validation"""
        print("\n" + "="*60)
        print("Test: Comprehensive Pre-Trade Validation")
        print("="*60)
        
        try:
            risk_mgr = RiskManager()
            
            # Test valid trade
            validation = await risk_mgr.validate_trade(
                account_id=self.account_id,
                symbol="AAPL",
                side="BUY",
                quantity=10,
                price_per_share=150.0,
                confidence_score=0.7
            )
            self.assert_test(
                "Valid trade validation",
                validation.can_proceed == True,
                f"Validation passed: {validation.compliance_check.message}"
            )
            
            # Test with confidence-based sizing
            validation = await risk_mgr.validate_trade(
                account_id=self.account_id,
                symbol="AAPL",
                side="BUY",
                price_per_share=150.0,
                confidence_score=0.8  # High confidence
            )
            self.assert_test(
                "Confidence-based sizing",
                validation.position_size is not None and validation.position_size.size_shares > 0,
                f"Calculated size: {validation.position_size.size_shares} shares"
            )
            
            # Test risk status
            status = await risk_mgr.get_risk_status(self.account_id)
            self.assert_test(
                "Risk status retrieval",
                status.account_id == self.account_id,
                f"Status retrieved: Cash mode={status.is_cash_account_mode}, "
                f"Day trades={status.day_trade_count}, "
                f"Settled cash=${status.available_settled_cash:,.2f}"
            )
            
        except Exception as e:
            self.assert_test("Comprehensive validation", False, f"Error: {e}")
    
    async def test_edge_cases(self):
        """Test edge cases and boundary conditions"""
        print("\n" + "="*60)
        print("Test: Edge Cases")
        print("="*60)
        
        try:
            # Test zero balance
            session = SessionLocal()
            try:
                cash_state = session.query(CashAccountState).filter(
                    CashAccountState.account_id == self.account_id
                ).first()
                original_balance = cash_state.balance
                cash_state.balance = 0.0
                session.commit()
                
                sizing = PositionSizingManager()
                result = await sizing.calculate_position_size(
                    account_id=self.account_id,
                    confidence_score=0.8,
                    price_per_share=150.0
                )
                self.assert_test(
                    "Zero balance handling",
                    result.size_shares == 0,
                    "Position size is 0 with zero balance"
                )
                
                # Restore balance
                cash_state.balance = original_balance
                session.commit()
            finally:
                session.close()
            
            # Test negative confidence (should raise error)
            sizing = PositionSizingManager()
            try:
                await sizing.calculate_position_size(
                    account_id=self.account_id,
                    confidence_score=-0.1,
                    price_per_share=150.0
                )
                self.assert_test("Negative confidence validation", False, "Should raise ValueError")
            except ValueError:
                self.assert_test("Negative confidence validation", True, "Correctly raises ValueError")
            
            # Test zero price
            try:
                await sizing.calculate_position_size(
                    account_id=self.account_id,
                    confidence_score=0.8,
                    price_per_share=0.0
                )
                self.assert_test("Zero price validation", False, "Should raise ValueError")
            except ValueError:
                self.assert_test("Zero price validation", True, "Correctly raises ValueError")
            
        except Exception as e:
            self.assert_test("Edge cases", False, f"Error: {e}")
    
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
    print("Risk Management End-to-End Test Suite")
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
    suite = RiskManagementTestSuite()
    
    # Setup test account
    print("\n2. Setting up test account...")
    try:
        suite.setup_test_account()
    except Exception as e:
        print(f"   ✗ Setup failed: {e}")
        return False
    
    # Initialize risk manager
    suite.risk_manager = RiskManager()
    
    # Run all tests
    await suite.test_account_monitoring()
    await suite.test_settlement_calculation()
    await suite.test_pdt_compliance()
    await suite.test_trade_frequency_limits()
    await suite.test_position_sizing()
    await suite.test_profit_taking()
    await suite.test_comprehensive_validation()
    await suite.test_edge_cases()
    
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

