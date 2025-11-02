"""
Sentiment API Routes
====================

API endpoints for sentiment data from various sources (Twitter, Reddit, etc.).
"""

from fastapi import APIRouter, HTTPException, Query, Body, Depends
from typing import List, Optional
from datetime import datetime, timedelta
from pydantic import BaseModel
import logging
import threading

from ...data.providers.sentiment import (
    TwitterSentimentProvider, 
    RedditSentimentProvider,
    NewsSentimentProvider,
    StockTwitsSentimentProvider,
    GoogleTrendsSentimentProvider,
    MentionVolumeProvider,
    AnalystRatingsSentimentProvider,
    SentimentAggregator
)

# Optional imports
try:
    from ...data.providers.sentiment.sec_filings import SECFilingsSentimentProvider
except ImportError:
    SECFilingsSentimentProvider = None

try:
    from ...data.providers.sentiment.analyst_ratings import AnalystRatingsSentimentProvider
except ImportError:
    AnalystRatingsSentimentProvider = None

try:
    from ...data.providers.sentiment.insider_trading import InsiderTradingSentimentProvider
except ImportError:
    InsiderTradingSentimentProvider = None

try:
    from ...data.providers.data.dark_pool import DarkPoolSentimentProvider
except ImportError:
    DarkPoolSentimentProvider = None

from ...data.providers.sentiment.repository import SentimentRepository
from ...data.providers.sentiment.validators import (
    validate_symbol,
    validate_hours,
    validate_days,
    validate_limit
)
from ...data.database import get_db
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)
router = APIRouter()

# Global provider instances (thread-safe singletons)
_twitter_provider: Optional[TwitterSentimentProvider] = None
_reddit_provider: Optional[RedditSentimentProvider] = None
_news_provider: Optional[NewsSentimentProvider] = None
_stocktwits_provider: Optional[StockTwitsSentimentProvider] = None
_google_trends_provider: Optional[GoogleTrendsSentimentProvider] = None
_mention_volume_provider: Optional[MentionVolumeProvider] = None
_analyst_ratings_provider: Optional[AnalystRatingsSentimentProvider] = None
_sentiment_aggregator: Optional[SentimentAggregator] = None
_aggregator: Optional[SentimentAggregator] = None  # Alias

# Locks for thread-safe initialization (double-check locking pattern)
_provider_locks = {
    'twitter': threading.Lock(),
    'reddit': threading.Lock(),
    'news': threading.Lock(),
    'stocktwits': threading.Lock(),
    'google_trends': threading.Lock(),
    'analyst_ratings': threading.Lock(),
    'aggregator': threading.Lock(),
}


def get_twitter_provider() -> TwitterSentimentProvider:
    """Get or create Twitter sentiment provider instance (thread-safe)"""
    global _twitter_provider
    if _twitter_provider is None:
        with _provider_locks['twitter']:
            # Double-check pattern to avoid unnecessary locks
    if _twitter_provider is None:
        _twitter_provider = TwitterSentimentProvider(persist_to_db=True)
                logger.info("Twitter provider initialized")
    return _twitter_provider


def get_news_provider() -> NewsSentimentProvider:
    """Get or create news sentiment provider instance"""
    global _news_provider
    if _news_provider is None:
        _news_provider = NewsSentimentProvider(persist_to_db=True)
    return _news_provider


def get_stocktwits_provider() -> StockTwitsSentimentProvider:
    """Get or create StockTwits sentiment provider instance"""
    global _stocktwits_provider
    if _stocktwits_provider is None:
        _stocktwits_provider = StockTwitsSentimentProvider(persist_to_db=True)
    return _stocktwits_provider


def get_sec_filings_provider():
    """Get or create SEC filings sentiment provider instance"""
    global _sec_filings_provider
    if _sec_filings_provider is None:
        try:
            from ...data.providers.sentiment.sec_filings import SECFilingsSentimentProvider
            _sec_filings_provider = SECFilingsSentimentProvider(persist_to_db=True)
        except ImportError:
            pass
    return _sec_filings_provider


def get_mention_volume_provider() -> MentionVolumeProvider:
    """Get or create mention volume provider instance"""
    global _mention_volume_provider
    if _mention_volume_provider is None:
        _mention_volume_provider = MentionVolumeProvider(persist_to_db=True)
    return _mention_volume_provider


def get_google_trends_provider() -> GoogleTrendsSentimentProvider:
    """Get or create Google Trends sentiment provider instance"""
    global _google_trends_provider
    if _google_trends_provider is None:
        _google_trends_provider = GoogleTrendsSentimentProvider(persist_to_db=True)
    return _google_trends_provider


def get_sentiment_aggregator() -> SentimentAggregator:
    """Get or create sentiment aggregator instance"""
    global _sentiment_aggregator
    if _sentiment_aggregator is None:
        _sentiment_aggregator = SentimentAggregator(persist_to_db=True)
    return _sentiment_aggregator


def get_reddit_provider() -> RedditSentimentProvider:
    """Get or create Reddit sentiment provider instance"""
    global _reddit_provider
    if _reddit_provider is None:
        _reddit_provider = RedditSentimentProvider(persist_to_db=True)
    return _reddit_provider


def get_aggregator() -> SentimentAggregator:
    """Get or create sentiment aggregator (alias for get_sentiment_aggregator)"""
    return get_sentiment_aggregator()


def get_google_trends_provider():
    """Get or create Google Trends sentiment provider instance"""
    global _google_trends_provider
    if _google_trends_provider is None and GoogleTrendsSentimentProvider is not None:
        _google_trends_provider = GoogleTrendsSentimentProvider(persist_to_db=True)
    return _google_trends_provider


# Response Models
class SentimentResponse(BaseModel):
    """Sentiment response model"""
    symbol: str
    timestamp: datetime
    mention_count: int
    average_sentiment: float
    weighted_sentiment: float
    influencer_sentiment: Optional[float] = None
    engagement_score: float
    sentiment_level: str
    confidence: float
    volume_trend: str

    class Config:
        from_attributes = True


class TweetMentionResponse(BaseModel):
    """Tweet mention response model"""
    tweet_id: str
    text: str
    author_username: str
    created_at: datetime
    like_count: int
    retweet_count: int
    sentiment_score: Optional[float] = None
    sentiment_level: Optional[str] = None

    class Config:
        from_attributes = True


class InfluencerResponse(BaseModel):
    """Influencer response model"""
    user_id: str
    username: str
    display_name: Optional[str] = None
    follower_count: int
    is_verified: bool
    category: str
    weight_multiplier: float
    is_active: bool

    class Config:
        from_attributes = True


class AddInfluencerRequest(BaseModel):
    """Add influencer request model"""
    user_id: str
    username: str
    category: str = "trader"
    weight_multiplier: float = 1.5


class SentimentTrendResponse(BaseModel):
    """Sentiment trend response model"""
    symbol: str
    data_points: List[SentimentResponse]
    trend_direction: str  # up, down, stable
    average_change: float


class AggregatedSentimentResponse(BaseModel):
    """Aggregated sentiment response model"""
    symbol: str
    timestamp: datetime
    unified_sentiment: float
    confidence: float
    sentiment_level: str
    source_count: int
    total_mentions: int
    divergence_score: float
    divergence_detected: bool
    providers_used: List[str]
    source_breakdown: Dict[str, float]
    sources: Dict[str, Dict[str, Any]]  # source_name -> source data

    class Config:
        from_attributes = True


@router.get("/twitter/status")
async def twitter_status():
    """Get Twitter sentiment provider status"""
    provider = get_twitter_provider()
    
    return {
        "available": provider.is_available(),
        "persist_to_db": provider.persist_to_db,
        "cache_enabled": True,
        "cache_ttl": provider.cache_ttl
    }


@router.get("/twitter/{symbol}", response_model=SentimentResponse)
async def get_twitter_sentiment(
    symbol: str,
    hours: int = Query(default=24, ge=1, le=168, description="Hours of data to analyze")
):
    """
    Get Twitter sentiment for a symbol
    
    Args:
        symbol: Stock symbol (e.g., AAPL, SPY)
        hours: Hours of historical data to analyze (1-168, default: 24)
    
    Returns:
        Current sentiment data for the symbol
    """
    # Validate inputs
    symbol = validate_symbol(symbol)
    hours = validate_hours(hours, min_hours=1, max_hours=168)
    
    provider = get_twitter_provider()
    
    if not provider.is_available():
        raise HTTPException(
            status_code=503,
            detail="Twitter sentiment provider is not available. Check API credentials."
        )
    
    try:
        sentiment = provider.get_sentiment(symbol.upper(), hours=hours)
        
        if sentiment is None:
            raise HTTPException(
                status_code=404,
                detail=f"No sentiment data available for {symbol}"
            )
        
        return SentimentResponse(
            symbol=sentiment.symbol,
            timestamp=sentiment.timestamp,
            mention_count=sentiment.mention_count,
            average_sentiment=sentiment.average_sentiment,
            weighted_sentiment=sentiment.weighted_sentiment,
            influencer_sentiment=sentiment.influencer_sentiment,
            engagement_score=sentiment.engagement_score,
            sentiment_level=sentiment.sentiment_level.value,
            confidence=sentiment.confidence,
            volume_trend=sentiment.volume_trend
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting Twitter sentiment for {symbol}: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Error retrieving sentiment data: {str(e)}"
        )


@router.get("/twitter/{symbol}/mentions", response_model=List[TweetMentionResponse])
async def get_twitter_mentions(
    symbol: str,
    hours: int = Query(default=24, ge=1, le=168, description="Hours of data to retrieve"),
    limit: int = Query(default=50, ge=1, le=200, description="Maximum number of mentions"),
    db: Session = Depends(get_db)
):
    """
    Get recent tweets mentioning a symbol
    
    Args:
        symbol: Stock symbol
        hours: Hours of historical data
        limit: Maximum number of mentions to return
    
    Returns:
        List of tweets mentioning the symbol
    """
    try:
        repository = SentimentRepository(db=db)
        tweets = repository.get_tweets_for_symbol(symbol.upper(), hours=hours, limit=limit)
        
        # Get sentiment scores for these tweets
        result = []
        for tweet in tweets:
            # Get sentiment for this tweet
            sentiments = [
                ts for ts in tweet.sentiments 
                if ts.symbol == symbol.upper()
            ]
            
            sentiment_score = None
            sentiment_level = None
            
            if sentiments:
                # Use most recent sentiment
                latest = sorted(sentiments, key=lambda x: x.analyzed_at, reverse=True)[0]
                sentiment_score = latest.sentiment_score
                sentiment_level = latest.sentiment_level
            
            result.append(TweetMentionResponse(
                tweet_id=tweet.tweet_id,
                text=tweet.text,
                author_username=tweet.author_username,
                created_at=tweet.created_at,
                like_count=tweet.like_count,
                retweet_count=tweet.retweet_count,
                sentiment_score=sentiment_score,
                sentiment_level=sentiment_level
            ))
        
        return result
    
    except Exception as e:
        logger.error(f"Error getting mentions for {symbol}: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Error retrieving mentions: {str(e)}"
        )


@router.get("/twitter/{symbol}/trend", response_model=SentimentTrendResponse)
async def get_twitter_sentiment_trend(
    symbol: str,
    hours: int = Query(default=24, ge=1, le=168, description="Hours of historical data"),
    interval_hours: int = Query(default=1, ge=1, le=24, description="Interval between data points"),
    db: Session = Depends(get_db)
):
    """
    Get sentiment trend over time for a symbol
    
    Args:
        symbol: Stock symbol
        hours: Total hours of historical data
        interval_hours: Interval between data points
    
    Returns:
        Sentiment trend data
    """
    try:
        repository = SentimentRepository(db=db)
        sentiments = repository.get_recent_sentiment(
            symbol.upper(), 
            hours=hours, 
            limit=1000
        )
        
        if not sentiments:
            raise HTTPException(
                status_code=404,
                detail=f"No historical sentiment data available for {symbol}"
            )
        
        # Group by time intervals
        cutoff = datetime.now() - timedelta(hours=hours)
        interval_seconds = interval_hours * 3600
        
        grouped = {}
        for sentiment in sentiments:
            if sentiment.timestamp < cutoff:
                continue
            
            # Round to interval
            interval_key = int((sentiment.timestamp - cutoff).total_seconds() / interval_seconds)
            
            if interval_key not in grouped:
                grouped[interval_key] = []
            
            grouped[interval_key].append(sentiment)
        
        # Calculate average for each interval
        data_points = []
        for interval_key in sorted(grouped.keys()):
            interval_sentiments = grouped[interval_key]
            
            avg_sentiment = sum(s.weighted_sentiment for s in interval_sentiments) / len(interval_sentiments)
            avg_mention_count = sum(s.mention_count for s in interval_sentiments) / len(interval_sentiments)
            avg_timestamp = max(s.timestamp for s in interval_sentiments)
            
            # Get most common sentiment level
            sentiment_levels = [s.sentiment_level for s in interval_sentiments]
            most_common_level = max(set(sentiment_levels), key=sentiment_levels.count)
            
            data_points.append(SentimentResponse(
                symbol=symbol.upper(),
                timestamp=avg_timestamp,
                mention_count=int(avg_mention_count),
                average_sentiment=avg_sentiment,
                weighted_sentiment=avg_sentiment,
                engagement_score=0.0,
                sentiment_level=most_common_level,
                confidence=0.0,
                volume_trend="stable"
            ))
        
        # Calculate trend direction
        if len(data_points) >= 2:
            first_half = data_points[:len(data_points)//2]
            second_half = data_points[len(data_points)//2:]
            
            first_avg = sum(p.weighted_sentiment for p in first_half) / len(first_half)
            second_avg = sum(p.weighted_sentiment for p in second_half) / len(second_half)
            
            change = second_avg - first_avg
            
            if change > 0.1:
                trend_direction = "up"
            elif change < -0.1:
                trend_direction = "down"
            else:
                trend_direction = "stable"
            
            average_change = change
        else:
            trend_direction = "stable"
            average_change = 0.0
        
        return SentimentTrendResponse(
            symbol=symbol.upper(),
            data_points=data_points,
            trend_direction=trend_direction,
            average_change=average_change
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting trend for {symbol}: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Error retrieving trend: {str(e)}"
        )


@router.get("/twitter/influencers", response_model=List[InfluencerResponse])
async def list_influencers(
    active_only: bool = Query(default=True, description="Only return active influencers"),
    db: Session = Depends(get_db)
):
    """
    List all tracked influencers
    
    Args:
        active_only: Only return active influencers
    
    Returns:
        List of influencers
    """
    try:
        repository = SentimentRepository(db=db)
        influencers = repository.get_influencers(active_only=active_only)
        
        return [
            InfluencerResponse(
                user_id=inf.user_id,
                username=inf.username,
                display_name=inf.display_name,
                follower_count=inf.follower_count,
                is_verified=inf.is_verified,
                category=inf.category,
                weight_multiplier=inf.weight_multiplier,
                is_active=inf.is_active
            )
            for inf in influencers
        ]
    
    except Exception as e:
        logger.error(f"Error getting influencers: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Error retrieving influencers: {str(e)}"
        )


@router.post("/twitter/influencers", response_model=InfluencerResponse)
async def add_influencer(
    request: AddInfluencerRequest,
    db: Session = Depends(get_db)
):
    """
    Add a new influencer to track
    
    Args:
        request: Influencer information
    
    Returns:
        Created influencer
    """
    provider = get_twitter_provider()
    
    if not provider.is_available():
        raise HTTPException(
            status_code=503,
            detail="Twitter provider is not available"
        )
    
    try:
        # Add influencer to provider (this will fetch user info)
        provider.add_influencer(
            user_id=request.user_id,
            username=request.username,
            category=request.category,
            weight_multiplier=request.weight_multiplier
        )
        
        # Get the influencer from provider
        if request.user_id not in provider.influencers:
            raise HTTPException(
                status_code=400,
                detail="Failed to add influencer"
            )
        
        influencer = provider.influencers[request.user_id]
        
        # Save to database
        repository = SentimentRepository(db=db)
        db_influencer = repository.save_influencer(influencer)
        
        if db_influencer is None:
            raise HTTPException(
                status_code=500,
                detail="Failed to save influencer to database"
            )
        
        return InfluencerResponse(
            user_id=db_influencer.user_id,
            username=db_influencer.username,
            display_name=db_influencer.display_name,
            follower_count=db_influencer.follower_count,
            is_verified=db_influencer.is_verified,
            category=db_influencer.category,
            weight_multiplier=db_influencer.weight_multiplier,
            is_active=db_influencer.is_active
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error adding influencer: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Error adding influencer: {str(e)}"
        )


@router.get("/twitter/trending")
async def get_trending_symbols(
    min_mentions: int = Query(default=10, ge=1, description="Minimum mentions to be trending"),
    hours: int = Query(default=24, ge=1, le=168, description="Hours of data to analyze"),
    limit: int = Query(default=20, ge=1, le=100, description="Maximum number of symbols to return"),
    db: Session = Depends(get_db)
):
    """
    Get trending stock symbols on Twitter based on mention counts
    
    Args:
        min_mentions: Minimum mentions to be considered trending
        hours: Hours of data to analyze
        limit: Maximum number of symbols to return
    
    Returns:
        List of trending symbols with mention counts and sentiment
    """
    try:
        repository = SentimentRepository(db=db)
        trending = repository.get_trending_symbols(
            hours=hours,
            min_mentions=min_mentions,
            limit=limit
        )
        
        return {
            "trending": trending,
            "count": len(trending),
            "hours_analyzed": hours,
            "min_mentions": min_mentions
        }
    
    except Exception as e:
        logger.error(f"Error getting trending symbols: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Error retrieving trending symbols: {str(e)}"
        )


# ==================== Reddit Sentiment Endpoints ====================

@router.get("/reddit/status")
async def reddit_status():
    """Get Reddit sentiment provider status"""
    provider = get_reddit_provider()
    
    return {
        "available": provider.is_available(),
        "persist_to_db": provider.persist_to_db,
        "cache_enabled": True,
        "cache_ttl": provider.cache_ttl
    }


@router.get("/reddit/{symbol}", response_model=SentimentResponse)
async def get_reddit_sentiment(
    symbol: str,
    hours: int = Query(default=24, ge=1, le=168, description="Hours of data to analyze")
):
    """
    Get Reddit sentiment for a symbol
    
    Args:
        symbol: Stock symbol (e.g., AAPL, SPY)
        hours: Hours of historical data to analyze (1-168, default: 24)
    
    Returns:
        Current sentiment data for the symbol
    """
    provider = get_reddit_provider()
    
    if not provider.is_available():
        raise HTTPException(
            status_code=503,
            detail="Reddit sentiment provider is not available. Check API credentials."
        )
    
    try:
        sentiment = provider.get_sentiment(symbol.upper(), hours=hours)
        
        if sentiment is None:
            raise HTTPException(
                status_code=404,
                detail=f"No sentiment data available for {symbol}"
            )
        
        return SentimentResponse(
            symbol=sentiment.symbol,
            timestamp=sentiment.timestamp,
            mention_count=sentiment.mention_count,
            average_sentiment=sentiment.average_sentiment,
            weighted_sentiment=sentiment.weighted_sentiment,
            influencer_sentiment=sentiment.influencer_sentiment,
            engagement_score=sentiment.engagement_score,
            sentiment_level=sentiment.sentiment_level.value,
            confidence=sentiment.confidence,
            volume_trend=sentiment.volume_trend
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting Reddit sentiment for {symbol}: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Error retrieving sentiment data: {str(e)}"
        )


@router.get("/reddit/{symbol}/mentions", response_model=List[TweetMentionResponse])
async def get_reddit_mentions(
    symbol: str,
    hours: int = Query(default=24, ge=1, le=168, description="Hours of data to retrieve"),
    limit: int = Query(default=50, ge=1, le=200, description="Maximum number of mentions"),
    db: Session = Depends(get_db)
):
    """
    Get recent Reddit posts/comments mentioning a symbol
    
    Args:
        symbol: Stock symbol
        hours: Hours of historical data
        limit: Maximum number of mentions to return
    
    Returns:
        List of Reddit posts/comments mentioning the symbol
    """
    try:
        repository = SentimentRepository(db=db)
        
        # Use Reddit-specific query method
        reddit_posts = repository.get_reddit_posts_for_symbol(
            symbol.upper(), 
            hours=hours, 
            limit=limit
        )
        
        # Get sentiment scores for these posts
        result = []
        for post in reddit_posts:
            # Get sentiment for this post
            sentiments = [
                ts for ts in post.sentiments 
                if ts.symbol == symbol.upper()
            ]
            
            sentiment_score = None
            sentiment_level = None
            
            if sentiments:
                # Use most recent sentiment
                latest = sorted(sentiments, key=lambda x: x.analyzed_at, reverse=True)[0]
                sentiment_score = latest.sentiment_score
                sentiment_level = latest.sentiment_level
            
            result.append(TweetMentionResponse(
                tweet_id=post.post_id,  # Use actual Reddit post ID
                text=post.text,
                author_username=post.author,
                created_at=post.created_at,
                like_count=post.score,
                retweet_count=post.num_comments,  # Use comment count as engagement
                sentiment_score=sentiment_score,
                sentiment_level=sentiment_level
            ))
        
        return result
    
    except Exception as e:
        logger.error(f"Error getting Reddit mentions for {symbol}: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Error retrieving mentions: {str(e)}"
        )


@router.get("/reddit/{symbol}/trend", response_model=SentimentTrendResponse)
async def get_reddit_sentiment_trend(
    symbol: str,
    hours: int = Query(default=24, ge=1, le=168, description="Hours of historical data"),
    interval_hours: int = Query(default=1, ge=1, le=24, description="Interval between data points"),
    db: Session = Depends(get_db)
):
    """
    Get Reddit sentiment trend over time for a symbol
    
    Args:
        symbol: Stock symbol
        hours: Total hours of historical data
        interval_hours: Interval between data points
    
    Returns:
        Sentiment trend data
    """
    try:
        repository = SentimentRepository(db=db)
        sentiments = repository.get_recent_sentiment(
            symbol.upper(), 
            hours=hours, 
            limit=1000
        )
        
        # Filter to Reddit-only sentiments (would need source tracking in future)
        # For now, we'll use all sentiments but could be enhanced
        
        if not sentiments:
            raise HTTPException(
                status_code=404,
                detail=f"No historical sentiment data available for {symbol}"
            )
        
        # Group by time intervals
        cutoff = datetime.now() - timedelta(hours=hours)
        interval_seconds = interval_hours * 3600
        
        grouped = {}
        for sentiment in sentiments:
            if sentiment.timestamp < cutoff:
                continue
            
            # Round to interval
            interval_key = int((sentiment.timestamp - cutoff).total_seconds() / interval_seconds)
            
            if interval_key not in grouped:
                grouped[interval_key] = []
            
            grouped[interval_key].append(sentiment)
        
        # Calculate average for each interval
        data_points = []
        for interval_key in sorted(grouped.keys()):
            interval_sentiments = grouped[interval_key]
            
            avg_sentiment = sum(s.weighted_sentiment for s in interval_sentiments) / len(interval_sentiments)
            avg_mention_count = sum(s.mention_count for s in interval_sentiments) / len(interval_sentiments)
            avg_timestamp = max(s.timestamp for s in interval_sentiments)
            
            # Get most common sentiment level
            sentiment_levels = [s.sentiment_level for s in interval_sentiments]
            most_common_level = max(set(sentiment_levels), key=sentiment_levels.count)
            
            data_points.append(SentimentResponse(
                symbol=symbol.upper(),
                timestamp=avg_timestamp,
                mention_count=int(avg_mention_count),
                average_sentiment=avg_sentiment,
                weighted_sentiment=avg_sentiment,
                engagement_score=0.0,
                sentiment_level=most_common_level,
                confidence=0.0,
                volume_trend="stable"
            ))
        
        # Calculate trend direction
        if len(data_points) >= 2:
            first_half = data_points[:len(data_points)//2]
            second_half = data_points[len(data_points)//2:]
            
            first_avg = sum(p.weighted_sentiment for p in first_half) / len(first_half)
            second_avg = sum(p.weighted_sentiment for p in second_half) / len(second_half)
            
            change = second_avg - first_avg
            
            if change > 0.1:
                trend_direction = "up"
            elif change < -0.1:
                trend_direction = "down"
            else:
                trend_direction = "stable"
            
            average_change = change
        else:
            trend_direction = "stable"
            average_change = 0.0
        
        return SentimentTrendResponse(
            symbol=symbol.upper(),
            data_points=data_points,
            trend_direction=trend_direction,
            average_change=average_change
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting Reddit trend for {symbol}: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Error retrieving trend: {str(e)}"
        )


# ==================== Aggregated Sentiment Endpoints ====================

@router.get("/aggregated/{symbol}", response_model=AggregatedSentimentResponse)
async def get_aggregated_sentiment(
    symbol: str,
    hours: int = Query(default=24, ge=1, le=168, description="Hours of data to analyze")
):
    """
    Get aggregated sentiment for a symbol across all providers (Twitter, Reddit, etc.)
    
    Args:
        symbol: Stock symbol (e.g., AAPL, SPY)
        hours: Hours of historical data to analyze (1-168, default: 24)
    
    Returns:
        Aggregated sentiment data from all available providers
    """
    # Validate inputs
    symbol = validate_symbol(symbol)
    hours = validate_hours(hours, min_hours=1, max_hours=168)
    
    aggregator = get_aggregator()
    
    try:
        aggregated = aggregator.get_aggregated_sentiment(symbol.upper(), hours=hours)
        
        if aggregated is None:
            raise HTTPException(
                status_code=404,
                detail=f"No aggregated sentiment data available for {symbol}. No providers returned valid data."
            )
        
        # Prepare source data for response
        sources_data = {}
        for source_name, source_sent in aggregated.sources.items():
            sources_data[source_name] = {
                "sentiment_score": source_sent.sentiment_score,
                "weighted_sentiment": source_sent.weighted_sentiment,
                "confidence": source_sent.confidence,
                "mention_count": source_sent.mention_count,
                "sentiment_level": source_sent.sentiment_level.value,
                "source_weight": source_sent.source_weight,
                "timestamp": source_sent.timestamp.isoformat()
            }
        
        return AggregatedSentimentResponse(
            symbol=aggregated.symbol,
            timestamp=aggregated.timestamp,
            unified_sentiment=aggregated.unified_sentiment,
            confidence=aggregated.confidence,
            sentiment_level=aggregated.sentiment_level.value,
            source_count=aggregated.source_count,
            total_mentions=aggregated.total_mentions,
            divergence_score=aggregated.divergence_score,
            divergence_detected=aggregated.divergence_detected,
            providers_used=aggregated.providers_used,
            source_breakdown=aggregated.source_breakdown,
            sources=sources_data
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting aggregated sentiment for {symbol}: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Error retrieving aggregated sentiment: {str(e)}"
        )


@router.get("/aggregated/status")
async def aggregated_status():
    """Get aggregator status and available sources"""
    aggregator = get_aggregator()
    
    available_sources = aggregator.get_available_sources()
    
    return {
        "aggregator_available": True,
        "available_sources": available_sources,
        "source_weights": aggregator.source_weights,
        "time_decay_hours": aggregator.time_decay_hours,
        "min_confidence": aggregator.min_confidence,
        "active_sources": len(available_sources),
        "total_sources": len(aggregator.source_weights)
    }


@router.get("/reddit/trending")
async def get_reddit_trending_symbols(
    min_mentions: int = Query(default=10, ge=1, description="Minimum mentions to be trending"),
    hours: int = Query(default=24, ge=1, le=168, description="Hours of data to analyze"),
    limit: int = Query(default=20, ge=1, le=100, description="Maximum number of symbols to return"),
    db: Session = Depends(get_db)
):
    """
    Get trending stock symbols on Reddit based on mention counts from database
    
    Args:
        min_mentions: Minimum mentions to be considered trending
        hours: Hours of data to analyze
        limit: Maximum number of symbols to return
    
    Returns:
        List of trending symbols with mention counts and sentiment
    """
    try:
        repository = SentimentRepository(db=db)
        
        # Use database aggregation for trending symbols (includes Reddit data)
        trending = repository.get_trending_symbols(
            hours=hours,
            min_mentions=min_mentions,
            limit=limit
        )
        
        return {
            "trending": trending,
            "count": len(trending),
            "hours_analyzed": hours,
            "min_mentions": min_mentions
        }
    
    except Exception as e:
        logger.error(f"Error getting Reddit trending symbols: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Error retrieving trending symbols: {str(e)}"
        )


# ==================== Google Trends Sentiment Endpoints ====================

@router.get("/google-trends/status")
async def google_trends_status():
    """Get Google Trends sentiment provider status"""
    provider = get_google_trends_provider()
    
    if provider is None:
        return {
            "available": False,
            "reason": "GoogleTrendsSentimentProvider not available (pytrends not installed?)"
        }
    
    return {
        "available": provider.is_available(),
        "persist_to_db": provider.persist_to_db,
        "cache_enabled": True,
        "cache_ttl": provider.cache_ttl
    }


@router.get("/google-trends/{symbol}", response_model=SentimentResponse)
async def get_google_trends_sentiment(
    symbol: str,
    hours: int = Query(default=24, ge=1, le=168, description="Hours of data to analyze")
):
    """
    Get Google Trends sentiment for a symbol
    
    Args:
        symbol: Stock symbol (e.g., AAPL, SPY)
        hours: Hours of historical data to analyze (for cache key, Trends uses fixed timeframes)
    
    Returns:
        Current sentiment data for the symbol based on search volume trends
    """
    provider = get_google_trends_provider()
    
    if provider is None:
        raise HTTPException(
            status_code=503,
            detail="Google Trends provider is not available. Install pytrends: pip install pytrends"
        )
    
    if not provider.is_available():
        raise HTTPException(
            status_code=503,
            detail="Google Trends sentiment provider is not available. Check configuration."
        )
    
    try:
        sentiment = provider.get_sentiment(symbol.upper(), hours=hours)
        
        if sentiment is None:
            raise HTTPException(
                status_code=404,
                detail=f"No Google Trends data available for {symbol}"
            )
        
        return SentimentResponse(
            symbol=sentiment.symbol,
            timestamp=sentiment.timestamp,
            mention_count=sentiment.mention_count,
            average_sentiment=sentiment.average_sentiment,
            weighted_sentiment=sentiment.weighted_sentiment,
            influencer_sentiment=sentiment.influencer_sentiment,
            engagement_score=sentiment.engagement_score,
            sentiment_level=sentiment.sentiment_level.value,
            confidence=sentiment.confidence,
            volume_trend=sentiment.volume_trend
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting Google Trends sentiment for {symbol}: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Error retrieving Google Trends sentiment: {str(e)}"
        )


@router.get("/google-trends/{symbol}/related")
async def get_google_trends_related_searches(symbol: str):
    """
    Get related searches for a symbol
    
    Args:
        symbol: Stock symbol
    
    Returns:
        Dictionary with 'rising' and 'top' related search queries
    """
    provider = get_google_trends_provider()
    
    if provider is None or not provider.is_available():
        raise HTTPException(
            status_code=503,
            detail="Google Trends provider is not available"
        )
    
    try:
        related = provider.get_related_searches(symbol.upper())
        
        if related is None:
            raise HTTPException(
                status_code=404,
                detail=f"No related searches available for {symbol}"
            )
        
        return {
            "symbol": symbol.upper(),
            "related_searches": related
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting related searches for {symbol}: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Error retrieving related searches: {str(e)}"
        )


# ==================== Analyst Ratings Sentiment Endpoints ====================

def get_analyst_ratings_provider() -> AnalystRatingsSentimentProvider:
    """Get or create analyst ratings sentiment provider instance (thread-safe)"""
    global _analyst_ratings_provider
    if _analyst_ratings_provider is None:
        with _provider_locks['analyst_ratings']:
            # Double-check pattern to avoid unnecessary locks
            if _analyst_ratings_provider is None:
                if AnalystRatingsSentimentProvider is not None:
                    _analyst_ratings_provider = AnalystRatingsSentimentProvider(persist_to_db=True)
                    logger.info("Analyst ratings provider initialized")
    return _analyst_ratings_provider


@router.get("/analyst-ratings/status")
async def analyst_ratings_status():
    """Get Analyst Ratings sentiment provider status"""
    provider = get_analyst_ratings_provider()
    
    if provider is None:
        return {
            "available": False,
            "reason": "AnalystRatingsSentimentProvider not available (yfinance not installed?)"
        }
    
    return {
        "available": provider.is_available(),
        "persist_to_db": provider.persist_to_db,
        "cache_enabled": True,
        "cache_ttl": provider.cache_ttl
    }


@router.get("/analyst-ratings/{symbol}", response_model=SentimentResponse)
async def get_analyst_ratings_sentiment(
    symbol: str,
    hours: int = Query(default=24, ge=1, le=168, description="Hours parameter (kept for API compatibility, not used)")
):
    """
    Get analyst ratings sentiment for a symbol
    
    Args:
        symbol: Stock symbol (e.g., AAPL, MSFT)
        hours: Hours parameter (not used for analyst ratings, kept for API compatibility)
    
    Returns:
        Current sentiment data for the symbol based on analyst ratings and price targets
    """
    provider = get_analyst_ratings_provider()
    
    if provider is None:
        raise HTTPException(
            status_code=503,
            detail="Analyst Ratings provider is not available. Install yfinance: pip install yfinance"
        )
    
    if not provider.is_available():
        raise HTTPException(
            status_code=503,
            detail="Analyst Ratings sentiment provider is not available. Check configuration."
        )
    
    try:
        sentiment = provider.get_sentiment(symbol.upper(), hours=hours)
        
        if sentiment is None:
            raise HTTPException(
                status_code=404,
                detail=f"No analyst ratings data available for {symbol}"
            )
        
        return SentimentResponse(
            symbol=sentiment.symbol,
            timestamp=sentiment.timestamp,
            mention_count=sentiment.mention_count,
            average_sentiment=sentiment.average_sentiment,
            weighted_sentiment=sentiment.weighted_sentiment,
            influencer_sentiment=sentiment.influencer_sentiment,
            engagement_score=sentiment.engagement_score,
            sentiment_level=sentiment.sentiment_level.value,
            confidence=sentiment.confidence,
            volume_trend=sentiment.volume_trend
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting analyst ratings sentiment for {symbol}: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Error retrieving analyst ratings sentiment: {str(e)}"
        )


@router.get("/analyst-ratings/{symbol}/details")
async def get_analyst_ratings_details(symbol: str):
    """
    Get detailed analyst ratings and price target information for a symbol
    
    Args:
        symbol: Stock symbol
    
    Returns:
        Detailed analyst rating information including price targets
    """
    provider = get_analyst_ratings_provider()
    
    if provider is None or not provider.is_available():
        raise HTTPException(
            status_code=503,
            detail="Analyst Ratings provider is not available"
        )
    
    try:
        rating = provider.get_analyst_rating(symbol.upper())
        
        if rating is None:
            raise HTTPException(
                status_code=404,
                detail=f"No analyst rating data available for {symbol}"
            )
        
        return {
            "symbol": rating.symbol,
            "rating": rating.rating,
            "rating_numeric": rating.rating_numeric,
            "price_target": rating.price_target,
            "price_target_high": rating.price_target_high,
            "price_target_low": rating.price_target_low,
            "price_target_mean": rating.price_target_mean,
            "number_of_analysts": rating.number_of_analysts,
            "current_price": rating.current_price,
            "price_target_upside": rating.price_target_upside,
            "timestamp": rating.timestamp.isoformat() if rating.timestamp else None
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting analyst ratings details for {symbol}: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Error retrieving analyst ratings details: {str(e)}"
        )


# ==================== Insider Trading Sentiment Endpoints ====================

_insider_trading_provider: Optional[Any] = None
_dark_pool_provider: Optional[Any] = None


def get_insider_trading_provider():
    """Get or create Insider Trading sentiment provider instance"""
    global _insider_trading_provider
    if _insider_trading_provider is None and InsiderTradingSentimentProvider is not None:
        _insider_trading_provider = InsiderTradingSentimentProvider(persist_to_db=True)
    return _insider_trading_provider


def get_dark_pool_provider():
    """Get or create Dark Pool sentiment provider instance"""
    global _dark_pool_provider
    if _dark_pool_provider is None and DarkPoolSentimentProvider is not None:
        _dark_pool_provider = DarkPoolSentimentProvider(persist_to_db=True)
    return _dark_pool_provider


@router.get("/insider-trading/status")
async def insider_trading_status():
    """Get Insider Trading sentiment provider status"""
    provider = get_insider_trading_provider()
    
    if provider is None:
        return {
            "available": False,
            "reason": "InsiderTradingSentimentProvider not available (yfinance not installed?)"
        }
    
    return {
        "available": provider.is_available(),
        "persist_to_db": provider.persist_to_db,
        "cache_enabled": True,
        "cache_ttl": provider.cache_ttl
    }


@router.get("/insider-trading/{symbol}", response_model=SentimentResponse)
async def get_insider_trading_sentiment(
    symbol: str,
    hours: int = Query(default=24, ge=1, le=168, description="Hours parameter (kept for API compatibility, not used)")
):
    """
    Get insider trading sentiment for a symbol
    
    Args:
        symbol: Stock symbol (e.g., AAPL, MSFT)
        hours: Hours parameter (not used for insider trading, kept for API compatibility)
    
    Returns:
        Current sentiment data for the symbol based on insider trading and institutional holdings
    """
    provider = get_insider_trading_provider()
    
    if provider is None:
        raise HTTPException(
            status_code=503,
            detail="Insider Trading provider is not available. Install yfinance: pip install yfinance"
        )
    
    if not provider.is_available():
        raise HTTPException(
            status_code=503,
            detail="Insider Trading sentiment provider is not available. Check configuration."
        )
    
    try:
        sentiment = provider.get_sentiment(symbol.upper(), hours=hours)
        
        if sentiment is None:
            raise HTTPException(
                status_code=404,
                detail=f"No insider trading data available for {symbol}"
            )
        
        return SentimentResponse(
            symbol=sentiment.symbol,
            timestamp=sentiment.timestamp,
            mention_count=sentiment.mention_count,
            average_sentiment=sentiment.average_sentiment,
            weighted_sentiment=sentiment.weighted_sentiment,
            influencer_sentiment=sentiment.influencer_sentiment,
            engagement_score=sentiment.engagement_score,
            sentiment_level=sentiment.sentiment_level.value,
            confidence=sentiment.confidence,
            volume_trend=sentiment.volume_trend
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting insider trading sentiment for {symbol}: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Error retrieving insider trading sentiment: {str(e)}"
        )


@router.get("/insider-trading/{symbol}/transactions")
async def get_insider_transactions(symbol: str):
    """
    Get recent insider transactions for a symbol
    
    Args:
        symbol: Stock symbol
    
    Returns:
        List of recent insider transactions
    """
    provider = get_insider_trading_provider()
    
    if provider is None or not provider.is_available():
        raise HTTPException(
            status_code=503,
            detail="Insider Trading provider is not available"
        )
    
    try:
        transactions = provider.get_insider_transactions(symbol.upper())
        
        if transactions is None:
            raise HTTPException(
                status_code=404,
                detail=f"No insider transactions available for {symbol}"
            )
        
        return {
            "symbol": symbol.upper(),
            "transactions": transactions,
            "count": len(transactions)
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting insider transactions for {symbol}: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Error retrieving insider transactions: {str(e)}"
        )


@router.get("/insider-trading/{symbol}/institutional")
async def get_institutional_holders(symbol: str):
    """
    Get institutional holders for a symbol
    
    Args:
        symbol: Stock symbol
    
    Returns:
        List of institutional holdings
    """
    provider = get_insider_trading_provider()
    
    if provider is None or not provider.is_available():
        raise HTTPException(
            status_code=503,
            detail="Insider Trading provider is not available"
        )
    
    try:
        holders = provider.get_institutional_holders(symbol.upper())
        
        if holders is None:
            raise HTTPException(
                status_code=404,
                detail=f"No institutional holders data available for {symbol}"
            )
        
        return {
            "symbol": symbol.upper(),
            "institutional_holders": holders,
            "count": len(holders)
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting institutional holders for {symbol}: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Error retrieving institutional holders: {str(e)}"
        )


@router.get("/insider-trading/{symbol}/major-holders")
async def get_major_holders(symbol: str):
    """
    Get major holders summary (insiders and institutions) for a symbol
    
    Args:
        symbol: Stock symbol
    
    Returns:
        Major holders summary with insider and institutional percentages
    """
    provider = get_insider_trading_provider()
    
    if provider is None or not provider.is_available():
        raise HTTPException(
            status_code=503,
            detail="Insider Trading provider is not available"
        )
    
    try:
        holders = provider.get_major_holders(symbol.upper())
        
        if holders is None:
            raise HTTPException(
                status_code=404,
                detail=f"No major holders data available for {symbol}"
            )
        
        return {
            "symbol": symbol.upper(),
            "major_holders": holders
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting major holders for {symbol}: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Error retrieving major holders: {str(e)}"
        )


# ==================== Dark Pool & Institutional Flow Sentiment Endpoints ====================

@router.get("/dark-pool/status")
async def dark_pool_status():
    """Get Dark Pool sentiment provider status"""
    provider = get_dark_pool_provider()
    
    if provider is None:
        return {
            "available": False,
            "provider": "DarkPoolSentimentProvider",
            "reason": "Provider not available. Install required dependencies and configure DARK_POOL_API_KEY."
        }
    
    return {
        "available": provider.is_available(),
        "provider": "DarkPoolSentimentProvider",
        "features": {
            "dark_pool_data": provider.client.is_available() if provider.client else False,
            "institutional_flow": provider.client.is_available() if provider.client else False,
            "cache_enabled": True,
            "cache_ttl": provider.cache_ttl
        }
    }


@router.get("/dark-pool/{symbol}", response_model=SentimentResponse)
async def get_dark_pool_sentiment(
    symbol: str,
    hours: int = Query(default=24, ge=1, le=168, description="Hours of data to analyze")
):
    """
    Get dark pool and institutional flow sentiment for a symbol
    
    Args:
        symbol: Stock symbol (e.g., AAPL, MSFT)
        hours: Hours of data to analyze (default: 24)
    
    Returns:
        Current sentiment data for the symbol based on dark pool and institutional flow
    """
    provider = get_dark_pool_provider()
    
    if provider is None:
        raise HTTPException(
            status_code=503,
            detail="Dark Pool provider is not available. Configure DARK_POOL_API_KEY to enable."
        )
    
    if not provider.is_available():
        raise HTTPException(
            status_code=503,
            detail="Dark Pool sentiment provider is not available. Configure DARK_POOL_API_KEY and DARK_POOL_BASE_URL."
        )
    
    try:
        sentiment = provider.get_sentiment(symbol.upper(), hours=hours)
        
        if sentiment is None:
            raise HTTPException(
                status_code=404,
                detail=f"No dark pool data available for {symbol}. Ensure API key is configured and valid."
            )
        
        return SentimentResponse(
            symbol=sentiment.symbol,
            timestamp=sentiment.timestamp,
            mention_count=sentiment.mention_count,
            average_sentiment=sentiment.average_sentiment,
            weighted_sentiment=sentiment.weighted_sentiment,
            influencer_sentiment=sentiment.influencer_sentiment,
            engagement_score=sentiment.engagement_score,
            sentiment_level=sentiment.sentiment_level.value,
            confidence=sentiment.confidence,
            volume_trend=sentiment.volume_trend
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting dark pool sentiment for {symbol}: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Error retrieving dark pool sentiment: {str(e)}"
        )


# ==================== StockTwits Sentiment Endpoints ====================

@router.get("/stocktwits/status")
async def stocktwits_status():
    """Get StockTwits sentiment provider status"""
    try:
        provider = get_stocktwits_provider()
        
        return {
            "available": provider.is_available(),
            "persist_to_db": provider.persist_to_db,
            "cache_enabled": True,
            "cache_ttl": provider.cache_ttl
        }
    except Exception as e:
        logger.error(f"Error getting StockTwits status: {e}", exc_info=True)
        return {
            "available": False,
            "error": str(e)
        }


@router.get("/stocktwits/{symbol}", response_model=SentimentResponse)
async def get_stocktwits_sentiment(
    symbol: str,
    hours: int = Query(default=24, ge=1, le=168, description="Hours of data to analyze")
):
    """
    Get StockTwits sentiment for a symbol
    
    Args:
        symbol: Stock symbol (e.g., AAPL, SPY)
        hours: Hours of historical data to analyze (1-168, default: 24)
    
    Returns:
        Current sentiment data for the symbol
    """
    provider = get_stocktwits_provider()
    
    if not provider.is_available():
        raise HTTPException(
            status_code=503,
            detail="StockTwits sentiment provider is not available."
        )
    
    try:
        sentiment = provider.get_sentiment(symbol.upper(), hours=hours)
        
        if sentiment is None:
            raise HTTPException(
                status_code=404,
                detail=f"No sentiment data available for {symbol}"
            )
        
        return SentimentResponse(
            symbol=sentiment.symbol,
            timestamp=sentiment.timestamp,
            mention_count=sentiment.mention_count,
            average_sentiment=sentiment.average_sentiment,
            weighted_sentiment=sentiment.weighted_sentiment,
            influencer_sentiment=sentiment.influencer_sentiment,
            engagement_score=sentiment.engagement_score,
            sentiment_level=sentiment.sentiment_level.value,
            confidence=sentiment.confidence,
            volume_trend=sentiment.volume_trend
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting StockTwits sentiment for {symbol}: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Error retrieving sentiment data: {str(e)}"
        )


@router.get("/stocktwits/{symbol}/mentions", response_model=List[TweetMentionResponse])
async def get_stocktwits_mentions(
    symbol: str,
    hours: int = Query(default=24, ge=1, le=168, description="Hours of data to retrieve"),
    limit: int = Query(default=50, ge=1, le=200, description="Maximum number of mentions"),
    db: Session = Depends(get_db)
):
    """
    Get recent StockTwits messages mentioning a symbol
    
    Args:
        symbol: Stock symbol
        hours: Hours of historical data
        limit: Maximum number of mentions to return
    
    Returns:
        List of StockTwits messages mentioning the symbol
    """
    try:
        repository = SentimentRepository(db=db)
        tweets = repository.get_tweets_for_symbol(symbol.upper(), hours=hours, limit=limit)
        
        # Filter for StockTwits messages (tweet_id starts with "stocktwits_")
        stocktwits_tweets = [t for t in tweets if t.tweet_id.startswith("stocktwits_")]
        
        # Get sentiment scores for these tweets
        result = []
        for tweet in stocktwits_tweets:
            # Get sentiment for this tweet
            sentiments = [
                ts for ts in tweet.sentiments 
                if ts.symbol == symbol.upper()
            ]
            
            sentiment_score = None
            sentiment_level = None
            
            if sentiments:
                # Use most recent sentiment
                latest = sorted(sentiments, key=lambda x: x.analyzed_at, reverse=True)[0]
                sentiment_score = latest.sentiment_score
                sentiment_level = latest.sentiment_level
            
            result.append(TweetMentionResponse(
                tweet_id=tweet.tweet_id,
                text=tweet.text,
                author_username=tweet.author_username,
                created_at=tweet.created_at,
                like_count=tweet.like_count,
                retweet_count=tweet.reply_count,  # Use reply count as engagement metric
                sentiment_score=sentiment_score,
                sentiment_level=sentiment_level
            ))
        
        return result
    
    except Exception as e:
        logger.error(f"Error getting StockTwits mentions for {symbol}: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Error retrieving mentions: {str(e)}"
        )


@router.get("/stocktwits/{symbol}/trend", response_model=SentimentTrendResponse)
async def get_stocktwits_sentiment_trend(
    symbol: str,
    hours: int = Query(default=24, ge=1, le=168, description="Hours of historical data"),
    interval_hours: int = Query(default=1, ge=1, le=24, description="Interval between data points"),
    db: Session = Depends(get_db)
):
    """
    Get sentiment trend over time for a symbol from StockTwits
    
    Args:
        symbol: Stock symbol
        hours: Total hours of historical data
        interval_hours: Interval between data points
    
    Returns:
        Sentiment trend data
    """
    try:
        repository = SentimentRepository(db=db)
        sentiments = repository.get_recent_sentiment(
            symbol.upper(), 
            hours=hours, 
            limit=1000
        )
        
        # Filter for StockTwits sentiments (from tweets with stocktwits_ prefix)
        # This would require filtering by source, but for now we'll use all
        
        if not sentiments:
            raise HTTPException(
                status_code=404,
                detail=f"No historical sentiment data available for {symbol}"
            )
        
        # Group by time intervals (same logic as Twitter/Reddit)
        cutoff = datetime.now() - timedelta(hours=hours)
        interval_seconds = interval_hours * 3600
        
        grouped = {}
        for sentiment in sentiments:
            if sentiment.timestamp < cutoff:
                continue
            
            # Round to interval
            interval_key = int((sentiment.timestamp - cutoff).total_seconds() / interval_seconds)
            
            if interval_key not in grouped:
                grouped[interval_key] = []
            
            grouped[interval_key].append(sentiment)
        
        # Calculate average for each interval
        data_points = []
        for interval_key in sorted(grouped.keys()):
            interval_sentiments = grouped[interval_key]
            
            avg_sentiment = sum(s.weighted_sentiment for s in interval_sentiments) / len(interval_sentiments)
            avg_mention_count = sum(s.mention_count for s in interval_sentiments) / len(interval_sentiments)
            avg_timestamp = max(s.timestamp for s in interval_sentiments)
            
            # Get most common sentiment level
            sentiment_levels = [s.sentiment_level for s in interval_sentiments]
            most_common_level = max(set(sentiment_levels), key=sentiment_levels.count)
            
            data_points.append(SentimentResponse(
                symbol=symbol.upper(),
                timestamp=avg_timestamp,
                mention_count=int(avg_mention_count),
                average_sentiment=avg_sentiment,
                weighted_sentiment=avg_sentiment,
                engagement_score=0.0,
                sentiment_level=most_common_level,
                confidence=0.0,
                volume_trend="stable"
            ))
        
        # Calculate trend direction
        if len(data_points) >= 2:
            first_half = data_points[:len(data_points)//2]
            second_half = data_points[len(data_points)//2:]
            
            first_avg = sum(p.weighted_sentiment for p in first_half) / len(first_half)
            second_avg = sum(p.weighted_sentiment for p in second_half) / len(second_half)
            
            change = second_avg - first_avg
            
            if change > 0.1:
                trend_direction = "up"
            elif change < -0.1:
                trend_direction = "down"
            else:
                trend_direction = "stable"
            
            average_change = change
        else:
            trend_direction = "stable"
            average_change = 0.0
        
        return SentimentTrendResponse(
            symbol=symbol.upper(),
            data_points=data_points,
            trend_direction=trend_direction,
            average_change=average_change
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting StockTwits trend for {symbol}: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Error retrieving trend data: {str(e)}"
        )


@router.get("/stocktwits/trending")
async def get_stocktwits_trending_symbols(
    limit: int = Query(default=20, ge=1, le=100, description="Maximum number of symbols to return")
):
    """
    Get trending stock symbols on StockTwits
    
    Args:
        limit: Maximum number of symbols to return
    
    Returns:
        List of trending symbols with watchlist counts
    """
    provider = get_stocktwits_provider()
    
    if not provider.is_available():
        raise HTTPException(
            status_code=503,
            detail="StockTwits sentiment provider is not available."
        )
    
    try:
        trending = provider.get_trending_symbols(limit=limit)
        
        return {
            "trending": trending,
            "count": len(trending),
            "source": "stocktwits"
        }
    
    except Exception as e:
        logger.error(f"Error getting StockTwits trending symbols: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Error retrieving trending symbols: {str(e)}"
        )


# ==================== Google Trends Sentiment Endpoints ====================

@router.get("/google-trends/status")
async def google_trends_status():
    """Get Google Trends sentiment provider status"""
    try:
        provider = get_google_trends_provider()
        
        return {
            "available": provider.is_available(),
            "persist_to_db": provider.persist_to_db,
            "cache_enabled": True,
            "cache_ttl": provider.cache_ttl
        }
    except Exception as e:
        logger.error(f"Error getting Google Trends status: {e}", exc_info=True)
        return {
            "available": False,
            "error": str(e)
        }


@router.get("/google-trends/{symbol}", response_model=SentimentResponse)
async def get_google_trends_sentiment(
    symbol: str,
    hours: int = Query(default=24, ge=1, le=168, description="Hours of data to analyze")
):
    """
    Get Google Trends sentiment for a symbol based on search volume
    
    Args:
        symbol: Stock symbol (e.g., AAPL, SPY)
        hours: Hours of historical data to analyze (1-168, default: 24)
               Note: Google Trends uses predefined timeframes, provider selects appropriate one
    
    Returns:
        Current sentiment data for the symbol from Google Trends search volume
    """
    provider = get_google_trends_provider()
    
    if not provider.is_available():
        raise HTTPException(
            status_code=503,
            detail="Google Trends sentiment provider is not available."
        )
    
    try:
        sentiment = provider.get_sentiment(symbol.upper(), hours=hours)
        
        if sentiment is None:
            raise HTTPException(
                status_code=404,
                detail=f"No Google Trends sentiment data available for {symbol}"
            )
        
        return SentimentResponse(
            symbol=sentiment.symbol,
            timestamp=sentiment.timestamp,
            mention_count=sentiment.mention_count,
            average_sentiment=sentiment.average_sentiment,
            weighted_sentiment=sentiment.weighted_sentiment,
            influencer_sentiment=sentiment.influencer_sentiment,
            engagement_score=sentiment.engagement_score,
            sentiment_level=sentiment.sentiment_level.value,
            confidence=sentiment.confidence,
            volume_trend=sentiment.volume_trend
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting Google Trends sentiment for {symbol}: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Error retrieving sentiment data: {str(e)}"
        )


# ==================== Mention Volume Endpoints ====================

@router.get("/mention-volume/{symbol}")
async def get_mention_volume(
    symbol: str,
    hours: int = Query(default=24, ge=1, le=168, description="Hours of data to analyze"),
    lookback_hours: int = Query(default=168, ge=24, le=720, description="Hours for baseline comparison")
):
    """
    Get aggregated mention volume for a symbol across all sources
    
    Args:
        symbol: Stock symbol
        hours: Hours of recent data to analyze
        lookback_hours: Hours to look back for baseline comparison (default: 7 days)
    
    Returns:
        Mention volume data including totals by source, trends, and spike detection
    """
    provider = get_mention_volume_provider()
    
    if not provider.is_available():
        raise HTTPException(
            status_code=503,
            detail="Mention Volume provider is not available. Requires database access."
        )
    
    try:
        volume = provider.get_mention_volume(symbol.upper(), hours=hours, lookback_hours=lookback_hours)
        
        if volume is None:
            raise HTTPException(
                status_code=404,
                detail=f"No mention volume data available for {symbol}"
            )
        
        return {
            "symbol": volume.symbol,
            "timestamp": volume.timestamp,
            "total_mentions": volume.total_mentions,
            "twitter_mentions": volume.twitter_mentions,
            "reddit_mentions": volume.reddit_mentions,
            "stocktwits_mentions": volume.stocktwits_mentions,
            "news_mentions": volume.news_mentions,
            "volume_trend": volume.volume_trend,
            "momentum_score": volume.momentum_score,
            "spike_detected": volume.spike_detected,
            "spike_magnitude": volume.spike_magnitude
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting mention volume for {symbol}: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Error retrieving mention volume: {str(e)}"
        )


@router.get("/mention-volume/{symbol}/trend")
async def get_mention_volume_trend(
    symbol: str,
    hours: int = Query(default=24, ge=1, le=168, description="Hours of historical data"),
    interval_hours: int = Query(default=1, ge=1, le=24, description="Interval between data points")
):
    """
    Get mention volume trend over time for a symbol
    
    Args:
        symbol: Stock symbol
        hours: Total hours of historical data
        interval_hours: Interval between data points
    
    Returns:
        List of volume data points over time
    """
    provider = get_mention_volume_provider()
    
    if not provider.is_available():
        raise HTTPException(
            status_code=503,
            detail="Mention Volume provider is not available."
        )
    
    try:
        trend = provider.get_volume_trend(symbol.upper(), hours=hours, interval_hours=interval_hours)
        
        return {
            "symbol": symbol.upper(),
            "data_points": trend,
            "count": len(trend),
            "interval_hours": interval_hours
        }
    
    except Exception as e:
        logger.error(f"Error getting mention volume trend for {symbol}: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Error retrieving volume trend: {str(e)}"
        )


@router.get("/mention-volume/trending")
async def get_trending_by_mention_volume(
    hours: int = Query(default=24, ge=1, le=168, description="Hours of data to analyze"),
    min_mentions: int = Query(default=10, ge=1, description="Minimum mentions required"),
    min_momentum: float = Query(default=0.3, ge=0.0, le=1.0, description="Minimum momentum score"),
    limit: int = Query(default=20, ge=1, le=100, description="Maximum results to return")
):
    """
    Get symbols trending by mention volume
    
    Args:
        hours: Hours of data to analyze
        min_mentions: Minimum mentions required
        min_momentum: Minimum momentum score for trending
        limit: Maximum results to return
    
    Returns:
        List of trending symbols with volume metrics
    """
    provider = get_mention_volume_provider()
    
    if not provider.is_available():
        raise HTTPException(
            status_code=503,
            detail="Mention Volume provider is not available."
        )
    
    try:
        trending = provider.get_trending_by_volume(
            hours=hours,
            min_mentions=min_mentions,
            min_momentum=min_momentum,
            limit=limit
        )
        
        return {
            "trending": trending,
            "count": len(trending),
            "hours_analyzed": hours,
            "min_mentions": min_mentions,
            "min_momentum": min_momentum
        }
    
    except Exception as e:
        logger.error(f"Error getting trending by volume: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Error retrieving trending symbols: {str(e)}"
        )


# ==================== Analyst Ratings Sentiment Endpoints ====================

@router.get("/analyst-ratings/status")
async def analyst_ratings_status():
    """Get Analyst Ratings sentiment provider status"""
    try:
        provider = get_analyst_ratings_provider()
        
        return {
            "available": provider.is_available(),
            "persist_to_db": provider.persist_to_db,
            "cache_enabled": True,
            "cache_ttl": provider.cache_ttl
        }
    except Exception as e:
        logger.error(f"Error getting Analyst Ratings status: {e}", exc_info=True)
        return {
            "available": False,
            "error": str(e)
        }


@router.get("/analyst-ratings/{symbol}", response_model=SentimentResponse)
async def get_analyst_ratings_sentiment(
    symbol: str,
    hours: int = Query(default=24, ge=1, le=168, description="Hours parameter (not used for analyst ratings, kept for API compatibility)")
):
    """
    Get analyst ratings sentiment for a symbol
    
    Args:
        symbol: Stock symbol (e.g., AAPL, SPY)
        hours: Hours parameter (kept for API compatibility, not used for analyst ratings)
    
    Returns:
        Current sentiment data for the symbol based on analyst ratings
    """
    provider = get_analyst_ratings_provider()
    
    if not provider.is_available():
        raise HTTPException(
            status_code=503,
            detail="Analyst Ratings sentiment provider is not available."
        )
    
    try:
        sentiment = provider.get_sentiment(symbol.upper(), hours=hours)
        
        if sentiment is None:
            raise HTTPException(
                status_code=404,
                detail=f"No analyst ratings sentiment data available for {symbol}"
            )
        
        return SentimentResponse(
            symbol=sentiment.symbol,
            timestamp=sentiment.timestamp,
            mention_count=sentiment.mention_count,
            average_sentiment=sentiment.average_sentiment,
            weighted_sentiment=sentiment.weighted_sentiment,
            influencer_sentiment=sentiment.influencer_sentiment,
            engagement_score=sentiment.engagement_score,
            sentiment_level=sentiment.sentiment_level.value,
            confidence=sentiment.confidence,
            volume_trend=sentiment.volume_trend
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting Analyst Ratings sentiment for {symbol}: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Error retrieving sentiment data: {str(e)}"
        )


@router.get("/analyst-ratings/{symbol}/rating")
async def get_analyst_rating_details(
    symbol: str
):
    """
    Get detailed analyst rating data for a symbol
    
    Args:
        symbol: Stock symbol
    
    Returns:
        Detailed analyst rating information including price targets
    """
    provider = get_analyst_ratings_provider()
    
    if not provider.is_available():
        raise HTTPException(
            status_code=503,
            detail="Analyst Ratings provider is not available."
        )
    
    try:
        rating = provider.get_analyst_rating(symbol.upper())
        
        if rating is None:
            raise HTTPException(
                status_code=404,
                detail=f"No analyst rating data available for {symbol}"
            )
        
        return {
            "symbol": rating.symbol,
            "rating": rating.rating,
            "rating_numeric": rating.rating_numeric,
            "price_target": rating.price_target,
            "price_target_high": rating.price_target_high,
            "price_target_low": rating.price_target_low,
            "price_target_mean": rating.price_target_mean,
            "number_of_analysts": rating.number_of_analysts,
            "current_price": rating.current_price,
            "price_target_upside": rating.price_target_upside,
            "timestamp": rating.timestamp
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting analyst rating for {symbol}: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Error retrieving analyst rating: {str(e)}"
        )


@router.post("/analyst-ratings/batch")
async def get_analyst_ratings_batch(
    symbols: List[str] = Body(..., description="List of stock symbols to fetch ratings for", example=["AAPL", "MSFT", "TSLA"])
):
    """
    Get analyst ratings for multiple symbols (batch fetch)
    
    Args:
        symbols: List of stock symbols
    
    Returns:
        Dictionary mapping symbols to analyst rating data
    """
    provider = get_analyst_ratings_provider()
    
    if not provider.is_available():
        raise HTTPException(
            status_code=503,
            detail="Analyst Ratings provider is not available."
        )
    
    if not symbols or len(symbols) == 0:
        raise HTTPException(
            status_code=400,
            detail="Symbols list cannot be empty"
        )
    
    if len(symbols) > 50:
        raise HTTPException(
            status_code=400,
            detail="Maximum 50 symbols per batch request"
        )
    
    try:
        ratings = provider.get_analyst_ratings_batch(symbols)
        
        # Format response
        result = {}
        for symbol, rating in ratings.items():
            if rating:
                result[symbol] = {
                    "symbol": rating.symbol,
                    "rating": rating.rating,
                    "rating_numeric": rating.rating_numeric,
                    "price_target": rating.price_target,
                    "price_target_high": rating.price_target_high,
                    "price_target_low": rating.price_target_low,
                    "price_target_mean": rating.price_target_mean,
                    "number_of_analysts": rating.number_of_analysts,
                    "current_price": rating.current_price,
                    "price_target_upside": rating.price_target_upside,
                    "timestamp": rating.timestamp
                }
            else:
                result[symbol] = None
        
        return {
            "ratings": result,
            "count": len([r for r in ratings.values() if r is not None]),
            "total_requested": len(symbols)
        }
    
    except Exception as e:
        logger.error(f"Error getting batch analyst ratings: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Error retrieving batch analyst ratings: {str(e)}"
        )


# ==================== News Sentiment Endpoints ====================

@router.get("/news/status")
async def news_status():
    """Get News sentiment provider status"""
    provider = get_news_provider()
    
    return {
        "available": provider.is_available(),
        "persist_to_db": provider.persist_to_db,
        "cache_enabled": True,
        "cache_ttl": provider.cache_ttl
    }


@router.get("/news/{symbol}", response_model=SentimentResponse)
async def get_news_sentiment(
    symbol: str,
    hours: int = Query(default=24, ge=1, le=168, description="Hours of data to analyze")
):
    """
    Get financial news sentiment for a symbol
    
    Args:
        symbol: Stock symbol (e.g., AAPL, SPY)
        hours: Hours of historical data to analyze (1-168, default: 24)
    
    Returns:
        Current sentiment data for the symbol from news articles
    """
    provider = get_news_provider()
    
    if not provider.is_available():
        raise HTTPException(
            status_code=503,
            detail="News sentiment provider is not available. Check dependencies."
        )
    
    try:
        sentiment = provider.get_sentiment(symbol.upper(), hours=hours)
        
        if sentiment is None:
            raise HTTPException(
                status_code=404,
                detail=f"No news sentiment data available for {symbol}"
            )
        
        return SentimentResponse(
            symbol=sentiment.symbol,
            timestamp=sentiment.timestamp,
            mention_count=sentiment.mention_count,
            average_sentiment=sentiment.average_sentiment,
            weighted_sentiment=sentiment.weighted_sentiment,
            influencer_sentiment=sentiment.influencer_sentiment,
            engagement_score=sentiment.engagement_score,
            sentiment_level=sentiment.sentiment_level.value,
            confidence=sentiment.confidence,
            volume_trend=sentiment.volume_trend
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting news sentiment for {symbol}: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Error retrieving news sentiment: {str(e)}"
        )


@router.get("/news/{symbol}/articles", response_model=List[TweetMentionResponse])
async def get_news_articles(
    symbol: str,
    hours: int = Query(default=24, ge=1, le=168, description="Hours of data to retrieve"),
    limit: int = Query(default=50, ge=1, le=200, description="Maximum number of articles"),
    db: Session = Depends(get_db)
):
    """
    Get recent news articles mentioning a symbol
    
    Args:
        symbol: Stock symbol
        hours: Hours of historical data
        limit: Maximum number of articles to return
    
    Returns:
        List of news articles mentioning the symbol
    """
    try:
        repository = SentimentRepository(db=db)
        
        # Filter for news articles (prefixed with "news_")
        tweets = repository.get_tweets_for_symbol(symbol.upper(), hours=hours, limit=limit * 2)
        
        # Filter to only news articles and limit
        news_articles = [
            tweet for tweet in tweets 
            if tweet.tweet_id.startswith("news_")
        ][:limit]
        
        # Get sentiment scores for these articles
        result = []
        for tweet in news_articles:
            # Get sentiment for this article
            sentiments = [
                ts for ts in tweet.sentiments 
                if ts.symbol == symbol.upper()
            ]
            
            sentiment_score = None
            sentiment_level = None
            
            if sentiments:
                # Use most recent sentiment
                latest = sorted(sentiments, key=lambda x: x.analyzed_at, reverse=True)[0]
                sentiment_score = latest.sentiment_score
                sentiment_level = latest.sentiment_level
            
            result.append(TweetMentionResponse(
                tweet_id=tweet.tweet_id.replace("news_", ""),  # Remove prefix for display
                text=tweet.text[:500],  # Truncate for display
                author_username=tweet.author_username,
                created_at=tweet.created_at,
                like_count=tweet.like_count,
                retweet_count=tweet.retweet_count,
                sentiment_score=sentiment_score,
                sentiment_level=sentiment_level
            ))
        
        return result
    
    except Exception as e:
        logger.error(f"Error getting news articles for {symbol}: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Error retrieving news articles: {str(e)}"
        )


# ============================================================================
# Aggregated Sentiment Endpoints
# ============================================================================

class AggregatedSentimentResponse(BaseModel):
    """Aggregated sentiment response model"""
    symbol: str
    timestamp: datetime
    unified_sentiment: float
    confidence: float
    sentiment_level: str
    total_mention_count: int
    provider_count: int
    providers_used: List[str]
    divergence_detected: bool
    divergence_score: float
    volume_trend: str
    twitter_sentiment: Optional[float] = None
    reddit_sentiment: Optional[float] = None
    options_sentiment: Optional[float] = None
    
    class Config:
        from_attributes = True


class ProviderBreakdownResponse(BaseModel):
    """Provider sentiment breakdown"""
    provider_name: str
    sentiment_score: float
    confidence: float
    mention_count: int
    weight: float
    time_decay_factor: float
    included: bool
    reason_excluded: Optional[str] = None


class AggregatedSentimentDetailedResponse(AggregatedSentimentResponse):
    """Detailed aggregated sentiment with provider breakdown"""
    provider_breakdown: List[ProviderBreakdownResponse]


@router.get("/aggregated/{symbol}", response_model=AggregatedSentimentResponse)
async def get_aggregated_sentiment(
    symbol: str,
    hours: int = Query(default=24, ge=1, le=168, description="Hours of data to analyze")
):
    """
    Get aggregated sentiment for a symbol from all available providers
    
    This endpoint combines sentiment data from Twitter, Reddit, and other sources
    into a unified sentiment score with weighted aggregation, time-decay, and
    divergence detection.
    
    Args:
        symbol: Stock symbol (e.g., AAPL, SPY)
        hours: Hours of historical data to analyze (1-168, default: 24)
    
    Returns:
        Aggregated sentiment data from all providers
    """
    aggregator = get_aggregator()
    
    try:
        aggregated = aggregator.get_aggregated_sentiment(symbol.upper(), hours=hours)
        
        if aggregated is None:
            raise HTTPException(
                status_code=404,
                detail=f"No aggregated sentiment data available for {symbol}. "
                       f"Minimum providers required: {aggregator.config.min_providers}"
            )
        
        return AggregatedSentimentResponse(
            symbol=aggregated.symbol,
            timestamp=aggregated.timestamp,
            unified_sentiment=aggregated.unified_sentiment,
            confidence=aggregated.confidence,
            sentiment_level=aggregated.sentiment_level.value,
            total_mention_count=aggregated.total_mention_count,
            provider_count=aggregated.provider_count,
            providers_used=aggregated.providers_used,
            divergence_detected=aggregated.divergence_detected,
            divergence_score=aggregated.divergence_score,
            volume_trend=aggregated.volume_trend,
            twitter_sentiment=aggregated.twitter_sentiment,
            reddit_sentiment=aggregated.reddit_sentiment,
            options_sentiment=aggregated.options_sentiment
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting aggregated sentiment for {symbol}: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Error retrieving aggregated sentiment: {str(e)}"
        )


@router.get("/aggregated/{symbol}/detailed", response_model=AggregatedSentimentDetailedResponse)
async def get_aggregated_sentiment_detailed(
    symbol: str,
    hours: int = Query(default=24, ge=1, le=168, description="Hours of data to analyze")
):
    """
    Get detailed aggregated sentiment with provider breakdown
    
    Returns the same aggregated sentiment but includes detailed information
    about each provider's contribution.
    
    Args:
        symbol: Stock symbol
        hours: Hours of historical data to analyze
    
    Returns:
        Detailed aggregated sentiment with provider breakdown
    """
    aggregator = get_aggregator()
    
    try:
        aggregated = aggregator.get_aggregated_sentiment(symbol.upper(), hours=hours)
        
        if aggregated is None:
            raise HTTPException(
                status_code=404,
                detail=f"No aggregated sentiment data available for {symbol}"
            )
        
        # Build provider breakdown from sources
        provider_breakdown = []
        for source_name, source_sent in aggregated.sources.items():
            # Calculate time decay factor
            time_weight = 1.0  # TODO: Calculate from timestamp
            source_weight = aggregated.source_breakdown.get(source_name, 0.0) / 100.0 if source_name in aggregated.source_breakdown else source_sent.source_weight
            
            provider_breakdown.append(ProviderBreakdownResponse(
                provider_name=source_name,
                sentiment_score=source_sent.sentiment_score,
                confidence=source_sent.confidence,
                mention_count=source_sent.mention_count,
                weight=source_weight,
                time_decay_factor=time_weight,
                included=True,  # Only included sources are in aggregated.sources
                reason_excluded=None
            ))
        
        return AggregatedSentimentDetailedResponse(
            symbol=aggregated.symbol,
            timestamp=aggregated.timestamp,
            unified_sentiment=aggregated.unified_sentiment,
            confidence=aggregated.confidence,
            sentiment_level=aggregated.sentiment_level.value,
            total_mention_count=aggregated.total_mention_count,
            provider_count=aggregated.provider_count,
            providers_used=aggregated.providers_used,
            divergence_detected=aggregated.divergence_detected,
            divergence_score=aggregated.divergence_score,
            volume_trend=aggregated.volume_trend,
            twitter_sentiment=aggregated.twitter_sentiment,
            reddit_sentiment=aggregated.reddit_sentiment,
            options_sentiment=aggregated.options_sentiment,
            provider_breakdown=provider_breakdown
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting detailed aggregated sentiment for {symbol}: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Error retrieving detailed aggregated sentiment: {str(e)}"
        )


# ==================== News Sentiment Endpoints ====================

@router.get("/news/status")
async def news_status():
    """Get News sentiment provider status"""
    provider = get_news_provider()
    
    return {
        "available": provider.is_available(),
        "persist_to_db": provider.persist_to_db,
        "cache_enabled": True,
        "cache_ttl": provider.cache_ttl
    }


@router.get("/news/{symbol}", response_model=SentimentResponse)
async def get_news_sentiment(
    symbol: str,
    hours: int = Query(default=24, ge=1, le=168, description="Hours of data to analyze")
):
    """
    Get news sentiment for a symbol
    
    Args:
        symbol: Stock symbol (e.g., AAPL, SPY)
        hours: Hours of historical data to analyze (1-168, default: 24)
    
    Returns:
        Current sentiment data for the symbol from news sources
    """
    provider = get_news_provider()
    
    if not provider.is_available():
        raise HTTPException(
            status_code=503,
            detail="News sentiment provider is not available. Check configuration."
        )
    
    try:
        sentiment = provider.get_sentiment(symbol.upper(), hours=hours)
        
        if sentiment is None:
            raise HTTPException(
                status_code=404,
                detail=f"No news sentiment data available for {symbol}"
            )
        
        return SentimentResponse(
            symbol=sentiment.symbol,
            timestamp=sentiment.timestamp,
            mention_count=sentiment.mention_count,
            average_sentiment=sentiment.average_sentiment,
            weighted_sentiment=sentiment.weighted_sentiment,
            influencer_sentiment=sentiment.influencer_sentiment,
            engagement_score=sentiment.engagement_score,
            sentiment_level=sentiment.sentiment_level.value,
            confidence=sentiment.confidence,
            volume_trend=sentiment.volume_trend
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting news sentiment for {symbol}: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Error retrieving sentiment data: {str(e)}"
        )


@router.get("/news/{symbol}/articles", response_model=List[TweetMentionResponse])
async def get_news_articles(
    symbol: str,
    hours: int = Query(default=24, ge=1, le=168, description="Hours of data to retrieve"),
    limit: int = Query(default=50, ge=1, le=200, description="Maximum number of articles"),
    db: Session = Depends(get_db)
):
    """
    Get recent news articles mentioning a symbol
    
    Args:
        symbol: Stock symbol
        hours: Hours of historical data
        limit: Maximum number of articles to return
    
    Returns:
        List of news articles mentioning the symbol
    """
    try:
        repository = SentimentRepository(db=db)
        
        # Filter for news articles (prefixed with "news_")
        tweets = repository.get_tweets_for_symbol(symbol.upper(), hours=hours, limit=limit * 2)
        
        # Filter to only news articles and limit
        news_articles = [
            tweet for tweet in tweets 
            if tweet.tweet_id.startswith("news_")
        ][:limit]
        
        # Get sentiment scores for these articles
        result = []
        for tweet in news_articles:
            # Get sentiment for this article
            sentiments = [
                ts for ts in tweet.sentiments 
                if ts.symbol == symbol.upper()
            ]
            
            sentiment_score = None
            sentiment_level = None
            
            if sentiments:
                # Use most recent sentiment
                latest = sorted(sentiments, key=lambda x: x.analyzed_at, reverse=True)[0]
                sentiment_score = latest.sentiment_score
                sentiment_level = latest.sentiment_level
            
            result.append(TweetMentionResponse(
                tweet_id=tweet.tweet_id.replace("news_", ""),  # Remove prefix for display
                text=tweet.text,
                author_username=tweet.author_username,  # This will be the news source
                created_at=tweet.created_at,
                like_count=tweet.like_count,
                retweet_count=tweet.retweet_count,
                sentiment_score=sentiment_score,
                sentiment_level=sentiment_level
            ))
        
        return result
    
    except Exception as e:
        logger.error(f"Error getting news articles for {symbol}: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Error retrieving articles: {str(e)}"
        )


# ==================== StockTwits Sentiment Endpoints ====================

@router.get("/stocktwits/status")
async def stocktwits_status():
    """Get StockTwits sentiment provider status"""
    provider = get_stocktwits_provider()
    
    return {
        "available": provider.is_available(),
        "persist_to_db": provider.persist_to_db,
        "cache_enabled": True,
        "cache_ttl": provider.cache_ttl
    }


@router.get("/stocktwits/{symbol}", response_model=SentimentResponse)
async def get_stocktwits_sentiment(
    symbol: str,
    hours: int = Query(default=24, ge=1, le=168, description="Hours of data to analyze")
):
    """
    Get StockTwits sentiment for a symbol
    
    Args:
        symbol: Stock symbol (e.g., AAPL, SPY)
        hours: Hours of historical data to analyze (1-168, default: 24)
    
    Returns:
        Current sentiment data for the symbol from StockTwits
    """
    provider = get_stocktwits_provider()
    
    if not provider.is_available():
        raise HTTPException(
            status_code=503,
            detail="StockTwits sentiment provider is not available. Check dependencies."
        )
    
    try:
        sentiment = provider.get_sentiment(symbol.upper(), hours=hours)
        
        if sentiment is None:
            raise HTTPException(
                status_code=404,
                detail=f"No StockTwits sentiment data available for {symbol}"
            )
        
        return SentimentResponse(
            symbol=sentiment.symbol,
            timestamp=sentiment.timestamp,
            mention_count=sentiment.mention_count,
            average_sentiment=sentiment.average_sentiment,
            weighted_sentiment=sentiment.weighted_sentiment,
            influencer_sentiment=sentiment.influencer_sentiment,
            engagement_score=sentiment.engagement_score,
            sentiment_level=sentiment.sentiment_level.value,
            confidence=sentiment.confidence,
            volume_trend=sentiment.volume_trend
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting StockTwits sentiment for {symbol}: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Error retrieving sentiment data: {str(e)}"
        )


@router.get("/stocktwits/{symbol}/messages", response_model=List[TweetMentionResponse])
async def get_stocktwits_messages(
    symbol: str,
    hours: int = Query(default=24, ge=1, le=168, description="Hours of data to retrieve"),
    limit: int = Query(default=50, ge=1, le=200, description="Maximum number of messages"),
    db: Session = Depends(get_db)
):
    """
    Get recent StockTwits messages mentioning a symbol
    
    Args:
        symbol: Stock symbol
        hours: Hours of historical data
        limit: Maximum number of messages to return
    
    Returns:
        List of StockTwits messages mentioning the symbol
    """
    try:
        repository = SentimentRepository(db=db)
        
        # Filter for StockTwits messages (prefixed with "stocktwits_")
        tweets = repository.get_tweets_for_symbol(symbol.upper(), hours=hours, limit=limit * 2)
        
        # Filter to only StockTwits messages and limit
        stocktwits_messages = [
            tweet for tweet in tweets 
            if tweet.tweet_id.startswith("stocktwits_")
        ][:limit]
        
        # Get sentiment scores for these messages
        result = []
        for tweet in stocktwits_messages:
            # Get sentiment for this tweet
            sentiments = [
                ts for ts in tweet.sentiments 
                if ts.symbol == symbol.upper()
            ]
            
            sentiment_score = None
            sentiment_level = None
            
            if sentiments:
                # Use most recent sentiment
                latest = sorted(sentiments, key=lambda x: x.analyzed_at, reverse=True)[0]
                sentiment_score = latest.sentiment_score
                sentiment_level = latest.sentiment_level
            
            result.append(TweetMentionResponse(
                tweet_id=tweet.tweet_id.replace("stocktwits_", ""),  # Remove prefix for display
                text=tweet.text,
                author_username=tweet.author_username,
                created_at=tweet.created_at,
                like_count=tweet.like_count,
                retweet_count=tweet.retweet_count,
                sentiment_score=sentiment_score,
                sentiment_level=sentiment_level
            ))
        
        return result
    
    except Exception as e:
        logger.error(f"Error getting StockTwits messages for {symbol}: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Error retrieving messages: {str(e)}"
        )


@router.get("/stocktwits/trending")
async def get_stocktwits_trending_symbols(
    min_watchlist: int = Query(default=100, ge=1, description="Minimum watchlist count to be trending"),
    limit: int = Query(default=20, ge=1, le=100, description="Maximum number of symbols to return")
):
    """
    Get trending stock symbols on StockTwits based on watchlist counts
    
    Args:
        min_watchlist: Minimum watchlist count to be considered trending
        limit: Maximum number of symbols to return
    
    Returns:
        List of trending symbols with watchlist counts
    """
    provider = get_stocktwits_provider()
    
    if not provider.is_available():
        raise HTTPException(
            status_code=503,
            detail="StockTwits sentiment provider is not available. Check dependencies."
        )
    
    try:
        trending = provider.get_trending_symbols(min_watchlist=min_watchlist)
        
        # Limit results
        trending = trending[:limit]
        
        return {
            "trending": trending,
            "count": len(trending),
            "min_watchlist": min_watchlist
        }
    
    except Exception as e:
        logger.error(f"Error getting StockTwits trending symbols: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Error retrieving trending symbols: {str(e)}"
        )


# ==================== SEC Filings Sentiment Endpoints ====================

@router.get("/sec-filings/status")
async def sec_filings_status():
    """Get SEC filings sentiment provider status"""
    provider = get_sec_filings_provider()
    
    if provider is None:
        return {
            "available": False,
            "error": "SEC Filings provider not available (dependencies may not be installed)"
        }
    
    return {
        "available": provider.is_available(),
        "persist_to_db": provider.persist_to_db,
        "cache_enabled": True,
        "cache_ttl": provider.cache_ttl
    }


@router.get("/sec-filings/{symbol}", response_model=SentimentResponse)
async def get_sec_filings_sentiment(
    symbol: str,
    hours: int = Query(default=8760, ge=1, le=17520, description="Hours of historical filings to analyze (1-17520, ~2 years). Note: SEC filings are infrequent, so longer windows recommended."),
    filing_types: Optional[str] = Query(default=None, description="Comma-separated filing types (e.g., '10-K,10-Q,8-K')")
):
    """
    Get SEC filings sentiment for a symbol
    
    Args:
        symbol: Stock symbol (e.g., AAPL, MSFT)
        hours: Hours of historical filings to analyze (default: 8760 = 365 days, max: 17520 = ~2 years)
               Note: Since SEC filings are quarterly/yearly, longer windows are recommended
        filing_types: Comma-separated list of filing types (default: 10-K,10-Q,8-K)
    
    Returns:
        Current sentiment data for the symbol from SEC filings
    """
    provider = get_sec_filings_provider()
    
    if provider is None:
        raise HTTPException(
            status_code=503,
            detail="SEC filings sentiment provider is not available. Install sec-edgar-downloader: pip install sec-edgar-downloader"
        )
    
    if not provider.is_available():
        raise HTTPException(
            status_code=503,
            detail="SEC filings sentiment provider is not available. Check configuration (SEC_FILINGS_USER_AGENT, SEC_FILINGS_EMAIL_ADDRESS)."
        )
    
    # Parse filing types
    filing_types_list = None
    if filing_types:
        filing_types_list = [ft.strip() for ft in filing_types.split(",")]
    
    try:
        sentiment = provider.get_sentiment(
            symbol=symbol.upper(),
            hours=hours,
            filing_types=filing_types_list
        )
        
        if sentiment is None:
            days = max(30, int(hours / 24))
            raise HTTPException(
                status_code=404,
                detail=f"No SEC filings sentiment data available for {symbol} in the last {days} days ({hours} hours)"
            )
        
        return SentimentResponse(
            symbol=sentiment.symbol,
            timestamp=sentiment.timestamp,
            mention_count=sentiment.mention_count,
            average_sentiment=sentiment.average_sentiment,
            weighted_sentiment=sentiment.weighted_sentiment,
            influencer_sentiment=sentiment.influencer_sentiment,
            engagement_score=sentiment.engagement_score,
            sentiment_level=sentiment.sentiment_level.value,
            confidence=sentiment.confidence,
            volume_trend=sentiment.volume_trend
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting SEC filings sentiment for {symbol}: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Error retrieving SEC filings sentiment: {str(e)}"
        )


@router.get("/news/{symbol}/trend", response_model=SentimentTrendResponse)
async def get_news_sentiment_trend(
    symbol: str,
    hours: int = Query(default=24, ge=1, le=168, description="Hours of historical data"),
    interval_hours: int = Query(default=1, ge=1, le=24, description="Interval between data points"),
    db: Session = Depends(get_db)
):
    """
    Get news sentiment trend over time for a symbol
    
    Args:
        symbol: Stock symbol
        hours: Total hours of historical data
        interval_hours: Interval between data points
    
    Returns:
        Sentiment trend data
    """
    try:
        repository = SentimentRepository(db=db)
        sentiments = repository.get_recent_sentiment(
            symbol.upper(), 
            hours=hours, 
            limit=1000
        )
        
        # Filter to news-only sentiments (would need source tracking in future)
        # For now, we'll use all sentiments but could be enhanced
        
        if not sentiments:
            raise HTTPException(
                status_code=404,
                detail=f"No historical news sentiment data available for {symbol}"
            )
        
        # Group by time intervals (same logic as Reddit/Twitter)
        cutoff = datetime.now() - timedelta(hours=hours)
        interval_seconds = interval_hours * 3600
        
        grouped = {}
        for sentiment in sentiments:
            if sentiment.timestamp < cutoff:
                continue
            
            # Round to interval
            interval_key = int((sentiment.timestamp - cutoff).total_seconds() / interval_seconds)
            
            if interval_key not in grouped:
                grouped[interval_key] = []
            
            grouped[interval_key].append(sentiment)
        
        # Calculate average for each interval
        data_points = []
        for interval_key in sorted(grouped.keys()):
            interval_sentiments = grouped[interval_key]
            
            avg_sentiment = sum(s.weighted_sentiment for s in interval_sentiments) / len(interval_sentiments)
            avg_mention_count = sum(s.mention_count for s in interval_sentiments) / len(interval_sentiments)
            avg_timestamp = max(s.timestamp for s in interval_sentiments)
            
            # Get most common sentiment level
            sentiment_levels = [s.sentiment_level for s in interval_sentiments]
            most_common_level = max(set(sentiment_levels), key=sentiment_levels.count)
            
            data_points.append(SentimentResponse(
                symbol=symbol.upper(),
                timestamp=avg_timestamp,
                mention_count=int(avg_mention_count),
                average_sentiment=avg_sentiment,
                weighted_sentiment=avg_sentiment,
                engagement_score=0.0,
                sentiment_level=most_common_level,
                confidence=0.0,
                volume_trend="stable"
            ))
        
        # Calculate trend direction
        if len(data_points) >= 2:
            first_half = data_points[:len(data_points)//2]
            second_half = data_points[len(data_points)//2:]
            
            first_avg = sum(p.weighted_sentiment for p in first_half) / len(first_half)
            second_avg = sum(p.weighted_sentiment for p in second_half) / len(second_half)
            
            change = second_avg - first_avg
            
            if change > 0.1:
                trend_direction = "up"
            elif change < -0.1:
                trend_direction = "down"
            else:
                trend_direction = "stable"
            
            average_change = change
        else:
            trend_direction = "stable"
            average_change = 0.0
        
        return SentimentTrendResponse(
            symbol=symbol.upper(),
            data_points=data_points,
            trend_direction=trend_direction,
            average_change=average_change
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting news trend for {symbol}: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Error retrieving trend: {str(e)}"
        )


@router.get("/news/trending")
async def get_news_trending_symbols(
    min_mentions: int = Query(default=5, ge=1, description="Minimum mentions to be trending"),
    limit: int = Query(default=20, ge=1, le=100, description="Maximum number of symbols to return")
):
    """
    Get trending stock symbols in news based on mention counts
    
    Args:
        min_mentions: Minimum mentions to be considered trending
        limit: Maximum number of symbols to return
    
    Returns:
        List of trending symbols with mention counts
    """
    provider = get_news_provider()
    
    if not provider.is_available():
        raise HTTPException(
            status_code=503,
            detail="News sentiment provider is not available. Check configuration."
        )
    
    try:
        trending = provider.get_trending_symbols(min_mentions=min_mentions)
        
        # Limit results
        trending = trending[:limit]
        
        return {
            "trending": trending,
            "count": len(trending),
            "min_mentions": min_mentions
        }
    
    except Exception as e:
        logger.error(f"Error getting news trending symbols: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Error retrieving trending symbols: {str(e)}"
        )


@router.get("/aggregated/status")
async def get_aggregator_status():
    """Get sentiment aggregator status and available providers"""
    aggregator = get_aggregator()
    
    available_providers = aggregator.get_available_providers()
    
    return {
        "available_providers": available_providers,
        "provider_count": len(available_providers),
        "min_providers_required": aggregator.config.min_providers,
        "weights": {
            "twitter": aggregator.config.weight_twitter,
            "reddit": aggregator.config.weight_reddit,
            "stocktwits": aggregator.config.weight_stocktwits,
            "news": aggregator.config.weight_news,
            "options": aggregator.config.weight_options
        },
        "time_decay_enabled": aggregator.config.time_decay_enabled,
        "time_decay_half_life_hours": aggregator.config.time_decay_half_life_hours,
        "divergence_threshold": aggregator.config.divergence_threshold,
        "min_provider_confidence": aggregator.config.min_provider_confidence
    }

