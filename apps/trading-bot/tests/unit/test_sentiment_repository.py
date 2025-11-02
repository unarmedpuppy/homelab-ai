"""
Unit Tests for Sentiment Repository
====================================
"""

import pytest
import json
from datetime import datetime, timedelta
from unittest.mock import Mock, patch

from src.data.providers.sentiment.repository import SentimentRepository
from src.data.providers.sentiment.models import (
    Tweet, TweetSentiment, SymbolSentiment, Influencer, SentimentLevel
)
from src.data.database.models import (
    Tweet as TweetModel,
    TweetSentiment as TweetSentimentModel,
    SymbolSentiment as SymbolSentimentModel,
    Influencer as InfluencerModel
)


class TestSentimentRepository:
    """Test suite for SentimentRepository"""
    
    def test_save_tweet_new(self, mock_db_session):
        """Test saving a new tweet"""
        repository = SentimentRepository(db=mock_db_session)
        
        # Mock query to return None (tweet doesn't exist)
        mock_db_session.query.return_value.filter.return_value.first.return_value = None
        
        tweet = Tweet(
            tweet_id="123",
            text="Test tweet",
            author_id="456",
            author_username="testuser",
            created_at=datetime.now(),
            symbols_mentioned=["AAPL"]
        )
        
        # Mock the commit to return the tweet
        saved_tweet = Mock(spec=TweetModel)
        saved_tweet.tweet_id = "123"
        mock_db_session.add = Mock()
        
        result = repository.save_tweet(tweet)
        
        # Should add to session
        mock_db_session.add.assert_called_once()
        mock_db_session.commit.assert_called_once()
    
    def test_save_tweet_existing(self, mock_db_session):
        """Test updating an existing tweet"""
        repository = SentimentRepository(db=mock_db_session)
        
        # Mock existing tweet
        existing_tweet = Mock(spec=TweetModel)
        existing_tweet.tweet_id = "123"
        mock_db_session.query.return_value.filter.return_value.first.return_value = existing_tweet
        
        tweet = Tweet(
            tweet_id="123",
            text="Updated tweet",
            author_id="456",
            author_username="testuser",
            created_at=datetime.now()
        )
        
        result = repository.save_tweet(tweet)
        
        # Should update, not add
        mock_db_session.add.assert_not_called()
        mock_db_session.commit.assert_called_once()
        assert existing_tweet.text == "Updated tweet"
    
    def test_save_tweet_sentiment(self, mock_db_session):
        """Test saving tweet sentiment"""
        repository = SentimentRepository(db=mock_db_session)
        
        tweet_model = Mock(spec=TweetModel)
        tweet_model.id = 1
        
        # Mock no existing sentiment
        mock_db_session.query.return_value.filter.return_value.first.return_value = None
        
        tweet_sentiment = TweetSentiment(
            tweet_id="123",
            symbol="AAPL",
            sentiment_score=0.5,
            confidence=0.8,
            sentiment_level=SentimentLevel.BULLISH,
            vader_scores={'compound': 0.5, 'pos': 0.6, 'neu': 0.3, 'neg': 0.1},
            engagement_score=0.7,
            influencer_weight=1.0,
            weighted_score=0.35
        )
        
        result = repository.save_tweet_sentiment(tweet_sentiment, tweet_model)
        
        mock_db_session.add.assert_called_once()
        mock_db_session.commit.assert_called_once()
    
    def test_save_symbol_sentiment(self, mock_db_session):
        """Test saving symbol sentiment"""
        repository = SentimentRepository(db=mock_db_session)
        
        symbol_sentiment = SymbolSentiment(
            symbol="AAPL",
            timestamp=datetime.now(),
            mention_count=100,
            average_sentiment=0.5,
            weighted_sentiment=0.6,
            sentiment_level=SentimentLevel.BULLISH,
            confidence=0.8
        )
        
        result = repository.save_symbol_sentiment(symbol_sentiment)
        
        mock_db_session.add.assert_called_once()
        mock_db_session.commit.assert_called_once()
    
    def test_save_influencer_new(self, mock_db_session):
        """Test saving a new influencer"""
        repository = SentimentRepository(db=mock_db_session)
        
        # Mock no existing influencer
        mock_db_session.query.return_value.filter.return_value.first.return_value = None
        
        influencer = Influencer(
            user_id="123",
            username="trader",
            display_name="Trader Pro",
            follower_count=10000,
            category="trader",
            weight_multiplier=1.5
        )
        
        result = repository.save_influencer(influencer)
        
        mock_db_session.add.assert_called_once()
        mock_db_session.commit.assert_called_once()
    
    def test_get_recent_sentiment(self, mock_db_session):
        """Test retrieving recent sentiment"""
        repository = SentimentRepository(db=mock_db_session)
        
        # Mock query results
        mock_sentiment = Mock(spec=SymbolSentimentModel)
        mock_sentiment.symbol = "AAPL"
        mock_sentiment.timestamp = datetime.now()
        
        mock_query = Mock()
        mock_query.filter.return_value.order_by.return_value.limit.return_value.all.return_value = [mock_sentiment]
        mock_db_session.query.return_value = mock_query
        
        results = repository.get_recent_sentiment("AAPL", hours=24, limit=10)
        
        assert len(results) == 1
        assert results[0].symbol == "AAPL"
    
    def test_get_tweets_for_symbol(self, mock_db_session):
        """Test retrieving tweets for a symbol"""
        repository = SentimentRepository(db=mock_db_session)
        
        # Mock tweet
        mock_tweet = Mock(spec=TweetModel)
        mock_tweet.tweet_id = "123"
        mock_tweet.text = "Test $AAPL"
        mock_tweet.symbols_mentioned = json.dumps(["AAPL"])
        mock_tweet.created_at = datetime.now()
        
        mock_query = Mock()
        mock_query.filter.return_value.order_by.return_value.limit.return_value.all.return_value = [mock_tweet]
        mock_db_session.query.return_value = mock_query
        
        results = repository.get_tweets_for_symbol("AAPL", hours=24, limit=10)
        
        # Should filter results
        assert len(results) <= 1
    
    def test_cleanup_old_data(self, mock_db_session):
        """Test cleaning up old data"""
        repository = SentimentRepository(db=mock_db_session)
        
        # Mock deletion
        mock_query = Mock()
        mock_query.filter.return_value.delete.return_value = 5
        mock_db_session.query.return_value = mock_query
        
        # Mock tweets query
        mock_db_session.query.return_value.filter.return_value.all.return_value = []
        
        deleted = repository.cleanup_old_data(days=90)
        
        assert deleted >= 0
        mock_db_session.commit.assert_called()
    
    def test_get_influencers(self, mock_db_session):
        """Test retrieving influencers"""
        repository = SentimentRepository(db=mock_db_session)
        
        # Mock influencer
        mock_influencer = Mock(spec=InfluencerModel)
        mock_influencer.user_id = "123"
        mock_influencer.username = "trader"
        mock_influencer.is_active = True
        
        mock_query = Mock()
        mock_query.filter.return_value.all.return_value = [mock_influencer]
        mock_db_session.query.return_value = mock_query
        
        results = repository.get_influencers(active_only=True)
        
        assert len(results) == 1
        assert results[0].user_id == "123"

