#!/usr/bin/env python3
"""
Trading Bot API Usage Examples
===============================

This script demonstrates how to use the Trading Bot API from Python.
Includes examples for sentiment analysis, options flow, confluence scoring, and more.
"""

import requests
import json
from typing import Optional, Dict, Any
from datetime import datetime

# Configuration
BASE_URL = "http://localhost:8000"
API_KEY: Optional[str] = None  # Set your API key here if authentication is enabled


def make_request(method: str, endpoint: str, params: Optional[Dict] = None, **kwargs) -> Dict[Any, Any]:
    """
    Make an API request with optional authentication
    
    Args:
        method: HTTP method (GET, POST, etc.)
        endpoint: API endpoint path
        params: Query parameters
        **kwargs: Additional arguments to requests
        
    Returns:
        JSON response as dictionary
    """
    url = f"{BASE_URL}{endpoint}"
    headers = kwargs.pop('headers', {})
    
    # Add API key if provided
    if API_KEY:
        headers['X-API-Key'] = API_KEY
    
    response = requests.request(method, url, params=params, headers=headers, **kwargs)
    
    # Print rate limit info if available
    if 'X-RateLimit-Limit' in response.headers:
        print(f"Rate Limit: {response.headers['X-RateLimit-Remaining']}/{response.headers['X-RateLimit-Limit']} "
              f"(resets at {response.headers.get('X-RateLimit-Reset', 'N/A')})")
    
    response.raise_for_status()
    return response.json()


# ==================== Sentiment Analysis Examples ====================

def get_twitter_sentiment(symbol: str, hours: int = 24) -> Dict:
    """Get Twitter/X sentiment for a symbol"""
    print(f"\n📱 Fetching Twitter sentiment for {symbol} (last {hours}h)...")
    return make_request('GET', f'/api/sentiment/twitter/{symbol}', params={'hours': hours})


def get_reddit_sentiment(symbol: str, hours: int = 24) -> Dict:
    """Get Reddit sentiment for a symbol"""
    print(f"\n📱 Fetching Reddit sentiment for {symbol} (last {hours}h)...")
    return make_request('GET', f'/api/sentiment/reddit/{symbol}', params={'hours': hours})


def get_aggregated_sentiment(symbol: str, hours: int = 24) -> Dict:
    """Get aggregated sentiment across all sources"""
    print(f"\n📊 Fetching aggregated sentiment for {symbol} (last {hours}h)...")
    return make_request('GET', f'/api/sentiment/aggregated/{symbol}', params={'hours': hours})


def get_detailed_aggregated_sentiment(symbol: str, hours: int = 24) -> Dict:
    """Get detailed aggregated sentiment with provider breakdown"""
    print(f"\n📊 Fetching detailed aggregated sentiment for {symbol}...")
    return make_request('GET', f'/api/sentiment/aggregated/{symbol}/detailed', params={'hours': hours})


# ==================== Options Flow Examples ====================

def get_options_flow(symbol: str, hours: int = 24) -> Dict:
    """Get options flow data with pattern detection"""
    print(f"\n📈 Fetching options flow for {symbol} (last {hours}h)...")
    return make_request('GET', f'/api/options-flow/{symbol}', params={'hours': hours})


def get_sweeps(symbol: str, hours: int = 24) -> Dict:
    """Get detected sweep patterns"""
    print(f"\n📈 Fetching sweeps for {symbol}...")
    return make_request('GET', f'/api/options-flow/{symbol}/sweeps', params={'hours': hours})


def get_put_call_ratio(symbol: str, hours: int = 24) -> Dict:
    """Get put/call ratios"""
    print(f"\n📈 Fetching put/call ratio for {symbol}...")
    return make_request('GET', f'/api/options-flow/{symbol}/pc-ratio', params={'hours': hours})


def get_options_metrics(symbol: str, hours: int = 24) -> Dict:
    """Get comprehensive options flow metrics"""
    print(f"\n📈 Fetching options metrics for {symbol}...")
    return make_request('GET', f'/api/options-flow/{symbol}/metrics', params={'hours': hours})


# ==================== Confluence Examples ====================

def get_confluence_score(symbol: str, hours: int = 24) -> Dict:
    """Get confluence score for a symbol"""
    print(f"\n🎯 Fetching confluence score for {symbol}...")
    return make_request('GET', f'/api/confluence/{symbol}', params={'hours': hours})


# ==================== Market Data Examples ====================

def get_quote(symbol: str) -> Dict:
    """Get real-time quote"""
    print(f"\n💹 Fetching quote for {symbol}...")
    return make_request('GET', f'/api/market-data/quote/{symbol}')


def get_historical_data(symbol: str, days: int = 30, interval: str = '1d') -> Dict:
    """Get historical price data"""
    print(f"\n💹 Fetching historical data for {symbol} ({days} days, {interval})...")
    return make_request('GET', f'/api/market-data/historical/{symbol}', 
                       params={'days': days, 'interval': interval})


# ==================== Monitoring Examples ====================

def get_health() -> Dict:
    """Get system health status"""
    print("\n🏥 Checking system health...")
    return make_request('GET', '/health')


def get_providers_status() -> Dict:
    """Get status of all data providers"""
    print("\n📡 Checking provider status...")
    return make_request('GET', '/api/monitoring/providers/status')


def get_rate_limits() -> Dict:
    """Get rate limit status for all data sources"""
    print("\n⏱️  Checking rate limits...")
    return make_request('GET', '/api/monitoring/rate-limits')


# ==================== Main Examples ====================

def example_sentiment_analysis():
    """Example: Complete sentiment analysis workflow"""
    print("\n" + "="*60)
    print("EXAMPLE: Sentiment Analysis Workflow")
    print("="*60)
    
    symbol = "AAPL"
    
    # Get individual source sentiments
    twitter = get_twitter_sentiment(symbol, hours=24)
    print(f"Twitter Sentiment: {twitter.get('weighted_sentiment', 'N/A')}")
    
    reddit = get_reddit_sentiment(symbol, hours=24)
    print(f"Reddit Sentiment: {reddit.get('weighted_sentiment', 'N/A')}")
    
    # Get aggregated sentiment
    aggregated = get_aggregated_sentiment(symbol, hours=24)
    print(f"\nAggregated Sentiment: {aggregated.get('unified_sentiment', 'N/A')}")
    print(f"Confidence: {aggregated.get('confidence', 'N/A')}")
    print(f"Providers Used: {aggregated.get('providers_used', [])}")


def example_options_flow_analysis():
    """Example: Options flow analysis"""
    print("\n" + "="*60)
    print("EXAMPLE: Options Flow Analysis")
    print("="*60)
    
    symbol = "SPY"
    
    # Get options flow
    flows = get_options_flow(symbol, hours=24)
    print(f"Found {len(flows)} option flows")
    
    # Get sweeps
    sweeps = get_sweeps(symbol, hours=24)
    print(f"Found {len(sweeps)} sweeps")
    
    # Get put/call ratio
    pc_ratio = get_put_call_ratio(symbol, hours=24)
    print(f"Put/Call Volume Ratio: {pc_ratio.get('volume_ratio', 'N/A')}")
    
    # Get metrics
    metrics = get_options_metrics(symbol, hours=24)
    print(f"Bullish Flow: {metrics.get('bullish_flow', 'N/A')}")
    print(f"Bearish Flow: {metrics.get('bearish_flow', 'N/A')}")


def example_confluence_scoring():
    """Example: Confluence scoring"""
    print("\n" + "="*60)
    print("EXAMPLE: Confluence Scoring")
    print("="*60)
    
    symbol = "AAPL"
    
    confluence = get_confluence_score(symbol, hours=24)
    print(f"Confluence Score: {confluence.get('confluence_score', 'N/A')}")
    print(f"Directional Bias: {confluence.get('directional_bias', 'N/A')}")
    print(f"Confidence: {confluence.get('confidence', 'N/A')}")
    print(f"Meets Minimum Threshold: {confluence.get('meets_minimum_threshold', False)}")


def example_complete_workflow():
    """Example: Complete trading workflow"""
    print("\n" + "="*60)
    print("EXAMPLE: Complete Trading Workflow")
    print("="*60)
    
    symbol = "AAPL"
    
    # 1. Check health
    health = get_health()
    print(f"System Status: {health.get('status', 'unknown')}")
    
    # 2. Get quote
    quote = get_quote(symbol)
    print(f"Current Price: ${quote.get('price', 'N/A')}")
    
    # 3. Get sentiment
    sentiment = get_aggregated_sentiment(symbol)
    print(f"Sentiment: {sentiment.get('unified_sentiment', 'N/A')}")
    
    # 4. Get options flow
    options_metrics = get_options_metrics(symbol)
    print(f"Options Bullish Flow: {options_metrics.get('bullish_flow', 'N/A')}")
    
    # 5. Get confluence
    confluence = get_confluence_score(symbol)
    print(f"Confluence Score: {confluence.get('confluence_score', 'N/A')}")
    
    # 6. Make trading decision
    if confluence.get('meets_minimum_threshold', False):
        print(f"\n✅ Trade signal: BUY {symbol}")
    else:
        print(f"\n❌ Trade signal: HOLD")


if __name__ == "__main__":
    print("Trading Bot API Usage Examples")
    print("="*60)
    print(f"Base URL: {BASE_URL}")
    print(f"API Key: {'Set' if API_KEY else 'Not set (using IP-based rate limiting)'}")
    
    try:
        # Run examples
        example_sentiment_analysis()
        example_options_flow_analysis()
        example_confluence_scoring()
        example_complete_workflow()
        
        print("\n" + "="*60)
        print("✅ All examples completed successfully!")
        print("="*60)
        
    except requests.exceptions.RequestException as e:
        print(f"\n❌ Error: {e}")
        if hasattr(e, 'response') and e.response is not None:
            print(f"Response: {e.response.text}")
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()

