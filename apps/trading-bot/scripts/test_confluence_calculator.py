#!/usr/bin/env python3
"""
Test Confluence Calculator
===========================

Test script for confluence calculator that combines technical indicators,
sentiment, and options flow.
"""

import sys
from pathlib import Path
from datetime import datetime
import pandas as pd
import numpy as np

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.core.confluence import ConfluenceCalculator
from src.config.settings import settings
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def generate_sample_market_data(days: int = 100) -> pd.DataFrame:
    """Generate sample OHLCV data for testing"""
    dates = pd.date_range(end=datetime.now(), periods=days, freq='D')
    
    # Generate realistic price data with some trend
    np.random.seed(42)
    base_price = 100.0
    returns = np.random.normal(0.001, 0.02, days)  # Daily returns
    prices = base_price * np.exp(np.cumsum(returns))
    
    # Generate OHLCV
    data = pd.DataFrame({
        'date': dates,
        'open': prices * (1 + np.random.normal(0, 0.005, days)),
        'high': prices * (1 + np.abs(np.random.normal(0.01, 0.01, days))),
        'low': prices * (1 - np.abs(np.random.normal(0.01, 0.01, days))),
        'close': prices,
        'volume': np.random.randint(1000000, 10000000, days)
    })
    
    # Ensure high >= close >= low and high >= open >= low
    data['high'] = data[['open', 'close', 'high']].max(axis=1)
    data['low'] = data[['open', 'close', 'low']].min(axis=1)
    
    return data.set_index('date')


def test_confluence():
    """Test confluence calculator"""
    print("=" * 60)
    print("Testing Confluence Calculator")
    print("=" * 60)
    print()
    
    # Check configuration
    print("📋 Configuration Check:")
    conf_config = settings.confluence
    print(f"   Technical Weight: {conf_config.weight_technical}")
    print(f"   Sentiment Weight: {conf_config.weight_sentiment}")
    print(f"   Options Flow Weight: {conf_config.weight_options_flow}")
    print(f"   Min Confluence: {conf_config.min_confluence}")
    print(f"   High Confluence: {conf_config.high_confluence}")
    print(f"   Use Sentiment: {conf_config.use_sentiment}")
    print(f"   Use Options Flow: {conf_config.use_options_flow}")
    print()
    
    # Create calculator
    print("🔧 Initializing Confluence Calculator...")
    calculator = ConfluenceCalculator()
    print("✅ Confluence calculator initialized")
    print()
    
    # Test symbols
    test_symbols = ["SPY", "AAPL"]
    
    for symbol in test_symbols:
        print(f"📊 Calculating confluence for {symbol}...")
        print("-" * 60)
        
        try:
            # Generate sample market data
            market_data = generate_sample_market_data(days=200)
            
            # Calculate confluence
            confluence = calculator.calculate_confluence(
                symbol=symbol,
                market_data=market_data,
                sentiment_hours=24
            )
            
            if confluence:
                print(f"✅ Confluence Score for {symbol}:")
                print(f"   Overall Confluence: {confluence.confluence_score:.3f}")
                print(f"   Confluence Level: {confluence.confluence_level.value}")
                print(f"   Directional Bias: {confluence.directional_bias:+.3f} "
                      f"({'Bullish' if confluence.directional_bias > 0 else 'Bearish' if confluence.directional_bias < 0 else 'Neutral'})")
                print(f"   Confidence: {confluence.confidence:.2%}")
                print(f"   Components Used: {', '.join(confluence.components_used)}")
                print(f"   Meets Minimum Threshold: {'✅' if confluence.meets_minimum_threshold else '❌'}")
                print(f"   Meets High Threshold: {'✅' if confluence.meets_high_threshold else '❌'}")
                print()
                
                # Technical breakdown
                print("   📈 Technical Breakdown:")
                tech = confluence.breakdown.technical_score
                print(f"      Overall Technical Score: {tech.overall_score:+.3f}")
                print(f"      RSI Score: {tech.rsi_score:+.3f} (RSI: {tech.indicators.get('rsi', 'N/A'):.1f})")
                print(f"      SMA Trend Score: {tech.sma_trend_score:+.3f}")
                print(f"      Volume Score: {tech.volume_score:+.3f}")
                print(f"      Bollinger Score: {tech.bollinger_score:+.3f}")
                print(f"      Contribution: {confluence.breakdown.technical_contribution:.1%}")
                print()
                
                # Sentiment breakdown
                if confluence.breakdown.sentiment_score:
                    sent = confluence.breakdown.sentiment_score
                    print("   💭 Sentiment Breakdown:")
                    print(f"      Sentiment Score: {sent.score:+.3f}")
                    print(f"      Confidence: {sent.confidence:.2%}")
                    print(f"      Source Count: {sent.source_count}")
                    print(f"      Divergence Detected: {'⚠️ Yes' if sent.divergence_detected else '✅ No'}")
                    print(f"      Contribution: {confluence.breakdown.sentiment_contribution:.1%}")
                    print()
                else:
                    print("   💭 Sentiment: Not available")
                    print()
                
                # Options flow breakdown
                if confluence.breakdown.options_flow_score:
                    opts = confluence.breakdown.options_flow_score
                    print("   📊 Options Flow Breakdown:")
                    print(f"      Options Flow Score: {opts.score:+.3f}")
                    print(f"      Unusual Activity: {'⚠️ Yes' if opts.unusual_activity else '✅ No'}")
                    print(f"      Contribution: {confluence.breakdown.options_flow_contribution:.1%}")
                    print()
                else:
                    print("   📊 Options Flow: Not available (async support pending)")
                    print()
                
                print()
            else:
                print(f"⚠️  No confluence data available for {symbol}")
                print("   (May need real market data or sentiment sources configured)")
                print()
                
        except Exception as e:
            print(f"❌ Error calculating confluence for {symbol}: {e}")
            import traceback
            traceback.print_exc()
            print()
    
    print("=" * 60)
    print("✅ Confluence calculator test completed!")
    print("=" * 60)
    
    return True

if __name__ == "__main__":
    try:
        success = test_confluence()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n⚠️  Test interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

