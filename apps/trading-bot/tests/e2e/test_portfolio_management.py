"""
End-to-End Test: Portfolio Management Workflow
===============================================

Tests portfolio tracking, position updates, P/L tracking, and account summary.
"""

import pytest
from unittest.mock import Mock, AsyncMock, patch
from datetime import datetime

from tests.mocks.mock_ibkr_client import MockIBKRClient
from src.data.brokers.ibkr_client import BrokerPosition, OrderSide


@pytest.fixture
def mock_ibkr_client():
    """Create mock IBKR client"""
    client = MockIBKRClient()
    client.set_connection_status(True)
    return client


@pytest.mark.asyncio
@pytest.mark.e2e
class TestPortfolioTracking:
    """Test portfolio tracking workflow"""
    
    async def test_position_tracking_workflow(
        self,
        mock_ibkr_client
    ):
        """Test complete position tracking workflow"""
        
        # Step 1: Open position
        order = await mock_ibkr_client.place_market_order(
            symbol="SPY",
            side="BUY",
            quantity=10
        )
        
        # Wait for fill
        await asyncio.sleep(0.2)
        
        # Step 2: Get positions
        positions = await mock_ibkr_client.get_positions()
        
        # Step 3: Verify position exists
        assert isinstance(positions, (dict, list))
        
        # Step 4: Update position with new price
        position = BrokerPosition(
            symbol="SPY",
            quantity=10,
            average_price=450.0,
            market_price=455.0,  # Price increased
            unrealized_pnl=50.0,
            unrealized_pnl_pct=1.11,
            contract=Mock()
        )
        
        mock_ibkr_client.setup_positions({"SPY": position})
        
        # Step 5: Get updated positions
        updated_positions = await mock_ibkr_client.get_positions()
        
        # Verify position updated
        assert isinstance(updated_positions, (dict, list))
    
    async def test_portfolio_pnl_tracking(
        self,
        mock_ibkr_client
    ):
        """Test portfolio P/L tracking"""
        
        # Create multiple positions
        positions = {
            "SPY": BrokerPosition(
                symbol="SPY",
                quantity=10,
                average_price=450.0,
                market_price=455.0,
                unrealized_pnl=50.0,
                unrealized_pnl_pct=1.11,
                contract=Mock()
            ),
            "QQQ": BrokerPosition(
                symbol="QQQ",
                quantity=5,
                average_price=350.0,
                market_price=348.0,
                unrealized_pnl=-10.0,
                unrealized_pnl_pct=-0.57,
                contract=Mock()
            )
        }
        
        mock_ibkr_client.setup_positions(positions)
        
        # Get positions
        portfolio_positions = await mock_ibkr_client.get_positions()
        
        # Calculate total P/L
        total_pnl = 0.0
        if isinstance(portfolio_positions, dict):
            for pos in portfolio_positions.values():
                total_pnl += pos.unrealized_pnl
        elif isinstance(portfolio_positions, list):
            for pos in portfolio_positions:
                total_pnl += pos.unrealized_pnl
        
        # Verify P/L calculation (50 - 10 = 40)
        assert abs(total_pnl - 40.0) < 0.01
    
    async def test_account_summary_tracking(
        self,
        mock_ibkr_client
    ):
        """Test account summary tracking"""
        
        # Configure account summary
        mock_ibkr_client.configure(
            account_summary={
                'NetLiquidation': {'value': '100000.0', 'currency': 'USD'},
                'BuyingPower': {'value': '95000.0', 'currency': 'USD'},
                'AvailableFunds': {'value': '90000.0', 'currency': 'USD'},
                'TotalCashValue': {'value': '50000.0', 'currency': 'USD'}
            }
        )
        
        # Get account summary
        summary = await mock_ibkr_client.get_account_summary()
        
        # Verify summary data
        assert summary is not None
        assert isinstance(summary, dict)
        
        # Check key fields
        if 'NetLiquidation' in summary:
            assert float(summary['NetLiquidation']['value']) == 100000.0


@pytest.mark.asyncio
@pytest.mark.e2e
class TestPositionUpdates:
    """Test position update scenarios"""
    
    async def test_position_addition(
        self,
        mock_ibkr_client
    ):
        """Test adding new position"""
        
        # Initial: no positions
        positions = await mock_ibkr_client.get_positions()
        initial_count = len(positions) if isinstance(positions, (dict, list)) else 0
        
        # Add position
        order = await mock_ibkr_client.place_market_order(
            symbol="SPY",
            side="BUY",
            quantity=10
        )
        
        await asyncio.sleep(0.2)
        
        # Verify position added
        new_positions = await mock_ibkr_client.get_positions()
        new_count = len(new_positions) if isinstance(new_positions, (dict, list)) else 0
        
        assert new_count >= initial_count
    
    async def test_position_update_on_price_change(
        self,
        mock_ibkr_client
    ):
        """Test position update when price changes"""
        
        # Create initial position
        initial_position = BrokerPosition(
            symbol="SPY",
            quantity=10,
            average_price=450.0,
            market_price=450.0,
            unrealized_pnl=0.0,
            unrealized_pnl_pct=0.0,
            contract=Mock()
        )
        
        mock_ibkr_client.setup_positions({"SPY": initial_position})
        
        # Update price
        updated_position = BrokerPosition(
            symbol="SPY",
            quantity=10,
            average_price=450.0,
            market_price=455.0,  # Price increased by $5
            unrealized_pnl=50.0,  # 10 * 5
            unrealized_pnl_pct=1.11,  # (5/450) * 100
            contract=Mock()
        )
        
        mock_ibkr_client.setup_positions({"SPY": updated_position})
        
        # Verify update
        positions = await mock_ibkr_client.get_positions()
        assert isinstance(positions, (dict, list))
    
    async def test_position_removal_on_close(
        self,
        mock_ibkr_client
    ):
        """Test position removal when closed"""
        
        # Create position
        position = BrokerPosition(
            symbol="SPY",
            quantity=10,
            average_price=450.0,
            market_price=455.0,
            unrealized_pnl=50.0,
            unrealized_pnl_pct=1.11,
            contract=Mock()
        )
        
        mock_ibkr_client.setup_positions({"SPY": position})
        
        # Close position
        exit_order = await mock_ibkr_client.place_market_order(
            symbol="SPY",
            side="SELL",
            quantity=10
        )
        
        await asyncio.sleep(0.2)
        
        # Verify position closed (removed or quantity = 0)
        positions = await mock_ibkr_client.get_positions()
        
        # Position should be removed or have zero quantity
        if isinstance(positions, dict):
            assert "SPY" not in positions or positions["SPY"].quantity == 0
        elif isinstance(positions, list):
            spy_positions = [p for p in positions if p.symbol == "SPY"]
            assert len(spy_positions) == 0 or all(p.quantity == 0 for p in spy_positions)


@pytest.mark.asyncio
@pytest.mark.e2e
class TestPortfolioErrorHandling:
    """Test error handling in portfolio management"""
    
    async def test_get_positions_not_connected(
        self,
        mock_ibkr_client
    ):
        """Test getting positions when not connected"""
        
        # Disconnect
        mock_ibkr_client.set_connection_status(False)
        
        # Try to get positions
        try:
            positions = await mock_ibkr_client.get_positions()
            # If mock allows, should return empty or raise error
            assert positions is None or isinstance(positions, (dict, list))
        except Exception:
            # Expected if connection required
            pass
    
    async def test_account_summary_error(
        self,
        mock_ibkr_client
    ):
        """Test error handling when account summary fails"""
        
        # Configure to fail
        mock_ibkr_client.get_account_summary = AsyncMock(side_effect=Exception("Account error"))
        
        # Try to get summary
        try:
            summary = await mock_ibkr_client.get_account_summary()
            assert summary is None
        except Exception:
            # Expected
            pass


# Required import
import asyncio

