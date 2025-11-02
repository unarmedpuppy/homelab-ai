"""
Pytest Configuration and Fixtures
==================================
"""

import pytest
from unittest.mock import Mock, MagicMock, patch, AsyncMock
from datetime import datetime, timedelta
from typing import Optional

# Mock database session fixture
@pytest.fixture
def mock_db_session():
    """Mock database session"""
    session = Mock()
    session.query = Mock()
    session.add = Mock()
    session.commit = Mock()
    session.rollback = Mock()
    session.refresh = Mock()
    session.close = Mock()
    session.delete = Mock()
    return session

# Mock Twitter client fixture
@pytest.fixture
def mock_twitter_client():
    """Mock Twitter API client"""
    client = Mock()
    client.is_available = Mock(return_value=True)
    client.search_tweets = Mock(return_value=[])
    client.get_user_info = Mock(return_value={
        'follower_count': 10000,
        'following_count': 500,
        'tweet_count': 5000,
        'verified': True
    })
    return client

# Mock sentiment analyzer fixture
@pytest.fixture
def mock_sentiment_analyzer():
    """Mock sentiment analyzer"""
    analyzer = Mock()
    analyzer.analyze_tweet = Mock(return_value=Mock(
        sentiment_score=0.5,
        confidence=0.8,
        sentiment_level=Mock(value='bullish'),
        vader_scores={'compound': 0.5, 'pos': 0.6, 'neu': 0.3, 'neg': 0.1},
        engagement_score=0.7,
        influencer_weight=1.0,
        weighted_score=0.35,
        timestamp=datetime.now()
    ))
    analyzer._calculate_engagement_score = Mock(return_value=0.7)
    analyzer.calculate_engagement_weight = Mock(return_value=1.0)
    analyzer._score_to_level = Mock(return_value=Mock(value='bullish'))
    return analyzer

# Mock cache manager fixture
@pytest.fixture
def mock_cache_manager():
    """Mock CacheManager"""
    cache = Mock()
    cache.get = Mock(return_value=None)
    cache.set = Mock()
    cache.delete = Mock()
    cache.exists = Mock(return_value=False)
    cache.get_ttl = Mock(return_value=None)
    return cache

# Mock rate limiter fixture
@pytest.fixture
def mock_rate_limiter():
    """Mock RateLimiter"""
    limiter = Mock()
    limiter.check_rate_limit = Mock(return_value=(True, Mock(is_limited=False)))
    limiter.wait_if_needed = Mock(return_value=Mock(is_limited=False))
    limiter.get_status = Mock(return_value=Mock(
        allowed=100,
        used=50,
        remaining=50,
        reset_at=datetime.now() + timedelta(minutes=15),
        is_limited=False
    ))
    return limiter

# Mock usage monitor fixture
@pytest.fixture
def mock_usage_monitor():
    """Mock UsageMonitor"""
    monitor = Mock()
    monitor.record_request = Mock()
    monitor.get_metrics = Mock(return_value=Mock(
        total_requests=100,
        successful_requests=95,
        failed_requests=5,
        cached_requests=50,
        avg_response_time=0.5
    ))
    return monitor

# Mock yfinance fixture
@pytest.fixture
def mock_yfinance():
    """Mock yfinance module"""
    mock_yf = Mock()
    mock_ticker = Mock()
    mock_ticker.info = {}
    mock_yf.Ticker = Mock(return_value=mock_ticker)
    mock_yf.Tickers = Mock(return_value=Mock(tickers={}))
    return mock_yf

# Mock httpx fixture for async clients
@pytest.fixture
def mock_httpx_client():
    """Mock httpx.AsyncClient"""
    client = AsyncMock()
    response = Mock()
    response.status_code = 200
    response.json = Mock(return_value={})
    client.get = AsyncMock(return_value=response)
    client.post = AsyncMock(return_value=response)
    return client

# Sample sentiment data fixtures
@pytest.fixture
def sample_symbol_sentiment():
    """Sample SymbolSentiment for testing"""
    from src.data.providers.sentiment.models import SymbolSentiment, SentimentLevel
    
    return SymbolSentiment(
        symbol="AAPL",
        timestamp=datetime.now(),
        mention_count=10,
        average_sentiment=0.6,
        weighted_sentiment=0.6,
        sentiment_level=SentimentLevel.BULLISH,
        confidence=0.8,
        volume_trend="up"
    )

@pytest.fixture
def sample_tweet():
    """Sample Tweet for testing"""
    from src.data.providers.sentiment.models import Tweet
    
    return Tweet(
        tweet_id="123",
        text="$AAPL is looking bullish today!",
        author_id="user123",
        author_username="trader1",
        created_at=datetime.now(),
        symbols_mentioned=["AAPL"]
    )

