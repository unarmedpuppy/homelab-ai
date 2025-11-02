"""
Event Calendar API Routes
=========================

API endpoints for earnings calendar and corporate events.
"""

from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional
from pydantic import BaseModel
import logging
from datetime import datetime

from ...data.providers.events import EarningsCalendarProvider, EarningsEvent, EventCalendarEntry
from ...api.models.errors import create_error_response

logger = logging.getLogger(__name__)
router = APIRouter()

# Global provider instance
_calendar_provider: Optional[EarningsCalendarProvider] = None


def get_calendar_provider() -> EarningsCalendarProvider:
    """Get or create earnings calendar provider instance"""
    global _calendar_provider
    if _calendar_provider is None:
        try:
            _calendar_provider = EarningsCalendarProvider()
        except Exception as e:
            logger.error(f"Failed to initialize earnings calendar provider: {e}")
            raise
    return _calendar_provider


# Response Models
class EarningsEventResponse(BaseModel):
    """Earnings event response"""
    symbol: str
    event_date: datetime
    event_type: str
    confirmed: bool
    estimated: bool
    time_of_day: Optional[str] = None
    metadata: dict = {}


class EventCalendarResponse(BaseModel):
    """Event calendar response"""
    symbol: str
    events: List[EarningsEventResponse]
    next_earnings_date: Optional[datetime] = None
    last_earnings_date: Optional[datetime] = None
    earnings_frequency: str
    metadata: dict = {}


@router.get("/status")
async def calendar_status():
    """Get earnings calendar provider status"""
    try:
        provider = get_calendar_provider()
        return {
            "available": provider.is_available(),
            "cache_ttl": provider.config.cache_ttl,
            "lookahead_days": provider.config.lookahead_days,
            "economic_events_enabled": provider.config.economic_events_enabled
        }
    except Exception as e:
        return {
            "available": False,
            "error": str(e)
        }


@router.get("/earnings/{symbol}", response_model=EventCalendarResponse)
async def get_earnings_calendar(
    symbol: str,
    days_ahead: Optional[int] = Query(default=None, ge=1, le=365, description="Days ahead to fetch")
):
    """
    Get earnings calendar for a symbol
    
    Args:
        symbol: Stock symbol (e.g., AAPL, SPY)
        days_ahead: Days ahead to fetch (default: from config)
    
    Returns:
        Earnings calendar with upcoming and past events
    """
    try:
        provider = get_calendar_provider()
        
        if not provider.is_available():
            error = create_error_response(
                message="Earnings calendar provider is not available. Check configuration.",
                error_code="PROVIDER_UNAVAILABLE",
                path=f"/api/data/events/earnings/{symbol}",
                status_code=503
            )
            raise HTTPException(status_code=503, detail=error)
        
        calendar = provider.get_calendar(symbol.upper())
        
        if calendar is None:
            error = create_error_response(
                message=f"No earnings calendar data available for {symbol}",
                error_code="DATA_NOT_FOUND",
                path=f"/api/data/events/earnings/{symbol}",
                status_code=404
            )
            raise HTTPException(status_code=404, detail=error)
        
        return EventCalendarResponse(
            symbol=calendar.symbol,
            events=[
                EarningsEventResponse(
                    symbol=e.symbol,
                    event_date=e.event_date,
                    event_type=e.event_type,
                    confirmed=e.confirmed,
                    estimated=e.estimated,
                    time_of_day=e.time_of_day,
                    metadata=e.metadata
                )
                for e in calendar.events
            ],
            next_earnings_date=calendar.next_earnings_date,
            last_earnings_date=calendar.last_earnings_date,
            earnings_frequency=calendar.earnings_frequency,
            metadata=calendar.metadata
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting earnings calendar for {symbol}: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Error retrieving earnings calendar: {str(e)}"
        )


@router.get("/earnings/{symbol}/upcoming", response_model=List[EarningsEventResponse])
async def get_upcoming_earnings(
    symbol: str,
    days_ahead: Optional[int] = Query(default=None, ge=1, le=365, description="Days ahead to fetch")
):
    """
    Get upcoming earnings events for a symbol
    
    Args:
        symbol: Stock symbol
        days_ahead: Days ahead to fetch
    
    Returns:
        List of upcoming earnings events
    """
    try:
        provider = get_calendar_provider()
        
        if not provider.is_available():
            raise HTTPException(
                status_code=503,
                detail="Earnings calendar provider is not available."
            )
        
        upcoming = provider.get_upcoming_earnings(symbol.upper(), days_ahead=days_ahead)
        
        if upcoming is None:
            return []
        
        return [
            EarningsEventResponse(
                symbol=e.symbol,
                event_date=e.event_date,
                event_type=e.event_type,
                confirmed=e.confirmed,
                estimated=e.estimated,
                time_of_day=e.time_of_day,
                metadata=e.metadata
            )
            for e in upcoming
        ]
    
    except HTTPException:
        raise
    except ValueError as e:
        error = create_error_response(
            message=str(e),
            error_code="VALIDATION_ERROR",
            path=f"/api/data/events/earnings/{symbol}/upcoming",
            status_code=400
        )
        raise HTTPException(status_code=400, detail=error)
    except Exception as e:
        logger.error(f"Error getting upcoming earnings for {symbol}: {e}", exc_info=True)
        error = create_error_response(
            message=f"Error retrieving upcoming earnings: {str(e)}",
            error_code="INTERNAL_ERROR",
            path=f"/api/data/events/earnings/{symbol}/upcoming",
            status_code=500
        )
        raise HTTPException(status_code=500, detail=error)


@router.get("/earnings/{symbol}/next")
async def get_next_earnings(symbol: str):
    """
    Get the next upcoming earnings date for a symbol
    
    Args:
        symbol: Stock symbol
    
    Returns:
        Next earnings date information
    """
    try:
        provider = get_calendar_provider()
        
        if not provider.is_available():
            raise HTTPException(
                status_code=503,
                detail="Earnings calendar provider is not available."
            )
        
        next_date = provider.get_next_earnings_date(symbol.upper())
        
        if next_date is None:
            raise HTTPException(
                status_code=404,
                detail=f"No upcoming earnings date found for {symbol}"
            )
        
        days_until = (next_date - datetime.now()).days
        
        return {
            "symbol": symbol.upper(),
            "next_earnings_date": next_date.isoformat(),
            "days_until": days_until,
            "is_near": provider.is_near_earnings(symbol.upper(), days_threshold=7)
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting next earnings for {symbol}: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Error retrieving next earnings: {str(e)}"
        )


@router.get("/earnings/{symbol}/near")
async def check_near_earnings(
    symbol: str,
    days_threshold: int = Query(default=7, ge=1, le=30, description="Days threshold for 'near'")
):
    """
    Check if symbol is near earnings announcement
    
    Args:
        symbol: Stock symbol
        days_threshold: Days threshold for "near" earnings
    
    Returns:
        Whether earnings is near and details
    """
    try:
        provider = get_calendar_provider()
        
        if not provider.is_available():
            raise HTTPException(
                status_code=503,
                detail="Earnings calendar provider is not available."
            )
        
        is_near = provider.is_near_earnings(symbol.upper(), days_threshold=days_threshold)
        next_date = provider.get_next_earnings_date(symbol.upper())
        
        return {
            "symbol": symbol.upper(),
            "is_near_earnings": is_near,
            "next_earnings_date": next_date.isoformat() if next_date else None,
            "days_threshold": days_threshold
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error checking near earnings for {symbol}: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Error checking near earnings: {str(e)}"
        )


@router.get("/earnings/calendar")
async def get_multiple_earnings_calendar(
    symbols: str = Query(..., description="Comma-separated list of symbols"),
    days_ahead: Optional[int] = Query(default=None, ge=1, le=365, description="Days ahead to fetch")
):
    """
    Get earnings calendar for multiple symbols
    
    Args:
        symbols: Comma-separated list of stock symbols
        days_ahead: Days ahead to fetch
    
    Returns:
        Dictionary mapping symbol -> list of earnings events
    """
    try:
        provider = get_calendar_provider()
        
        if not provider.is_available():
            raise HTTPException(
                status_code=503,
                detail="Earnings calendar provider is not available."
            )
        
        symbol_list = [s.strip().upper() for s in symbols.split(",") if s.strip()]
        
        if not symbol_list:
            raise HTTPException(status_code=400, detail="No symbols provided")
        
        if len(symbol_list) > 50:
            raise HTTPException(status_code=400, detail="Too many symbols (max 50)")
        
        calendar = provider.get_earnings_calendar(symbol_list, days_ahead=days_ahead)
        
        # Convert to response format
        result = {}
        for symbol, events in calendar.items():
            result[symbol] = [
                {
                    "symbol": e.symbol,
                    "event_date": e.event_date.isoformat(),
                    "event_type": e.event_type,
                    "confirmed": e.confirmed,
                    "estimated": e.estimated,
                    "time_of_day": e.time_of_day,
                    "metadata": e.metadata
                }
                for e in events
            ]
        
        return {
            "calendar": result,
            "symbols_requested": len(symbol_list),
            "symbols_with_events": len(result),
            "days_ahead": days_ahead or provider.config.lookahead_days
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting earnings calendar for multiple symbols: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Error retrieving earnings calendar: {str(e)}"
        )

