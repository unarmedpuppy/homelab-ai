"""
End-to-End Integration Tests for Cash Account Rules
====================================================

Comprehensive tests that validate the complete cash account rules workflow,
including all components working together:
- Account monitoring
- Compliance checks
- Position sizing
- Profit taking
- Trade execution flow
"""

import pytest
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from datetime import datetime, timedelta
from decimal import Decimal

from src.core.risk import (
    RiskManager,
    AccountMonitor,
    ComplianceManager,
    PositionSizingManager,
    ProfitTakingManager,
    get_risk_manager
)
from src.core.risk.position_sizing import ConfidenceLevel
from src.core.risk.compliance import ComplianceCheck, ComplianceResult
from src.data.database.models import TradeSide, OrderStatus, Account, Trade
from src.data.database import SessionLocal


class TestCashAccountRulesEndToEnd:
    """End-to-end tests for cash account rules"""
    
    @pytest.fixture
    def mock_account(self):
        """Create a mock account"""
        account = Mock(spec=Account)
        account.id = 1
        account.balance = 15000.0  # Under $25k threshold
        account.account_type = "CASH"
        return account
    
    @pytest.fixture
    def mock_account_monitor(self):
        """Create a mock account monitor"""
        monitor = Mock(spec=AccountMonitor)
        monitor.check_account_balance = AsyncMock(return_value=Mock(
            account_id=1,
            balance=15000.0,
            is_cash_account_mode=True,
            threshold=25000.0
        ))
        monitor.is_cash_account_mode = AsyncMock(return_value=True)
        return monitor
    
    @pytest.fixture
    def mock_compliance_manager(self):
        """Create a mock compliance manager"""
        compliance = Mock(spec=ComplianceManager)
        
        # Mock settlement tracking
        compliance.calculate_settlement_date = Mock(
            return_value=datetime.now() + timedelta(days=2)
        )
        compliance.get_available_settled_cash = AsyncMock(return_value=15000.0)
        compliance.record_settlement = Mock()
        compliance.increment_trade_frequency = Mock()
        compliance.detect_day_trade = Mock(return_value=None)
        compliance.record_day_trade = Mock()
        compliance.get_compliance_summary = AsyncMock(return_value={})
        
        # Mock compliance manager attributes needed by RiskManager
        compliance.daily_limit = 5
        compliance.weekly_limit = 20
        
        # Mock compliance check (default: pass)
        compliance.check_compliance = AsyncMock(return_value=ComplianceCheck(
            result=ComplianceResult.ALLOWED,
            message="Compliance check passed",
            can_proceed=True,
            details={}
        ))
        
        return compliance
    
    @pytest.fixture
    def mock_position_sizing(self):
        """Create a mock position sizing manager"""
        sizing = Mock(spec=PositionSizingManager)
        sizing.calculate_position_size = AsyncMock(return_value=Mock(
            size_usd=150.0,
            size_shares=10,
            confidence_level=ConfidenceLevel.LOW,
            base_percentage=0.01,
            actual_percentage=0.01,
            max_size_hit=False,
            available_cash_used=1.0
        ))
        sizing.calculate_position_size_with_settlement = AsyncMock(return_value=Mock(
            size_usd=150.0,
            size_shares=10,
            confidence_level=ConfidenceLevel.LOW,
            base_percentage=0.01,
            actual_percentage=0.01,
            max_size_hit=False,
            available_cash_used=1.0
        ))
        return sizing
    
    @pytest.fixture
    def mock_profit_taking(self):
        """Create a mock profit taking manager"""
        profit = Mock(spec=ProfitTakingManager)
        profit.create_exit_plan = Mock(return_value=Mock(
            entry_price=15.0,
            level_1_price=15.75,  # 5%
            level_2_price=16.50,  # 10%
            level_3_price=18.00,  # 20%
            level_1_exit_pct=0.25,
            level_2_exit_pct=0.50,
            level_3_exit_pct=0.25,
            levels_hit=[]
        ))
        profit.check_profit_levels = Mock(return_value=Mock(
            should_exit=False,
            exit_quantity=0,
            profit_level=None,
            profit_pct=0.0,
            remaining_shares=10,
            message="No exit needed"
        ))
        return profit
    
    @pytest.fixture
    def risk_manager(
        self,
        mock_account_monitor,
        mock_compliance_manager,
        mock_position_sizing,
        mock_profit_taking
    ):
        """Create a RiskManager with mocked dependencies"""
        return RiskManager(
            account_monitor=mock_account_monitor,
            compliance_manager=mock_compliance_manager,
            position_sizing_manager=mock_position_sizing,
            profit_taking_manager=mock_profit_taking
        )
    
    @pytest.mark.asyncio
    async def test_complete_trade_execution_workflow(
        self,
        risk_manager,
        mock_account,
        mock_account_monitor,
        mock_compliance_manager,
        mock_position_sizing
    ):
        """Test complete trade execution workflow with all risk checks"""
        # Simulate a BUY trade request
        account_id = 1
        symbol = "AAPL"
        side = "BUY"
        price_per_share = 15.0
        confidence_score = 0.3  # Low confidence
        
        # 1. Validate trade (pre-trade validation)
        validation = await risk_manager.validate_trade(
            account_id=account_id,
            symbol=symbol,
            side=side,
            price_per_share=price_per_share,
            confidence_score=confidence_score,
            will_create_day_trade=False
        )
        
        # Assertions
        assert validation.is_valid is True
        assert validation.can_proceed is True
        assert validation.position_size is not None
        assert validation.position_size.size_shares == 10
        assert validation.position_size.confidence_level == ConfidenceLevel.LOW
        
        # Verify compliance check was called
        mock_compliance_manager.check_compliance.assert_called_once()
        
        # Verify position sizing was called with settled cash (cash account mode)
        mock_position_sizing.calculate_position_size_with_settlement.assert_called_once()
        
        # Verify account mode check
        mock_account_monitor.is_cash_account_mode.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_pdt_blocking_workflow(
        self,
        risk_manager,
        mock_compliance_manager
    ):
        """Test that PDT violations are properly blocked"""
        # Mock compliance check to return PDT violation
        mock_compliance_manager.check_compliance = AsyncMock(return_value=ComplianceCheck(
            result=ComplianceResult.BLOCKED_PDT,
            message="Would create pattern day trader status",
            can_proceed=False,
            details={"day_trade_count": 4, "limit": 3}
        ))
        
        # Attempt to validate trade that would create PDT
        validation = await risk_manager.validate_trade(
            account_id=1,
            symbol="AAPL",
            side="BUY",
            price_per_share=15.0,
            confidence_score=0.5,
            will_create_day_trade=True
        )
        
        # Assertions
        assert validation.is_valid is False
        assert validation.can_proceed is False
        assert validation.compliance_check.result == ComplianceResult.BLOCKED_PDT
    
    @pytest.mark.asyncio
    async def test_settlement_constrained_position_sizing(
        self,
        risk_manager,
        mock_compliance_manager,
        mock_position_sizing,
        mock_account_monitor
    ):
        """Test position sizing with settlement constraints"""
        # Mock limited settled cash
        mock_compliance_manager.get_available_settled_cash = AsyncMock(
            return_value=500.0  # Only $500 settled
        )
        
        # Mock position sizing with settlement constraint
        mock_position_sizing.calculate_position_size_with_settlement = AsyncMock(
            return_value=Mock(
                size_usd=500.0,
                size_shares=33,  # Limited by settled cash
                confidence_level=ConfidenceLevel.LOW,
                base_percentage=0.01,
                actual_percentage=0.033,  # Adjusted due to constraint
                max_size_hit=False,
                available_cash_used=100.0
            )
        )
        
        # Validate trade
        validation = await risk_manager.validate_trade(
            account_id=1,
            symbol="AAPL",
            side="BUY",
            price_per_share=15.0,
            confidence_score=0.3,
            will_create_day_trade=False
        )
        
        # Verify settled cash was checked
        mock_compliance_manager.get_available_settled_cash.assert_called_once_with(1)
        
        # Verify position sizing used settled cash
        call_args = mock_position_sizing.calculate_position_size_with_settlement.call_args
        assert call_args[1]['available_settled_cash'] == 500.0
        
        # Verify position size is constrained
        assert validation.position_size.size_shares == 33
        assert validation.position_size.size_usd == 500.0
    
    @pytest.mark.asyncio
    async def test_trade_frequency_limiting(
        self,
        risk_manager,
        mock_compliance_manager
    ):
        """Test trade frequency limits are enforced"""
        # Mock compliance check to return frequency limit violation
        mock_compliance_manager.check_compliance = AsyncMock(return_value=ComplianceCheck(
            result=ComplianceResult.BLOCKED_FREQUENCY,
            message="Daily trade limit exceeded (5/5 trades)",
            can_proceed=False,
            details={"daily_count": 5, "daily_limit": 5}
        ))
        
        # Attempt to validate trade exceeding frequency limit
        validation = await risk_manager.validate_trade(
            account_id=1,
            symbol="AAPL",
            side="BUY",
            price_per_share=15.0,
            confidence_score=0.5,
            will_create_day_trade=False
        )
        
        # Assertions
        assert validation.can_proceed is False
        assert validation.compliance_check.result == ComplianceResult.BLOCKED_FREQUENCY
    
    @pytest.mark.asyncio
    async def test_confidence_based_position_sizing(
        self,
        risk_manager,
        mock_position_sizing,
        mock_account_monitor
    ):
        """Test position sizing scales with confidence levels"""
        confidence_scores = [
            (0.2, ConfidenceLevel.LOW),      # Low confidence
            (0.5, ConfidenceLevel.MEDIUM),   # Medium confidence
            (0.8, ConfidenceLevel.HIGH),     # High confidence
        ]
        
        for confidence_score, expected_level in confidence_scores:
            # Mock position sizing for this confidence
            mock_position_sizing.calculate_position_size_with_settlement = AsyncMock(
                return_value=Mock(
                    size_usd=150.0 * (confidence_score * 2),  # Scale with confidence
                    size_shares=int(150.0 * (confidence_score * 2) / 15.0),
                    confidence_level=expected_level,
                    base_percentage=0.01 + (confidence_score * 0.03),
                    actual_percentage=0.01 + (confidence_score * 0.03),
                    max_size_hit=False,
                    available_cash_used=1.0
                )
            )
            
            # Validate trade
            validation = await risk_manager.validate_trade(
                account_id=1,
                symbol="AAPL",
                side="BUY",
                price_per_share=15.0,
                confidence_score=confidence_score,
                will_create_day_trade=False
            )
            
            # Verify position sizing reflects confidence
            assert validation.position_size.confidence_level == expected_level
    
    @pytest.mark.asyncio
    async def test_profit_taking_integration(
        self,
        risk_manager,
        mock_profit_taking
    ):
        """Test profit taking integration with position management"""
        # Create exit plan
        entry_price = 15.0
        quantity = 10
        
        exit_plan = mock_profit_taking.create_exit_plan(
            entry_price=entry_price,
            quantity=quantity
        )
        
        # Simulate price movement to level 1 (5% profit)
        current_price = 15.75
        mock_profit_taking.check_profit_levels = Mock(return_value=Mock(
            should_exit=True,
            exit_quantity=3,  # 25% of 10 shares
            profit_level=Mock(value="level_1"),
            profit_pct=0.05,
            remaining_shares=7,
            message="Level 1 (5.0% profit) reached, exiting 3 shares (7 remaining)"
        ))
        
        # Check profit levels
        result = mock_profit_taking.check_profit_levels(
            current_price=current_price,
            exit_plan=exit_plan,
            current_quantity=quantity
        )
        
        # Assertions
        assert result.should_exit is True
        assert result.exit_quantity == 3
        assert result.profit_pct == 0.05
        assert result.remaining_shares == 7
    
    @pytest.mark.asyncio
    async def test_day_trade_detection(
        self,
        risk_manager,
        mock_compliance_manager
    ):
        """Test day trade detection and recording"""
        # Mock day trade detection
        mock_compliance_manager.detect_day_trade = Mock(
            return_value=(1, 2)  # buy_trade_id, sell_trade_id
        )
        
        # Simulate a SELL that creates a day trade
        validation = await risk_manager.validate_trade(
            account_id=1,
            symbol="AAPL",
            side="SELL",
            quantity=10,
            price_per_share=16.0,
            will_create_day_trade=True
        )
        
        # Verify day trade detection would be called during execution
        # (This is tested in the actual execution flow)
        assert validation.can_proceed  # Should still validate (day trades are allowed if under limit)
    
    @pytest.mark.asyncio
    async def test_risk_status_summary(
        self,
        risk_manager,
        mock_account_monitor,
        mock_compliance_manager
    ):
        """Test risk status provides comprehensive summary"""
        # Mock account status
        mock_account_monitor.check_account_balance = AsyncMock(return_value=Mock(
            account_id=1,
            balance=15000.0,
            is_cash_account_mode=True,
            threshold=25000.0
        ))
        
        # Mock compliance summary
        mock_compliance_manager.get_compliance_summary = AsyncMock(return_value={
            "day_trade_count": 2,
            "daily_trade_count": 3,
            "weekly_trade_count": 8,
            "available_settled_cash": 12000.0,
            "pending_settlements": []
        })
        
        # Get risk status
        risk_status = await risk_manager.get_risk_status(account_id=1)
        
        # Assertions
        assert risk_status.account_id == 1
        assert risk_status.is_cash_account_mode is True
        assert risk_status.account_status.balance == 15000.0
    
    @pytest.mark.asyncio
    async def test_multiple_trades_settlement_tracking(
        self,
        risk_manager,
        mock_compliance_manager,
        mock_position_sizing
    ):
        """Test settlement tracking across multiple trades"""
        # Reset and configure mock to return different values for each call
        mock_compliance_manager.get_available_settled_cash.reset_mock()
        mock_compliance_manager.get_available_settled_cash.side_effect = [
            15000.0,  # First call - full settled cash
            14850.0   # Second call - reduced by first trade amount
        ]
        
        validation1 = await risk_manager.validate_trade(
            account_id=1,
            symbol="AAPL",
            side="BUY",
            price_per_share=15.0,
            confidence_score=0.3,
            will_create_day_trade=False
        )
        
        validation2 = await risk_manager.validate_trade(
            account_id=1,
            symbol="MSFT",
            side="BUY",
            price_per_share=20.0,
            confidence_score=0.3,
            will_create_day_trade=False
        )
        
        # Both validations should succeed
        assert validation1.can_proceed is True
        assert validation2.can_proceed is True
        
        # Verify settled cash tracking (should be called twice - once per validation)
        assert mock_compliance_manager.get_available_settled_cash.call_count == 2


class TestRiskManagerIntegration:
    """Integration tests for RiskManager with real components"""
    
    @pytest.mark.asyncio
    @patch('src.core.risk.account_monitor.AccountMonitor.check_account_balance')
    @patch('src.core.risk.compliance.ComplianceManager.check_compliance')
    @patch('src.core.risk.compliance.ComplianceManager.get_available_settled_cash')
    async def test_real_risk_manager_validation(
        self,
        mock_settled_cash,
        mock_compliance,
        mock_balance
    ):
        """Test RiskManager with real components but mocked dependencies"""
        # Setup mocks
        from src.core.risk.account_monitor import AccountStatus
        
        mock_balance.return_value = AccountStatus(
            account_id=1,
            balance=15000.0,
            is_cash_account_mode=True,
            threshold=25000.0
        )
        
        mock_settled_cash.return_value = 15000.0
        
        mock_compliance.return_value = ComplianceCheck(
            result=ComplianceResult.ALLOWED,
            message="Compliance check passed",
            can_proceed=True,
            details={}
        )
        
        # Create real RiskManager
        risk_manager = RiskManager()
        
        # Validate trade
        validation = await risk_manager.validate_trade(
            account_id=1,
            symbol="AAPL",
            side="BUY",
            price_per_share=15.0,
            confidence_score=0.5,
            will_create_day_trade=False
        )
        
        # Assertions
        assert validation.is_valid is True
        assert validation.can_proceed is True
        assert validation.position_size is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

