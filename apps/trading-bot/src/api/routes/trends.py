"""
Trends Data API Routes
======================

API endpoints for trends and search interest data (Google Trends, etc.).
"""

from fastapi import APIRouter, HTTPException, Query
from typing import Optional
from pydantic import BaseModel
import logging
from datetime import datetime

from ...data.providers.trends import GoogleTrendsProvider

logger = logging.getLogger(__name__)
router = APIRouter()

# Global provider instance
_trends_provider: Optional[GoogleTrendsProvider] = None


def get_trends_provider() -> GoogleTrendsProvider:
    """Get or create Google Trends provider instance"""
    global _trends_provider
    if _trends_provider is None:
        try:
            _trends_provider = GoogleTrendsProvider()
        except Exception as e:
            logger.error(f"Failed to initialize Google Trends provider: {e}")
            raise
    return _trends_provider


# Response Models
class InterestDataResponse(BaseModel):
    """Interest data response"""
    symbol: str
    keyword: str
    interest_score: float  # 0-100
    max_interest: float
    recent_avg_interest: float
    trend_change: float  # Percentage change
    trend_score: float  # -100 to 100
    timeframe: str
    geo: str
    top_rising_queries: list
    top_queries: list
    timestamp: datetime


class TrendSentimentResponse(BaseModel):
    """Trend-based sentiment response"""
    symbol: str
    timestamp: datetime
    interest_score: float  # 0-100
    sentiment_score: float  # -1.0 to 1.0
    sentiment_level: str
    confidence: float
    trend_direction: str
    trend_change: float


@router.get("/status")
async def trends_status():
    """Get Google Trends provider status"""
    if GoogleTrendsProvider is None:
        return {
            "available": False,
            "error": "Google Trends provider not available (missing dependencies)"
        }
    
    try:
        provider = get_trends_provider()
        return {
            "available": provider.is_available(),
            "cache_ttl": provider.config.cache_ttl,
            "rate_limit_enabled": provider.config.rate_limit_enabled,
            "default_geo": provider.config.default_geo
        }
    except Exception as e:
        return {
            "available": False,
            "error": str(e)
        }


@router.get("/{symbol}", response_model=InterestDataResponse)
async def get_trends(
    symbol: str,
    timeframe: str = Query(
        default="today 1-m",
        description="Timeframe for trends (e.g., 'today 1-m', 'today 3-m', 'today 12-m')"
    ),
    geo: str = Query(default="US", description="Geographic location")
):
    """
    Get Google Trends search interest data for a symbol
    
    Args:
        symbol: Stock symbol (e.g., AAPL, SPY)
        timeframe: Timeframe for trends
        geo: Geographic location (default: US)
    
    Returns:
        Interest data with trend information
    """
    if GoogleTrendsProvider is None:
        raise HTTPException(
            status_code=503,
            detail="Google Trends provider is not available. Install required dependencies (pytrends)."
        )
    
    try:
        provider = get_trends_provider()
        
        if not provider.is_available():
            raise HTTPException(
                status_code=503,
                detail="Google Trends provider is not available. Check configuration."
            )
        
        interest_data = provider.get_search_interest(
            symbol.upper(),
            timeframe=timeframe,
            geo=geo
        )
        
        if interest_data is None:
            raise HTTPException(
                status_code=404,
                detail=f"No Google Trends data available for {symbol}"
            )
        
        return InterestDataResponse(**interest_data)
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting Google Trends data for {symbol}: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Error retrieving trends data: {str(e)}"
        )


@router.get("/{symbol}/sentiment", response_model=TrendSentimentResponse)
async def get_trend_sentiment(
    symbol: str,
    hours: int = Query(default=24, ge=1, le=720, description="Hours of historical data")
):
    """
    Get sentiment-like score based on Google Trends search interest
    
    Converts search interest and trend data into a sentiment score that can
    be integrated with other sentiment sources.
    
    Args:
        symbol: Stock symbol
        hours: Hours of historical data
    
    Returns:
        Trend-based sentiment data
    """
    if GoogleTrendsProvider is None:
        raise HTTPException(
            status_code=503,
            detail="Google Trends provider is not available. Install required dependencies (pytrends)."
        )
    
    try:
        provider = get_trends_provider()
        
        if not provider.is_available():
            raise HTTPException(
                status_code=503,
                detail="Google Trends provider is not available. Check configuration."
            )
        
        sentiment = provider.get_interest_sentiment(symbol.upper(), hours=hours)
        
        if sentiment is None:
            raise HTTPException(
                status_code=404,
                detail=f"No trend sentiment data available for {symbol}"
            )
        
        # Get interest data for additional context
        interest_data = provider.get_search_interest(symbol.upper())
        
        return TrendSentimentResponse(
            symbol=sentiment.symbol,
            timestamp=sentiment.timestamp,
            interest_score=sentiment.mention_count,  # Interest score used as mention count
            sentiment_score=sentiment.weighted_sentiment,
            sentiment_level=sentiment.sentiment_level.value,
            confidence=sentiment.confidence,
            trend_direction=sentiment.volume_trend,
            trend_change=interest_data.get('trend_change', 0.0) if interest_data else 0.0
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting trend sentiment for {symbol}: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Error retrieving trend sentiment: {str(e)}"
        )


@router.get("/{symbol}/related")
async def get_related_searches(
    symbol: str,
    geo: str = Query(default="US", description="Geographic location")
):
    """
    Get related search queries for a symbol
    
    Args:
        symbol: Stock symbol
        geo: Geographic location
    
    Returns:
        Related search queries (rising and top)
    """
    if GoogleTrendsProvider is None:
        raise HTTPException(
            status_code=503,
            detail="Google Trends provider is not available. Install required dependencies (pytrends)."
        )
    
    try:
        provider = get_trends_provider()
        
        if not provider.is_available():
            raise HTTPException(
                status_code=503,
                detail="Google Trends provider is not available. Check configuration."
            )
        
        interest_data = provider.get_search_interest(
            symbol.upper(),
            timeframe="today 1-m",
            geo=geo
        )
        
        if interest_data is None:
            raise HTTPException(
                status_code=404,
                detail=f"No related searches data available for {symbol}"
            )
        
        return {
            "symbol": symbol.upper(),
            "geo": geo,
            "top_rising": interest_data.get('top_rising_queries', []),
            "top_queries": interest_data.get('top_queries', [])
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting related searches for {symbol}: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Error retrieving related searches: {str(e)}"
        )

