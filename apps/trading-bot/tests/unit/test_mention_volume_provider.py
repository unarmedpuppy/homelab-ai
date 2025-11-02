"""
Unit Tests for Mention Volume Provider
=======================================

Comprehensive unit tests for MentionVolumeProvider.
"""

import pytest
from unittest.mock import Mock, MagicMock, patch
from datetime import datetime, timedelta
from collections import defaultdict

from src.data.providers.sentiment.mention_volume import (
    MentionVolumeProvider,
    MentionVolume
)
from src.data.providers.sentiment.repository import SentimentRepository


class TestMentionVolumeProvider:
    """Test suite for MentionVolumeProvider"""
    
    @pytest.fixture
    def mock_repository(self):
        """Mock SentimentRepository"""
        repo = Mock(spec=SentimentRepository)
        repo.get_tweets_for_symbol = Mock(return_value=[])
        repo.get_reddit_posts_for_symbol = Mock(return_value=[])
        repo.get_trending_symbols = Mock(return_value=[])
        return repo
    
    @pytest.fixture
    def provider(self, mock_repository):
        """Create MentionVolumeProvider with mocked repository"""
        with patch('src.data.providers.sentiment.mention_volume.SentimentRepository', return_value=mock_repository):
            provider = MentionVolumeProvider(persist_to_db=True)
            provider.repository = mock_repository
            return provider
    
    def test_provider_initialization(self, provider):
        """Test provider initialization"""
        assert provider.repository is not None
        assert provider.config is not None
    
    def test_is_available(self, provider):
        """Test availability check"""
        assert provider.is_available()
        
        provider.persist_to_db = False
        assert not provider.is_available()
    
    def test_get_mention_volume_success(self, provider, mock_repository):
        """Test successful mention volume retrieval"""
        # Mock tweets and Reddit posts
        from src.data.providers.sentiment.models import Tweet
        
        tweets = [
            Tweet(
                tweet_id="1",
                text="$AAPL is great",
                author_id="user1",
                author_username="user1",
                created_at=datetime.now() - timedelta(hours=1),
                symbols_mentioned=["AAPL"]
            ),
            Tweet(
                tweet_id="stocktwits_2",
                text="$AAPL bullish",
                author_id="user2",
                author_username="user2",
                created_at=datetime.now() - timedelta(hours=2),
                symbols_mentioned=["AAPL"]
            )
        ]
        
        from src.data.providers.sentiment.models import RedditPost
        
        reddit_posts = [
            RedditPost(
                post_id="reddit1",
                title="AAPL discussion",
                text="Discussion about AAPL",
                subreddit="stocks",
                author="redditor1",
                created_at=datetime.now() - timedelta(hours=1),
                symbols_mentioned=["AAPL"]
            )
        ]
        
        mock_repository.get_tweets_for_symbol.return_value = tweets
        mock_repository.get_reddit_posts_for_symbol.return_value = reddit_posts
        
        volume = provider.get_mention_volume("AAPL", hours=24)
        
        assert volume is not None
        assert volume.symbol == "AAPL"
        assert volume.twitter_mentions == 1  # One non-stocktwits tweet
        assert volume.stocktwits_mentions == 1
        assert volume.reddit_mentions == 1
        assert volume.total_mentions == 3
    
    def test_get_mention_volume_no_mentions(self, provider, mock_repository):
        """Test mention volume when no mentions found"""
        mock_repository.get_tweets_for_symbol.return_value = []
        mock_repository.get_reddit_posts_for_symbol.return_value = []
        
        volume = provider.get_mention_volume("AAPL", hours=24)
        
        assert volume is None
    
    def test_calculate_volume_trend_up(self, provider):
        """Test volume trend calculation for upward trend"""
        trend = provider._calculate_volume_trend(
            current_mentions=120,
            baseline_avg=100,
            hours=24
        )
        
        assert trend == "up"
    
    def test_calculate_volume_trend_down(self, provider):
        """Test volume trend calculation for downward trend"""
        trend = provider._calculate_volume_trend(
            current_mentions=80,
            baseline_avg=100,
            hours=24
        )
        
        assert trend == "down"
    
    def test_calculate_volume_trend_stable(self, provider):
        """Test volume trend calculation for stable trend"""
        trend = provider._calculate_volume_trend(
            current_mentions=100,
            baseline_avg=100,
            hours=24
        )
        
        assert trend == "stable"
    
    def test_detect_spike(self, provider):
        """Test spike detection"""
        with patch.object(provider.config, 'spike_threshold', 2.0):
            spike_detected, magnitude = provider._detect_spike(
                current_mentions=250,
                baseline_avg=100
            )
            
            assert spike_detected is True
            assert magnitude == 2.5
    
    def test_calculate_momentum(self, provider, mock_repository):
        """Test momentum calculation"""
        # Mock tweets for first and second half
        from src.data.providers.sentiment.models import Tweet
        
        cutoff = datetime.now() - timedelta(hours=12)
        first_half = [
            Tweet(
                tweet_id=f"t{i}",
                text=f"Tweet {i}",
                author_id="user",
                author_username="user",
                created_at=cutoff - timedelta(hours=i),
                symbols_mentioned=["AAPL"]
            )
            for i in range(5)
        ]
        
        second_half = [
            Tweet(
                tweet_id=f"t{i+10}",
                text=f"Tweet {i+10}",
                author_id="user",
                author_username="user",
                created_at=cutoff + timedelta(hours=i),
                symbols_mentioned=["AAPL"]
            )
            for i in range(10)
        ]
        
        # Mock repository to return combined list
        all_tweets = first_half + second_half
        mock_repository.get_tweets_for_symbol.return_value = all_tweets
        mock_repository.get_reddit_posts_for_symbol.return_value = []
        
        momentum = provider._calculate_momentum("AAPL", hours=24)
        
        # Second half has more mentions, so momentum should be positive
        assert momentum > 0
    
    def test_get_volume_trend(self, provider, mock_repository):
        """Test volume trend over time"""
        from src.data.providers.sentiment.models import Tweet
        
        tweets = [
            Tweet(
                tweet_id=f"t{i}",
                text=f"Tweet {i}",
                author_id="user",
                author_username="user",
                created_at=datetime.now() - timedelta(hours=24-i),
                symbols_mentioned=["AAPL"]
            )
            for i in range(24)
        ]
        
        mock_repository.get_tweets_for_symbol.return_value = tweets
        mock_repository.get_reddit_posts_for_symbol.return_value = []
        
        trend = provider.get_volume_trend("AAPL", hours=24, interval_hours=1)
        
        assert len(trend) > 0
        assert all('timestamp' in point for point in trend)
        assert all('mentions' in point for point in trend)
    
    def test_get_trending_by_volume(self, provider, mock_repository):
        """Test trending symbols by volume"""
        mock_repository.get_trending_symbols.return_value = [
            {'symbol': 'AAPL', 'average_sentiment': 0.5, 'last_mentioned': datetime.now()},
            {'symbol': 'MSFT', 'average_sentiment': 0.3, 'last_mentioned': datetime.now()}
        ]
        
        # Mock get_mention_volume to return volume data
        provider.get_mention_volume = Mock(side_effect=lambda s, **kwargs: MentionVolume(
            symbol=s,
            timestamp=datetime.now(),
            total_mentions=100,
            momentum_score=0.5
        ) if s == 'AAPL' else None)
        
        trending = provider.get_trending_by_volume(
            hours=24,
            min_mentions=10,
            min_momentum=0.3,
            limit=10
        )
        
        assert len(trending) > 0

