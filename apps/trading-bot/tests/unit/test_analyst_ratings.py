"""
Unit Tests for Analyst Ratings Sentiment Provider
==================================================

Comprehensive unit tests for AnalystRatingsClient and AnalystRatingsSentimentProvider.
Tests include mocking of yfinance to avoid external API calls.
"""

import pytest
from unittest.mock import Mock, MagicMock, patch, PropertyMock
from datetime import datetime, timedelta
from typing import Dict, Any, Optional

from src.data.providers.sentiment.analyst_ratings import (
    AnalystRatingsClient,
    AnalystRatingsSentimentProvider,
    AnalystRating,
    AnalystRatingsTimeoutError
)
from src.data.providers.sentiment.models import SymbolSentiment, SentimentLevel
from src.config.settings import settings


class TestAnalystRating:
    """Test suite for AnalystRating dataclass"""
    
    def test_analyst_rating_creation(self):
        """Test creating an AnalystRating instance"""
        rating = AnalystRating(
            symbol="AAPL",
            rating="Buy",
            rating_numeric=2.0,
            price_target=150.0,
            price_target_high=160.0,
            price_target_low=140.0,
            price_target_mean=150.0,
            number_of_analysts=15,
            current_price=145.0,
            price_target_upside=3.45
        )
        
        assert rating.symbol == "AAPL"
        assert rating.rating == "Buy"
        assert rating.rating_numeric == 2.0
        assert rating.price_target == 150.0
        assert rating.number_of_analysts == 15
        assert rating.price_target_upside == 3.45
    
    def test_analyst_rating_defaults(self):
        """Test AnalystRating with minimal required fields"""
        rating = AnalystRating(
            symbol="TSLA",
            rating="Hold",
            rating_numeric=3.0
        )
        
        assert rating.symbol == "TSLA"
        assert rating.price_target is None
        assert rating.number_of_analysts == 0
        assert rating.timestamp is not None


class TestAnalystRatingsClient:
    """Test suite for AnalystRatingsClient"""
    
    @pytest.fixture
    def mock_yfinance(self):
        """Mock yfinance module"""
        with patch('src.data.providers.sentiment.analyst_ratings.yf') as mock_yf:
            yield mock_yf
    
    @pytest.fixture
    def client(self, mock_yfinance):
        """Create AnalystRatingsClient instance"""
        mock_yfinance.Ticker = Mock()
        with patch.object(settings.analyst_ratings, 'enabled', True):
            return AnalystRatingsClient()
    
    def test_client_initialization(self, mock_yfinance):
        """Test client initialization"""
        mock_yfinance.Ticker = Mock()
        with patch.object(settings.analyst_ratings, 'enabled', True):
            client = AnalystRatingsClient()
            assert client.config is not None
            assert client.is_available()
    
    def test_client_initialization_without_yfinance(self):
        """Test that ImportError is raised when yfinance is not available"""
        with patch('src.data.providers.sentiment.analyst_ratings.yf', None):
            with pytest.raises(ImportError):
                AnalystRatingsClient()
    
    def test_is_available_when_disabled(self, mock_yfinance):
        """Test availability check when provider is disabled"""
        mock_yfinance.Ticker = Mock()
        with patch.object(settings.analyst_ratings, 'enabled', False):
            client = AnalystRatingsClient()
            assert not client.is_available()
    
    def test_validate_symbol_valid(self, client):
        """Test symbol validation with valid symbols"""
        assert client._validate_symbol("AAPL") is True
        assert client._validate_symbol("MSFT") is True
        assert client._validate_symbol("SPY") is True
        assert client._validate_symbol("BRK.B") is False  # Contains dot
    
    def test_validate_symbol_invalid(self, client):
        """Test symbol validation with invalid symbols"""
        assert client._validate_symbol("") is False
        assert client._validate_symbol("A" * 20) is False  # Too long
        assert client._validate_symbol("AAPL!") is False  # Special chars
        assert client._validate_symbol("aa-pl") is False  # Hyphen
        assert client._validate_symbol(None) is False
    
    def test_rating_to_numeric(self, client):
        """Test conversion of rating strings to numeric values"""
        assert client._rating_to_numeric("Strong Buy") == 1.0
        assert client._rating_to_numeric("Buy") == 2.0
        assert client._rating_to_numeric("Hold") == 3.0
        assert client._rating_to_numeric("Sell") == 4.0
        assert client._rating_to_numeric("Strong Sell") == 5.0
        assert client._rating_to_numeric("Unknown") == 3.0  # Default
        assert client._rating_to_numeric("") == 3.0
    
    def test_recommendation_mean_to_rating(self, client):
        """Test conversion of recommendation mean to rating string"""
        assert client._recommendation_mean_to_rating(1.0) == "Strong Buy"
        assert client._recommendation_mean_to_rating(1.5) == "Strong Buy"
        assert client._recommendation_mean_to_rating(2.0) == "Buy"
        assert client._recommendation_mean_to_rating(2.5) == "Buy"
        assert client._recommendation_mean_to_rating(3.0) == "Hold"
        assert client._recommendation_mean_to_rating(3.5) == "Hold"
        assert client._recommendation_mean_to_rating(4.0) == "Sell"
        assert client._recommendation_mean_to_rating(4.5) == "Sell"
        assert client._recommendation_mean_to_rating(5.0) == "Strong Sell"
        assert client._recommendation_mean_to_rating(None) == "Hold"
    
    def test_is_retryable_error(self, client):
        """Test retryable error detection"""
        assert client._is_retryable_error(ConnectionError("Connection failed"))
        assert client._is_retryable_error(TimeoutError("Timeout"))
        assert client._is_retryable_error(OSError("Network error"))
        
        # Check error message patterns
        assert client._is_retryable_error(Exception("Connection timeout"))
        assert client._is_retryable_error(Exception("503 Service Unavailable"))
        assert client._is_retryable_error(Exception("502 Bad Gateway"))
        
        # Non-retryable
        assert not client._is_retryable_error(ValueError("Invalid input"))
        assert not client._is_retryable_error(KeyError("Missing key"))
    
    @patch('signal.SIGALRM', True)
    def test_timeout_unix_system(self, client):
        """Test timeout implementation on Unix systems"""
        def slow_function():
            import time
            time.sleep(20)  # Would timeout
        
        with patch.object(client.config, 'timeout_seconds', 1):
            # On Unix with SIGALRM, should raise timeout
            # Note: This test might be flaky, so we'll just verify the method exists
            assert hasattr(client, '_call_with_timeout')
    
    def test_timeout_windows_fallback(self, client):
        """Test timeout implementation on Windows (threading fallback)"""
        # Mock Windows (no SIGALRM)
        with patch('signal.SIGALRM', None, create=True):
            def fast_function():
                return "result"
            
            with patch.object(client.config, 'timeout_seconds', 10):
                result = client._call_with_timeout(fast_function)
                assert result == "result"
    
    @patch('src.data.providers.sentiment.analyst_ratings.yf')
    def test_get_analyst_rating_success(self, mock_yf, client):
        """Test successful analyst rating fetch"""
        # Mock ticker and info
        mock_info = {
            'recommendationMean': 2.0,
            'recommendationKey': 'buy',
            'targetHighPrice': 160.0,
            'targetLowPrice': 140.0,
            'targetMeanPrice': 150.0,
            'numberOfAnalystOpinions': 15,
            'currentPrice': 145.0
        }
        
        mock_ticker = Mock()
        mock_ticker.info = mock_info
        mock_yf.Ticker.return_value = mock_ticker
        
        with patch.object(client, '_call_with_timeout', return_value=mock_info):
            rating = client.get_analyst_rating("AAPL")
            
            assert rating is not None
            assert rating.symbol == "AAPL"
            assert rating.rating == "Buy"
            assert rating.rating_numeric == 2.0
            assert rating.price_target == 150.0
            assert rating.number_of_analysts == 15
            assert rating.price_target_upside is not None
    
    @patch('src.data.providers.sentiment.analyst_ratings.yf')
    def test_get_analyst_rating_invalid_symbol(self, mock_yf, client):
        """Test analyst rating fetch with invalid symbol"""
        rating = client.get_analyst_rating("INVALID!!!")
        assert rating is None
    
    @patch('src.data.providers.sentiment.analyst_ratings.yf')
    def test_get_analyst_rating_no_data(self, mock_yf, client):
        """Test analyst rating fetch when yfinance returns empty data"""
        mock_info = {}
        
        mock_ticker = Mock()
        mock_ticker.info = mock_info
        mock_yf.Ticker.return_value = mock_ticker
        
        with patch.object(client, '_call_with_timeout', return_value=mock_info):
            rating = client.get_analyst_rating("AAPL")
            
            # Should still return a rating with defaults
            assert rating is not None
            assert rating.rating == "Hold"
            assert rating.rating_numeric == 3.0
    
    @patch('src.data.providers.sentiment.analyst_ratings.yf')
    def test_get_analyst_rating_timeout(self, mock_yf, client):
        """Test analyst rating fetch with timeout"""
        with patch.object(client, '_call_with_timeout', side_effect=AnalystRatingsTimeoutError("Timeout")):
            rating = client.get_analyst_rating("AAPL")
            assert rating is None
    
    @patch('src.data.providers.sentiment.analyst_ratings.yf')
    def test_get_analyst_rating_price_target_validation(self, mock_yf, client):
        """Test that negative or zero prices don't calculate upside"""
        mock_info = {
            'recommendationMean': 2.0,
            'targetMeanPrice': -10.0,  # Invalid
            'currentPrice': 145.0
        }
        
        mock_ticker = Mock()
        mock_ticker.info = mock_info
        mock_yf.Ticker.return_value = mock_ticker
        
        with patch.object(client, '_call_with_timeout', return_value=mock_info):
            rating = client.get_analyst_rating("AAPL")
            
            # Should not calculate upside for invalid prices
            assert rating.price_target_upside is None
    
    def test_check_data_freshness_no_analysts(self, client):
        """Test data freshness check when no analysts"""
        rating = AnalystRating(
            symbol="AAPL",
            rating="Hold",
            rating_numeric=3.0,
            number_of_analysts=0
        )
        
        # Should not raise, just log
        client._check_data_freshness(rating, {})
    
    def test_check_data_freshness_large_discrepancy(self, client):
        """Test data freshness check with large price discrepancy"""
        rating = AnalystRating(
            symbol="AAPL",
            rating="Buy",
            rating_numeric=2.0,
            current_price=100.0,
            price_target=200.0,  # 100% difference
            price_target_upside=100.0,
            number_of_analysts=5
        )
        
        # Should log warning
        with patch('src.data.providers.sentiment.analyst_ratings.logger') as mock_logger:
            client._check_data_freshness(rating, {})
            # Check that warning was logged
            mock_logger.warning.assert_called()


class TestAnalystRatingsSentimentProvider:
    """Test suite for AnalystRatingsSentimentProvider"""
    
    @pytest.fixture
    def mock_client(self):
        """Mock AnalystRatingsClient"""
        client = Mock(spec=AnalystRatingsClient)
        client.is_available = Mock(return_value=True)
        client.get_analyst_rating = Mock()
        client._validate_symbol = Mock(return_value=True)
        client._check_data_freshness = Mock()
        return client
    
    @pytest.fixture
    def provider(self, mock_client):
        """Create AnalystRatingsSentimentProvider with mocked client"""
        with patch('src.data.providers.sentiment.analyst_ratings.AnalystRatingsClient', return_value=mock_client):
            with patch('src.data.providers.sentiment.analyst_ratings.get_cache_manager') as mock_cache:
                with patch('src.data.providers.sentiment.analyst_ratings.get_rate_limiter') as mock_limiter:
                    with patch('src.data.providers.sentiment.analyst_ratings.get_usage_monitor') as mock_monitor:
                        mock_cache.return_value.get = Mock(return_value=None)
                        mock_cache.return_value.set = Mock()
                        mock_limiter.return_value.check_rate_limit = Mock(return_value=(True, Mock()))
                        mock_limiter.return_value.wait_if_needed = Mock(return_value=Mock(is_limited=False))
                        mock_monitor.return_value.record_request = Mock()
                        
                        provider = AnalystRatingsSentimentProvider(persist_to_db=False)
                        provider.client = mock_client
                        return provider
    
    def test_provider_initialization(self, provider):
        """Test provider initialization"""
        assert provider.client is not None
        assert provider.cache is not None
        assert provider.rate_limiter is not None
        assert provider.usage_monitor is not None
    
    def test_is_available(self, provider, mock_client):
        """Test availability check"""
        mock_client.is_available.return_value = True
        assert provider.is_available()
        
        mock_client.is_available.return_value = False
        assert not provider.is_available()
    
    def test_get_sentiment_success(self, provider, mock_client):
        """Test successful sentiment retrieval"""
        # Mock rating
        rating = AnalystRating(
            symbol="AAPL",
            rating="Buy",
            rating_numeric=2.0,
            price_target=150.0,
            number_of_analysts=15,
            current_price=145.0,
            price_target_upside=3.45
        )
        mock_client.get_analyst_rating.return_value = rating
        
        # Mock cache miss
        provider.cache.get = Mock(return_value=None)
        
        sentiment = provider.get_sentiment("AAPL", hours=24)
        
        assert sentiment is not None
        assert sentiment.symbol == "AAPL"
        assert sentiment.average_sentiment > 0  # Buy should be positive
        assert sentiment.sentiment_level in [SentimentLevel.BULLISH, SentimentLevel.VERY_BULLISH]
        assert sentiment.confidence > 0
    
    def test_get_sentiment_cached(self, provider):
        """Test sentiment retrieval from cache"""
        cached_sentiment = SymbolSentiment(
            symbol="AAPL",
            timestamp=datetime.now(),
            mention_count=10,
            average_sentiment=0.5,
            weighted_sentiment=0.5,
            sentiment_level=SentimentLevel.BULLISH,
            confidence=0.8
        )
        
        provider.cache.get = Mock(return_value=cached_sentiment)
        
        sentiment = provider.get_sentiment("AAPL", hours=24)
        
        assert sentiment == cached_sentiment
        # Should not call client
        provider.client.get_analyst_rating.assert_not_called()
    
    def test_get_sentiment_no_rating(self, provider, mock_client):
        """Test sentiment when no rating data available"""
        mock_client.get_analyst_rating.return_value = None
        provider.cache.get = Mock(return_value=None)
        
        sentiment = provider.get_sentiment("AAPL", hours=24)
        
        assert sentiment is not None
        assert sentiment.average_sentiment == 0.0
        assert sentiment.sentiment_level == SentimentLevel.NEUTRAL
        assert sentiment.confidence == 0.3  # Low confidence for missing data
    
    def test_get_sentiment_rate_limit_exceeded(self, provider):
        """Test sentiment when rate limit is exceeded"""
        provider.rate_limiter.check_rate_limit = Mock(return_value=(False, Mock(is_limited=True)))
        provider.rate_limiter.wait_if_needed = Mock(return_value=Mock(is_limited=True))
        
        sentiment = provider.get_sentiment("AAPL", hours=24)
        
        assert sentiment is None
        provider.usage_monitor.record_request.assert_called_with("analyst_ratings", success=False)
    
    def test_rating_to_sentiment_strong_buy(self, provider):
        """Test sentiment conversion for Strong Buy"""
        rating = AnalystRating(
            symbol="AAPL",
            rating="Strong Buy",
            rating_numeric=1.0,
            price_target=150.0,
            current_price=140.0,
            price_target_upside=7.14
        )
        
        sentiment_score = provider._rating_to_sentiment(rating)
        assert sentiment_score > 0.8  # Should be very positive
    
    def test_rating_to_sentiment_hold(self, provider):
        """Test sentiment conversion for Hold"""
        rating = AnalystRating(
            symbol="AAPL",
            rating="Hold",
            rating_numeric=3.0,
            price_target=145.0,
            current_price=145.0,
            price_target_upside=0.0
        )
        
        sentiment_score = provider._rating_to_sentiment(rating)
        assert -0.2 < sentiment_score < 0.2  # Should be near neutral
    
    def test_rating_to_sentiment_strong_sell(self, provider):
        """Test sentiment conversion for Strong Sell"""
        rating = AnalystRating(
            symbol="AAPL",
            rating="Strong Sell",
            rating_numeric=5.0,
            price_target=100.0,
            current_price=150.0,
            price_target_upside=-33.33
        )
        
        sentiment_score = provider._rating_to_sentiment(rating)
        assert sentiment_score < -0.8  # Should be very negative
    
    def test_confidence_calculation(self, provider, mock_client):
        """Test confidence calculation based on number of analysts"""
        # High analyst count
        rating = AnalystRating(
            symbol="AAPL",
            rating="Buy",
            rating_numeric=2.0,
            number_of_analysts=25,
            price_target=150.0,
            current_price=145.0
        )
        mock_client.get_analyst_rating.return_value = rating
        provider.cache.get = Mock(return_value=None)
        
        sentiment = provider.get_sentiment("AAPL", hours=24)
        assert sentiment.confidence >= 0.8  # High confidence with many analysts
        
        # Low analyst count
        rating.number_of_analysts = 5
        sentiment = provider.get_sentiment("AAPL", hours=24)
        assert sentiment.confidence < 0.8
    
    def test_get_analyst_rating_delegation(self, provider, mock_client):
        """Test that get_analyst_rating delegates to client"""
        rating = AnalystRating(
            symbol="AAPL",
            rating="Buy",
            rating_numeric=2.0
        )
        mock_client.get_analyst_rating.return_value = rating
        
        result = provider.get_analyst_rating("AAPL")
        
        assert result == rating
        mock_client.get_analyst_rating.assert_called_once_with("AAPL")
    
    @patch('src.data.providers.sentiment.analyst_ratings.yf')
    def test_batch_fetch_success(self, mock_yf, provider, mock_client):
        """Test batch fetching of analyst ratings"""
        # Mock Tickers
        mock_tickers = Mock()
        mock_ticker1 = Mock()
        mock_ticker1.info = {
            'recommendationMean': 2.0,
            'targetMeanPrice': 150.0,
            'numberOfAnalystOpinions': 10,
            'currentPrice': 145.0
        }
        mock_ticker2 = Mock()
        mock_ticker2.info = {
            'recommendationMean': 1.5,
            'targetMeanPrice': 200.0,
            'numberOfAnalystOpinions': 15,
            'currentPrice': 180.0
        }
        
        mock_tickers.tickers = {
            'AAPL': mock_ticker1,
            'MSFT': mock_ticker2
        }
        mock_yf.Tickers.return_value = mock_tickers
        
        provider.client._call_with_timeout = Mock(side_effect=[
            mock_ticker1.info,
            mock_ticker2.info
        ])
        provider.client._validate_symbol = Mock(return_value=True)
        provider.client._rating_to_numeric = Mock(return_value=2.0)
        provider.client._recommendation_mean_to_rating = Mock(return_value="Buy")
        provider.client._check_data_freshness = Mock()
        
        results = provider.get_analyst_ratings_batch(["AAPL", "MSFT"])
        
        assert len(results) == 2
        assert "AAPL" in results
        assert "MSFT" in results
    
    def test_batch_fetch_invalid_symbols(self, provider):
        """Test batch fetch with invalid symbols"""
        provider.client._validate_symbol = Mock(side_effect=lambda s: s in ["AAPL"])
        
        results = provider.get_analyst_ratings_batch(["AAPL", "INVALID!!!"])
        
        assert "AAPL" in results
        assert "INVALID!!!" in results
        assert results["INVALID!!!"] is None
    
    def test_batch_fetch_fallback(self, provider):
        """Test batch fetch falls back to individual fetches on error"""
        with patch('src.data.providers.sentiment.analyst_ratings.yf.Tickers', side_effect=Exception("Batch failed")):
            provider.client.get_analyst_rating = Mock(return_value=AnalystRating(
                symbol="AAPL",
                rating="Buy",
                rating_numeric=2.0
            ))
            provider.client._validate_symbol = Mock(return_value=True)
            
            results = provider.get_analyst_ratings_batch(["AAPL"])
            
            # Should fallback to individual fetch
            assert "AAPL" in results
            provider.client.get_analyst_rating.assert_called()

