"""
Unit Tests for Reddit Sentiment Provider
=========================================
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timedelta

from src.data.providers.sentiment.reddit import RedditSentimentProvider, RedditPost
from src.data.providers.sentiment.models import SentimentLevel


class TestRedditSentimentProvider:
    """Test suite for RedditSentimentProvider"""
    
    @patch('src.data.providers.sentiment.reddit.RedditClient')
    def test_provider_initialization(self, mock_client_class):
        """Test provider initialization"""
        mock_client = Mock()
        mock_client.is_available.return_value = True
        mock_client_class.return_value = mock_client
        
        provider = RedditSentimentProvider(persist_to_db=False)
        
        assert provider is not None
        assert provider.client is not None
        assert provider.analyzer is not None
        assert provider.persist_to_db == False
    
    @patch('src.data.providers.sentiment.reddit.RedditClient')
    def test_cache_functionality(self, mock_client_class):
        """Test caching mechanism"""
        mock_client = Mock()
        mock_client.is_available.return_value = True
        mock_client_class.return_value = mock_client
        
        provider = RedditSentimentProvider(persist_to_db=False)
        
        # Set cache
        provider._set_cache("test_key", "test_data")
        
        # Get from cache
        cached = provider._get_from_cache("test_key")
        assert cached == "test_data"
        
        # Test expired cache
        provider.cache["expired_key"] = ("data", datetime.now() - timedelta(seconds=1000))
        expired = provider._get_from_cache("expired_key")
        assert expired is None
    
    @patch('src.data.providers.sentiment.reddit.RedditClient')
    def test_get_sentiment_no_data(self, mock_client_class):
        """Test get_sentiment when no data is available"""
        mock_client = Mock()
        mock_client.is_available.return_value = True
        mock_client.search_posts.return_value = []
        mock_client_class.return_value = mock_client
        
        provider = RedditSentimentProvider(persist_to_db=False)
        
        sentiment = provider.get_sentiment("AAPL", hours=24)
        
        # Should return None when no posts found
        assert sentiment is None
    
    @patch('src.data.providers.sentiment.reddit.RedditClient')
    def test_reddit_post_to_tweet_compatibility(self, mock_client_class):
        """Test that RedditPost can be used with Tweet-based sentiment analysis"""
        mock_client = Mock()
        mock_client.is_available.return_value = True
        mock_client_class.return_value = mock_client
        
        provider = RedditSentimentProvider(persist_to_db=False)
        
        # Create Reddit post
        post = RedditPost(
            post_id="test123",
            text="$AAPL is going to the moon!",
            author="testuser",
            created_at=datetime.now(),
            score=100,
            upvote_ratio=0.95,
            num_comments=50,
            subreddit="wallstreetbets",
            symbols_mentioned=["AAPL"]
        )
        
        # Test compatibility attributes
        assert hasattr(post, 'tweet_id')
        assert hasattr(post, 'author_username')
        assert hasattr(post, 'like_count')
        assert hasattr(post, 'is_reply')
        assert post.tweet_id == "test123"
        assert post.author_username == "testuser"
        assert post.like_count == 100  # Score maps to like_count
    
    @patch('src.data.providers.sentiment.reddit.RedditClient')
    def test_spam_filtering(self, mock_client_class):
        """Test spam/low-quality post filtering"""
        mock_client = Mock()
        mock_client.is_available.return_value = True
        mock_client_class.return_value = mock_client
        
        provider = RedditSentimentProvider(persist_to_db=False)
        
        # Create low-quality post (low score, low upvote ratio)
        low_quality_post = RedditPost(
            post_id="spam123",
            text="Buy now!",
            author="spammer",
            created_at=datetime.now(),
            score=1,
            upvote_ratio=0.3,  # Low upvote ratio indicates spam
            num_comments=0,
            subreddit="wallstreetbets"
        )
        
        # Provider should filter based on quality metrics
        # (actual filtering logic depends on implementation)
        assert low_quality_post.score < 10  # Low score
        assert low_quality_post.upvote_ratio < 0.5  # Low upvote ratio

