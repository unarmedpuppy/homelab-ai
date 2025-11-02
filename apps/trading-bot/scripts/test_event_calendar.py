#!/usr/bin/env python3
"""
Test Event Calendar Provider
=============================

Test script for earnings calendar and event calendar integration.
"""

import sys
from pathlib import Path
from datetime import datetime, timedelta

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.data.providers.data.event_calendar import EventCalendarProvider, EventType
from src.config.settings import settings
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def test_event_calendar():
    """Test event calendar provider"""
    print("=" * 60)
    print("Testing Event Calendar Provider")
    print("=" * 60)
    print()
    
    # Check configuration
    print("📋 Configuration Check:")
    print(f"   Cache TTL: {settings.event_calendar.cache_ttl}s")
    print(f"   Default Lookahead: {settings.event_calendar.default_lookahead_days} days")
    print(f"   Economic Events: {'✅ Enabled' if settings.event_calendar.enable_economic_events else '❌ Disabled'}")
    print()
    
    # Create provider
    print("🔧 Initializing Event Calendar Provider...")
    provider = EventCalendarProvider()
    
    if not provider.is_available():
        print("❌ Event calendar provider not available")
        return False
    
    print("✅ Event calendar provider initialized")
    print()
    
    # Test 1: Get earnings calendar for a symbol
    print("=" * 60)
    print("Test 1: Earnings Calendar for Symbol")
    print("=" * 60)
    print()
    
    test_symbols = ["AAPL", "MSFT", "TSLA"]
    
    for symbol in test_symbols:
        print(f"📊 Getting earnings calendar for {symbol}...")
        print("-" * 60)
        
        try:
            calendar = provider.get_earnings_calendar(
                symbol=symbol,
                start_date=datetime.now(),
                end_date=datetime.now() + timedelta(days=90)
            )
            
            print(f"✅ Found {len(calendar.earnings_events)} events for {symbol}")
            
            if calendar.earnings_events:
                for i, event in enumerate(calendar.earnings_events[:5], 1):  # Show first 5
                    days_until = (event.event_date - datetime.now()).days
                    print(f"   {i}. {event.event_type.value.upper()}: {event.event_date.strftime('%Y-%m-%d')} "
                          f"({days_until} days) - Impact: {event.impact.value}")
                
                if len(calendar.earnings_events) > 5:
                    print(f"   ... and {len(calendar.earnings_events) - 5} more events")
            else:
                print(f"   ⚠️  No events found in next 90 days")
            
            print()
        
        except Exception as e:
            print(f"❌ Error getting calendar for {symbol}: {e}")
            import traceback
            traceback.print_exc()
            print()
    
    # Test 2: Get next earnings
    print("=" * 60)
    print("Test 2: Next Earnings Event")
    print("=" * 60)
    print()
    
    symbol = "AAPL"
    try:
        next_earnings = provider.get_next_earnings(symbol)
        
        if next_earnings:
            days_until = (next_earnings.event_date - datetime.now()).days
            impact_score = provider.get_event_impact_score(next_earnings)
            
            print(f"✅ Next earnings for {symbol}:")
            print(f"   Date: {next_earnings.event_date.strftime('%Y-%m-%d %H:%M')}")
            print(f"   Days Until: {days_until}")
            print(f"   Impact: {next_earnings.impact.value}")
            print(f"   Impact Score: {impact_score:.3f}")
            print(f"   Confidence: {next_earnings.confidence:.2%}")
        else:
            print(f"⚠️  No upcoming earnings found for {symbol}")
    
    except Exception as e:
        print(f"❌ Error getting next earnings: {e}")
        import traceback
        traceback.print_exc()
    
    print()
    
    # Test 3: Event impact scoring
    print("=" * 60)
    print("Test 3: Event Impact Scoring")
    print("=" * 60)
    print()
    
    try:
        calendar = provider.get_earnings_calendar("AAPL", days=90)
        if calendar.earnings_events:
            print(f"📈 Impact scores for {len(calendar.earnings_events)} events:")
            for event in calendar.earnings_events[:10]:  # First 10
                score = provider.get_event_impact_score(event)
                days_until = (event.event_date - datetime.now()).days
                print(f"   {event.event_date.strftime('%Y-%m-%d')} ({days_until}d): {score:.3f}")
        else:
            print("⚠️  No events to score")
    except Exception as e:
        print(f"❌ Error calculating impact scores: {e}")
    
    print()
    
    # Test 4: Economic events (if enabled)
    if settings.event_calendar.enable_economic_events:
        print("=" * 60)
        print("Test 4: Economic Events")
        print("=" * 60)
        print()
        
        try:
            events = provider.get_economic_events(
                start_date=datetime.now(),
                end_date=datetime.now() + timedelta(days=30)
            )
            print(f"✅ Found {len(events)} economic events")
            for event in events[:5]:
                print(f"   - {event.event_name} ({event.event_date.strftime('%Y-%m-%d')})")
        except Exception as e:
            print(f"❌ Error getting economic events: {e}")
    
    print()
    print("=" * 60)
    print("✅ Event Calendar Provider Test Complete")
    print("=" * 60)
    
    return True


if __name__ == "__main__":
    success = test_event_calendar()
    sys.exit(0 if success else 1)

