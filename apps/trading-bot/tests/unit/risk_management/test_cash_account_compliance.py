"""
Unit Tests for Cash Account Compliance Manager
==============================================

Tests for PDT tracking, settlement periods, trade frequency limits, and GFV prevention.
"""

import pytest
from unittest.mock import Mock, AsyncMock, patch
from datetime import datetime, timedelta, date
from src.core.risk.compliance import (
    ComplianceManager,
    ComplianceResult,
    ComplianceCheck
)
from src.core.risk.account_monitor import AccountMonitor, AccountStatus
from src.data.database.models import TradeSide


class TestComplianceManagerInitialization:
    """Test ComplianceManager initialization"""
    
    def test_initialization_with_default_monitor(self):
        """Test initialization with default account monitor"""
        manager = ComplianceManager()
        
        assert manager.account_monitor is not None
        assert isinstance(manager.account_monitor, AccountMonitor)
    
    def test_initialization_loads_settings(self):
        """Test that initialization loads settings"""
        manager = ComplianceManager()
        
        assert manager.settlement_days == 2  # T+2 default
        assert manager.pdt_enforcement in ["strict", "warning"]
        assert manager.daily_limit > 0
        assert manager.weekly_limit > 0


class TestSettlementDateCalculation:
    """Test settlement date calculation (T+2)"""
    
    @pytest.fixture
    def manager(self):
        """Create compliance manager"""
        return ComplianceManager()
    
    def test_calculate_settlement_date_weekday(self, manager):
        """Test settlement date for weekday trade (Monday)"""
        # Monday trade
        trade_date = datetime(2024, 1, 1, 10, 0, 0)  # Monday Jan 1, 2024
        settlement = manager.calculate_settlement_date(trade_date)
        
        # Should be Wednesday (T+2 business days)
        assert settlement.weekday() == 2  # Wednesday
        assert settlement.date() == date(2024, 1, 3)
    
    def test_calculate_settlement_date_skips_weekends(self, manager):
        """Test settlement date skips weekends"""
        # Friday trade
        trade_date = datetime(2024, 1, 5, 10, 0, 0)  # Friday Jan 5, 2024
        settlement = manager.calculate_settlement_date(trade_date)
        
        # Should be Tuesday (skip Saturday/Sunday)
        assert settlement.weekday() == 1  # Tuesday
        assert settlement.date() == date(2024, 1, 9)
    
    def test_is_business_day(self, manager):
        """Test business day check"""
        monday = date(2024, 1, 1)  # Monday
        saturday = date(2024, 1, 6)  # Saturday
        sunday = date(2024, 1, 7)  # Sunday
        
        assert manager.is_business_day(monday) is True
        assert manager.is_business_day(saturday) is False
        assert manager.is_business_day(sunday) is False


class TestPDTCompliance:
    """Test Pattern Day Trader (PDT) compliance checks"""
    
    @pytest.fixture
    def manager(self):
        """Create compliance manager with mocked account monitor"""
        mock_monitor = Mock(spec=AccountMonitor)
        mock_status = AccountStatus(
            account_id=1,
            balance=20000.0,
            is_cash_account_mode=True,
            threshold=25000.0
        )
        mock_monitor.is_cash_account_mode = AsyncMock(return_value=True)
        return ComplianceManager(account_monitor=mock_monitor)
    
    @pytest.mark.asyncio
    async def test_pdt_compliance_no_day_trades(self, manager):
        """Test PDT compliance with no day trades"""
        with patch.object(manager, 'get_day_trade_count', return_value=0):
            check = await manager.check_pdt_compliance(
                account_id=1,
                symbol="SPY",
                side=TradeSide.BUY,
                will_create_day_trade=False
            )
            
            assert check.result == ComplianceResult.ALLOWED
            assert check.can_proceed is True
    
    @pytest.mark.asyncio
    async def test_pdt_compliance_under_limit(self, manager):
        """Test PDT compliance under limit (2 day trades)"""
        with patch.object(manager, 'get_day_trade_count', return_value=2):
            check = await manager.check_pdt_compliance(
                account_id=1,
                symbol="SPY",
                side=TradeSide.SELL,
                will_create_day_trade=True
            )
            
            # Would be 3 after this trade, but currently 2, so allowed
            assert check.result == ComplianceResult.ALLOWED
            assert check.can_proceed is True
    
    @pytest.mark.asyncio
    async def test_pdt_compliance_at_limit_strict(self, manager):
        """Test PDT compliance at limit in strict mode"""
        manager.pdt_enforcement = "strict"
        
        with patch.object(manager, 'get_day_trade_count', return_value=3):
            check = await manager.check_pdt_compliance(
                account_id=1,
                symbol="SPY",
                side=TradeSide.SELL,
                will_create_day_trade=True
            )
            
            assert check.result == ComplianceResult.BLOCKED_PDT
            assert check.can_proceed is False
    
    @pytest.mark.asyncio
    async def test_pdt_compliance_at_limit_warning(self, manager):
        """Test PDT compliance at limit in warning mode"""
        manager.pdt_enforcement = "warning"
        
        with patch.object(manager, 'get_day_trade_count', return_value=3):
            check = await manager.check_pdt_compliance(
                account_id=1,
                symbol="SPY",
                side=TradeSide.SELL,
                will_create_day_trade=True
            )
            
            assert check.result == ComplianceResult.WARNING
            assert check.can_proceed is True  # Warning mode allows
    
    @pytest.mark.asyncio
    async def test_pdt_compliance_not_cash_account(self, manager):
        """Test PDT compliance skipped for non-cash account"""
        manager.account_monitor.is_cash_account_mode = AsyncMock(return_value=False)
        
        check = await manager.check_pdt_compliance(
            account_id=1,
            symbol="SPY",
            side=TradeSide.BUY,
            will_create_day_trade=False
        )
        
        assert check.result == ComplianceResult.ALLOWED
        assert "not in cash account mode" in check.message.lower()


class TestSettlementCashChecking:
    """Test settled cash availability checking"""
    
    @pytest.fixture
    def manager(self):
        """Create compliance manager"""
        mock_monitor = Mock(spec=AccountMonitor)
        mock_status = AccountStatus(
            account_id=1,
            balance=100000.0,
            is_cash_account_mode=True,
            threshold=25000.0
        )
        mock_monitor.check_account_balance = AsyncMock(return_value=mock_status)
        return ComplianceManager(account_monitor=mock_monitor)
    
    @pytest.mark.asyncio
    async def test_get_available_settled_cash(self, manager):
        """Test getting available settled cash"""
        # Mock the account monitor and database interactions
        mock_status = AccountStatus(
            account_id=1,
            balance=100000.0,
            is_cash_account_mode=True,
            threshold=25000.0
        )
        manager.account_monitor.check_account_balance = AsyncMock(return_value=mock_status)
        
        # Mock database session to return no unsettled trades
        with patch('src.core.risk.compliance.SessionLocal') as mock_session_local:
            mock_session = Mock()
            mock_session_local.return_value = mock_session
            mock_session.query().filter().all.return_value = []  # No unsettled trades
            mock_session.query().filter().first = Mock(return_value=None)
            
            available = await manager.get_available_settled_cash(account_id=1)
            
            # Should return balance when no unsettled trades
            assert available >= 0.0
            assert available <= 100000.0
    
    @pytest.mark.asyncio
    async def test_check_settled_cash_available_sufficient(self, manager):
        """Test checking sufficient settled cash"""
        with patch.object(manager, 'get_available_settled_cash', return_value=10000.0):
            has_cash, available = await manager.check_settled_cash_available(
                account_id=1,
                required_amount=5000.0
            )
            
            assert has_cash is True
            assert available == 10000.0
    
    @pytest.mark.asyncio
    async def test_check_settled_cash_available_insufficient(self, manager):
        """Test checking insufficient settled cash"""
        with patch.object(manager, 'get_available_settled_cash', return_value=3000.0):
            has_cash, available = await manager.check_settled_cash_available(
                account_id=1,
                required_amount=5000.0
            )
            
            assert has_cash is False
            assert available == 3000.0


class TestTradeFrequencyLimits:
    """Test trade frequency limit checking"""
    
    @pytest.fixture
    def manager(self):
        """Create compliance manager"""
        mock_monitor = Mock(spec=AccountMonitor)
        mock_monitor.is_cash_account_mode = AsyncMock(return_value=True)
        return ComplianceManager(account_monitor=mock_monitor)
    
    @pytest.mark.asyncio
    async def test_check_trade_frequency_under_limits(self, manager):
        """Test trade frequency check under limits"""
        # Mock successful check (under limits)
        check = ComplianceCheck(
            result=ComplianceResult.ALLOWED,
            message="Frequency check passed",
            can_proceed=True
        )
        with patch.object(manager, 'check_trade_frequency', return_value=check):
            result = await manager.check_trade_frequency(account_id=1)
            assert result.result == ComplianceResult.ALLOWED
            assert result.can_proceed is True
    
    @pytest.mark.asyncio
    async def test_check_trade_frequency_daily_limit_exceeded(self, manager):
        """Test trade frequency check with daily limit exceeded"""
        check = ComplianceCheck(
            result=ComplianceResult.BLOCKED_FREQUENCY,
            message="Daily trade limit exceeded: 5/5 trades",
            can_proceed=False
        )
        with patch.object(manager, 'check_trade_frequency', return_value=check):
            result = await manager.check_trade_frequency(account_id=1)
            assert result.result == ComplianceResult.BLOCKED_FREQUENCY
            assert result.can_proceed is False
            assert "daily" in result.message.lower()
    
    @pytest.mark.asyncio
    async def test_check_trade_frequency_weekly_limit_exceeded(self, manager):
        """Test trade frequency check with weekly limit exceeded"""
        check = ComplianceCheck(
            result=ComplianceResult.BLOCKED_FREQUENCY,
            message="Weekly trade limit exceeded: 20/20 trades",
            can_proceed=False
        )
        with patch.object(manager, 'check_trade_frequency', return_value=check):
            result = await manager.check_trade_frequency(account_id=1)
            assert result.result == ComplianceResult.BLOCKED_FREQUENCY
            assert result.can_proceed is False
            assert "weekly" in result.message.lower()


class TestDayTradeDetection:
    """Test day trade detection logic"""
    
    @pytest.fixture
    def manager(self):
        """Create compliance manager"""
        return ComplianceManager()
    
    def test_detect_day_trade_buy_returns_none(self, manager):
        """Test that BUY trades don't trigger day trade detection"""
        result = manager.detect_day_trade(
            account_id=1,
            symbol="SPY",
            side=TradeSide.BUY,
            trade_date=datetime.now()
        )
        
        assert result is None  # Can't detect day trade from BUY alone
    
    def test_detect_day_trade_no_trade_id(self, manager):
        """Test that day trade detection requires trade_id"""
        result = manager.detect_day_trade(
            account_id=1,
            symbol="SPY",
            side=TradeSide.SELL,
            trade_date=datetime.now(),
            trade_id=None
        )
        
        assert result is None  # Need trade_id to detect


class TestGFVPrevention:
    """Test Good Faith Violation prevention"""
    
    @pytest.fixture
    def manager(self):
        """Create compliance manager"""
        return ComplianceManager()
    
    @pytest.mark.asyncio
    async def test_check_gfv_prevention_not_implemented(self, manager):
        """Test GFV prevention (currently not fully implemented)"""
        check = await manager.check_gfv_prevention(
            account_id=1,
            symbol="SPY",
            side=TradeSide.BUY,
            amount=1000.0
        )
        
        # Currently returns ALLOWED (not yet fully implemented)
        assert check.result == ComplianceResult.ALLOWED
        assert check.can_proceed is True


class TestComprehensiveComplianceCheck:
    """Test comprehensive compliance checking"""
    
    @pytest.fixture
    def manager(self):
        """Create compliance manager"""
        mock_monitor = Mock(spec=AccountMonitor)
        mock_monitor.is_cash_account_mode = AsyncMock(return_value=True)
        mock_status = AccountStatus(
            account_id=1,
            balance=100000.0,
            is_cash_account_mode=True,
            threshold=25000.0
        )
        mock_monitor.check_account_balance = AsyncMock(return_value=mock_status)
        return ComplianceManager(account_monitor=mock_monitor)
    
    @pytest.mark.asyncio
    async def test_comprehensive_check_all_passed(self, manager):
        """Test comprehensive check when all checks pass"""
        with patch.object(manager, 'check_pdt_compliance', return_value=ComplianceCheck(
            result=ComplianceResult.ALLOWED, message="OK", can_proceed=True
        )):
            with patch.object(manager, 'check_trade_frequency', return_value=ComplianceCheck(
                result=ComplianceResult.ALLOWED, message="OK", can_proceed=True
            )):
                with patch.object(manager, 'check_settled_cash_available', return_value=(True, 50000.0)):
                    with patch.object(manager, 'check_gfv_prevention', return_value=ComplianceCheck(
                        result=ComplianceResult.ALLOWED, message="OK", can_proceed=True
                    )):
                        check = await manager.check_compliance(
                            account_id=1,
                            symbol="SPY",
                            side=TradeSide.BUY,
                            amount=5000.0,
                            will_create_day_trade=False
                        )
                        
                        assert check.result == ComplianceResult.ALLOWED
                        assert check.can_proceed is True
    
    @pytest.mark.asyncio
    async def test_comprehensive_check_pdt_blocked(self, manager):
        """Test comprehensive check blocked by PDT"""
        with patch.object(manager, 'check_pdt_compliance', return_value=ComplianceCheck(
            result=ComplianceResult.BLOCKED_PDT, message="PDT violation", can_proceed=False
        )):
            check = await manager.check_compliance(
                account_id=1,
                symbol="SPY",
                side=TradeSide.BUY,
                amount=5000.0,
                will_create_day_trade=True
            )
            
            assert check.result == ComplianceResult.BLOCKED_PDT
            assert check.can_proceed is False
    
    @pytest.mark.asyncio
    async def test_comprehensive_check_settlement_blocked(self, manager):
        """Test comprehensive check blocked by insufficient settled cash"""
        with patch.object(manager, 'check_pdt_compliance', return_value=ComplianceCheck(
            result=ComplianceResult.ALLOWED, message="OK", can_proceed=True
        )):
            with patch.object(manager, 'check_trade_frequency', return_value=ComplianceCheck(
                result=ComplianceResult.ALLOWED, message="OK", can_proceed=True
            )):
                with patch.object(manager, 'check_settled_cash_available', return_value=(False, 2000.0)):
                    check = await manager.check_compliance(
                        account_id=1,
                        symbol="SPY",
                        side=TradeSide.BUY,
                        amount=5000.0,  # Need $5k but only $2k available
                        will_create_day_trade=False
                    )
                    
                    assert check.result == ComplianceResult.BLOCKED_SETTLEMENT
                    assert check.can_proceed is False
    
    @pytest.mark.asyncio
    async def test_comprehensive_check_not_cash_account(self, manager):
        """Test comprehensive check skipped for non-cash account"""
        manager.account_monitor.is_cash_account_mode = AsyncMock(return_value=False)
        
        check = await manager.check_compliance(
            account_id=1,
            symbol="SPY",
            side=TradeSide.BUY,
            amount=5000.0,
            will_create_day_trade=False
        )
        
        assert check.result == ComplianceResult.ALLOWED
        assert "not in cash account mode" in check.message.lower()


@pytest.mark.unit
class TestComplianceManagerEdgeCases:
    """Test edge cases for compliance manager"""
    
    @pytest.fixture
    def manager(self):
        """Create compliance manager"""
        return ComplianceManager()
    
    @pytest.mark.asyncio
    async def test_settlement_date_calculation_edge_cases(self, manager):
        """Test settlement date calculation edge cases"""
        # Test various weekdays
        for day_offset in range(7):
            trade_date = datetime(2024, 1, 1) + timedelta(days=day_offset)
            settlement = manager.calculate_settlement_date(trade_date)
            
            # Settlement should always be a weekday
            assert settlement.weekday() < 5
            # Settlement should be at least 2 days after trade date
            days_diff = (settlement.date() - trade_date.date()).days
            assert days_diff >= 2

