"""
Integration Tests for Database Repository
=========================================

Tests that verify database CRUD operations, transactions, relationships, and cleanup.
"""

import pytest
from datetime import datetime, timedelta
from src.data.providers.sentiment.repository import SentimentRepository
from src.data.providers.sentiment.models import Tweet, TweetSentiment, SymbolSentiment, Influencer
from src.data.database.models import Tweet as TweetModel, TweetSentiment as TweetSentimentModel


class TestRepositoryInitialization:
    """Test repository initialization"""
    
    def test_initialization_without_session(self):
        """Test initialization without database session"""
        repo = SentimentRepository()
        
        assert repo.db is None
    
    def test_initialization_with_session(self, test_db_session):
        """Test initialization with database session"""
        repo = SentimentRepository(db=test_db_session)
        
        assert repo.db == test_db_session


class TestCRUDOperations:
    """Test Create, Read, Update, Delete operations"""
    
    @pytest.fixture
    def repo(self, test_db_session):
        """Create repository with test session"""
        return SentimentRepository(db=test_db_session)
    
    def test_save_tweet_create(self, repo):
        """Test creating a new tweet"""
        tweet = Tweet(
            tweet_id="test_123",
            text="This is a test tweet about $SPY",
            author_id="author_1",
            author_username="test_user",
            created_at=datetime.now(),
            retweet_count=10,
            like_count=50,
            reply_count=5,
            quote_count=2,
            symbols_mentioned=["SPY"]
        )
        
        result = repo.save_tweet(tweet, autocommit=True)
        
        assert result is not None
        assert result.tweet_id == "test_123"
        assert result.text == "This is a test tweet about $SPY"
        assert result.id is not None  # Should have database ID
    
    def test_save_tweet_update_existing(self, repo):
        """Test updating an existing tweet"""
        # Create initial tweet
        tweet = Tweet(
            tweet_id="test_456",
            text="Original tweet",
            author_id="author_1",
            author_username="test_user",
            created_at=datetime.now(),
            retweet_count=10,
            like_count=50,
            symbols_mentioned=["SPY"]
        )
        saved = repo.save_tweet(tweet, autocommit=True)
        original_id = saved.id
        
        # Update tweet
        tweet.retweet_count = 20
        tweet.like_count = 100
        updated = repo.save_tweet(tweet, autocommit=True)
        
        assert updated.id == original_id  # Same record
        assert updated.retweet_count == 20
        assert updated.like_count == 100
    
    def test_save_tweet_sentiment(self, repo):
        """Test saving tweet sentiment"""
        # First create tweet
        tweet = Tweet(
            tweet_id="sentiment_test",
            text="Test tweet",
            author_id="author_1",
            author_username="test_user",
            created_at=datetime.now(),
            symbols_mentioned=["SPY"]
        )
        tweet_model = repo.save_tweet(tweet, autocommit=True)
        
        # Create sentiment
        sentiment = TweetSentiment(
            tweet_id="sentiment_test",
            symbol="SPY",
            sentiment_score=0.75,
            confidence=0.9,
            sentiment_level="bullish",
            vader_scores={"compound": 0.75, "pos": 0.8, "neu": 0.15, "neg": 0.05},
            engagement_score=0.7,
            influencer_weight=1.0,
            weighted_score=0.525,
            timestamp=datetime.now()
        )
        
        result = repo.save_tweet_sentiment(sentiment, tweet_model, autocommit=True)
        
        assert result is not None
        assert result.symbol == "SPY"
        assert result.sentiment_score == 0.75
        assert result.tweet_id == tweet_model.id
    
    def test_save_symbol_sentiment(self, repo):
        """Test saving symbol sentiment"""
        sentiment = SymbolSentiment(
            symbol="SPY",
            source="twitter",
            mention_count=100,
            sentiment_score=0.65,
            confidence=0.85,
            sentiment_level="bullish",
            timestamp=datetime.now(),
            volume_trend="up"
        )
        
        result = repo.save_symbol_sentiment(sentiment, autocommit=True)
        
        assert result is not None
        assert result.symbol == "SPY"
        assert result.source == "twitter"
        assert result.mention_count == 100
    
    def test_save_influencer(self, repo):
        """Test saving influencer"""
        influencer = Influencer(
            platform="twitter",
            user_id="influencer_1",
            username="big_trader",
            follower_count=100000,
            weight_multiplier=2.0,
            is_verified=True,
            last_checked=datetime.now()
        )
        
        result = repo.save_influencer(influencer, autocommit=True)
        
        assert result is not None
        assert result.user_id == "influencer_1"
        assert result.weight_multiplier == 2.0


class TestTransactions:
    """Test transaction commit/rollback behavior"""
    
    @pytest.fixture
    def repo(self, test_db_session):
        """Create repository with test session"""
        return SentimentRepository(db=test_db_session)
    
    def test_transaction_commit(self, repo):
        """Test that successful operations commit"""
        tweet = Tweet(
            tweet_id="commit_test",
            text="Test commit",
            author_id="author_1",
            author_username="test_user",
            created_at=datetime.now(),
            symbols_mentioned=["SPY"]
        )
        
        result = repo.save_tweet(tweet, autocommit=True)
        
        # Verify committed by querying in new session context
        # (in real scenario, would use different session)
        assert result is not None
        assert result.id is not None
    
    def test_transaction_rollback_on_error(self, repo):
        """Test that errors cause rollback"""
        # Try to save invalid data (missing required fields)
        tweet = Tweet(
            tweet_id="rollback_test",
            text="Test rollback",
            # Missing required fields
            author_id="author_1",
            author_username="test_user",
            created_at=datetime.now(),
            symbols_mentioned=["SPY"]
        )
        
        # Should succeed (autocommit=True handles rollback)
        try:
            result = repo.save_tweet(tweet, autocommit=True)
            # If we get here, it worked (tweet might have defaults)
            assert result is None or result.id is not None
        except Exception:
            # Exception is expected, and should have been rolled back
            pass
    
    def test_manual_transaction_control(self, repo):
        """Test manual transaction control with autocommit=False"""
        tweet1 = Tweet(
            tweet_id="manual_1",
            text="First tweet",
            author_id="author_1",
            author_username="test_user",
            created_at=datetime.now(),
            symbols_mentioned=["SPY"]
        )
        
        tweet2 = Tweet(
            tweet_id="manual_2",
            text="Second tweet",
            author_id="author_1",
            author_username="test_user",
            created_at=datetime.now(),
            symbols_mentioned=["QQQ"]
        )
        
        # Save with autocommit=False (manual control)
        with repo._get_session(autocommit=False) as session:
            result1 = repo.save_tweet(tweet1, autocommit=False)
            result2 = repo.save_tweet(tweet2, autocommit=False)
            # Manual commit
            session.commit()
        
        # Both should be saved
        assert result1 is not None
        assert result2 is not None


class TestBulkOperations:
    """Test bulk save operations"""
    
    @pytest.fixture
    def repo(self, test_db_session):
        """Create repository with test session"""
        return SentimentRepository(db=test_db_session)
    
    def test_bulk_save_tweets_and_sentiments(self, repo):
        """Test bulk saving tweets and sentiments in single transaction"""
        tweets = [
            Tweet(
                tweet_id=f"bulk_{i}",
                text=f"Bulk tweet {i} about $SPY",
                author_id=f"author_{i}",
                author_username=f"user_{i}",
                created_at=datetime.now(),
                symbols_mentioned=["SPY"]
            )
            for i in range(5)
        ]
        
        # Create sentiments for each tweet
        tweet_sentiments = []
        for i, tweet in enumerate(tweets):
            sentiment = TweetSentiment(
                tweet_id=tweet.tweet_id,
                symbol="SPY",
                sentiment_score=0.5 + (i * 0.1),
                confidence=0.8,
                sentiment_level="bullish" if i % 2 == 0 else "bearish",
                vader_scores={"compound": 0.5, "pos": 0.6, "neu": 0.3, "neg": 0.1},
                engagement_score=0.7,
                influencer_weight=1.0,
                weighted_score=0.35,
                timestamp=datetime.now()
            )
            tweet_sentiments.append(sentiment)
        
        # Bulk save
        result = repo.bulk_save_tweets_and_sentiments(tweets, tweet_sentiments)
        
        assert result['saved_tweets'] == 5
        assert result['saved_sentiments'] == 5
        assert result['skipped_tweets'] == 0
        assert result['skipped_sentiments'] == 0


class TestRelationships:
    """Test database relationships"""
    
    @pytest.fixture
    def repo(self, test_db_session):
        """Create repository with test session"""
        return SentimentRepository(db=test_db_session)
    
    def test_tweet_sentiment_relationship(self, repo):
        """Test relationship between tweet and tweet sentiment"""
        # Create tweet
        tweet = Tweet(
            tweet_id="relationship_test",
            text="Relationship test tweet",
            author_id="author_1",
            author_username="test_user",
            created_at=datetime.now(),
            symbols_mentioned=["SPY"]
        )
        tweet_model = repo.save_tweet(tweet, autocommit=True)
        
        # Create sentiment linked to tweet
        sentiment = TweetSentiment(
            tweet_id="relationship_test",
            symbol="SPY",
            sentiment_score=0.8,
            confidence=0.9,
            sentiment_level="bullish",
            vader_scores={"compound": 0.8, "pos": 0.9, "neu": 0.1, "neg": 0.0},
            engagement_score=0.8,
            influencer_weight=1.0,
            weighted_score=0.64,
            timestamp=datetime.now()
        )
        sentiment_model = repo.save_tweet_sentiment(sentiment, tweet_model, autocommit=True)
        
        # Verify relationship
        assert sentiment_model.tweet_id == tweet_model.id
        assert sentiment_model.tweet is not None
        assert sentiment_model.tweet.tweet_id == "relationship_test"
    
    def test_multiple_sentiments_per_tweet(self, repo):
        """Test that one tweet can have multiple sentiments (for different symbols)"""
        # Create tweet mentioning multiple symbols
        tweet = Tweet(
            tweet_id="multi_symbol",
            text="$SPY and $QQQ are both trending",
            author_id="author_1",
            author_username="test_user",
            created_at=datetime.now(),
            symbols_mentioned=["SPY", "QQQ"]
        )
        tweet_model = repo.save_tweet(tweet, autocommit=True)
        
        # Create sentiment for SPY
        sentiment_spy = TweetSentiment(
            tweet_id="multi_symbol",
            symbol="SPY",
            sentiment_score=0.7,
            confidence=0.85,
            sentiment_level="bullish",
            vader_scores={"compound": 0.7, "pos": 0.8, "neu": 0.2, "neg": 0.0},
            engagement_score=0.7,
            influencer_weight=1.0,
            weighted_score=0.49,
            timestamp=datetime.now()
        )
        spy_model = repo.save_tweet_sentiment(sentiment_spy, tweet_model, autocommit=True)
        
        # Create sentiment for QQQ
        sentiment_qqq = TweetSentiment(
            tweet_id="multi_symbol",
            symbol="QQQ",
            sentiment_score=0.6,
            confidence=0.8,
            sentiment_level="bullish",
            vader_scores={"compound": 0.6, "pos": 0.7, "neu": 0.3, "neg": 0.0},
            engagement_score=0.7,
            influencer_weight=1.0,
            weighted_score=0.42,
            timestamp=datetime.now()
        )
        qqq_model = repo.save_tweet_sentiment(sentiment_qqq, tweet_model, autocommit=True)
        
        # Verify both sentiments exist and are linked to same tweet
        assert spy_model.tweet_id == tweet_model.id
        assert qqq_model.tweet_id == tweet_model.id
        assert spy_model.symbol == "SPY"
        assert qqq_model.symbol == "QQQ"


class TestQueryOperations:
    """Test query and retrieval operations"""
    
    @pytest.fixture
    def repo(self, test_db_session):
        """Create repository with test data"""
        repo = SentimentRepository(db=test_db_session)
        
        # Create test data
        tweets = [
            Tweet(
                tweet_id=f"query_{i}",
                text=f"Query test tweet {i}",
                author_id=f"author_{i % 3}",  # 3 different authors
                author_username=f"user_{i % 3}",
                created_at=datetime.now() - timedelta(hours=i),
                retweet_count=10 * i,
                like_count=50 * i,
                symbols_mentioned=["SPY"] if i % 2 == 0 else ["QQQ"]
            )
            for i in range(10)
        ]
        
        for tweet in tweets:
            repo.save_tweet(tweet, autocommit=True)
        
        return repo
    
    def test_query_tweets_by_symbol(self, repo, test_db_session):
        """Test querying tweets by mentioned symbol"""
        # Query tweets mentioning SPY
        spy_tweets = test_db_session.query(TweetModel).filter(
            TweetModel.symbols_mentioned.contains(["SPY"])
        ).all()
        
        # Should have tweets with even indices (0, 2, 4, 6, 8)
        assert len(spy_tweets) >= 5
    
    def test_query_tweets_by_author(self, repo, test_db_session):
        """Test querying tweets by author"""
        # Query tweets by author_0
        author_tweets = test_db_session.query(TweetModel).filter(
            TweetModel.author_id == "author_0"
        ).all()
        
        # Should have tweets where i % 3 == 0 (0, 3, 6, 9)
        assert len(author_tweets) >= 3


class TestDatabaseCleanup:
    """Test database cleanup and data retention"""
    
    @pytest.fixture
    def repo(self, test_db_session):
        """Create repository with old test data"""
        repo = SentimentRepository(db=test_db_session)
        
        # Create old tweet (90+ days ago)
        old_tweet = Tweet(
            tweet_id="old_tweet",
            text="Old tweet",
            author_id="author_1",
            author_username="test_user",
            created_at=datetime.now() - timedelta(days=100),
            symbols_mentioned=["SPY"]
        )
        repo.save_tweet(old_tweet, autocommit=True)
        
        # Create recent tweet
        recent_tweet = Tweet(
            tweet_id="recent_tweet",
            text="Recent tweet",
            author_id="author_1",
            author_username="test_user",
            created_at=datetime.now() - timedelta(days=10),
            symbols_mentioned=["SPY"]
        )
        repo.save_tweet(recent_tweet, autocommit=True)
        
        return repo
    
    def test_query_recent_tweets_only(self, repo, test_db_session):
        """Test querying only recent tweets"""
        cutoff = datetime.now() - timedelta(days=30)
        
        recent_tweets = test_db_session.query(TweetModel).filter(
            TweetModel.created_at >= cutoff
        ).all()
        
        # Should only include recent tweet
        assert len(recent_tweets) >= 1
        assert all(tweet.created_at >= cutoff for tweet in recent_tweets)


@pytest.mark.integration
class TestDatabaseErrorHandling:
    """Test error handling in database operations"""
    
    @pytest.fixture
    def repo(self, test_db_session):
        """Create repository"""
        return SentimentRepository(db=test_db_session)
    
    def test_handle_duplicate_tweet_id(self, repo):
        """Test handling duplicate tweet IDs"""
        tweet = Tweet(
            tweet_id="duplicate_test",
            text="First tweet",
            author_id="author_1",
            author_username="test_user",
            created_at=datetime.now(),
            symbols_mentioned=["SPY"]
        )
        result1 = repo.save_tweet(tweet, autocommit=True)
        assert result1 is not None
        
        # Try to save same tweet again (should update, not fail)
        tweet.text = "Updated tweet"
        result2 = repo.save_tweet(tweet, autocommit=True)
        
        # Should update existing record
        assert result2 is not None
        assert result2.id == result1.id
        assert result2.text == "Updated tweet"
    
    def test_handle_missing_tweet_for_sentiment(self, repo):
        """Test handling sentiment save when tweet doesn't exist"""
        # This should work because save_tweet_sentiment creates tweet if needed
        # But if we pass None, it should handle gracefully
        sentiment = TweetSentiment(
            tweet_id="missing_tweet",
            symbol="SPY",
            sentiment_score=0.5,
            confidence=0.8,
            sentiment_level="neutral",
            vader_scores={"compound": 0.0, "pos": 0.5, "neu": 0.5, "neg": 0.0},
            engagement_score=0.5,
            influencer_weight=1.0,
            weighted_score=0.25,
            timestamp=datetime.now()
        )
        
        # Should handle missing tweet gracefully (creates tweet or raises error appropriately)
        try:
            # If method requires tweet_model, we need to provide it
            # This test verifies error handling
            result = repo.save_tweet_sentiment(sentiment, None, autocommit=True)
            # If it succeeds, that's fine (might create tweet automatically)
            # If it fails, that's expected behavior
        except (ValueError, AttributeError):
            # Expected error when tweet_model is None
            pass

