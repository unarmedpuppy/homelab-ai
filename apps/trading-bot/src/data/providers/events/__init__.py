"""
Event Calendar Providers
========================

Providers for tracking earnings announcements and other corporate events.
"""

try:
    from .earnings_calendar import (
        EarningsCalendarProvider, 
        EarningsEvent, 
        EventCalendarEntry,
        get_provider_instance
    )
except ImportError:
    EarningsCalendarProvider = None
    EarningsEvent = None
    EventCalendarEntry = None
    get_provider_instance = None

__all__ = [
    'EarningsCalendarProvider',
    'EarningsEvent',
    'EventCalendarEntry',
    'get_provider_instance',
]

