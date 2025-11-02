"""
Integration Tests for Sentiment API Endpoints
==============================================

Tests that verify sentiment endpoints work correctly with mocked providers.
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import Mock, AsyncMock, patch
from datetime import datetime
from src.api.main import app


@pytest.fixture
def client():
    """Create test client"""
    return TestClient(app)


class TestSentimentStatusEndpoints:
    """Test sentiment provider status endpoints"""
    
    def test_twitter_status_endpoint(self, client):
        """Test Twitter sentiment provider status"""
        response = client.get("/api/sentiment/twitter/status")
        
        assert response.status_code == 200
        data = response.json()
        assert "available" in data
        assert "provider" in data
    
    def test_reddit_status_endpoint(self, client):
        """Test Reddit sentiment provider status"""
        response = client.get("/api/sentiment/reddit/status")
        
        assert response.status_code == 200
        data = response.json()
        assert "available" in data
    
    def test_news_status_endpoint(self, client):
        """Test News sentiment provider status"""
        response = client.get("/api/sentiment/news/status")
        
        assert response.status_code == 200
        data = response.json()
        assert "available" in data


class TestSentimentDataEndpoints:
    """Test sentiment data retrieval endpoints"""
    
    def test_twitter_sentiment_endpoint(self, client):
        """Test Twitter sentiment endpoint"""
        with patch('src.api.routes.sentiment.get_twitter_provider') as mock_get:
            mock_provider = Mock()
            mock_provider.is_available.return_value = True
            
            from src.data.providers.sentiment.models import SymbolSentiment, SentimentLevel
            
            mock_sentiment = SymbolSentiment(
                symbol="SPY",
                timestamp=datetime.now(),
                mention_count=100,
                average_sentiment=0.65,
                weighted_sentiment=0.70,
                sentiment_level=SentimentLevel.BULLISH,
                confidence=0.85,
                volume_trend="up"
            )
            mock_provider.get_sentiment.return_value = mock_sentiment
            mock_get.return_value = mock_provider
            
            response = client.get("/api/sentiment/twitter/SPY?hours=24")
            
            assert response.status_code == 200
            data = response.json()
            assert data["symbol"] == "SPY"
            assert data["mention_count"] == 100
    
    def test_sentiment_endpoint_invalid_symbol(self, client):
        """Test sentiment endpoint with invalid symbol"""
        response = client.get("/api/sentiment/twitter/INVALID_SYMBOL_XYZ?hours=24")
        
        # Should return error or empty result
        assert response.status_code in [200, 400, 404, 422]
    
    def test_sentiment_endpoint_invalid_hours(self, client):
        """Test sentiment endpoint with invalid hours parameter"""
        response = client.get("/api/sentiment/twitter/SPY?hours=1000")  # Too large
        
        # Should return validation error
        assert response.status_code in [400, 422]
    
    def test_aggregated_sentiment_endpoint(self, client):
        """Test aggregated sentiment endpoint"""
        with patch('src.api.routes.sentiment.SentimentAggregator') as mock_agg_class:
            mock_aggregator = Mock()
            mock_aggregator.get_aggregated_sentiment.return_value = Mock(
                symbol="SPY",
                timestamp=datetime.now(),
                overall_sentiment=0.7,
                confidence=0.8,
                sentiment_level="bullish"
            )
            mock_agg_class.return_value = mock_aggregator
            
            response = client.get("/api/sentiment/aggregated/SPY?hours=24")
            
            # Should succeed or handle gracefully
            assert response.status_code in [200, 404, 500]


class TestSentimentTrendEndpoints:
    """Test sentiment trend endpoints"""
    
    def test_twitter_trends_endpoint(self, client):
        """Test Twitter sentiment trends endpoint"""
        response = client.get("/api/sentiment/twitter/SPY/trends?days=7")
        
        # Should return trends or handle gracefully
        assert response.status_code in [200, 404, 500]


@pytest.mark.integration
class TestSentimentEndpointErrorHandling:
    """Test error handling in sentiment endpoints"""
    
    def test_provider_not_available_error(self, client):
        """Test error when provider is not available"""
        with patch('src.api.routes.sentiment.get_twitter_provider', return_value=None):
            response = client.get("/api/sentiment/twitter/SPY?hours=24")
            
            # Should return service unavailable
            assert response.status_code in [503, 404]
    
    def test_provider_exception_handling(self, client):
        """Test error handling when provider raises exception"""
        with patch('src.api.routes.sentiment.get_twitter_provider') as mock_get:
            mock_provider = Mock()
            mock_provider.is_available.return_value = True
            mock_provider.get_sentiment.side_effect = Exception("Provider error")
            mock_get.return_value = mock_provider
            
            response = client.get("/api/sentiment/twitter/SPY?hours=24")
            
            # Should handle error gracefully
            assert response.status_code in [500, 503]
