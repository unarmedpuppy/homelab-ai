"""
Event Calendar API Routes
==========================

API endpoints for earnings calendar and economic events.
"""

import logging
from typing import Optional, List
from datetime import datetime, timedelta
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from ...data.providers.data.event_calendar import (
    EventCalendarProvider,
    EarningsEvent,
    EconomicEvent,
    EventType,
    EventImpact
)
from ...config.settings import settings

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/calendar", tags=["calendar"])


# Response Models
class EarningsEventResponse(BaseModel):
    """Earnings event response"""
    symbol: str
    event_date: str
    estimated_eps: Optional[float] = None
    actual_eps: Optional[float] = None
    estimated_revenue: Optional[float] = None
    actual_revenue: Optional[float] = None
    fiscal_period: Optional[str] = None
    impact_score: float
    is_confirmed: bool
    conference_call_time: Optional[str] = None
    
    class Config:
        from_attributes = True


class EconomicEventResponse(BaseModel):
    """Economic event response"""
    event_type: str
    event_name: str
    event_date: str
    expected_value: Optional[float] = None
    actual_value: Optional[float] = None
    previous_value: Optional[float] = None
    impact_score: float
    description: Optional[str] = None
    
    class Config:
        from_attributes = True


class CalendarResponse(BaseModel):
    """Event calendar response"""
    symbol: Optional[str] = None
    start_date: str
    end_date: str
    earnings_events: List[EarningsEventResponse]
    economic_events: List[EconomicEventResponse]
    total_events: int
    next_event: Optional[EarningsEventResponse] = None


# Global provider instance
_provider: Optional[EventCalendarProvider] = None


def get_provider() -> EventCalendarProvider:
    """Get or create event calendar provider instance"""
    global _provider
    if _provider is None:
        _provider = EventCalendarProvider()
    return _provider


@router.get("/status")
async def calendar_status():
    """Get event calendar provider status"""
    provider = get_provider()
    
    return {
        "status": "available" if provider.is_available() else "unavailable",
        "provider": "EventCalendarProvider",
        "features": {
            "earnings_calendar": True,
            "economic_events": settings.event_calendar.economic_events_enabled,
            "cache_enabled": True,
            "cache_ttl": settings.event_calendar.cache_ttl,
            "default_lookahead_days": getattr(settings.event_calendar, 'lookahead_days', 90)
        }
    }


@router.get("/earnings/{symbol}", response_model=List[EarningsEventResponse])
async def get_earnings_calendar(
    symbol: str,
    days: int = Query(default=90, ge=1, le=365, description="Days ahead to look for earnings"),
    limit: int = Query(default=50, ge=1, le=500, description="Maximum number of events to return")
):
    """
    Get earnings calendar for a symbol
    
    Returns upcoming earnings announcements, dividends, and stock splits.
    """
    provider = get_provider()
    
    if not provider.is_available():
        raise HTTPException(
            status_code=503,
            detail="Event calendar provider is not available"
        )
    
    try:
        # Get earnings event for the symbol
        event = provider.earnings_provider.get_earnings_event(symbol.upper())
        
        if not event:
            return []  # No earnings event found
        
        # Check if event is within the requested timeframe
        end_date = datetime.now() + timedelta(days=days)
        if event.event_date > end_date:
            return []  # Event is beyond requested timeframe
        
        # Return single event (or multiple if we have history)
        return [EarningsEventResponse(
            symbol=event.symbol,
            event_date=event.event_date.isoformat(),
            estimated_eps=event.estimated_eps,
            actual_eps=event.actual_eps,
            estimated_revenue=event.estimated_revenue,
            actual_revenue=event.actual_revenue,
            fiscal_period=event.fiscal_period,
            impact_score=event.impact_score,
            is_confirmed=event.is_confirmed,
            conference_call_time=event.conference_call_time.isoformat() if event.conference_call_time else None
        )]
    
    except Exception as e:
        logger.error(f"Error getting earnings calendar for {symbol}: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Error retrieving earnings calendar: {str(e)}"
        )


@router.get("/earnings/{symbol}/next", response_model=EarningsEventResponse)
async def get_next_earnings(symbol: str):
    """Get next earnings announcement for a symbol"""
    provider = get_provider()
    
    if not provider.is_available():
        raise HTTPException(
            status_code=503,
            detail="Event calendar provider is not available"
        )
    
    try:
        event = provider.earnings_provider.get_earnings_event(symbol.upper())
        
        if not event:
            raise HTTPException(
                status_code=404,
                detail=f"No upcoming earnings found for {symbol}"
            )
        
        return EarningsEventResponse(
            symbol=event.symbol,
            event_date=event.event_date.isoformat(),
            estimated_eps=event.estimated_eps,
            actual_eps=event.actual_eps,
            estimated_revenue=event.estimated_revenue,
            actual_revenue=event.actual_revenue,
            fiscal_period=event.fiscal_period,
            impact_score=event.impact_score,
            is_confirmed=event.is_confirmed,
            conference_call_time=event.conference_call_time.isoformat() if event.conference_call_time else None
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting next earnings for {symbol}: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Error retrieving next earnings: {str(e)}"
        )


@router.get("/calendar", response_model=CalendarResponse)
async def get_event_calendar(
    symbol: Optional[str] = Query(default=None, description="Stock symbol (optional)"),
    start_date: Optional[str] = Query(default=None, description="Start date (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(default=None, description="End date (YYYY-MM-DD)"),
    days: int = Query(default=90, ge=1, le=365, description="Days ahead (used if dates not provided)"),
    limit: int = Query(default=100, ge=1, le=500, description="Maximum events to return")
):
    """
    Get comprehensive event calendar
    
    Returns earnings events and economic events for the specified period.
    """
    provider = get_provider()
    
    if not provider.is_available():
        raise HTTPException(
            status_code=503,
            detail="Event calendar provider is not available"
        )
    
    try:
        # Parse dates
        if start_date:
            start = datetime.fromisoformat(start_date)
        else:
            start = datetime.now()
        
        if end_date:
            end = datetime.fromisoformat(end_date)
        else:
            end = start + timedelta(days=days)
        
        # Get calendar using new method signature
        symbols = [symbol.upper()] if symbol else None
        calendar = provider.get_calendar(
            symbols=symbols,
            start_date=start,
            end_date=end,
            include_economic=settings.event_calendar.economic_events_enabled
        )
        
        # Format earnings events
        earnings_events = []
        for event in calendar.earnings_events:
            earnings_events.append(EarningsEventResponse(
                symbol=event.symbol,
                event_date=event.event_date.isoformat(),
                estimated_eps=event.estimated_eps,
                actual_eps=event.actual_eps,
                estimated_revenue=event.estimated_revenue,
                actual_revenue=event.actual_revenue,
                fiscal_period=event.fiscal_period,
                impact_score=event.impact_score,
                is_confirmed=event.is_confirmed,
                conference_call_time=event.conference_call_time.isoformat() if event.conference_call_time else None
            ))
        
        # Format economic events
        economic_events = []
        for event in calendar.economic_events:
            economic_events.append(EconomicEventResponse(
                event_type=event.event_type.value,
                event_name=event.event_name,
                event_date=event.event_date.isoformat(),
                expected_value=event.expected_value,
                actual_value=event.actual_value,
                previous_value=event.previous_value,
                impact_score=event.impact_score,
                description=event.description
            ))
        
        # Get next event (first upcoming event)
        next_event = None
        upcoming = calendar.get_upcoming_events(days=365)
        if upcoming:
            next_evt = upcoming[0][1]  # Get event from tuple
            if isinstance(next_evt, EarningsEvent):
                next_event = EarningsEventResponse(
                    symbol=next_evt.symbol,
                    event_date=next_evt.event_date.isoformat(),
                    estimated_eps=next_evt.estimated_eps,
                    actual_eps=next_evt.actual_eps,
                    estimated_revenue=next_evt.estimated_revenue,
                    actual_revenue=next_evt.actual_revenue,
                    fiscal_period=next_evt.fiscal_period,
                    impact_score=next_evt.impact_score,
                    is_confirmed=next_evt.is_confirmed,
                    conference_call_time=next_evt.conference_call_time.isoformat() if next_evt.conference_call_time else None
                )
        
        return CalendarResponse(
            symbol=symbol,
            start_date=start.isoformat(),
            end_date=end.isoformat(),
            earnings_events=earnings_events,
            economic_events=economic_events,
            total_events=len(earnings_events) + len(economic_events),
            next_event=next_event
        )
    
    except Exception as e:
        logger.error(f"Error getting event calendar: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Error retrieving event calendar: {str(e)}"
        )


@router.get("/economic", response_model=List[EconomicEventResponse])
async def get_economic_events(
    start_date: Optional[str] = Query(default=None, description="Start date (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(default=None, description="End date (YYYY-MM-DD)"),
    days: int = Query(default=30, ge=1, le=365, description="Days ahead (used if dates not provided)")
):
    """
    Get economic calendar events
    
    Returns economic events like CPI, Fed meetings, GDP, etc.
    Note: Requires EVENT_CALENDAR_ENABLE_ECONOMIC_EVENTS=true
    """
    provider = get_provider()
    
    if not settings.event_calendar.economic_events_enabled:
        raise HTTPException(
            status_code=501,
            detail="Economic events are not enabled. Set EVENT_CALENDAR_ECONOMIC_EVENTS_ENABLED=true"
        )
    
    try:
        # Parse dates
        if start_date:
            start = datetime.fromisoformat(start_date)
        else:
            start = datetime.now()
        
        if end_date:
            end = datetime.fromisoformat(end_date)
        else:
            end = start + timedelta(days=days)
        
        # Get calendar with economic events
        calendar = provider.get_calendar(
            symbols=None,  # No earnings events
            start_date=start,
            end_date=end,
            include_economic=True
        )
        
        return [
            EconomicEventResponse(
                event_type=e.event_type.value,
                event_name=e.event_name,
                event_date=e.event_date.isoformat(),
                expected_value=e.expected_value,
                actual_value=e.actual_value,
                previous_value=e.previous_value,
                impact_score=e.impact_score,
                description=e.description
            )
            for e in calendar.economic_events
        ]
    
    except Exception as e:
        logger.error(f"Error getting economic events: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Error retrieving economic events: {str(e)}"
        )

