"""
Sentiment Data Repository
=========================

Repository layer for persisting sentiment data to the database.
"""

import json
import logging
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from contextlib import contextmanager
from sqlalchemy.orm import Session
from sqlalchemy import and_, desc, func

from ...database import get_db, SessionLocal
from ...database.models import (
    Tweet as TweetModel,
    TweetSentiment as TweetSentimentModel,
    SymbolSentiment as SymbolSentimentModel,
    Influencer as InfluencerModel,
    RedditPost as RedditPostModel,
    RedditSentiment as RedditSentimentModel,
    AggregatedSentiment as AggregatedSentimentModel,
    ConfluenceScore as ConfluenceScoreModel
)
from .models import Tweet, TweetSentiment, SymbolSentiment, Influencer

logger = logging.getLogger(__name__)


class SentimentRepository:
    """
    Repository for sentiment data persistence
    """
    
    def __init__(self, db: Optional[Session] = None):
        """
        Initialize repository
        
        Args:
            db: Database session (if None, will create new session)
        """
        self.db = db
    
    @contextmanager
    def _get_session(self, autocommit: bool = True):
        """
        Get database session as context manager (thread-safe)
        
        Args:
            autocommit: If True, automatically commit on success and rollback on error.
                       If False, caller must handle commit/rollback manually.
        
        Yields:
            Session: Database session
            
        Usage:
            with repository._get_session(autocommit=True) as session:
                # Use session here - auto-commits on success
        """
        if self.db:
            # External session - don't close it, don't auto-commit
            yield self.db
        else:
            # Create new session - automatically closed
            session = SessionLocal()
            try:
                yield session
                if autocommit:
                    session.commit()
            except Exception:
                if autocommit:
                    session.rollback()
                raise
            finally:
                session.close()
    
    def _get_session_legacy(self) -> Session:
        """
        Legacy method for backwards compatibility.
        Use _get_session() context manager instead.
        """
        if self.db:
            return self.db
        return SessionLocal()
    
    def _close_session(self, session: Session, created: bool):
        """
        Close session if we created it (legacy method).
        Use _get_session() context manager instead.
        """
        if created and not self.db:
            session.close()
    
    def save_tweet(self, tweet: Tweet, autocommit: bool = True) -> Optional[TweetModel]:
        """
        Save or update a tweet in the database
        
        Args:
            tweet: Tweet dataclass object
            autocommit: If True, commit immediately. If False, caller must commit.
            
        Returns:
            TweetModel instance or None
        """
        with self._get_session(autocommit=autocommit) as session:
            try:
                # Check if tweet already exists
                existing = session.query(TweetModel).filter(
                    TweetModel.tweet_id == tweet.tweet_id
                ).first()
                
                if existing:
                    # Update existing tweet
                    existing.text = tweet.text
                    existing.author_id = tweet.author_id
                    existing.author_username = tweet.author_username
                    existing.created_at = tweet.created_at
                    existing.like_count = tweet.like_count
                    existing.retweet_count = tweet.retweet_count
                    existing.reply_count = tweet.reply_count
                    existing.quote_count = tweet.quote_count
                    existing.is_retweet = tweet.is_retweet
                    existing.is_quote = tweet.is_quote
                    existing.is_reply = tweet.is_reply
                    existing.language = tweet.language
                    existing.symbols_mentioned = json.dumps(tweet.symbols_mentioned) if tweet.symbols_mentioned else None
                    existing.raw_data = json.dumps(tweet.raw_data) if tweet.raw_data else None
                    
                    if autocommit and not self.db:
                        session.commit()
                    return existing
                else:
                    # Create new tweet
                    db_tweet = TweetModel(
                        tweet_id=tweet.tweet_id,
                        text=tweet.text,
                        author_id=tweet.author_id,
                        author_username=tweet.author_username,
                        created_at=tweet.created_at,
                        like_count=tweet.like_count,
                        retweet_count=tweet.retweet_count,
                        reply_count=tweet.reply_count,
                        quote_count=tweet.quote_count,
                        is_retweet=tweet.is_retweet,
                        is_quote=tweet.is_quote,
                        is_reply=tweet.is_reply,
                        language=tweet.language,
                        symbols_mentioned=json.dumps(tweet.symbols_mentioned) if tweet.symbols_mentioned else None,
                        raw_data=json.dumps(tweet.raw_data) if tweet.raw_data else None
                    )
                    
                    session.add(db_tweet)
                    if autocommit and not self.db:
                        session.commit()
                        session.refresh(db_tweet)
                    return db_tweet
                    
            except Exception as e:
                logger.error(
                    f"Error saving tweet {tweet.tweet_id}: {e}",
                    exc_info=True,
                    extra={
                        'tweet_id': tweet.tweet_id,
                        'symbol': tweet.symbols_mentioned[0] if tweet.symbols_mentioned else None,
                        'operation': 'save_tweet'
                    }
                )
                if not self.db:
                    session.rollback()
                raise
    
    def save_tweet_sentiment(self, tweet_sentiment: TweetSentiment, tweet_model: TweetModel, autocommit: bool = True) -> Optional[TweetSentimentModel]:
        """
        Save tweet sentiment analysis result
        
        Args:
            tweet_sentiment: TweetSentiment dataclass
            tweet_model: TweetModel instance (from database)
            autocommit: If True, commit immediately. If False, caller must commit.
            
        Returns:
            TweetSentimentModel instance or None
        """
        with self._get_session(autocommit=autocommit) as session:
            try:
                # Check if sentiment already exists for this tweet+symbol
                existing = session.query(TweetSentimentModel).filter(
                    and_(
                        TweetSentimentModel.tweet_id == tweet_model.id,
                        TweetSentimentModel.symbol == tweet_sentiment.symbol
                    )
                ).first()
                
                if existing:
                    # Update existing sentiment
                    existing.sentiment_score = tweet_sentiment.sentiment_score
                    existing.confidence = tweet_sentiment.confidence
                    existing.sentiment_level = tweet_sentiment.sentiment_level.value
                    existing.vader_compound = tweet_sentiment.vader_scores.get('compound')
                    existing.vader_pos = tweet_sentiment.vader_scores.get('pos')
                    existing.vader_neu = tweet_sentiment.vader_scores.get('neu')
                    existing.vader_neg = tweet_sentiment.vader_scores.get('neg')
                    existing.engagement_score = tweet_sentiment.engagement_score
                    existing.influencer_weight = tweet_sentiment.influencer_weight
                    existing.weighted_score = tweet_sentiment.weighted_score
                    existing.analyzed_at = tweet_sentiment.timestamp
                    
                    if autocommit and not self.db:
                        session.commit()
                    return existing
                else:
                    # Create new sentiment record
                    db_sentiment = TweetSentimentModel(
                        tweet_id=tweet_model.id,
                        symbol=tweet_sentiment.symbol,
                        sentiment_score=tweet_sentiment.sentiment_score,
                        confidence=tweet_sentiment.confidence,
                        sentiment_level=tweet_sentiment.sentiment_level.value,
                        vader_compound=tweet_sentiment.vader_scores.get('compound'),
                        vader_pos=tweet_sentiment.vader_scores.get('pos'),
                        vader_neu=tweet_sentiment.vader_scores.get('neu'),
                        vader_neg=tweet_sentiment.vader_scores.get('neg'),
                        engagement_score=tweet_sentiment.engagement_score,
                        influencer_weight=tweet_sentiment.influencer_weight,
                        weighted_score=tweet_sentiment.weighted_score,
                        analyzed_at=tweet_sentiment.timestamp
                    )
                    
                    session.add(db_sentiment)
                    if autocommit and not self.db:
                        session.commit()
                        session.refresh(db_sentiment)
                    return db_sentiment
                    
            except Exception as e:
                logger.error(
                    f"Error saving tweet sentiment for tweet_id={tweet_model.id}, symbol={tweet_sentiment.symbol}: {e}",
                    exc_info=True,
                    extra={
                        'tweet_id': tweet_model.id,
                        'symbol': tweet_sentiment.symbol,
                        'operation': 'save_tweet_sentiment'
                    }
                )
                if not self.db:
                    session.rollback()
                raise
    
    def save_symbol_sentiment(self, symbol_sentiment: SymbolSentiment, autocommit: bool = True) -> Optional[SymbolSentimentModel]:
        """
        Save aggregated symbol sentiment
        
        Args:
            symbol_sentiment: SymbolSentiment dataclass
            autocommit: If True, commit immediately. If False, caller must commit.
            
        Returns:
            SymbolSentimentModel instance or None
        """
        with self._get_session(autocommit=autocommit) as session:
            try:
                db_sentiment = SymbolSentimentModel(
                    symbol=symbol_sentiment.symbol,
                    timestamp=symbol_sentiment.timestamp,
                    mention_count=symbol_sentiment.mention_count,
                    average_sentiment=symbol_sentiment.average_sentiment,
                    weighted_sentiment=symbol_sentiment.weighted_sentiment,
                    influencer_sentiment=symbol_sentiment.influencer_sentiment,
                    engagement_score=symbol_sentiment.engagement_score,
                    sentiment_level=symbol_sentiment.sentiment_level.value,
                    confidence=symbol_sentiment.confidence,
                    volume_trend=symbol_sentiment.volume_trend,
                    tweet_ids=json.dumps([ts.tweet_id for ts in symbol_sentiment.tweets[:50]]) if symbol_sentiment.tweets else None
                )
                
                session.add(db_sentiment)
                if autocommit and not self.db:
                    session.commit()
                    session.refresh(db_sentiment)
                return db_sentiment
                
            except Exception as e:
                logger.error(
                    f"Error saving symbol sentiment for symbol={symbol_sentiment.symbol}: {e}",
                    exc_info=True,
                    extra={
                        'symbol': symbol_sentiment.symbol,
                        'timestamp': symbol_sentiment.timestamp.isoformat(),
                        'operation': 'save_symbol_sentiment'
                    }
                )
                if not self.db:
                    session.rollback()
                raise
    
    def save_influencer(self, influencer: Influencer, autocommit: bool = True) -> Optional[InfluencerModel]:
        """
        Save or update influencer information
        
        Args:
            influencer: Influencer dataclass
            autocommit: If True, commit immediately. If False, caller must commit.
            
        Returns:
            InfluencerModel instance or None
        """
        with self._get_session(autocommit=autocommit) as session:
            try:
                # Check if influencer exists
                existing = session.query(InfluencerModel).filter(
                    InfluencerModel.user_id == influencer.user_id
                ).first()
                
                if existing:
                    # Update existing
                    existing.username = influencer.username
                    existing.display_name = influencer.display_name
                    existing.follower_count = influencer.follower_count
                    existing.following_count = influencer.following_count
                    existing.tweet_count = influencer.tweet_count
                    existing.is_verified = influencer.is_verified
                    existing.is_protected = influencer.is_protected
                    existing.category = influencer.category
                    existing.weight_multiplier = influencer.weight_multiplier
                    existing.is_active = influencer.is_active
                    existing.updated_at = datetime.now()
                    
                    if autocommit and not self.db:
                        session.commit()
                    return existing
                else:
                    # Create new
                    db_influencer = InfluencerModel(
                        user_id=influencer.user_id,
                        username=influencer.username,
                        display_name=influencer.display_name,
                        follower_count=influencer.follower_count,
                        following_count=influencer.following_count,
                        tweet_count=influencer.tweet_count,
                        is_verified=influencer.is_verified,
                        is_protected=influencer.is_protected,
                        category=influencer.category,
                        weight_multiplier=influencer.weight_multiplier,
                        is_active=influencer.is_active,
                        added_at=influencer.added_at
                    )
                    
                    session.add(db_influencer)
                    if autocommit and not self.db:
                        session.commit()
                        session.refresh(db_influencer)
                    return db_influencer
                    
            except Exception as e:
                logger.error(
                    f"Error saving influencer user_id={influencer.user_id}, username={influencer.username}: {e}",
                    exc_info=True,
                    extra={
                        'user_id': influencer.user_id,
                        'username': influencer.username,
                        'operation': 'save_influencer'
                    }
                )
                if not self.db:
                    session.rollback()
                raise
    
    def bulk_save_tweets_and_sentiments(
        self,
        tweets: List[Tweet],
        tweet_sentiments: List[TweetSentiment],
        tweet_models_mapping: Optional[Dict[str, TweetModel]] = None
    ) -> Dict[str, Any]:
        """
        Batch save tweets and their sentiments in a single transaction (CRITICAL FIX #3)
        
        Args:
            tweets: List of tweets to save
            tweet_sentiments: List of sentiments (must match tweets)
            tweet_models_mapping: Optional mapping of tweet_id -> TweetModel for sentiments
            
        Returns:
            Dict with counts of saved records
        """
        saved_tweets = 0
        saved_sentiments = 0
        tweet_id_to_model = tweet_models_mapping or {}
        
        with self._get_session(autocommit=False) as session:
            try:
                # Save all tweets first
                for tweet in tweets:
                    existing = session.query(TweetModel).filter(
                        TweetModel.tweet_id == tweet.tweet_id
                    ).first()
                    
                    if existing:
                        # Update existing
                        existing.text = tweet.text
                        existing.author_id = tweet.author_id
                        existing.author_username = tweet.author_username
                        existing.created_at = tweet.created_at
                        existing.like_count = tweet.like_count
                        existing.retweet_count = tweet.retweet_count
                        existing.reply_count = tweet.reply_count
                        existing.quote_count = tweet.quote_count
                        existing.is_retweet = tweet.is_retweet
                        existing.is_quote = tweet.is_quote
                        existing.is_reply = tweet.is_reply
                        existing.language = tweet.language
                        existing.symbols_mentioned = json.dumps(tweet.symbols_mentioned) if tweet.symbols_mentioned else None
                        existing.raw_data = json.dumps(tweet.raw_data) if tweet.raw_data else None
                        tweet_id_to_model[tweet.tweet_id] = existing
                    else:
                        # Create new
                        db_tweet = TweetModel(
                            tweet_id=tweet.tweet_id,
                            text=tweet.text,
                            author_id=tweet.author_id,
                            author_username=tweet.author_username,
                            created_at=tweet.created_at,
                            like_count=tweet.like_count,
                            retweet_count=tweet.retweet_count,
                            reply_count=tweet.reply_count,
                            quote_count=tweet.quote_count,
                            is_retweet=tweet.is_retweet,
                            is_quote=tweet.is_quote,
                            is_reply=tweet.is_reply,
                            language=tweet.language,
                            symbols_mentioned=json.dumps(tweet.symbols_mentioned) if tweet.symbols_mentioned else None,
                            raw_data=json.dumps(tweet.raw_data) if tweet.raw_data else None
                        )
                        session.add(db_tweet)
                        session.flush()  # Flush to get IDs
                        tweet_id_to_model[tweet.tweet_id] = db_tweet
                        saved_tweets += 1
                
                # Save all sentiments
                for tweet_sentiment in tweet_sentiments:
                    # Get tweet model from mapping
                    tweet_model = tweet_id_to_model.get(tweet_sentiment.tweet_id)
                    if not tweet_model:
                        logger.warning(f"No tweet model found for sentiment tweet_id={tweet_sentiment.tweet_id}")
                        continue
                    
                    # Check if sentiment exists
                    existing_sentiment = session.query(TweetSentimentModel).filter(
                        and_(
                            TweetSentimentModel.tweet_id == tweet_model.id,
                            TweetSentimentModel.symbol == tweet_sentiment.symbol
                        )
                    ).first()
                    
                    if existing_sentiment:
                        # Update existing
                        existing_sentiment.sentiment_score = tweet_sentiment.sentiment_score
                        existing_sentiment.confidence = tweet_sentiment.confidence
                        existing_sentiment.sentiment_level = tweet_sentiment.sentiment_level.value
                        existing_sentiment.vader_compound = tweet_sentiment.vader_scores.get('compound')
                        existing_sentiment.vader_pos = tweet_sentiment.vader_scores.get('pos')
                        existing_sentiment.vader_neu = tweet_sentiment.vader_scores.get('neu')
                        existing_sentiment.vader_neg = tweet_sentiment.vader_scores.get('neg')
                        existing_sentiment.engagement_score = tweet_sentiment.engagement_score
                        existing_sentiment.influencer_weight = tweet_sentiment.influencer_weight
                        existing_sentiment.weighted_score = tweet_sentiment.weighted_score
                        existing_sentiment.analyzed_at = tweet_sentiment.timestamp
                    else:
                        # Create new
                        db_sentiment = TweetSentimentModel(
                            tweet_id=tweet_model.id,
                            symbol=tweet_sentiment.symbol,
                            sentiment_score=tweet_sentiment.sentiment_score,
                            confidence=tweet_sentiment.confidence,
                            sentiment_level=tweet_sentiment.sentiment_level.value,
                            vader_compound=tweet_sentiment.vader_scores.get('compound'),
                            vader_pos=tweet_sentiment.vader_scores.get('pos'),
                            vader_neu=tweet_sentiment.vader_scores.get('neu'),
                            vader_neg=tweet_sentiment.vader_scores.get('neg'),
                            engagement_score=tweet_sentiment.engagement_score,
                            influencer_weight=tweet_sentiment.influencer_weight,
                            weighted_score=tweet_sentiment.weighted_score,
                            analyzed_at=tweet_sentiment.timestamp
                        )
                        session.add(db_sentiment)
                        saved_sentiments += 1
                
                # Commit all changes atomically
                session.commit()
                logger.info(f"Bulk saved {saved_tweets} tweets and {saved_sentiments} sentiments in single transaction")
                
                return {
                    'tweets_saved': saved_tweets,
                    'sentiments_saved': saved_sentiments,
                    'tweet_models': tweet_id_to_model
                }
                
            except Exception as e:
                logger.error(
                    f"Error in bulk save operation: {e}",
                    exc_info=True,
                    extra={
                        'tweet_count': len(tweets),
                        'sentiment_count': len(tweet_sentiments),
                        'operation': 'bulk_save_tweets_and_sentiments'
                    }
                )
                if not self.db:
                    session.rollback()
                raise
    
    def get_recent_sentiment(
        self, 
        symbol: str, 
        hours: int = 24,
        limit: int = 100
    ) -> List[SymbolSentimentModel]:
        """
        Get recent sentiment data for a symbol
        
        Args:
            symbol: Stock symbol
            hours: Hours of historical data to retrieve
            limit: Maximum number of records to return
            
        Returns:
            List of SymbolSentimentModel instances
        """
        with self._get_session(autocommit=False) as session:  # Read-only, no commit needed
            try:
                cutoff_time = datetime.now() - timedelta(hours=hours)
                
                results = session.query(SymbolSentimentModel).filter(
                    and_(
                        SymbolSentimentModel.symbol == symbol.upper(),
                        SymbolSentimentModel.timestamp >= cutoff_time
                    )
                ).order_by(desc(SymbolSentimentModel.timestamp)).limit(limit).all()
                
                return results
            except Exception as e:
                logger.error(
                    f"Error getting recent sentiment for symbol={symbol}, hours={hours}: {e}",
                    exc_info=True,
                    extra={
                        'symbol': symbol,
                        'hours': hours,
                        'limit': limit,
                        'operation': 'get_recent_sentiment'
                    }
                )
                return []
    
    def get_tweets_for_symbol(
        self,
        symbol: str,
        hours: int = 24,
        limit: int = 100
    ) -> List[TweetModel]:
        """
        Get tweets mentioning a symbol
        
        Args:
            symbol: Stock symbol
            hours: Hours of historical data
            limit: Maximum number of tweets
            
        Returns:
            List of TweetModel instances
        """
        with self._get_session(autocommit=False) as session:  # Read-only
            try:
                cutoff_time = datetime.now() - timedelta(hours=hours)
                
                # Query tweets that mention the symbol
                results = session.query(TweetModel).filter(
                    and_(
                        TweetModel.created_at >= cutoff_time,
                        TweetModel.symbols_mentioned.contains(f'"{symbol.upper()}"')
                    )
                ).order_by(desc(TweetModel.created_at)).limit(limit).all()
                
                return results
            except Exception as e:
                logger.error(
                    f"Error getting tweets for symbol={symbol}, hours={hours}: {e}",
                    exc_info=True,
                    extra={
                        'symbol': symbol,
                        'hours': hours,
                        'limit': limit,
                        'operation': 'get_tweets_for_symbol'
                    }
                )
                return []
    
    def cleanup_old_data(self, days: int = 90) -> int:
        """
        Clean up old sentiment data
        
        Args:
            days: Number of days of data to keep
            
        Returns:
            Number of records deleted
        """
        with self._get_session(autocommit=False) as session:
            try:
                cutoff_time = datetime.now() - timedelta(days=days)
                deleted_count = 0
                
                # Delete old symbol sentiments
                deleted_count += session.query(SymbolSentimentModel).filter(
                    SymbolSentimentModel.timestamp < cutoff_time
                ).delete(synchronize_session=False)
                
                # Delete old tweet sentiments
                deleted_count += session.query(TweetSentimentModel).filter(
                    TweetSentimentModel.analyzed_at < cutoff_time
                ).delete(synchronize_session=False)
                
                # Delete old tweets (only if no sentiments reference them)
                old_tweets = session.query(TweetModel).filter(
                    TweetModel.created_at < cutoff_time
                ).all()
                
                for tweet in old_tweets:
                    # Check if any sentiments reference this tweet
                    has_sentiments = session.query(TweetSentimentModel).filter(
                        TweetSentimentModel.tweet_id == tweet.id
                    ).first() is not None
                    
                    if not has_sentiments:
                        session.delete(tweet)
                        deleted_count += 1
                
                session.commit()
                logger.info(f"Cleaned up {deleted_count} old sentiment records")
                return deleted_count
                
            except Exception as e:
                logger.error(
                    f"Error cleaning up old data: {e}",
                    exc_info=True,
                    extra={
                        'days': days,
                        'operation': 'cleanup_old_data'
                    }
                )
                if not self.db:
                    session.rollback()
                return 0
    
    def get_influencers(self, active_only: bool = True) -> List[InfluencerModel]:
        """
        Get all influencers
        
        Args:
            active_only: Only return active influencers
            
        Returns:
            List of InfluencerModel instances
        """
        with self._get_session(autocommit=False) as session:  # Read-only
            try:
                query = session.query(InfluencerModel)
                if active_only:
                    query = query.filter(InfluencerModel.is_active == True)
                return query.all()
            except Exception as e:
                logger.error(
                    f"Error getting influencers: {e}",
                    exc_info=True,
                    extra={
                        'active_only': active_only,
                        'operation': 'get_influencers'
                    }
                )
                return []
    
    def get_trending_symbols(
        self,
        hours: int = 24,
        min_mentions: int = 5,
        limit: int = 20
    ) -> List[Dict[str, Any]]:
        """
        Get trending symbols based on mention counts
        
        Args:
            hours: Hours of historical data to analyze
            min_mentions: Minimum mentions to be considered trending
            limit: Maximum number of symbols to return
            
        Returns:
            List of trending symbols with mention counts and sentiment
        """
        with self._get_session(autocommit=False) as session:  # Read-only
            try:
                cutoff_time = datetime.now() - timedelta(hours=hours)
                
                # Aggregate mentions by symbol
                results = session.query(
                    SymbolSentimentModel.symbol,
                    func.count(SymbolSentimentModel.id).label('mention_count'),
                    func.avg(SymbolSentimentModel.weighted_sentiment).label('avg_sentiment')
                ).filter(
                    SymbolSentimentModel.timestamp >= cutoff_time
                ).group_by(
                    SymbolSentimentModel.symbol
                ).having(
                    func.count(SymbolSentimentModel.id) >= min_mentions
                ).order_by(
                    desc('mention_count')
                ).limit(limit).all()
                
                trending = [
                    {
                        'symbol': row.symbol,
                        'mentions': row.mention_count,
                        'average_sentiment': float(row.avg_sentiment) if row.avg_sentiment else 0.0
                    }
                    for row in results
                ]
                
                return trending
            except Exception as e:
                logger.error(
                    f"Error getting trending symbols: {e}",
                    exc_info=True,
                    extra={
                        'hours': hours,
                        'min_mentions': min_mentions,
                        'limit': limit,
                        'operation': 'get_trending_symbols'
                    }
                )
                return []
