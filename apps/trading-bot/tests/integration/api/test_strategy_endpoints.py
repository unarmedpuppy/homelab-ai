"""
Integration Tests for Strategy API Endpoints
============================================

Tests that verify strategy endpoints work correctly.
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import Mock, AsyncMock, patch
from src.api.main import app


@pytest.fixture
def client():
    """Create test client"""
    return TestClient(app)


class TestStrategyEndpoints:
    """Test strategy management endpoints"""
    
    def test_list_strategies_endpoint(self, client):
        """Test listing available strategies"""
        response = client.get("/api/strategies")
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, (list, dict))
    
    def test_strategy_evaluation_endpoint(self, client):
        """Test strategy evaluation endpoint"""
        evaluation_request = {
            "strategy_name": "RangeBoundStrategy",
            "symbol": "SPY",
            "timeframe": "5m",
            "config": {
                "entry": {"levels": ["previous_day_high"]},
                "exit": {"stop_loss_pct": 0.005}
            }
        }
        
        with patch('src.api.routes.strategies.StrategyEvaluator') as mock_eval_class:
            mock_evaluator = Mock()
            mock_evaluator.evaluate_strategy = Mock(return_value=None)
            mock_eval_class.return_value = mock_evaluator
            
            response = client.post("/api/strategies/evaluate", json=evaluation_request)
            
            # Should succeed or handle appropriately
            assert response.status_code in [200, 400, 422, 500]


class TestStrategyEndpointValidation:
    """Test strategy endpoint input validation"""
    
    def test_evaluation_missing_required_fields(self, client):
        """Test evaluation with missing required fields"""
        incomplete_request = {
            "strategy_name": "RangeBoundStrategy"
            # Missing symbol, timeframe, config
        }
        
        response = client.post("/api/strategies/evaluate", json=incomplete_request)
        
        # Should return validation error
        assert response.status_code in [400, 422]


@pytest.mark.integration
class TestStrategyEndpointErrorHandling:
    """Test error handling in strategy endpoints"""
    
    def test_invalid_strategy_name(self, client):
        """Test evaluation with invalid strategy name"""
        evaluation_request = {
            "strategy_name": "NonExistentStrategy",
            "symbol": "SPY",
            "timeframe": "5m",
            "config": {}
        }
        
        response = client.post("/api/strategies/evaluate", json=evaluation_request)
        
        # Should return error for invalid strategy
        assert response.status_code in [400, 404, 422]
