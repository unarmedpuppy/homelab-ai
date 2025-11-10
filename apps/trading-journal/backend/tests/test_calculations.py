"""
Unit tests for P&L calculation utilities.

Tests verify that all calculations match the formulas from STARTUP_GUIDE.md.
"""

import pytest
from decimal import Decimal

from app.utils.calculations import (
    calculate_net_pnl,
    calculate_roi,
    calculate_r_multiple,
)


class TestCalculateNetPnl:
    """Tests for calculate_net_pnl function."""
    
    def test_long_stock_profitable(self):
        """Test LONG stock trade with profit."""
        result = calculate_net_pnl(
            entry_price=Decimal("100.00"),
            exit_price=Decimal("110.00"),
            quantity=Decimal("10"),
            entry_commission=Decimal("1.00"),
            exit_commission=Decimal("1.00"),
            trade_type="STOCK",
            side="LONG"
        )
        # (110 - 100) * 10 - 1 - 1 = 100 - 2 = 98
        assert result == Decimal("98.00")
    
    def test_long_stock_loss(self):
        """Test LONG stock trade with loss."""
        result = calculate_net_pnl(
            entry_price=Decimal("100.00"),
            exit_price=Decimal("90.00"),
            quantity=Decimal("10"),
            entry_commission=Decimal("1.00"),
            exit_commission=Decimal("1.00"),
            trade_type="STOCK",
            side="LONG"
        )
        # (90 - 100) * 10 - 1 - 1 = -100 - 2 = -102
        assert result == Decimal("-102.00")
    
    def test_short_stock_profitable(self):
        """Test SHORT stock trade with profit."""
        result = calculate_net_pnl(
            entry_price=Decimal("100.00"),
            exit_price=Decimal("90.00"),
            quantity=Decimal("10"),
            entry_commission=Decimal("1.00"),
            exit_commission=Decimal("1.00"),
            trade_type="STOCK",
            side="SHORT"
        )
        # (100 - 90) * 10 - 1 - 1 = 100 - 2 = 98
        assert result == Decimal("98.00")
    
    def test_short_stock_loss(self):
        """Test SHORT stock trade with loss."""
        result = calculate_net_pnl(
            entry_price=Decimal("100.00"),
            exit_price=Decimal("110.00"),
            quantity=Decimal("10"),
            entry_commission=Decimal("1.00"),
            exit_commission=Decimal("1.00"),
            trade_type="STOCK",
            side="SHORT"
        )
        # (100 - 110) * 10 - 1 - 1 = -100 - 2 = -102
        assert result == Decimal("-102.00")
    
    def test_long_option_profitable(self):
        """Test LONG option trade with profit."""
        result = calculate_net_pnl(
            entry_price=Decimal("5.00"),
            exit_price=Decimal("7.50"),
            quantity=Decimal("2"),  # 2 contracts
            entry_commission=Decimal("2.00"),
            exit_commission=Decimal("2.00"),
            trade_type="OPTION",
            side="LONG"
        )
        # (7.50 - 5.00) * 2 * 100 - 2 - 2 = 500 - 4 = 496
        assert result == Decimal("496.00")
    
    def test_long_option_loss(self):
        """Test LONG option trade with loss."""
        result = calculate_net_pnl(
            entry_price=Decimal("5.00"),
            exit_price=Decimal("3.00"),
            quantity=Decimal("2"),
            entry_commission=Decimal("2.00"),
            exit_commission=Decimal("2.00"),
            trade_type="OPTION",
            side="LONG"
        )
        # (3.00 - 5.00) * 2 * 100 - 2 - 2 = -400 - 4 = -404
        assert result == Decimal("-404.00")
    
    def test_crypto_spot(self):
        """Test crypto spot trade."""
        result = calculate_net_pnl(
            entry_price=Decimal("50000.00"),
            exit_price=Decimal("51000.00"),
            quantity=Decimal("0.5"),
            entry_commission=Decimal("25.00"),
            exit_commission=Decimal("25.50"),
            trade_type="CRYPTO_SPOT",
            side="LONG"
        )
        # (51000 - 50000) * 0.5 - 25 - 25.50 = 500 - 50.50 = 449.50
        assert result == Decimal("449.50")
    
    def test_no_commissions(self):
        """Test trade with no commissions."""
        result = calculate_net_pnl(
            entry_price=Decimal("100.00"),
            exit_price=Decimal("110.00"),
            quantity=Decimal("10"),
            entry_commission=Decimal("0"),
            exit_commission=Decimal("0"),
            trade_type="STOCK",
            side="LONG"
        )
        # (110 - 100) * 10 = 100
        assert result == Decimal("100.00")
    
    def test_partial_fill_handling(self):
        """Test that quantity parameter handles partial fills correctly."""
        # Partial fill: entered 10 shares, exited 5 shares
        result = calculate_net_pnl(
            entry_price=Decimal("100.00"),
            exit_price=Decimal("110.00"),
            quantity=Decimal("5"),  # Partial fill quantity
            entry_commission=Decimal("1.00"),
            exit_commission=Decimal("0.50"),
            trade_type="STOCK",
            side="LONG"
        )
        # (110 - 100) * 5 - 1 - 0.50 = 50 - 1.50 = 48.50
        assert result == Decimal("48.50")


class TestCalculateRoi:
    """Tests for calculate_roi function."""
    
    def test_profitable_stock(self):
        """Test ROI calculation for profitable stock trade."""
        net_pnl = Decimal("98.00")
        result = calculate_roi(
            entry_price=Decimal("100.00"),
            quantity=Decimal("10"),
            entry_commission=Decimal("1.00"),
            net_pnl=net_pnl,
            trade_type="STOCK"
        )
        # Total cost = (100 * 10) + 1 = 1001
        # ROI = (98 / 1001) * 100 = 9.79%
        expected = (net_pnl / Decimal("1001.00")) * Decimal("100")
        assert abs(result - expected) < Decimal("0.01")
    
    def test_losing_stock(self):
        """Test ROI calculation for losing stock trade."""
        net_pnl = Decimal("-102.00")
        result = calculate_roi(
            entry_price=Decimal("100.00"),
            quantity=Decimal("10"),
            entry_commission=Decimal("1.00"),
            net_pnl=net_pnl,
            trade_type="STOCK"
        )
        # Total cost = (100 * 10) + 1 = 1001
        # ROI = (-102 / 1001) * 100 = -10.19%
        expected = (net_pnl / Decimal("1001.00")) * Decimal("100")
        assert abs(result - expected) < Decimal("0.01")
    
    def test_profitable_option(self):
        """Test ROI calculation for profitable option trade."""
        net_pnl = Decimal("496.00")
        result = calculate_roi(
            entry_price=Decimal("5.00"),
            quantity=Decimal("2"),
            entry_commission=Decimal("2.00"),
            net_pnl=net_pnl,
            trade_type="OPTION"
        )
        # Total cost = (5 * 2 * 100) + 2 = 1002
        # ROI = (496 / 1002) * 100 = 49.50%
        expected = (net_pnl / Decimal("1002.00")) * Decimal("100")
        assert abs(result - expected) < Decimal("0.01")
    
    def test_zero_cost(self):
        """Test ROI calculation with zero cost (edge case)."""
        result = calculate_roi(
            entry_price=Decimal("0"),
            quantity=Decimal("0"),
            entry_commission=Decimal("0"),
            net_pnl=Decimal("100.00"),
            trade_type="STOCK"
        )
        assert result == Decimal("0")
    
    def test_zero_pnl(self):
        """Test ROI calculation with zero P&L."""
        result = calculate_roi(
            entry_price=Decimal("100.00"),
            quantity=Decimal("10"),
            entry_commission=Decimal("1.00"),
            net_pnl=Decimal("0"),
            trade_type="STOCK"
        )
        assert result == Decimal("0")


class TestCalculateRMultiple:
    """Tests for calculate_r_multiple function."""
    
    def test_long_without_stop_loss(self):
        """Test R-multiple for LONG trade without stop loss."""
        # Uses entry price as risk
        result = calculate_r_multiple(
            entry_price=Decimal("100.00"),
            quantity=Decimal("10"),
            net_pnl=Decimal("50.00"),
            trade_type="STOCK",
            side="LONG",
            stop_loss=None
        )
        # Risk = 100 * 10 = 1000
        # R-multiple = 50 / 1000 = 0.05
        assert result == Decimal("0.05")
    
    def test_long_with_stop_loss(self):
        """Test R-multiple for LONG trade with stop loss."""
        result = calculate_r_multiple(
            entry_price=Decimal("100.00"),
            quantity=Decimal("10"),
            net_pnl=Decimal("50.00"),
            trade_type="STOCK",
            side="LONG",
            stop_loss=Decimal("95.00")
        )
        # Risk per unit = 100 - 95 = 5
        # Risk = 5 * 10 = 50
        # R-multiple = 50 / 50 = 1.0
        assert result == Decimal("1.0")
    
    def test_short_with_stop_loss(self):
        """Test R-multiple for SHORT trade with stop loss."""
        result = calculate_r_multiple(
            entry_price=Decimal("100.00"),
            quantity=Decimal("10"),
            net_pnl=Decimal("50.00"),
            trade_type="STOCK",
            side="SHORT",
            stop_loss=Decimal("105.00")
        )
        # Risk per unit = 105 - 100 = 5
        # Risk = 5 * 10 = 50
        # R-multiple = 50 / 50 = 1.0
        assert result == Decimal("1.0")
    
    def test_option_with_stop_loss(self):
        """Test R-multiple for option trade with stop loss."""
        result = calculate_r_multiple(
            entry_price=Decimal("5.00"),
            quantity=Decimal("2"),
            net_pnl=Decimal("200.00"),
            trade_type="OPTION",
            side="LONG",
            stop_loss=Decimal("4.00")
        )
        # Risk per unit = 5 - 4 = 1
        # Risk = 1 * 2 * 100 = 200
        # R-multiple = 200 / 200 = 1.0
        assert result == Decimal("1.0")
    
    def test_negative_r_multiple(self):
        """Test R-multiple for losing trade."""
        result = calculate_r_multiple(
            entry_price=Decimal("100.00"),
            quantity=Decimal("10"),
            net_pnl=Decimal("-50.00"),
            trade_type="STOCK",
            side="LONG",
            stop_loss=None
        )
        # Risk = 100 * 10 = 1000
        # R-multiple = -50 / 1000 = -0.05
        assert result == Decimal("-0.05")
    
    def test_zero_risk(self):
        """Test R-multiple with zero risk (edge case)."""
        result = calculate_r_multiple(
            entry_price=Decimal("0"),
            quantity=Decimal("0"),
            net_pnl=Decimal("100.00"),
            trade_type="STOCK",
            side="LONG",
            stop_loss=None
        )
        assert result == Decimal("0")
    
    def test_stop_loss_above_entry_long(self):
        """Test R-multiple when stop loss is above entry (for LONG, this is unusual but handled)."""
        result = calculate_r_multiple(
            entry_price=Decimal("100.00"),
            quantity=Decimal("10"),
            net_pnl=Decimal("50.00"),
            trade_type="STOCK",
            side="LONG",
            stop_loss=Decimal("105.00")
        )
        # Risk per unit = |100 - 105| = 5
        # Risk = 5 * 10 = 50
        # R-multiple = 50 / 50 = 1.0
        assert result == Decimal("1.0")

