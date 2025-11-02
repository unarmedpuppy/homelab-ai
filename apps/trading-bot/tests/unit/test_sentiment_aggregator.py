"""
Unit Tests for Sentiment Aggregator
====================================

Comprehensive unit tests for SentimentAggregator.
"""

import pytest
from unittest.mock import Mock, MagicMock, patch
from datetime import datetime, timedelta

from src.data.providers.sentiment.aggregator import (
    SentimentAggregator,
    AggregatedSentiment
)
from src.data.providers.sentiment.models import SymbolSentiment, SentimentLevel


class TestSentimentAggregator:
    """Test suite for SentimentAggregator"""
    
    @pytest.fixture
    def mock_providers(self):
        """Mock sentiment providers"""
        twitter_provider = Mock()
        twitter_provider.is_available = Mock(return_value=True)
        twitter_provider.get_sentiment = Mock(return_value=SymbolSentiment(
            symbol="AAPL",
            timestamp=datetime.now(),
            mention_count=10,
            average_sentiment=0.6,
            weighted_sentiment=0.6,
            sentiment_level=SentimentLevel.BULLISH,
            confidence=0.8
        ))
        
        reddit_provider = Mock()
        reddit_provider.is_available = Mock(return_value=True)
        reddit_provider.get_sentiment = Mock(return_value=SymbolSentiment(
            symbol="AAPL",
            timestamp=datetime.now(),
            mention_count=5,
            average_sentiment=0.4,
            weighted_sentiment=0.4,
            sentiment_level=SentimentLevel.BULLISH,
            confidence=0.7
        ))
        
        return {
            'twitter': twitter_provider,
            'reddit': reddit_provider
        }
    
    @pytest.fixture
    def aggregator(self, mock_providers):
        """Create SentimentAggregator with mocked providers"""
        with patch('src.data.providers.sentiment.aggregator.get_cache_manager') as mock_cache:
            mock_cache.return_value.get = Mock(return_value=None)
            mock_cache.return_value.set = Mock()
            
            aggregator = SentimentAggregator(persist_to_db=False)
            aggregator.providers = mock_providers
            return aggregator
    
    def test_aggregator_initialization(self, aggregator):
        """Test aggregator initialization"""
        assert aggregator.providers is not None
        assert aggregator.cache is not None
    
    def test_get_aggregated_sentiment_success(self, aggregator, mock_providers):
        """Test successful sentiment aggregation"""
        aggregated = aggregator.get_aggregated_sentiment("AAPL", hours=24)
        
        assert aggregated is not None
        assert aggregated.symbol == "AAPL"
        assert aggregated.unified_sentiment is not None
        assert len(aggregated.providers_used) > 0
        assert 'twitter' in aggregated.providers_used
        assert 'reddit' in aggregated.providers_used
    
    def test_get_aggregated_sentiment_no_providers(self, aggregator):
        """Test aggregation when no providers available"""
        aggregator.providers = {}
        
        aggregated = aggregator.get_aggregated_sentiment("AAPL", hours=24)
        
        assert aggregated is None
    
    def test_get_aggregated_sentiment_one_provider_fails(self, aggregator, mock_providers):
        """Test aggregation when one provider fails"""
        mock_providers['twitter'].get_sentiment.return_value = None
        
        aggregated = aggregator.get_aggregated_sentiment("AAPL", hours=24)
        
        # Should still aggregate from other providers
        assert aggregated is not None
        assert 'reddit' in aggregated.providers_used
    
    def test_weighted_averaging(self, aggregator):
        """Test that weighted averaging works correctly"""
        sentiments = [
            SymbolSentiment(
                symbol="AAPL",
                timestamp=datetime.now(),
                mention_count=10,
                average_sentiment=0.8,
                weighted_sentiment=0.8,
                sentiment_level=SentimentLevel.VERY_BULLISH,
                confidence=0.9
            ),
            SymbolSentiment(
                symbol="AAPL",
                timestamp=datetime.now(),
                mention_count=5,
                average_sentiment=0.2,
                weighted_sentiment=0.2,
                sentiment_level=SentimentLevel.BULLISH,
                confidence=0.6
            )
        ]
        
        # Test weighted calculation
        weights = {'source1': 0.7, 'source2': 0.3}
        weighted_score = aggregator._calculate_weighted_average(sentiments, weights)
        
        # Should be closer to 0.8 (higher weight)
        assert weighted_score > 0.5
    
    def test_divergence_detection(self, aggregator):
        """Test divergence detection when providers disagree"""
        sentiments = [
            SymbolSentiment(
                symbol="AAPL",
                timestamp=datetime.now(),
                mention_count=10,
                average_sentiment=0.8,  # Very bullish
                weighted_sentiment=0.8,
                sentiment_level=SentimentLevel.VERY_BULLISH,
                confidence=0.9
            ),
            SymbolSentiment(
                symbol="AAPL",
                timestamp=datetime.now(),
                mention_count=5,
                average_sentiment=-0.7,  # Very bearish
                weighted_sentiment=-0.7,
                sentiment_level=SentimentLevel.VERY_BEARISH,
                confidence=0.8
            )
        ]
        
        # Should detect high divergence
        divergence = aggregator._calculate_divergence(sentiments)
        
        assert divergence > 0.5  # High divergence threshold
    
    def test_time_decay_weighting(self, aggregator):
        """Test that recent data is weighted more"""
        recent_sentiment = SymbolSentiment(
            symbol="AAPL",
            timestamp=datetime.now() - timedelta(hours=1),
            mention_count=10,
            average_sentiment=0.8,
            weighted_sentiment=0.8,
            sentiment_level=SentimentLevel.BULLISH,
            confidence=0.9
        )
        
        old_sentiment = SymbolSentiment(
            symbol="AAPL",
            timestamp=datetime.now() - timedelta(hours=25),
            mention_count=10,
            average_sentiment=0.2,
            weighted_sentiment=0.2,
            sentiment_level=SentimentLevel.BULLISH,
            confidence=0.9
        )
        
        # Recent sentiment should have higher weight
        recent_weight = aggregator._calculate_time_decay_weight(recent_sentiment.timestamp, hours=24)
        old_weight = aggregator._calculate_time_decay_weight(old_sentiment.timestamp, hours=24)
        
        assert recent_weight > old_weight
    
    def test_min_confidence_filtering(self, aggregator, mock_providers):
        """Test that low-confidence providers are filtered out"""
        with patch.object(aggregator.config, 'min_provider_confidence', 0.8):
            # One provider has low confidence
            mock_providers['reddit'].get_sentiment.return_value = SymbolSentiment(
                symbol="AAPL",
                timestamp=datetime.now(),
                mention_count=5,
                average_sentiment=0.4,
                weighted_sentiment=0.4,
                sentiment_level=SentimentLevel.BULLISH,
                confidence=0.5  # Low confidence
            )
            
            aggregated = aggregator.get_aggregated_sentiment("AAPL", hours=24)
            
            # Should exclude low-confidence provider
            if aggregated:
                assert 'reddit' not in aggregated.providers_used or aggregated.confidence >= 0.8

