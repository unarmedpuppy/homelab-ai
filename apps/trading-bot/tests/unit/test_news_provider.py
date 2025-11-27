"""
Unit Tests for News Sentiment Provider
=======================================

Comprehensive unit tests for NewsClient and NewsSentimentProvider.
"""

import pytest
from unittest.mock import Mock, MagicMock, patch
from datetime import datetime, timedelta

from src.data.providers.sentiment.news import (
    NewsClient,
    NewsSentimentProvider,
    NewsArticle
)
from src.data.providers.sentiment.models import SymbolSentiment, SentimentLevel


class TestNewsClient:
    """Test suite for NewsClient"""
    
    @pytest.fixture
    def mock_feedparser(self):
        """Mock feedparser module"""
        with patch('src.data.providers.sentiment.news.feedparser') as mock_fp:
            yield mock_fp
    
    @pytest.fixture
    def client(self, mock_feedparser):
        """Create NewsClient instance"""
        with patch('src.config.settings.settings.news.enabled', True):
            return NewsClient()
    
    def test_client_initialization(self, client):
        """Test client initialization"""
        assert client.config is not None
    
    @pytest.mark.asyncio
    async def test_fetch_from_rss_success(self, client, mock_feedparser):
        """Test successful RSS feed fetch"""
        mock_entry = Mock()
        mock_entry.title = "AAPL stock news"
        mock_entry.link = "https://example.com/news"
        mock_entry.published = "2024-01-01T12:00:00Z"
        mock_entry.summary = "Apple stock is rising"
        
        mock_feed = Mock()
        mock_feed.entries = [mock_entry]
        mock_feedparser.parse.return_value = mock_feed
        
        with patch('src.config.settings.settings.news.enabled', True):
            articles = client.fetch_from_rss(symbol="AAPL", hours=24)
        
        assert len(articles) > 0
        assert articles[0].title == "AAPL stock news"
    
    def test_fetch_from_newsapi_success(self, client):
        """Test successful NewsAPI fetch"""
        mock_newsapi = Mock()
        mock_newsapi.get_everything.return_value = {
            'status': 'ok',
            'articles': [
                {
                    'title': 'AAPL news',
                    'url': 'https://example.com',
                    'publishedAt': '2024-01-01T12:00:00Z',
                    'description': 'News about Apple'
                }
            ]
        }
        
        client.newsapi_client = mock_newsapi
        
        with patch('src.config.settings.settings.news.enabled', True):
            articles = client.fetch_from_newsapi(symbol="AAPL", hours=24)
        
        assert len(articles) > 0


class TestNewsSentimentProvider:
    """Test suite for NewsSentimentProvider"""
    
    @pytest.fixture
    def mock_client(self):
        """Mock NewsClient"""
        client = Mock(spec=NewsClient)
        client.is_available = Mock(return_value=True)
        client.fetch_from_rss = Mock(return_value=[])
        client.fetch_from_newsapi = Mock(return_value=None)
        return client
    
    @pytest.fixture
    def provider(self, mock_client):
        """Create NewsSentimentProvider with mocked client"""
        with patch('src.data.providers.sentiment.news.NewsClient', return_value=mock_client):
            with patch('src.data.providers.sentiment.news.get_cache_manager') as mock_cache:
                with patch('src.data.providers.sentiment.news.get_rate_limiter') as mock_limiter:
                    with patch('src.data.providers.sentiment.news.get_usage_monitor') as mock_monitor:
                        mock_cache.return_value.get = Mock(return_value=None)
                        mock_cache.return_value.set = Mock()
                        mock_limiter.return_value.check_rate_limit = Mock(return_value=(True, Mock()))
                        mock_limiter.return_value.wait_if_needed = Mock(return_value=Mock(is_limited=False))
                        mock_monitor.return_value.record_request = Mock()
                        
                        provider = NewsSentimentProvider(persist_to_db=False)
                        provider.client = mock_client
                        return provider
    
    def test_provider_initialization(self, provider):
        """Test provider initialization"""
        assert provider.client is not None
        assert provider.cache is not None
    
    def test_get_sentiment_success(self, provider, mock_client):
        """Test successful sentiment retrieval"""
        # Mock articles
        articles = [
            NewsArticle(
                article_id="1",
                title="AAPL stock news",
                text="Apple stock is rising",
                source="Reuters",
                url="https://example.com",
                published_at=datetime.now(),
                symbols_mentioned=["AAPL"]
            )
        ]
        
        mock_client.fetch_from_rss.return_value = articles
        
        # Mock sentiment analyzer
        provider.analyzer.analyze_tweet = Mock(return_value=Mock(
            sentiment_score=0.7,
            confidence=0.8,
            sentiment_level=SentimentLevel.BULLISH
        ))
        
        # Mock cache miss
        provider.cache.get = Mock(return_value=None)
        
        sentiment = provider.get_sentiment("AAPL", hours=24)
        
        assert sentiment is not None
        assert sentiment.symbol == "AAPL"

