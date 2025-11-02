"""
Unit Tests for Position Sizing Manager
=======================================

Tests for confidence-based position sizing and risk management.
"""

import pytest
from unittest.mock import Mock, AsyncMock, patch
from src.core.risk.position_sizing import (
    PositionSizingManager,
    PositionSizeResult,
    ConfidenceLevel
)
from src.core.risk.account_monitor import AccountMonitor, AccountStatus


class TestPositionSizingManagerInitialization:
    """Test PositionSizingManager initialization"""
    
    def test_initialization_with_default_account_monitor(self):
        """Test initialization with default account monitor"""
        manager = PositionSizingManager()
        
        assert manager.account_monitor is not None
        assert isinstance(manager.account_monitor, AccountMonitor)
    
    def test_initialization_with_custom_account_monitor(self):
        """Test initialization with custom account monitor"""
        mock_monitor = Mock(spec=AccountMonitor)
        manager = PositionSizingManager(account_monitor=mock_monitor)
        
        assert manager.account_monitor == mock_monitor
    
    def test_initialization_loads_settings(self):
        """Test that initialization loads settings from config"""
        manager = PositionSizingManager()
        
        # Settings should be loaded
        assert manager.low_confidence_pct is not None
        assert manager.medium_confidence_pct is not None
        assert manager.high_confidence_pct is not None
        assert manager.max_position_size_pct is not None
        
        # Verify defaults match settings (from RiskManagementSettings)
        # These may be configurable, so just verify they're loaded
        assert manager.low_confidence_pct > 0
        assert manager.medium_confidence_pct > manager.low_confidence_pct
        assert manager.high_confidence_pct > manager.medium_confidence_pct
        assert manager.max_position_size_pct > 0


class TestConfidenceLevelDetermination:
    """Test confidence level determination"""
    
    @pytest.fixture
    def manager(self):
        """Create position sizing manager"""
        return PositionSizingManager()
    
    def test_get_confidence_level_high(self, manager):
        """Test high confidence level (>= 0.7)"""
        assert manager._get_confidence_level(0.7) == ConfidenceLevel.HIGH
        assert manager._get_confidence_level(0.8) == ConfidenceLevel.HIGH
        assert manager._get_confidence_level(1.0) == ConfidenceLevel.HIGH
    
    def test_get_confidence_level_medium(self, manager):
        """Test medium confidence level (0.4 - 0.69)"""
        assert manager._get_confidence_level(0.4) == ConfidenceLevel.MEDIUM
        assert manager._get_confidence_level(0.5) == ConfidenceLevel.MEDIUM
        assert manager._get_confidence_level(0.69) == ConfidenceLevel.MEDIUM
    
    def test_get_confidence_level_low(self, manager):
        """Test low confidence level (< 0.4)"""
        assert manager._get_confidence_level(0.0) == ConfidenceLevel.LOW
        assert manager._get_confidence_level(0.3) == ConfidenceLevel.LOW
        assert manager._get_confidence_level(0.39) == ConfidenceLevel.LOW
    
    def test_get_base_position_percentage_high(self, manager):
        """Test base position percentage for high confidence"""
        pct = manager._get_base_position_percentage(ConfidenceLevel.HIGH)
        assert pct == manager.high_confidence_pct
    
    def test_get_base_position_percentage_medium(self, manager):
        """Test base position percentage for medium confidence"""
        pct = manager._get_base_position_percentage(ConfidenceLevel.MEDIUM)
        assert pct == manager.medium_confidence_pct
    
    def test_get_base_position_percentage_low(self, manager):
        """Test base position percentage for low confidence"""
        pct = manager._get_base_position_percentage(ConfidenceLevel.LOW)
        assert pct == manager.low_confidence_pct


class TestPositionSizeCalculation:
    """Test position size calculation"""
    
    @pytest.fixture
    def manager(self):
        """Create position sizing manager with mocked account monitor"""
        mock_monitor = Mock(spec=AccountMonitor)
        mock_status = AccountStatus(
            account_id=1,
            balance=100000.0,
            is_cash_account_mode=False,
            threshold=25000.0
        )
        mock_monitor.check_account_balance = AsyncMock(return_value=mock_status)
        return PositionSizingManager(account_monitor=mock_monitor)
    
    @pytest.mark.asyncio
    async def test_calculate_position_size_low_confidence(self, manager):
        """Test position sizing for low confidence"""
        result = await manager.calculate_position_size(
            account_id=1,
            confidence_score=0.3,  # Low confidence
            price_per_share=100.0
        )
        
        assert result.confidence_level == ConfidenceLevel.LOW
        assert result.size_shares > 0
        # Should be approximately 1% of account (1000 shares * $100 = $10,000)
        assert result.size_usd <= 100000.0 * 0.01 + 100.0  # Allow rounding
        assert result.base_percentage == 0.01
    
    @pytest.mark.asyncio
    async def test_calculate_position_size_medium_confidence(self, manager):
        """Test position sizing for medium confidence"""
        result = await manager.calculate_position_size(
            account_id=1,
            confidence_score=0.5,  # Medium confidence
            price_per_share=100.0
        )
        
        assert result.confidence_level == ConfidenceLevel.MEDIUM
        assert result.size_shares > 0
        # Should be approximately 2.5% of account (2500 shares * $100 = $25,000)
        assert result.base_percentage == 0.025
    
    @pytest.mark.asyncio
    async def test_calculate_position_size_high_confidence(self, manager):
        """Test position sizing for high confidence"""
        result = await manager.calculate_position_size(
            account_id=1,
            confidence_score=0.8,  # High confidence
            price_per_share=100.0
        )
        
        assert result.confidence_level == ConfidenceLevel.HIGH
        assert result.size_shares > 0
        # Should be approximately 4% of account (4000 shares * $100 = $40,000)
        assert result.base_percentage == 0.04
    
    @pytest.mark.asyncio
    async def test_calculate_position_size_respects_max_limit(self, manager):
        """Test that position size respects maximum cap"""
        result = await manager.calculate_position_size(
            account_id=1,
            confidence_score=0.9,  # High confidence
            price_per_share=100.0
        )
        
        # Max is 10% by default, but high confidence is 4%, so should not hit max
        assert result.max_size_hit is False
        
        # But if we manually set a lower max, it should cap
        manager.max_position_size_pct = 0.02  # 2% max
        result2 = await manager.calculate_position_size(
            account_id=1,
            confidence_score=0.9,  # Would normally be 4%
            price_per_share=100.0
        )
        
        assert result2.max_size_hit is True
        assert result2.actual_percentage <= 0.02
    
    @pytest.mark.asyncio
    async def test_calculate_position_size_minimum_shares(self, manager):
        """Test minimum shares requirement"""
        result = await manager.calculate_position_size(
            account_id=1,
            confidence_score=0.3,
            price_per_share=1000000.0,  # Very expensive stock
            min_shares=1
        )
        
        # Should return 0 shares if minimum can't be met
        # With $100k account and 1% ($1k) position, can't afford $1M share
        assert result.size_shares == 0
        assert result.size_usd == 0.0
    
    @pytest.mark.asyncio
    async def test_calculate_position_size_invalid_confidence(self, manager):
        """Test validation of confidence score"""
        with pytest.raises(ValueError, match="Confidence score must be between"):
            await manager.calculate_position_size(
                account_id=1,
                confidence_score=1.5,  # Invalid: > 1.0
                price_per_share=100.0
            )
        
        with pytest.raises(ValueError, match="Confidence score must be between"):
            await manager.calculate_position_size(
                account_id=1,
                confidence_score=-0.1,  # Invalid: < 0.0
                price_per_share=100.0
            )
    
    @pytest.mark.asyncio
    async def test_calculate_position_size_invalid_price(self, manager):
        """Test validation of price per share"""
        with pytest.raises(ValueError, match="Price per share must be positive"):
            await manager.calculate_position_size(
                account_id=1,
                confidence_score=0.5,
                price_per_share=0.0  # Invalid
            )
        
        with pytest.raises(ValueError, match="Price per share must be positive"):
            await manager.calculate_position_size(
                account_id=1,
                confidence_score=0.5,
                price_per_share=-10.0  # Invalid
            )
    
    @pytest.mark.asyncio
    async def test_calculate_position_size_zero_balance(self, manager):
        """Test position sizing with zero account balance"""
        mock_monitor = Mock(spec=AccountMonitor)
        mock_status = AccountStatus(
            account_id=1,
            balance=0.0,
            is_cash_account_mode=False,
            threshold=25000.0
        )
        mock_monitor.check_account_balance = AsyncMock(return_value=mock_status)
        manager.account_monitor = mock_monitor
        
        result = await manager.calculate_position_size(
            account_id=1,
            confidence_score=0.8,
            price_per_share=100.0
        )
        
        assert result.size_usd == 0.0
        assert result.size_shares == 0
        assert result.max_size_hit is True


class TestPositionSizeWithSettlement:
    """Test position sizing with settlement constraints"""
    
    @pytest.fixture
    def manager(self):
        """Create position sizing manager"""
        mock_monitor = Mock(spec=AccountMonitor)
        mock_status = AccountStatus(
            account_id=1,
            balance=100000.0,
            is_cash_account_mode=True,
            threshold=25000.0
        )
        mock_monitor.check_account_balance = AsyncMock(return_value=mock_status)
        return PositionSizingManager(account_monitor=mock_monitor)
    
    @pytest.mark.asyncio
    async def test_calculate_with_settlement_limited_by_cash(self, manager):
        """Test position size limited by settled cash"""
        # Account has $100k, but only $5k settled cash
        result = await manager.calculate_position_size_with_settlement(
            account_id=1,
            confidence_score=0.8,  # Would normally be 4% = $4k
            price_per_share=100.0,
            available_settled_cash=5000.0
        )
        
        # Should be limited by settled cash
        assert result.size_usd <= 5000.0
        assert result.size_shares <= 50  # $5k / $100 = 50 shares
    
    @pytest.mark.asyncio
    async def test_calculate_with_settlement_not_limited(self, manager):
        """Test position size when settled cash is sufficient"""
        # Account has $100k, settled cash is $50k
        result = await manager.calculate_position_size_with_settlement(
            account_id=1,
            confidence_score=0.8,  # Would be 4% = $4k
            price_per_share=100.0,
            available_settled_cash=50000.0
        )
        
        # Should not be limited by settled cash (desired size is less)
        assert result.size_usd <= 50000.0  # But should be around $4k (4% of $100k)
        assert result.size_shares > 0


class TestSynchronousPositionSizeCalculation:
    """Test synchronous position size calculation (for testing)"""
    
    @pytest.fixture
    def manager(self):
        """Create position sizing manager"""
        return PositionSizingManager()
    
    def test_get_position_size_for_confidence_low(self, manager):
        """Test synchronous calculation for low confidence"""
        size_usd, size_shares = manager.get_position_size_for_confidence(
            account_balance=100000.0,
            confidence_level=ConfidenceLevel.LOW,
            price_per_share=100.0
        )
        
        # Should be approximately 1% = $1k = 10 shares
        # Account for rounding (size_usd is recalculated from shares * price)
        assert size_shares >= 9  # At least 9 shares (rounding)
        assert size_shares <= 10
        # USD should be shares * price
        assert abs(size_usd - (size_shares * 100.0)) < 0.01
    
    def test_get_position_size_for_confidence_respects_max(self, manager):
        """Test synchronous calculation respects max cap"""
        # Set low max to force capping
        manager.max_position_size_pct = 0.02  # 2% max
        
        size_usd, size_shares = manager.get_position_size_for_confidence(
            account_balance=100000.0,
            confidence_level=ConfidenceLevel.HIGH,  # Would normally be 4%
            price_per_share=100.0
        )
        
        # Should be capped at 2% = $2k = 20 shares
        assert size_usd <= 2000.0
        assert size_shares <= 20


@pytest.mark.unit
class TestPositionSizingEdgeCases:
    """Test edge cases for position sizing"""
    
    @pytest.fixture
    def manager(self):
        """Create position sizing manager"""
        mock_monitor = Mock(spec=AccountMonitor)
        mock_status = AccountStatus(
            account_id=1,
            balance=100000.0,
            is_cash_account_mode=False,
            threshold=25000.0
        )
        mock_monitor.check_account_balance = AsyncMock(return_value=mock_status)
        return PositionSizingManager(account_monitor=mock_monitor)
    
    @pytest.mark.asyncio
    async def test_position_size_rounding_down(self, manager):
        """Test that shares are rounded down (not up)"""
        result = await manager.calculate_position_size(
            account_id=1,
            confidence_score=0.5,  # 2.5% = $2,500
            price_per_share=33.33  # Would give ~75.01 shares, should round to 75
        )
        
        # Size should be shares * price, which is <= desired amount
        calculated_usd = result.size_shares * 33.33
        assert calculated_usd <= 2500.0
        assert result.size_usd == calculated_usd  # Should match exactly
    
    @pytest.mark.asyncio
    async def test_position_size_boundary_confidence_levels(self, manager):
        """Test boundary values for confidence levels"""
        # Test exactly at thresholds
        result_07 = await manager.calculate_position_size(
            account_id=1,
            confidence_score=0.7,  # Exactly at high threshold
            price_per_share=100.0
        )
        assert result_07.confidence_level == ConfidenceLevel.HIGH
        
        result_04 = await manager.calculate_position_size(
            account_id=1,
            confidence_score=0.4,  # Exactly at medium threshold
            price_per_share=100.0
        )
        assert result_04.confidence_level == ConfidenceLevel.MEDIUM
        
        result_039 = await manager.calculate_position_size(
            account_id=1,
            confidence_score=0.39,  # Just below medium threshold
            price_per_share=100.0
        )
        assert result_039.confidence_level == ConfidenceLevel.LOW

