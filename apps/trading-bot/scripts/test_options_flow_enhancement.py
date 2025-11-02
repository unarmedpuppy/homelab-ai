#!/usr/bin/env python3
"""
Test Options Flow Enhancement
==============================

Test script for enhanced options flow analysis including pattern detection,
metrics, and sentiment.
"""

import sys
import asyncio
from pathlib import Path
from datetime import datetime

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.data.providers.unusual_whales import UnusualWhalesClient
from src.data.providers.options.pattern_detector import PatternDetector
from src.data.providers.options.metrics_calculator import OptionsMetricsCalculator
from src.data.providers.options.chain_analyzer import OptionsChainAnalyzer
from src.data.providers.sentiment.options_flow_sentiment import OptionsFlowSentimentProvider
from src.config.settings import settings
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def test_options_flow_enhancement():
    """Test options flow enhancement features"""
    print("=" * 60)
    print("Testing Options Flow Enhancement")
    print("=" * 60)
    print()
    
    # Check configuration
    print("📋 Configuration Check:")
    print(f"   Unusual Whales API Key: {'✅ Set' if settings.unusual_whales.api_key else '❌ Not set'}")
    print(f"   Base URL: {settings.unusual_whales.base_url}")
    print()
    
    if not settings.unusual_whales.api_key:
        print("❌ Unusual Whales API key not configured")
        print("   Please set UW_API_KEY in your .env file")
        return False
    
    # Test 1: Basic Options Flow
    print("=" * 60)
    print("Test 1: Fetch Options Flow Data")
    print("=" * 60)
    print()
    
    symbol = "SPY"
    try:
        async with UnusualWhalesClient(settings.unusual_whales.api_key) as client:
            flows = await client.get_options_flow(symbol, hours=24)
        
        if flows:
            print(f"✅ Retrieved {len(flows)} options flows for {symbol}")
            print(f"   Sample flow: {flows[0].symbol} {flows[0].option_type} ${flows[0].strike}")
        else:
            print(f"⚠️  No flows returned for {symbol}")
    except Exception as e:
        print(f"❌ Error fetching flows: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    # Test 2: Pattern Detection
    print()
    print("=" * 60)
    print("Test 2: Pattern Detection (Sweeps & Blocks)")
    print("=" * 60)
    print()
    
    try:
        detector = PatternDetector()
        flows_with_patterns = detector.detect_patterns(flows)
        
        sweeps = [f for f in flows_with_patterns if f.is_sweep]
        blocks = [f for f in flows_with_patterns if f.is_block]
        
        print(f"✅ Pattern Detection Results:")
        print(f"   Total flows: {len(flows_with_patterns)}")
        print(f"   Sweeps detected: {len(sweeps)}")
        print(f"   Blocks detected: {len(blocks)}")
        
        if sweeps:
            print(f"\n   Sample Sweep:")
            sweep = sweeps[0]
            print(f"     Symbol: {sweep.symbol}")
            print(f"     Strike: ${sweep.strike}")
            print(f"     Type: {sweep.option_type}")
            print(f"     Strength: {sweep.sweep_strength:.2f}")
        
        if blocks:
            print(f"\n   Sample Block:")
            block = blocks[0]
            print(f"     Symbol: {block.symbol}")
            print(f"     Premium: ${block.premium:,.2f}")
            print(f"     Volume: {block.volume}")
    except Exception as e:
        print(f"❌ Error in pattern detection: {e}")
        import traceback
        traceback.print_exc()
    
    # Test 3: Metrics Calculation
    print()
    print("=" * 60)
    print("Test 3: Metrics Calculation (P/C Ratios)")
    print("=" * 60)
    print()
    
    try:
        calculator = OptionsMetricsCalculator()
        pc_ratios = calculator.calculate_put_call_ratio(flows_with_patterns)
        metrics = calculator.calculate_flow_metrics(flows_with_patterns)
        
        print(f"✅ Metrics Calculated:")
        print(f"   Put/Call Volume Ratio: {pc_ratios.volume_ratio:.3f}")
        print(f"   Put/Call Premium Ratio: {pc_ratios.premium_ratio:.3f}")
        if pc_ratios.oi_ratio:
            print(f"   Put/Call OI Ratio: {pc_ratios.oi_ratio:.3f}")
        
        print(f"\n   Flow Metrics:")
        print(f"     Total Volume: {metrics.total_volume:,}")
        print(f"     Total Premium: ${metrics.total_premium:,.2f}")
        print(f"     Bullish Flow: {metrics.bullish_flow:.2%}")
        print(f"     Bearish Flow: {metrics.bearish_flow:.2%}")
        print(f"     Unusual Activity: {metrics.unusual_count}")
        print(f"     Sweeps: {metrics.sweep_count}")
        print(f"     Blocks: {metrics.block_count}")
    except Exception as e:
        print(f"❌ Error calculating metrics: {e}")
        import traceback
        traceback.print_exc()
    
    # Test 4: Chain Analysis
    print()
    print("=" * 60)
    print("Test 4: Options Chain Analysis")
    print("=" * 60)
    print()
    
    try:
        analyzer = OptionsChainAnalyzer()
        # Assume current price (you'd normally get this from market data)
        analysis = analyzer.analyze_chain(flows_with_patterns, current_price=None)
        
        print(f"✅ Chain Analysis:")
        print(f"   Max Pain: ${analysis.max_pain:.2f}")
        print(f"   Gamma Exposure: {analysis.gamma_exposure:,.0f}")
        print(f"   Call Dominance: {analysis.call_dominance:.2%}")
        print(f"   Put Dominance: {analysis.put_dominance:.2%}")
        print(f"   High Volume Strikes: {len(analysis.high_volume_strikes)}")
        if analysis.high_volume_strikes:
            top_strike = analysis.high_volume_strikes[0]
            print(f"     Top: ${top_strike[0]:.2f} ({top_strike[1]:,} volume)")
    except Exception as e:
        print(f"❌ Error in chain analysis: {e}")
        import traceback
        traceback.print_exc()
    
    # Test 5: Sentiment Provider
    print()
    print("=" * 60)
    print("Test 5: Options Flow Sentiment")
    print("=" * 60)
    print()
    
    try:
        provider = OptionsFlowSentimentProvider()
        
        if provider.is_available():
            sentiment = provider.get_sentiment(symbol, hours=24)
            
            if sentiment:
                print(f"✅ Sentiment Calculated:")
                print(f"   Symbol: {sentiment.symbol}")
                print(f"   Sentiment Score: {sentiment.weighted_sentiment:.3f}")
                print(f"   Sentiment Level: {sentiment.sentiment_level.value}")
                print(f"   Confidence: {sentiment.confidence:.2%}")
                print(f"   Mention Count: {sentiment.mention_count}")
                print(f"   Engagement Score: {sentiment.engagement_score:.3f}")
            else:
                print(f"⚠️  No sentiment data available for {symbol}")
        else:
            print(f"⚠️  Options flow sentiment provider not available")
    except Exception as e:
        print(f"❌ Error getting sentiment: {e}")
        import traceback
        traceback.print_exc()
    
    print()
    print("=" * 60)
    print("✅ Options flow enhancement test completed!")
    print("=" * 60)
    
    return True


if __name__ == "__main__":
    try:
        success = asyncio.run(test_options_flow_enhancement())
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n⚠️  Test interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

