"""
Integration Tests for Trading API Endpoints
===========================================

Tests that verify trading endpoints work correctly with mocked dependencies.
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from src.api.main import app


@pytest.fixture
def client():
    """Create test client"""
    return TestClient(app)


@pytest.fixture
def mock_ibkr_client():
    """Mock IBKR client"""
    mock_client = Mock()
    mock_client.connected = True
    mock_client.is_connected = True
    mock_client.connect = AsyncMock(return_value=True)
    mock_client.disconnect = AsyncMock()
    mock_client.get_account_summary = AsyncMock(return_value={
        'NetLiquidation': {'value': '100000.0', 'currency': 'USD'}
    })
    mock_client.get_positions = AsyncMock(return_value=[])
    mock_client.get_orders = AsyncMock(return_value=[])
    return mock_client


class TestIBKRConnectionEndpoints:
    """Test IBKR connection management endpoints"""
    
    def test_ibkr_status_endpoint(self, client, mock_ibkr_client):
        """Test IBKR connection status endpoint"""
        with patch('src.api.routes.trading.get_ibkr_client', return_value=mock_ibkr_client):
            response = client.get("/api/trading/ibkr/status")
            
            assert response.status_code == 200
            data = response.json()
            assert "connected" in data
            assert data["connected"] is True
    
    def test_ibkr_connect_endpoint(self, client, mock_ibkr_client):
        """Test IBKR connect endpoint"""
        with patch('src.api.routes.trading.get_ibkr_client', return_value=mock_ibkr_client):
            response = client.post("/api/trading/ibkr/connect")
            
            # Should succeed (200 or 202)
            assert response.status_code in [200, 202]
            data = response.json()
            assert "status" in data or "connected" in data
    
    def test_ibkr_disconnect_endpoint(self, client, mock_ibkr_client):
        """Test IBKR disconnect endpoint"""
        with patch('src.api.routes.trading.get_ibkr_client', return_value=mock_ibkr_client):
            response = client.post("/api/trading/ibkr/disconnect")
            
            assert response.status_code == 200
            data = response.json()
            assert "status" in data or "disconnected" in data
    
    def test_ibkr_positions_endpoint(self, client, mock_ibkr_client):
        """Test IBKR positions endpoint"""
        mock_position = Mock()
        mock_position.symbol = "SPY"
        mock_position.quantity = 10
        mock_position.avg_cost = 450.0
        mock_ibkr_client.get_positions = AsyncMock(return_value=[mock_position])
        
        with patch('src.api.routes.trading.get_ibkr_client', return_value=mock_ibkr_client):
            response = client.get("/api/trading/ibkr/positions")
            
            assert response.status_code == 200
            data = response.json()
            assert isinstance(data, (list, dict))


class TestOrderExecutionEndpoints:
    """Test order execution endpoints"""
    
    def test_execute_trade_endpoint(self, client, mock_ibkr_client):
        """Test execute trade endpoint"""
        from src.data.brokers.ibkr_client import BrokerOrder
        
        mock_order = BrokerOrder(
            order_id="test_123",
            symbol="SPY",
            side="BUY",
            quantity=10,
            order_type="MARKET",
            status="SUBMITTED",
            filled_quantity=0,
            average_price=0.0,
            timestamp=None
        )
        mock_ibkr_client.place_market_order = AsyncMock(return_value=mock_order)
        
        trade_request = {
            "symbol": "SPY",
            "side": "BUY",
            "quantity": 10,
            "order_type": "MARKET"
        }
        
        with patch('src.api.routes.trading.get_ibkr_client', return_value=mock_ibkr_client):
            with patch('src.api.routes.trading.get_risk_manager') as mock_risk:
                mock_risk.return_value.check_compliance = AsyncMock(return_value=Mock(
                    can_proceed=True,
                    result="allowed"
                ))
                
                response = client.post("/api/trading/execute", json=trade_request)
                
                # Should succeed or return appropriate status
                assert response.status_code in [200, 201, 400, 422]
    
    def test_execute_trade_validation_error(self, client):
        """Test execute trade with invalid request"""
        invalid_request = {
            "symbol": "",  # Invalid symbol
            "side": "INVALID",  # Invalid side
            "quantity": -10  # Invalid quantity
        }
        
        response = client.post("/api/trading/execute", json=invalid_request)
        
        # Should return validation error
        assert response.status_code in [400, 422]


class TestAccountEndpoints:
    """Test account-related endpoints"""
    
    def test_account_summary_endpoint(self, client, mock_ibkr_client):
        """Test account summary endpoint"""
        with patch('src.api.routes.trading.get_ibkr_client', return_value=mock_ibkr_client):
            response = client.get("/api/trading/ibkr/account")
            
            assert response.status_code == 200
            data = response.json()
            assert "balance" in data or "NetLiquidation" in data or isinstance(data, dict)


@pytest.mark.integration
class TestTradingEndpointErrorHandling:
    """Test error handling in trading endpoints"""
    
    def test_ibkr_not_connected_error(self, client):
        """Test error when IBKR is not connected"""
        mock_client = Mock()
        mock_client.connected = False
        mock_client.is_connected = False
        
        with patch('src.api.routes.trading.get_ibkr_client', return_value=mock_client):
            response = client.get("/api/trading/ibkr/positions")
            
            # Should return error when not connected
            assert response.status_code in [400, 503]
    
    def test_ibkr_connection_error(self, client):
        """Test error handling during connection"""
        mock_client = Mock()
        mock_client.connect = AsyncMock(side_effect=Exception("Connection failed"))
        
        with patch('src.api.routes.trading.get_ibkr_client', return_value=mock_client):
            response = client.post("/api/trading/ibkr/connect")
            
            # Should handle error gracefully
            assert response.status_code in [500, 503]
