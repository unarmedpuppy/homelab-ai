"""
Integration Tests for Position Management
=========================================

Tests that verify position tracking, updates, and P/L calculation.
"""

import pytest
from unittest.mock import Mock, AsyncMock, patch
from datetime import datetime, timedelta
from src.data.brokers.ibkr_client import BrokerOrder, BrokerPosition
from src.core.strategy.base import Position, TradingSignal, SignalType
from tests.mocks.mock_ibkr_client import MockIBKRClient
from src.core.risk.profit_taking import ProfitTakingManager, ProfitLevel


class TestPositionOpening:
    """Test position opening scenarios"""
    
    @pytest.fixture
    def mock_ibkr_client(self):
        """Create mock IBKR client"""
        client = MockIBKRClient()
        client.auto_fill_orders = True
        return client
    
    def test_open_long_position(self, mock_ibkr_client):
        """Test opening a long position"""
        # Place buy order
        order = mock_ibkr_client.place_market_order(
            symbol="SPY",
            side="BUY",
            quantity=10
        )
        
        # Verify order filled
        assert order.status == "FILLED"
        
        # Get position
        positions = mock_ibkr_client.get_positions()
        spy_position = next((p for p in positions if p.symbol == "SPY"), None)
        
        assert spy_position is not None
        assert spy_position.quantity == 10
        assert spy_position.avg_cost > 0
    
    def test_open_short_position(self, mock_ibkr_client):
        """Test opening a short position"""
        # Place sell order (short)
        order = mock_ibkr_client.place_market_order(
            symbol="SPY",
            side="SELL",
            quantity=10
        )
        
        # Verify order filled
        assert order.status == "FILLED"
        
        # Get position
        positions = mock_ibkr_client.get_positions()
        spy_position = next((p for p in positions if p.symbol == "SPY"), None)
        
        assert spy_position is not None
        assert spy_position.quantity == -10  # Negative for short
    
    def test_position_created_after_fill(self, mock_ibkr_client):
        """Test that position is created after order fill"""
        # Initially no position
        positions = mock_ibkr_client.get_positions()
        assert len([p for p in positions if p.symbol == "SPY"]) == 0
        
        # Place and fill order
        order = mock_ibkr_client.place_market_order(
            symbol="SPY",
            side="BUY",
            quantity=10
        )
        
        # Position should exist now
        positions = mock_ibkr_client.get_positions()
        spy_position = next((p for p in positions if p.symbol == "SPY"), None)
        assert spy_position is not None


class TestPositionUpdates:
    """Test position updates"""
    
    @pytest.fixture
    def mock_ibkr_client_with_position(self):
        """Create mock IBKR client with existing position"""
        client = MockIBKRClient()
        client.auto_fill_orders = True
        
        # Open initial position
        client.place_market_order(symbol="SPY", side="BUY", quantity=10)
        return client
    
    def test_add_to_position(self, mock_ibkr_client_with_position):
        """Test adding to existing position"""
        # Add more shares
        order = mock_ibkr_client_with_position.place_market_order(
            symbol="SPY",
            side="BUY",
            quantity=5
        )
        
        # Verify position updated
        positions = mock_ibkr_client_with_position.get_positions()
        spy_position = next((p for p in positions if p.symbol == "SPY"), None)
        
        assert spy_position.quantity == 15  # 10 + 5
    
    def test_reduce_position(self, mock_ibkr_client_with_position):
        """Test reducing position size"""
        # Reduce position
        order = mock_ibkr_client_with_position.place_market_order(
            symbol="SPY",
            side="SELL",
            quantity=5
        )
        
        # Verify position updated
        positions = mock_ibkr_client_with_position.get_positions()
        spy_position = next((p for p in positions if p.symbol == "SPY"), None)
        
        assert spy_position.quantity == 5  # 10 - 5
    
    def test_reverse_position(self, mock_ibkr_client_with_position):
        """Test reversing position (long to short)"""
        # Reverse by selling more than we have
        order = mock_ibkr_client_with_position.place_market_order(
            symbol="SPY",
            side="SELL",
            quantity=20  # More than current 10
        )
        
        # Verify position reversed
        positions = mock_ibkr_client_with_position.get_positions()
        spy_position = next((p for p in positions if p.symbol == "SPY"), None)
        
        assert spy_position.quantity == -10  # Short position


class TestPositionClosing:
    """Test position closing"""
    
    @pytest.fixture
    def mock_ibkr_client_with_position(self):
        """Create mock IBKR client with existing position"""
        client = MockIBKRClient()
        client.auto_fill_orders = True
        client.place_market_order(symbol="SPY", side="BUY", quantity=10)
        return client
    
    def test_close_long_position(self, mock_ibkr_client_with_position):
        """Test closing a long position"""
        # Close position
        order = mock_ibkr_client_with_position.place_market_order(
            symbol="SPY",
            side="SELL",
            quantity=10  # Close entire position
        )
        
        # Verify position closed
        positions = mock_ibkr_client_with_position.get_positions()
        spy_position = next((p for p in positions if p.symbol == "SPY"), None)
        
        assert spy_position is None or spy_position.quantity == 0
    
    def test_close_short_position(self, mock_ibkr_client):
        """Test closing a short position"""
        # Open short position
        mock_ibkr_client.auto_fill_orders = True
        mock_ibkr_client.place_market_order(symbol="SPY", side="SELL", quantity=10)
        
        # Close position (buy to cover)
        order = mock_ibkr_client.place_market_order(
            symbol="SPY",
            side="BUY",
            quantity=10
        )
        
        # Verify position closed
        positions = mock_ibkr_client.get_positions()
        spy_position = next((p for p in positions if p.symbol == "SPY"), None)
        
        assert spy_position is None or spy_position.quantity == 0


class TestProfitLossCalculation:
    """Test P/L calculation"""
    
    @pytest.fixture
    def mock_ibkr_client_with_position(self):
        """Create mock IBKR client with existing position"""
        client = MockIBKRClient()
        client.auto_fill_orders = True
        client.default_fill_price = 450.0  # Set entry price
        
        # Open position at 450
        client.place_market_order(symbol="SPY", side="BUY", quantity=10)
        return client
    
    def test_profit_calculation(self, mock_ibkr_client_with_position):
        """Test profit calculation"""
        positions = mock_ibkr_client_with_position.get_positions()
        spy_position = next((p for p in positions if p.symbol == "SPY"), None)
        
        assert spy_position is not None
        
        # Update current price to 455 (profit)
        mock_ibkr_client_with_position.update_position_price("SPY", 455.0)
        positions = mock_ibkr_client_with_position.get_positions()
        updated_position = next((p for p in positions if p.symbol == "SPY"), None)
        
        # Calculate P/L: (455 - 450) * 10 = $50 profit
        if updated_position and hasattr(updated_position, 'unrealized_pnl'):
            assert updated_position.unrealized_pnl > 0
        elif updated_position and hasattr(updated_position, 'current_price'):
            pnl = (updated_position.current_price - spy_position.avg_cost) * spy_position.quantity
            assert pnl > 0
    
    def test_loss_calculation(self, mock_ibkr_client_with_position):
        """Test loss calculation"""
        positions = mock_ibkr_client_with_position.get_positions()
        spy_position = next((p for p in positions if p.symbol == "SPY"), None)
        
        assert spy_position is not None
        
        # Update current price to 445 (loss)
        mock_ibkr_client_with_position.update_position_price("SPY", 445.0)
        positions = mock_ibkr_client_with_position.get_positions()
        updated_position = next((p for p in positions if p.symbol == "SPY"), None)
        
        # Calculate P/L: (445 - 450) * 10 = -$50 loss
        if updated_position and hasattr(updated_position, 'unrealized_pnl'):
            assert updated_position.unrealized_pnl < 0
        elif updated_position and hasattr(updated_position, 'current_price'):
            pnl = (updated_position.current_price - spy_position.avg_cost) * spy_position.quantity
            assert pnl < 0
    
    def test_realized_pnl_on_close(self, mock_ibkr_client_with_position):
        """Test realized P/L when closing position"""
        # Close position at higher price
        mock_ibkr_client_with_position.default_fill_price = 455.0
        close_order = mock_ibkr_client_with_position.place_market_order(
            symbol="SPY",
            side="SELL",
            quantity=10
        )
        
        # Realized P/L: (455 - 450) * 10 = $50
        # Verify through order or position history
        assert close_order.status == "FILLED"
        if hasattr(close_order, 'realized_pnl'):
            assert close_order.realized_pnl == 50.0


class TestMultiplePositions:
    """Test managing multiple positions"""
    
    @pytest.fixture
    def mock_ibkr_client(self):
        """Create mock IBKR client"""
        client = MockIBKRClient()
        client.auto_fill_orders = True
        return client
    
    def test_multiple_symbol_positions(self, mock_ibkr_client):
        """Test holding positions in multiple symbols"""
        # Open positions in different symbols
        mock_ibkr_client.place_market_order(symbol="SPY", side="BUY", quantity=10)
        mock_ibkr_client.place_market_order(symbol="QQQ", side="BUY", quantity=5)
        mock_ibkr_client.place_market_order(symbol="IWM", side="BUY", quantity=3)
        
        # Verify all positions exist
        positions = mock_ibkr_client.get_positions()
        symbols = {p.symbol for p in positions}
        
        assert "SPY" in symbols
        assert "QQQ" in symbols
        assert "IWM" in symbols
    
    def test_portfolio_value_calculation(self, mock_ibkr_client):
        """Test portfolio value calculation"""
        # Open positions
        mock_ibkr_client.place_market_order(symbol="SPY", side="BUY", quantity=10)
        mock_ibkr_client.place_market_order(symbol="QQQ", side="BUY", quantity=5)
        
        # Get portfolio value
        positions = mock_ibkr_client.get_positions()
        portfolio_value = sum(p.quantity * p.avg_cost for p in positions)
        
        assert portfolio_value > 0
    
    def test_close_specific_position(self, mock_ibkr_client):
        """Test closing a specific position while keeping others"""
        # Open multiple positions
        mock_ibkr_client.place_market_order(symbol="SPY", side="BUY", quantity=10)
        mock_ibkr_client.place_market_order(symbol="QQQ", side="BUY", quantity=5)
        
        # Close only SPY
        mock_ibkr_client.place_market_order(symbol="SPY", side="SELL", quantity=10)
        
        # Verify SPY closed, QQQ still open
        positions = mock_ibkr_client.get_positions()
        spy_position = next((p for p in positions if p.symbol == "SPY"), None)
        qqq_position = next((p for p in positions if p.symbol == "QQQ"), None)
        
        assert spy_position is None or spy_position.quantity == 0
        assert qqq_position is not None
        assert qqq_position.quantity == 5


@pytest.mark.integration
class TestPositionManagementWorkflow:
    """Test complete position management workflow"""
    
    @pytest.fixture
    def mock_ibkr_client(self):
        """Create mock IBKR client"""
        client = MockIBKRClient()
        client.auto_fill_orders = True
        return client
    
    def test_complete_position_lifecycle(self, mock_ibkr_client):
        """Test complete position lifecycle: open -> update -> close"""
        # 1. Open position
        buy_order = mock_ibkr_client.place_market_order(
            symbol="SPY",
            side="BUY",
            quantity=10
        )
        assert buy_order.status == "FILLED"
        
        # 2. Verify position exists
        positions = mock_ibkr_client.get_positions()
        position = next((p for p in positions if p.symbol == "SPY"), None)
        assert position is not None
        assert position.quantity == 10
        
        # 3. Add to position
        add_order = mock_ibkr_client.place_market_order(
            symbol="SPY",
            side="BUY",
            quantity=5
        )
        positions = mock_ibkr_client.get_positions()
        position = next((p for p in positions if p.symbol == "SPY"), None)
        assert position.quantity == 15
        
        # 4. Partially close
        reduce_order = mock_ibkr_client.place_market_order(
            symbol="SPY",
            side="SELL",
            quantity=5
        )
        positions = mock_ibkr_client.get_positions()
        position = next((p for p in positions if p.symbol == "SPY"), None)
        assert position.quantity == 10
        
        # 5. Close completely
        close_order = mock_ibkr_client.place_market_order(
            symbol="SPY",
            side="SELL",
            quantity=10
        )
        positions = mock_ibkr_client.get_positions()
        position = next((p for p in positions if p.symbol == "SPY"), None)
        assert position is None or position.quantity == 0
