"""
Unit Tests for Sentiment Analyzer
==================================
"""

import pytest
from datetime import datetime
from unittest.mock import Mock

from src.data.providers.sentiment.sentiment_analyzer import SentimentAnalyzer
from src.data.providers.sentiment.models import Tweet, SentimentLevel


class TestSentimentAnalyzer:
    """Test suite for SentimentAnalyzer"""
    
    def test_analyzer_initialization(self):
        """Test that analyzer initializes correctly"""
        analyzer = SentimentAnalyzer()
        assert analyzer is not None
        assert analyzer.analyzer is not None
    
    def test_calculate_engagement_score(self):
        """Test engagement score calculation"""
        analyzer = SentimentAnalyzer()
        
        # Create mock tweet with high engagement
        tweet = Tweet(
            tweet_id="123",
            text="Test tweet",
            author_id="456",
            author_username="testuser",
            created_at=datetime.now(),
            like_count=100,
            retweet_count=50,
            reply_count=25,
            quote_count=10
        )
        
        score = analyzer._calculate_engagement_score(tweet)
        assert 0 <= score <= 1
        assert score > 0  # Should have positive engagement
    
    def test_calculate_engagement_weight(self):
        """Test engagement weight calculation"""
        analyzer = SentimentAnalyzer()
        
        # High engagement should return higher weight
        high_weight = analyzer.calculate_engagement_weight(0.8)
        low_weight = analyzer.calculate_engagement_weight(0.2)
        
        assert high_weight > low_weight
        assert high_weight >= 1.0
        assert low_weight >= 1.0
    
    def test_analyze_tweet_bullish(self):
        """Test sentiment analysis for bullish tweet"""
        analyzer = SentimentAnalyzer()
        
        tweet = Tweet(
            tweet_id="123",
            text="$AAPL is going to the moon! Great earnings! 🚀",
            author_id="456",
            author_username="trader",
            created_at=datetime.now(),
            symbols_mentioned=["AAPL"]
        )
        
        result = analyzer.analyze_tweet(
            tweet=tweet,
            symbol="AAPL",
            engagement_weight=1.0,
            influencer_weight=1.0
        )
        
        assert result is not None
        assert result.symbol == "AAPL"
        assert result.tweet_id == "123"
        assert -1.0 <= result.sentiment_score <= 1.0
        assert 0.0 <= result.confidence <= 1.0
        assert result.sentiment_score > 0  # Should be positive/bullish
        assert 'compound' in result.vader_scores
    
    def test_analyze_tweet_bearish(self):
        """Test sentiment analysis for bearish tweet"""
        analyzer = SentimentAnalyzer()
        
        tweet = Tweet(
            tweet_id="123",
            text="$TSLA is crashing! Bad news ahead. 😱",
            author_id="456",
            author_username="trader",
            created_at=datetime.now(),
            symbols_mentioned=["TSLA"]
        )
        
        result = analyzer.analyze_tweet(
            tweet=tweet,
            symbol="TSLA",
            engagement_weight=1.0,
            influencer_weight=1.0
        )
        
        assert result is not None
        assert result.sentiment_score < 0  # Should be negative/bearish
    
    def test_analyze_tweet_neutral(self):
        """Test sentiment analysis for neutral tweet"""
        analyzer = SentimentAnalyzer()
        
        tweet = Tweet(
            tweet_id="123",
            text="$SPY trading at 450. Volume is normal.",
            author_id="456",
            author_username="trader",
            created_at=datetime.now(),
            symbols_mentioned=["SPY"]
        )
        
        result = analyzer.analyze_tweet(
            tweet=tweet,
            symbol="SPY",
            engagement_weight=1.0,
            influencer_weight=1.0
        )
        
        assert result is not None
        # Neutral should be close to 0
        assert abs(result.sentiment_score) < 0.3
    
    def test_score_to_level(self):
        """Test sentiment score to level conversion"""
        analyzer = SentimentAnalyzer()
        
        assert analyzer._score_to_level(0.8).value == SentimentLevel.VERY_BULLISH.value
        assert analyzer._score_to_level(0.3).value == SentimentLevel.BULLISH.value
        assert analyzer._score_to_level(0.1).value == SentimentLevel.NEUTRAL.value
        assert analyzer._score_to_level(-0.3).value == SentimentLevel.BEARISH.value
        assert analyzer._score_to_level(-0.8).value == SentimentLevel.VERY_BEARISH.value
    
    def test_weighted_score_calculation(self):
        """Test that weighted score accounts for engagement and influencer weights"""
        analyzer = SentimentAnalyzer()
        
        tweet = Tweet(
            tweet_id="123",
            text="$AAPL is amazing!",
            author_id="456",
            author_username="trader",
            created_at=datetime.now(),
            symbols_mentioned=["AAPL"],
            like_count=1000,
            retweet_count=500
        )
        
        # High engagement and influencer weight
        result1 = analyzer.analyze_tweet(
            tweet=tweet,
            symbol="AAPL",
            engagement_weight=2.0,
            influencer_weight=1.5
        )
        
        # Low weights
        result2 = analyzer.analyze_tweet(
            tweet=tweet,
            symbol="AAPL",
            engagement_weight=1.0,
            influencer_weight=1.0
        )
        
        # Weighted scores should differ
        assert result1.weighted_score != result2.weighted_score
        assert result1.engagement_score == result2.engagement_score  # Same tweet
        assert result1.influencer_weight == 1.5
        assert result2.influencer_weight == 1.0

