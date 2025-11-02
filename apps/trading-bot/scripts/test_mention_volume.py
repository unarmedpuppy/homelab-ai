#!/usr/bin/env python3
"""
Test Mention Volume Integration
================================

Test script for mention volume provider.
"""

import sys
from pathlib import Path
from datetime import datetime

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.data.providers.sentiment.mention_volume import MentionVolumeProvider
from src.config.settings import settings
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def test_mention_volume():
    """Test mention volume provider"""
    print("=" * 60)
    print("Testing Mention Volume Provider")
    print("=" * 60)
    print()
    
    # Check configuration
    print("📋 Configuration Check:")
    print(f"   Mention Volume Enabled: {'✅ Enabled' if settings.mention_volume.enabled else '❌ Disabled'}")
    print(f"   Spike Threshold: {settings.mention_volume.spike_threshold}x")
    print(f"   Momentum Threshold: {settings.mention_volume.momentum_threshold}")
    print(f"   Baseline Lookback: {settings.mention_volume.baseline_lookback_hours} hours")
    print()
    
    # Create provider
    print("🔧 Initializing Mention Volume Provider...")
    provider = MentionVolumeProvider(persist_to_db=True)
    
    if not provider.is_available():
        print("❌ Mention Volume provider not available")
        print("   Provider requires database access")
        return False
    
    print("✅ Mention Volume provider initialized")
    print(f"   Database Persistence: {'✅ Enabled' if provider.persist_to_db else '❌ Disabled'}")
    print()
    
    # Test symbol mention volume
    test_symbols = ["SPY", "AAPL", "TSLA"]
    
    for symbol in test_symbols:
        print(f"📊 Analyzing mention volume for {symbol}...")
        print("-" * 60)
        
        try:
            volume = provider.get_mention_volume(symbol, hours=24)
            
            if volume:
                print(f"✅ Mention Volume for {symbol}:")
                print(f"   Total Mentions: {volume.total_mentions}")
                print(f"   Twitter: {volume.twitter_mentions}")
                print(f"   Reddit: {volume.reddit_mentions}")
                print(f"   StockTwits: {volume.stocktwits_mentions}")
                print(f"   News: {volume.news_mentions}")
                print(f"   Volume Trend: {volume.volume_trend}")
                print(f"   Momentum Score: {volume.momentum_score:.3f}")
                print(f"   Spike Detected: {'✅ Yes' if volume.spike_detected else '❌ No'}")
                if volume.spike_detected:
                    print(f"   Spike Magnitude: {volume.spike_magnitude:.2f}x")
                print()
            else:
                print(f"⚠️  No mention volume data available for {symbol}")
                print()
                
        except Exception as e:
            print(f"❌ Error analyzing {symbol}: {e}")
            import traceback
            traceback.print_exc()
            print()
    
    # Test volume trend
    print("=" * 60)
    print("📈 Testing Volume Trend Analysis...")
    print("=" * 60)
    print()
    
    try:
        test_symbol = "SPY"
        trend = provider.get_volume_trend(test_symbol, hours=24, interval_hours=1)
        
        if trend:
            print(f"✅ Volume trend for {test_symbol}:")
            print(f"   Data Points: {len(trend)}")
            if len(trend) > 0:
                print(f"   Latest: {trend[-1]['mentions']} mentions at {trend[-1]['timestamp']}")
            print()
        else:
            print("⚠️  No trend data available")
            print()
            
    except Exception as e:
        print(f"❌ Error getting volume trend: {e}")
        import traceback
        traceback.print_exc()
        print()
    
    # Test trending by volume
    print("=" * 60)
    print("🔥 Testing Trending by Volume...")
    print("=" * 60)
    print()
    
    try:
        trending = provider.get_trending_by_volume(
            hours=24,
            min_mentions=5,
            min_momentum=0.2,
            limit=10
        )
        
        if trending:
            print(f"✅ Found {len(trending)} trending symbols:")
            for i, symbol_data in enumerate(trending[:10], 1):
                symbol = symbol_data.get("symbol", "Unknown")
                mentions = symbol_data.get("total_mentions", 0)
                momentum = symbol_data.get("momentum_score", 0.0)
                spike = symbol_data.get("spike_detected", False)
                print(f"   {i}. {symbol}: {mentions} mentions, momentum={momentum:.2f}, "
                      f"spike={'✅' if spike else '❌'}")
            print()
        else:
            print("⚠️  No trending symbols found")
            print()
            
    except Exception as e:
        print(f"❌ Error getting trending by volume: {e}")
        import traceback
        traceback.print_exc()
        print()
    
    print("=" * 60)
    print("✅ Mention Volume Provider Test Complete")
    print("=" * 60)
    
    return True

if __name__ == "__main__":
    success = test_mention_volume()
    sys.exit(0 if success else 1)

