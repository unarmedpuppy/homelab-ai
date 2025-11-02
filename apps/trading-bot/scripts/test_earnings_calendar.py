#!/usr/bin/env python3
"""
Test Earnings Calendar Integration
===================================

Test script for earnings calendar and event calendar provider.
"""

import sys
from pathlib import Path
from datetime import datetime, timedelta

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.data.providers.data import EventCalendarProvider, EarningsCalendarProvider, EconomicEventProvider
from src.config.settings import settings
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def test_earnings_calendar():
    """Test earnings calendar provider"""
    print("=" * 60)
    print("Testing Earnings Calendar Provider")
    print("=" * 60)
    print()
    
    # Check configuration
    print("📋 Configuration Check:")
    config = settings.event_calendar
    print(f"   Event Calendar Enabled: {config.enabled}")
    print(f"   Cache TTL: {config.cache_ttl}s")
    print(f"   Lookahead Days: {config.lookahead_days}")
    print(f"   Economic Events Enabled: {config.economic_events_enabled}")
    print()
    
    # Create provider
    print("🔧 Initializing Earnings Calendar Provider...")
    try:
        earnings_provider = EarningsCalendarProvider()
    except ImportError as e:
        print(f"❌ Error: {e}")
        print("   Please install yfinance: pip install yfinance")
        return False
    
    if not earnings_provider.is_available():
        print("❌ Earnings calendar provider not available")
        print("   Please configure EARNINGS_CALENDAR_ENABLED=true")
        return False
    
    print("✅ Earnings calendar provider initialized")
    print()
    
    # Test getting earnings date for a symbol
    test_symbols = ["AAPL", "MSFT", "SPY"]
    
    for symbol in test_symbols:
        print(f"📅 Getting earnings date for {symbol}...")
        print("-" * 60)
        
        try:
            earnings_date = earnings_provider.get_earnings_date(symbol)
            
            if earnings_date:
                print(f"✅ Next earnings date for {symbol}:")
                print(f"   Date: {earnings_date.strftime('%Y-%m-%d %H:%M:%S')}")
                print(f"   Days until: {(earnings_date - datetime.now()).days} days")
            else:
                print(f"ℹ️  No earnings date found for {symbol}")
            
            # Get detailed earnings event
            print(f"\n📊 Getting detailed earnings event for {symbol}...")
            event = earnings_provider.get_earnings_event(symbol)
            
            if event:
                print(f"✅ Earnings Event for {symbol}:")
                print(f"   Event Date: {event.event_date.strftime('%Y-%m-%d')}")
                print(f"   Impact Score: {event.impact_score:.2f}")
                print(f"   Is Confirmed: {event.is_confirmed}")
                if event.fiscal_period:
                    print(f"   Fiscal Period: {event.fiscal_period}")
                if event.estimated_eps is not None:
                    print(f"   Estimated EPS: ${event.estimated_eps:.2f}")
                if event.actual_eps is not None:
                    print(f"   Actual EPS: ${event.actual_eps:.2f}")
            else:
                print(f"ℹ️  No detailed earnings event found for {symbol}")
            
            print()
        
        except Exception as e:
            print(f"❌ Error getting earnings for {symbol}: {e}")
            logger.exception(f"Error details:")
            print()
            continue
    
    # Test getting upcoming earnings for multiple symbols
    print("📋 Getting upcoming earnings for multiple symbols...")
    print("-" * 60)
    
    try:
        upcoming = earnings_provider.get_upcoming_earnings(
            symbols=test_symbols,
            days=60
        )
        
        if upcoming:
            print(f"✅ Found {len(upcoming)} upcoming earnings events:")
            for event in upcoming[:5]:  # Show first 5
                print(f"   {event.symbol}: {event.event_date.strftime('%Y-%m-%d')} (Impact: {event.impact_score:.2f})")
        else:
            print("ℹ️  No upcoming earnings found")
        print()
    
    except Exception as e:
        print(f"❌ Error getting upcoming earnings: {e}")
        logger.exception(f"Error details:")
        print()
    
    return True

def test_economic_events():
    """Test economic event provider"""
    print("=" * 60)
    print("Testing Economic Event Provider")
    print("=" * 60)
    print()
    
    print("🔧 Initializing Economic Event Provider...")
    economic_provider = EconomicEventProvider()
    
    if not economic_provider.is_available():
        print("❌ Economic event provider not available")
        return False
    
    print("✅ Economic event provider initialized")
    print()
    
    # Test Fed meeting schedule
    print("🏦 Getting Fed meeting schedule for 2024...")
    print("-" * 60)
    
    try:
        fed_meetings = economic_provider.get_fed_meeting_schedule(year=2024)
        
        if fed_meetings:
            print(f"✅ Found {len(fed_meetings)} Fed meetings in 2024:")
            for meeting in fed_meetings:
                if meeting.event_date >= datetime.now():
                    days_until = (meeting.event_date - datetime.now()).days
                    print(f"   {meeting.event_date.strftime('%Y-%m-%d')}: {meeting.event_name} (in {days_until} days, Impact: {meeting.impact_score:.2f})")
        else:
            print("ℹ️  No Fed meetings found")
        print()
    except Exception as e:
        print(f"❌ Error getting Fed meetings: {e}")
        logger.exception(f"Error details:")
        print()
    
    # Test CPI schedule
    print("📈 Getting CPI release schedule for 2024...")
    print("-" * 60)
    
    try:
        cpi_releases = economic_provider.get_cpi_schedule(year=2024)
        
        if cpi_releases:
            upcoming_cpi = [c for c in cpi_releases if c.event_date >= datetime.now()]
            print(f"✅ Found {len(upcoming_cpi)} upcoming CPI releases in 2024:")
            for cpi in upcoming_cpi[:6]:  # Show next 6 months
                days_until = (cpi.event_date - datetime.now()).days
                print(f"   {cpi.event_date.strftime('%Y-%m-%d')}: {cpi.event_name} (in {days_until} days, Impact: {cpi.impact_score:.2f})")
        else:
            print("ℹ️  No CPI releases found")
        print()
    except Exception as e:
        print(f"❌ Error getting CPI schedule: {e}")
        logger.exception(f"Error details:")
        print()
    
    return True

def test_event_calendar():
    """Test unified event calendar provider"""
    print("=" * 60)
    print("Testing Unified Event Calendar Provider")
    print("=" * 60)
    print()
    
    print("🔧 Initializing Event Calendar Provider...")
    try:
        calendar_provider = EventCalendarProvider()
    except ImportError as e:
        print(f"❌ Error: {e}")
        return False
    
    if not calendar_provider.is_available():
        print("❌ Event calendar provider not available")
        return False
    
    print("✅ Event calendar provider initialized")
    print()
    
    # Test getting calendar for symbols
    test_symbols = ["AAPL", "MSFT"]
    
    print(f"📅 Getting event calendar for symbols: {', '.join(test_symbols)}")
    print("-" * 60)
    
    try:
        calendar = calendar_provider.get_calendar(
            symbols=test_symbols,
            start_date=datetime.now(),
            end_date=datetime.now() + timedelta(days=60),
            include_economic=True
        )
        
        print(f"✅ Calendar retrieved:")
        print(f"   Earnings Events: {len(calendar.earnings_events)}")
        print(f"   Economic Events: {len(calendar.economic_events)}")
        print(f"   Total Events: {len(calendar.earnings_events) + len(calendar.economic_events)}")
        print()
        
        # Show upcoming events
        print("📋 Upcoming Events (next 7 days):")
        upcoming = calendar.get_upcoming_events(days=7)
        
        if upcoming:
            for event_type, event in upcoming[:10]:  # Show first 10
                if event_type == 'earnings':
                    print(f"   📊 {event.symbol} Earnings: {event.event_date.strftime('%Y-%m-%d')} (Impact: {event.impact_score:.2f})")
                elif event_type == 'economic':
                    print(f"   📈 {event.event_name}: {event.event_date.strftime('%Y-%m-%d')} (Impact: {event.impact_score:.2f})")
        else:
            print("   ℹ️  No events in the next 7 days")
        print()
        
        # Test getting events for a specific symbol
        symbol = "AAPL"
        print(f"📊 Getting all events for {symbol}...")
        events = calendar_provider.get_events_for_symbol(symbol, days=60)
        
        if events:
            print(f"✅ Events for {symbol}:")
            if events['earnings_event']:
                e = events['earnings_event']
                print(f"   Earnings: {e.event_date.strftime('%Y-%m-%d')} (Impact: {e.impact_score:.2f})")
            print(f"   Economic Events: {len(events['economic_events'])}")
            print(f"   Total Upcoming Events: {len(events['upcoming_events'])}")
        else:
            print(f"ℹ️  No events found for {symbol}")
        print()
    
    except Exception as e:
        print(f"❌ Error getting calendar: {e}")
        logger.exception(f"Error details:")
        print()
        return False
    
    return True

if __name__ == "__main__":
    print()
    success = True
    
    # Test earnings calendar
    success &= test_earnings_calendar()
    print()
    
    # Test economic events
    success &= test_economic_events()
    print()
    
    # Test unified calendar
    success &= test_event_calendar()
    print()
    
    print("=" * 60)
    if success:
        print("✅ All tests completed successfully!")
    else:
        print("⚠️  Some tests had issues - check logs above")
    print("=" * 60)
    print()
    
    sys.exit(0 if success else 1)

