"""
Unit Tests for StockTwits Sentiment Provider
=============================================

Comprehensive unit tests for StockTwitsClient and StockTwitsSentimentProvider.
"""

import pytest
from unittest.mock import Mock, MagicMock, patch, AsyncMock
from datetime import datetime, timedelta
from typing import List, Dict, Any

from src.data.providers.sentiment.stocktwits import (
    StockTwitsClient,
    StockTwitsSentimentProvider,
    StockTwitsMessage
)
from src.data.providers.sentiment.models import SymbolSentiment, SentimentLevel


class TestStockTwitsClient:
    """Test suite for StockTwitsClient"""
    
    @pytest.fixture
    def client(self):
        """Create StockTwitsClient instance"""
        with patch.object(pytest, 'importorskip', return_value=Mock()):
            with patch('src.data.providers.sentiment.stocktwits.httpx') as mock_httpx:
                with patch.object(pytest.importorskip('src.config.settings').stocktwits, 'enabled', True):
                    return StockTwitsClient()
    
    def test_client_initialization(self):
        """Test client initialization"""
        with patch('src.data.providers.sentiment.stocktwits.httpx.AsyncClient') as mock_client:
            with patch.object(pytest.importorskip('src.config.settings').stocktwits, 'enabled', True):
                client = StockTwitsClient()
                assert client.config is not None
    
    def test_is_available(self):
        """Test availability check"""
        with patch('src.data.providers.sentiment.stocktwits.httpx.AsyncClient'):
            with patch.object(pytest.importorskip('src.config.settings').stocktwits, 'enabled', True):
                client = StockTwitsClient()
                assert client.is_available()
    
    @pytest.mark.asyncio
    async def test_get_messages_for_symbol_success(self):
        """Test successful message fetching"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'messages': [
                {
                    'id': 123,
                    'body': 'Bullish on $AAPL',
                    'user': {'username': 'trader1'},
                    'created_at': '2024-01-01T12:00:00Z',
                    'sentiment': 'bullish'
                }
            ]
        }
        
        mock_client = AsyncMock()
        mock_client.get.return_value = mock_response
        
        with patch('src.data.providers.sentiment.stocktwits.httpx.AsyncClient', return_value=mock_client):
            with patch.object(pytest.importorskip('src.config.settings').stocktwits, 'enabled', True):
                client = StockTwitsClient()
                messages = await client.get_messages_for_symbol("AAPL", limit=10)
                
                assert len(messages) == 1
                assert messages[0].body == 'Bullish on $AAPL'
    
    @pytest.mark.asyncio
    async def test_get_messages_for_symbol_rate_limited(self):
        """Test message fetching when rate limited"""
        mock_response = Mock()
        mock_response.status_code = 429  # Rate limited
        
        mock_client = AsyncMock()
        mock_client.get.return_value = mock_response
        
        with patch('src.data.providers.sentiment.stocktwits.httpx.AsyncClient', return_value=mock_client):
            with patch.object(pytest.importorskip('src.config.settings').stocktwits, 'enabled', True):
                client = StockTwitsClient()
                messages = await client.get_messages_for_symbol("AAPL")
                
                assert len(messages) == 0


class TestStockTwitsSentimentProvider:
    """Test suite for StockTwitsSentimentProvider"""
    
    @pytest.fixture
    def mock_client(self):
        """Mock StockTwitsClient"""
        client = AsyncMock(spec=StockTwitsClient)
        client.is_available = Mock(return_value=True)
        client.get_messages_for_symbol = AsyncMock(return_value=[])
        return client
    
    @pytest.fixture
    def provider(self, mock_client):
        """Create StockTwitsSentimentProvider with mocked client"""
        with patch('src.data.providers.sentiment.stocktwits.StockTwitsClient', return_value=mock_client):
            with patch('src.data.providers.sentiment.stocktwits.get_cache_manager') as mock_cache:
                with patch('src.data.providers.sentiment.stocktwits.get_rate_limiter') as mock_limiter:
                    with patch('src.data.providers.sentiment.stocktwits.get_usage_monitor') as mock_monitor:
                        mock_cache.return_value.get = Mock(return_value=None)
                        mock_cache.return_value.set = Mock()
                        mock_limiter.return_value.check_rate_limit = Mock(return_value=(True, Mock()))
                        mock_limiter.return_value.wait_if_needed = Mock(return_value=Mock(is_limited=False))
                        mock_monitor.return_value.record_request = Mock()
                        
                        provider = StockTwitsSentimentProvider(persist_to_db=False)
                        provider.client = mock_client
                        return provider
    
    def test_provider_initialization(self, provider):
        """Test provider initialization"""
        assert provider.client is not None
        assert provider.cache is not None
    
    @pytest.mark.asyncio
    async def test_get_sentiment_success(self, provider, mock_client):
        """Test successful sentiment retrieval"""
        # Mock messages
        messages = [
            StockTwitsMessage(
                message_id=1,
                body="Bullish on $AAPL",
                username="trader1",
                created_at=datetime.now(),
                sentiment="bullish"
            )
        ]
        mock_client.get_messages_for_symbol.return_value = messages
        
        # Mock cache miss
        provider.cache.get = Mock(return_value=None)
        
        # Mock sentiment analyzer
        provider.analyzer.analyze_tweet = Mock(return_value=Mock(
            sentiment_score=0.7,
            confidence=0.8,
            sentiment_level=SentimentLevel.BULLISH
        ))
        
        sentiment = await provider.get_sentiment("AAPL", hours=24)
        
        assert sentiment is not None
        assert sentiment.symbol == "AAPL"
    
    @pytest.mark.asyncio
    async def test_get_sentiment_no_messages(self, provider, mock_client):
        """Test sentiment when no messages available"""
        mock_client.get_messages_for_symbol.return_value = []
        provider.cache.get = Mock(return_value=None)
        
        sentiment = await provider.get_sentiment("AAPL", hours=24)
        
        assert sentiment is None
    
    def test_sentiment_to_score(self, provider):
        """Test sentiment string to score conversion"""
        assert provider._sentiment_to_score("bullish") > 0
        assert provider._sentiment_to_score("bearish") < 0
        assert provider._sentiment_to_score(None) == 0.0
        assert provider._sentiment_to_score("neutral") == 0.0

