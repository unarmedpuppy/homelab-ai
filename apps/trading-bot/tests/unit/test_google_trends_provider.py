"""
Unit Tests for Google Trends Sentiment Provider
================================================

Comprehensive unit tests for GoogleTrendsClient and GoogleTrendsSentimentProvider.
"""

import pytest
from unittest.mock import Mock, MagicMock, patch
from datetime import datetime, timedelta
import pandas as pd

from src.data.providers.sentiment.google_trends import (
    GoogleTrendsClient,
    GoogleTrendsSentimentProvider
)
from src.data.providers.sentiment.models import SymbolSentiment, SentimentLevel


class TestGoogleTrendsClient:
    """Test suite for GoogleTrendsClient"""
    
    @pytest.fixture
    def mock_pytrends(self):
        """Mock pytrends module"""
        with patch('src.data.providers.sentiment.google_trends.pytrends_available', True):
            with patch('src.data.providers.sentiment.google_trends.TrendReq') as mock_trend_req:
                yield mock_trend_req
    
    @pytest.fixture
    def client(self, mock_pytrends):
        """Create GoogleTrendsClient instance"""
        mock_instance = Mock()
        mock_pytrends.return_value = mock_instance
        with patch('src.config.settings.settings.google_trends.enabled', True):
            return GoogleTrendsClient()
    
    def test_client_initialization(self, mock_pytrends):
        """Test client initialization"""
        mock_instance = Mock()
        mock_pytrends.return_value = mock_instance
        with patch('src.config.settings.settings.google_trends.enabled', True):
            client = GoogleTrendsClient()
            assert client.pytrends is not None
    
    def test_is_available(self, client):
        """Test availability check"""
        assert client.is_available()
    
    def test_get_interest_over_time_success(self, client):
        """Test successful interest over time fetch"""
        # Mock pytrends response
        mock_data = pd.DataFrame({
            'AAPL stock': [50, 60, 70, 80],
            'isPartial': [False, False, False, False]
        }, index=pd.date_range('2024-01-01', periods=4, freq='D'))
        
        client.pytrends.interest_over_time = Mock(return_value=mock_data)
        client.pytrends.build_payload = Mock()
        
        result = client.get_interest_over_time("AAPL stock")
        
        assert result is not None
        assert 'keyword' in result
        assert 'data' in result
    
    def test_get_interest_over_time_empty(self, client):
        """Test interest over time with empty data"""
        mock_data = pd.DataFrame()
        client.pytrends.interest_over_time = Mock(return_value=mock_data)
        client.pytrends.build_payload = Mock()
        
        result = client.get_interest_over_time("AAPL stock")
        
        assert result is None


class TestGoogleTrendsSentimentProvider:
    """Test suite for GoogleTrendsSentimentProvider"""
    
    @pytest.fixture
    def mock_client(self):
        """Mock GoogleTrendsClient"""
        client = Mock(spec=GoogleTrendsClient)
        client.is_available = Mock(return_value=True)
        client.get_interest_over_time = Mock(return_value=None)
        return client
    
    @pytest.fixture
    def provider(self, mock_client):
        """Create GoogleTrendsSentimentProvider with mocked client"""
        with patch('src.data.providers.sentiment.google_trends.GoogleTrendsClient', return_value=mock_client):
            provider = GoogleTrendsSentimentProvider(persist_to_db=False)
            provider.client = mock_client
            return provider
    
    def test_provider_initialization(self, provider):
        """Test provider initialization"""
        assert provider.client is not None
        assert hasattr(provider, 'cache')
    
    def test_get_sentiment_success(self, provider, mock_client):
        """Test successful sentiment retrieval"""
        # Mock interest data with upward trend
        mock_client.get_interest_over_time.return_value = {
            'keyword': 'AAPL stock',
            'data': [
                {'timestamp': '2024-01-01', 'value': 50},
                {'timestamp': '2024-01-02', 'value': 60},
                {'timestamp': '2024-01-03', 'value': 70},
                {'timestamp': '2024-01-04', 'value': 80}  # Rising trend
            ]
        }
        
        provider.cache = {}
        
        sentiment = provider.get_sentiment("AAPL", hours=24)
        
        assert sentiment is not None
        assert sentiment.symbol == "AAPL"
        # Rising trend should indicate positive sentiment
    
    def test_get_sentiment_no_data(self, provider, mock_client):
        """Test sentiment when no data available"""
        mock_client.get_interest_over_time.return_value = None
        
        sentiment = provider.get_sentiment("AAPL", hours=24)
        
        assert sentiment is None
    
    def test_calculate_sentiment_from_trend_rising(self, provider):
        """Test sentiment calculation for rising trend"""
        data = [50, 60, 70, 80]
        sentiment = provider._calculate_sentiment_from_trend(data)
        
        assert sentiment > 0  # Rising trend should be positive

