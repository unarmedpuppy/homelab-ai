#!/usr/bin/env python3
"""
Test SEC Filings Sentiment Integration
======================================

Test script for SEC filings sentiment provider.
"""

import sys
from pathlib import Path
from datetime import datetime

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    from src.data.providers.sentiment.sec_filings import SECFilingsSentimentProvider
    from src.config.settings import settings
    IMPORTS_AVAILABLE = True
except ImportError as e:
    print(f"⚠️  Import error: {e}")
    print("\nNote: Dependencies may not be installed. Try:")
    print("  1. Install dependencies: pip install -r requirements/base.txt")
    print("  2. Or run in Docker: docker-compose exec bot python scripts/test_sec_filings_sentiment.py")
    IMPORTS_AVAILABLE = False

import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def test_sec_filings_sentiment():
    """Test SEC filings sentiment provider"""
    if not IMPORTS_AVAILABLE:
        return False
    
    print("=" * 60)
    print("Testing SEC Filings Sentiment Provider")
    print("=" * 60)
    print()
    
    # Check configuration
    print("📋 Configuration Check:")
    if hasattr(settings, 'sec_filings'):
        config = settings.sec_filings
        print(f"   SEC Filings Enabled: {'✅ Enabled' if config.enabled else '❌ Disabled'}")
        print(f"   User Agent: {config.user_agent}")
        print(f"   Email Address: {config.email_address}")
        print(f"   Rate Limit Enabled: {config.rate_limit_enabled}")
        print(f"   Cache TTL: {config.cache_ttl}s")
        print(f"   Max Filings Per Type: {config.max_filings_per_type}")
        print(f"   Filing Types: {', '.join(config.filing_types)}")
    else:
        print("   ⚠️  SEC Filings settings not found")
    print()
    
    # Create provider
    print("🔧 Initializing SEC Filings Sentiment Provider...")
    try:
        provider = SECFilingsSentimentProvider(persist_to_db=True)
    except ImportError as e:
        print(f"❌ Failed to initialize provider: {e}")
        print("   Please install: pip install sec-edgar-downloader")
        return False
    
    if not provider.is_available():
        print("❌ SEC filings provider not available")
        print("   Please check SEC_FILINGS_USER_AGENT and SEC_FILINGS_EMAIL_ADDRESS in your .env file")
        print("   SEC requires a valid user agent with email address")
        return False
    
    print("✅ SEC filings provider initialized")
    print(f"   Database Persistence: {'✅ Enabled' if provider.persist_to_db else '❌ Disabled'}")
    print()
    
    # Test symbol sentiment
    test_symbols = ["AAPL", "MSFT", "TSLA"]
    
    for symbol in test_symbols:
        print(f"📊 Analyzing sentiment for {symbol} from SEC filings...")
        print("-" * 60)
        
        try:
            # Test with 365 days of data
            sentiment = provider.get_sentiment(symbol, days=365)
            
            if sentiment:
                print(f"✅ Sentiment Analysis for {symbol}:")
                print(f"   Filings Analyzed: {sentiment.mention_count}")
                print(f"   Average Sentiment: {sentiment.average_sentiment:.3f}")
                print(f"   Weighted Sentiment: {sentiment.weighted_sentiment:.3f}")
                print(f"   Sentiment Level: {sentiment.sentiment_level.value}")
                print(f"   Confidence: {sentiment.confidence:.2%}")
                print(f"   Engagement Score: {sentiment.engagement_score:.3f}")
                print()
                
                if sentiment.tweets:
                    print(f"   Sample Filings ({len(sentiment.tweets)}):")
                    for i, filing_sentiment in enumerate(sentiment.tweets[:3], 1):
                        print(f"      {i}. Score: {filing_sentiment.sentiment_score:.3f}, "
                              f"Level: {filing_sentiment.sentiment_level.value}")
                    print()
            else:
                print(f"⚠️  No sentiment data available for {symbol}")
                print(f"   This might mean no recent filings found in the last 365 days")
                print()
                
        except Exception as e:
            print(f"❌ Error analyzing {symbol}: {e}")
            import traceback
            traceback.print_exc()
            print()
    
    print("=" * 60)
    print("✅ SEC Filings Sentiment Provider Test Complete")
    print("=" * 60)
    print()
    print("Note: SEC filings are official company documents with high confidence.")
    print("      This provider analyzes Management Discussion & Analysis (MD&A),")
    print("      Risk Factors, and other key sections for sentiment.")
    
    return True


if __name__ == "__main__":
    success = test_sec_filings_sentiment()
    sys.exit(0 if success else 1)

