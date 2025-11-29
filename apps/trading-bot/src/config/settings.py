"""
Configuration Management
========================

Centralized configuration management using Pydantic settings.
Supports environment-specific configurations and validation.
"""

from pydantic_settings import BaseSettings
from pydantic import Field, validator
from typing import Optional, List, Union, Dict
import os
from pathlib import Path

class DatabaseSettings(BaseSettings):
    """Database configuration"""
    url: str = Field(default="sqlite:///./bot.db", description="Database connection URL")
    echo: bool = Field(default=False, description="Enable SQLAlchemy query logging")
    pool_size: int = Field(default=5, description="Connection pool size")
    max_overflow: int = Field(default=10, description="Max overflow connections")
    
    class Config:
        env_prefix = "DB_"

class IBKRSettings(BaseSettings):
    """Interactive Brokers configuration"""
    host: str = Field(default="127.0.0.1", description="TWS/Gateway host")
    port: int = Field(default=7497, description="TWS/Gateway port")
    client_id: int = Field(default=9, description="Client ID")
    timeout: int = Field(default=10, description="Connection timeout in seconds")
    
    @validator('port')
    def validate_port(cls, v):
        if not 1 <= v <= 65535:
            raise ValueError('Port must be between 1 and 65535')
        return v
    
    class Config:
        env_prefix = "IBKR_"

class UnusualWhalesSettings(BaseSettings):
    """Unusual Whales API configuration"""
    api_key: Optional[str] = Field(default=None, description="API key for Unusual Whales")
    base_url: str = Field(default="https://api.unusualwhales.com", description="Base API URL")
    timeout: int = Field(default=30, description="Request timeout in seconds")
    rate_limit: int = Field(default=100, description="Requests per minute")
    
    class Config:
        env_prefix = "UW_"

class TwitterSettings(BaseSettings):
    """Twitter/X API configuration"""
    api_key: Optional[str] = Field(default=None, description="Twitter API Key")
    api_secret: Optional[str] = Field(default=None, description="Twitter API Secret")
    bearer_token: Optional[str] = Field(default=None, description="Twitter Bearer Token")
    access_token: Optional[str] = Field(default=None, description="Twitter Access Token")
    access_token_secret: Optional[str] = Field(default=None, description="Twitter Access Token Secret")
    rate_limit_enabled: bool = Field(default=True, description="Enable rate limiting")
    cache_ttl: int = Field(default=300, description="Cache TTL in seconds")
    max_results: int = Field(default=100, description="Maximum results per search")
    search_language: str = Field(default="en", description="Search language code")
    
    @validator('max_results')
    def validate_max_results(cls, v):
        if not 10 <= v <= 100:
            raise ValueError('max_results must be between 10 and 100')
        return v
    
    class Config:
        env_prefix = "TWITTER_"

class StockTwitsSettings(BaseSettings):
    """StockTwits API configuration"""
    api_token: Optional[str] = Field(default=None, description="StockTwits API token (optional, for authenticated requests)")
    cache_ttl: int = Field(default=300, description="Cache TTL in seconds")
    rate_limit_enabled: bool = Field(default=True, description="Enable rate limiting")
    max_results: int = Field(default=30, description="Maximum messages per request (API limit: 30)")
    enable_vader: bool = Field(default=False, description="Enable VADER sentiment enhancement (optional)")
    base_url: str = Field(default="https://api.stocktwits.com/api/2", description="StockTwits API base URL")
    
    @validator('max_results')
    def validate_max_results(cls, v):
        if not 1 <= v <= 30:
            raise ValueError('max_results must be between 1 and 30 (API limit)')
        return v
    
    class Config:
        env_prefix = "STOCKTWITS_"

class RedditSettings(BaseSettings):
    """Reddit API configuration"""
    client_id: Optional[str] = Field(default=None, description="Reddit Client ID")
    client_secret: Optional[str] = Field(default=None, description="Reddit Client Secret")
    user_agent: str = Field(default="TradingBot/1.0 by /u/tradingbot", description="Reddit User Agent")
    username: Optional[str] = Field(default=None, description="Reddit Username (optional)")
    password: Optional[str] = Field(default=None, description="Reddit Password (optional)")
    rate_limit_enabled: bool = Field(default=True, description="Enable rate limiting")
    cache_ttl: int = Field(default=300, description="Cache TTL in seconds")
    max_results: int = Field(default=100, description="Maximum results per search")
    subreddits: str = Field(default="wallstreetbets,stocks,investing", description="Comma-separated subreddit names")
    min_score: int = Field(default=0, description="Minimum post/comment score to include")
    min_length: int = Field(default=10, description="Minimum text length for analysis")
    
    @validator('max_results')
    def validate_max_results(cls, v):
        if not 10 <= v <= 1000:
            raise ValueError('max_results must be between 10 and 1000')
        return v
    
    class Config:
        env_prefix = "REDDIT_"

class NewsSettings(BaseSettings):
    """Financial News aggregation configuration"""
    enabled: bool = Field(default=True, description="Enable news sentiment provider")
    newsapi_key: Optional[str] = Field(default=None, description="NewsAPI API key (optional)")
    rss_feeds: str = Field(
        default="https://feeds.finance.yahoo.com/rss/2.0/headline",
        description="Comma-separated RSS feed URLs"
    )
    fetch_full_text: bool = Field(default=True, description="Fetch full article text (requires newspaper3k)")
    cache_ttl: int = Field(default=600, description="Cache TTL in seconds (10 min default)")
    max_results: int = Field(default=50, description="Maximum articles per source")
    
    @validator('max_results')
    def validate_max_results(cls, v):
        if not 10 <= v <= 200:
            raise ValueError('max_results must be between 10 and 200')
        return v
    
    class Config:
        env_prefix = "NEWS_"

class StockTwitsSettings(BaseSettings):
    """StockTwits API configuration"""
    enabled: bool = Field(default=True, description="Enable StockTwits sentiment provider")
    base_url: str = Field(default="https://api.stocktwits.com/api/2", description="StockTwits API base URL")
    access_token: Optional[str] = Field(default=None, description="StockTwits access token (optional, increases rate limits)")
    user_agent: str = Field(default="TradingBot/1.0", description="User agent for API requests")
    rate_limit_enabled: bool = Field(default=True, description="Enable rate limiting")
    cache_ttl: int = Field(default=300, description="Cache TTL in seconds")
    max_results: int = Field(default=30, description="Maximum messages per request (API max is 30)")
    timeout: int = Field(default=30, description="API request timeout in seconds")
    enable_vader: bool = Field(default=False, description="Enable VADER sentiment enhancement")

    @validator('max_results')
    def validate_max_results(cls, v):
        if not 10 <= v <= 30:
            raise ValueError('max_results must be between 10 and 30')
        return v

    class Config:
        env_prefix = "STOCKTWITS_"

class GoogleTrendsSettings(BaseSettings):
    """Google Trends API configuration"""
    enabled: bool = Field(default=True, description="Enable Google Trends provider")
    rate_limit_enabled: bool = Field(default=True, description="Enable rate limiting")
    cache_ttl: int = Field(default=3600, description="Cache TTL in seconds (1 hour default)")
    default_geo: str = Field(default="US", description="Default geographic location")
    request_delay: float = Field(default=1.0, description="Delay between requests in seconds")

    @property
    def geo(self) -> str:
        """Alias for default_geo for compatibility"""
        return self.default_geo

    class Config:
        env_prefix = "GOOGLE_TRENDS_"

class MentionVolumeSettings(BaseSettings):
    """Mention Volume aggregation configuration"""
    enabled: bool = Field(default=True, description="Enable mention volume provider")
    spike_threshold: float = Field(default=2.0, description="Mention spike threshold (multiplier of baseline)")
    momentum_threshold: float = Field(default=0.3, description="Minimum momentum score for trending")
    baseline_lookback_hours: int = Field(default=168, description="Hours to look back for baseline (default: 7 days)")
    # Query limits
    max_query_limit: int = Field(default=10000, description="Maximum records to fetch per query")
    volume_trend_max_limit: int = Field(default=50000, description="Maximum records for volume trend queries")
    batch_size: int = Field(default=10, description="Batch size for processing multiple symbols")
    # Trend calculation thresholds
    volume_trend_change_threshold: float = Field(default=0.2, description="Percentage change threshold for trend detection (20%)")
    
    class Config:
        env_prefix = "MENTION_VOLUME_"

class AnalystRatingsSettings(BaseSettings):
    """Analyst Ratings configuration"""
    enabled: bool = Field(default=True, description="Enable analyst ratings sentiment provider")
    cache_ttl: int = Field(default=3600, description="Cache TTL in seconds (1 hour default)")
    use_price_target_weighting: bool = Field(default=True, description="Weight sentiment by price target upside/downside")
    timeout_seconds: int = Field(default=10, description="Timeout for yfinance API calls in seconds")
    max_retries: int = Field(default=3, description="Maximum number of retry attempts for failed requests")
    retry_backoff_factor: float = Field(default=1.5, description="Exponential backoff factor for retries")
    data_freshness_warning_days: int = Field(default=7, description="Warn if analyst data appears stale (days since last update)")
    
    class Config:
        env_prefix = "ANALYST_RATINGS_"

class InsiderTradingSettings(BaseSettings):
    """Insider Trading & Institutional Holdings configuration"""
    enabled: bool = Field(default=True, description="Enable insider trading sentiment provider")
    cache_ttl: int = Field(default=3600, description="Cache TTL in seconds (1 hour default)")
    insider_weight: float = Field(default=0.6, description="Weight for insider trading sentiment (0.0-1.0)")
    institutional_weight: float = Field(default=0.4, description="Weight for institutional holdings sentiment (0.0-1.0)")
    timeout_seconds: int = Field(default=10, description="Timeout for yfinance API calls in seconds")
    max_retries: int = Field(default=3, description="Maximum number of retry attempts for failed requests")
    retry_backoff_factor: float = Field(default=1.5, description="Exponential backoff factor for retries")
    rate_limit_requests_per_minute: int = Field(default=60, description="Rate limit for yfinance API calls (requests per minute)")
    
    @validator('insider_weight', 'institutional_weight')
    def validate_weights(cls, v):
        if not 0.0 <= v <= 1.0:
            raise ValueError('Weights must be between 0.0 and 1.0')
        return v
    
    @validator('timeout_seconds')
    def validate_timeout(cls, v):
        if not 1 <= v <= 60:
            raise ValueError('Timeout must be between 1 and 60 seconds')
        return v
    
    @validator('max_retries')
    def validate_max_retries(cls, v):
        if not 0 <= v <= 10:
            raise ValueError('Max retries must be between 0 and 10')
        return v
    
    @validator('rate_limit_requests_per_minute')
    def validate_rate_limit(cls, v):
        if not 1 <= v <= 1000:
            raise ValueError('Rate limit must be between 1 and 1000 requests per minute')
        return v
    
    class Config:
        env_prefix = "INSIDER_TRADING_"

class EventCalendarSettings(BaseSettings):
    """Earnings & Event Calendar configuration"""
    enabled: bool = Field(default=True, description="Enable event calendar provider")
    cache_ttl: int = Field(default=3600, description="Cache TTL in seconds (1 hour default)")
    lookahead_days: int = Field(default=90, description="Days ahead to fetch earnings calendar")
    economic_events_enabled: bool = Field(default=False, description="Enable economic events tracking (CPI, Fed meetings)")
    max_concurrent_workers: int = Field(default=10, description="Maximum concurrent workers for processing multiple symbols")
    retry_attempts: int = Field(default=3, description="Number of retry attempts for failed API calls")
    retry_backoff_multiplier: float = Field(default=1.0, description="Multiplier for exponential backoff on retries")
    
    @validator('max_concurrent_workers')
    def validate_max_workers(cls, v):
        if not 1 <= v <= 50:
            raise ValueError('max_concurrent_workers must be between 1 and 50')
        return v
    
    @validator('retry_attempts')
    def validate_retry_attempts(cls, v):
        if not 1 <= v <= 10:
            raise ValueError('retry_attempts must be between 1 and 10')
        return v
    
    class Config:
        env_prefix = "EVENT_CALENDAR_"

class DarkPoolSettings(BaseSettings):
    """Dark Pool & Institutional Flow configuration"""
    enabled: bool = Field(default=False, description="Enable dark pool sentiment provider (requires API key)")
    api_key: Optional[str] = Field(default=None, description="Dark pool data API key (e.g., FlowAlgo, Cheddar Flow)")
    base_url: Optional[str] = Field(default=None, description="Dark pool API base URL")
    cache_ttl: int = Field(default=1800, description="Cache TTL in seconds (30 min default)")
    
    class Config:
        env_prefix = "DARK_POOL_"

class WebSocketSettings(BaseSettings):
    """WebSocket configuration"""
    enabled: bool = Field(default=True, description="Enable WebSocket server")
    ping_interval: int = Field(default=30, description="Ping interval in seconds for keepalive")
    heartbeat_timeout: int = Field(default=60, description="Heartbeat timeout in seconds (disconnect if no pong)")
    price_update_interval: int = Field(default=3, description="Price update interval in seconds")
    portfolio_update_interval: int = Field(default=5, description="Portfolio update interval in seconds")
    market_data_interval: int = Field(default=5, description="Market data (OHLCV) update interval in seconds")
    options_flow_interval: int = Field(default=10, description="Options flow update interval in seconds")
    max_connections: int = Field(default=100, description="Maximum concurrent WebSocket connections")
    
    @validator('ping_interval', 'heartbeat_timeout', 'price_update_interval', 'portfolio_update_interval', 
               'market_data_interval', 'options_flow_interval')
    def validate_interval(cls, v):
        if not 1 <= v <= 300:
            raise ValueError('Interval must be between 1 and 300 seconds')
        return v
    
    @validator('max_connections')
    def validate_max_connections(cls, v):
        if not 1 <= v <= 1000:
            raise ValueError('Max connections must be between 1 and 1000')
        return v
    
    class Config:
        env_prefix = "WEBSOCKET_"

class SentimentAggregatorSettings(BaseSettings):
    """Sentiment Aggregator configuration"""
    cache_ttl: int = Field(default=300, description="Aggregator cache TTL in seconds")
    # Provider weights (0.0 to 1.0, should sum to ~1.0)
    weight_twitter: float = Field(default=0.5, description="Weight for Twitter sentiment")
    weight_reddit: float = Field(default=0.3, description="Weight for Reddit sentiment")
    weight_stocktwits: float = Field(default=0.1, description="Weight for StockTwits sentiment")
    weight_news: float = Field(default=0.1, description="Weight for news sentiment")
    weight_options: float = Field(default=0.2, description="Weight for options flow sentiment")
    weight_analyst_ratings: float = Field(default=0.15, description="Weight for analyst ratings sentiment")
    weight_google_trends: float = Field(default=0.15, description="Weight for Google Trends sentiment")
    weight_sec_filings: float = Field(default=0.2, description="Weight for SEC filings sentiment (higher weight due to official nature)")
    weight_insider_trading: float = Field(default=0.25, description="Weight for insider trading sentiment")
    # Time decay settings
    time_decay_enabled: bool = Field(default=True, description="Enable time-decay weighting")
    time_decay_half_life_hours: float = Field(default=6.0, description="Half-life for time decay in hours")
    # Divergence detection
    divergence_threshold: float = Field(default=0.5, description="Threshold for detecting sentiment divergence")
    # Minimum confidence to include provider
    min_provider_confidence: float = Field(default=0.3, description="Minimum confidence to include provider")
    # Minimum providers required for aggregation
    min_providers: int = Field(default=1, description="Minimum number of providers required")
    
    @validator('weight_twitter', 'weight_reddit', 'weight_stocktwits', 'weight_news', 
               'weight_options', 'weight_analyst_ratings', 'weight_google_trends',
               'weight_insider_trading', 'weight_sec_filings')
    def validate_weights(cls, v):
        if not 0.0 <= v <= 1.0:
            raise ValueError('Weights must be between 0.0 and 1.0')
        return v
    
    @validator('min_providers')
    def validate_min_providers(cls, v):
        if not 1 <= v <= 10:
            raise ValueError('min_providers must be between 1 and 10')
        return v
    
    class Config:
        env_prefix = "SENTIMENT_AGGREGATOR_"

class ConfluenceSettings(BaseSettings):
    """Confluence Calculator configuration"""
    # Component weights (should sum to ~1.0)
    weight_technical: float = Field(default=0.50, description="Weight for technical indicators")
    weight_sentiment: float = Field(default=0.30, description="Weight for sentiment data")
    weight_options_flow: float = Field(default=0.20, description="Weight for options flow data")
    
    # Thresholds
    min_confluence: float = Field(default=0.6, description="Minimum confluence to execute trade (0.0-1.0)")
    high_confluence: float = Field(default=0.8, description="High confidence confluence threshold (0.0-1.0)")
    
    # Technical indicator weights (for internal technical score calculation)
    weight_rsi: float = Field(default=0.25, description="Weight for RSI in technical score")
    weight_sma_trend: float = Field(default=0.30, description="Weight for SMA trend in technical score")
    weight_volume: float = Field(default=0.25, description="Weight for volume in technical score")
    weight_bollinger: float = Field(default=0.20, description="Weight for Bollinger Bands in technical score")
    
    # Enable/disable components
    use_sentiment: bool = Field(default=True, description="Include sentiment in confluence")
    use_options_flow: bool = Field(default=True, description="Include options flow in confluence")
    
    # Cache
    cache_ttl: int = Field(default=300, description="Cache TTL in seconds")
    
    @validator('weight_technical', 'weight_sentiment', 'weight_options_flow')
    def validate_component_weights(cls, v):
        if not 0.0 <= v <= 1.0:
            raise ValueError('Component weights must be between 0.0 and 1.0')
        return v
    
    @validator('min_confluence', 'high_confluence')
    def validate_thresholds(cls, v):
        if not 0.0 <= v <= 1.0:
            raise ValueError('Thresholds must be between 0.0 and 1.0')
        return v
    
    class Config:
        env_prefix = "CONFLUENCE_"

class DataRetentionSettings(BaseSettings):
    """Data retention configuration"""
    retention_tweets_days: int = Field(default=90, description="Retention period for tweets (days)")
    retention_reddit_posts_days: int = Field(default=90, description="Retention period for Reddit posts (days)")
    retention_symbol_sentiments_days: int = Field(default=365, description="Retention period for symbol sentiments (days)")
    retention_aggregated_sentiments_days: int = Field(default=730, description="Retention period for aggregated sentiments (days)")
    retention_confluence_scores_days: int = Field(default=730, description="Retention period for confluence scores (days)")
    enable_cleanup: bool = Field(default=True, description="Enable automatic cleanup")
    cleanup_schedule_hours: int = Field(default=24, description="Hours between cleanup runs")
    
    @validator('retention_tweets_days', 'retention_reddit_posts_days', 'retention_symbol_sentiments_days',
               'retention_aggregated_sentiments_days', 'retention_confluence_scores_days')
    def validate_retention_days(cls, v):
        if v < 1:
            raise ValueError('Retention days must be at least 1')
        return v
    
    class Config:
        env_prefix = "RETENTION_"

class TradingSettings(BaseSettings):
    """Trading strategy configuration"""
    default_qty: int = Field(default=10, description="Default position size")
    default_entry_threshold: float = Field(default=0.005, description="Default SMA entry threshold (0.5%)")
    default_take_profit: float = Field(default=0.20, description="Default take profit (20%)")
    default_stop_loss: float = Field(default=0.10, description="Default stop loss (10%)")
    max_position_size: int = Field(default=1000, description="Maximum position size")
    max_daily_trades: int = Field(default=50, description="Maximum trades per day")
    
    @validator('default_entry_threshold', 'default_take_profit', 'default_stop_loss')
    def validate_percentages(cls, v):
        if not 0 <= v <= 1:
            raise ValueError('Percentage values must be between 0 and 1')
        return v
    
    class Config:
        env_prefix = "TRADING_"

class LoggingSettings(BaseSettings):
    """Logging configuration"""
    level: str = Field(default="INFO", description="Logging level")
    format: str = Field(default="json", description="Log format (json/text)")
    file: Optional[str] = Field(default=None, description="Log file path")
    max_size: int = Field(default=10485760, description="Max log file size (10MB)")
    backup_count: int = Field(default=5, description="Number of backup files")
    
    @validator('level')
    def validate_level(cls, v):
        valid_levels = ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']
        if v.upper() not in valid_levels:
            raise ValueError(f'Log level must be one of {valid_levels}')
        return v.upper()
    
    class Config:
        env_prefix = "LOG_"

class APISettings(BaseSettings):
    """API configuration"""
    host: str = Field(default="0.0.0.0", description="API host")
    port: int = Field(default=8000, description="API port")
    debug: bool = Field(default=False, description="Enable debug mode")
    cors_origins: List[str] = Field(default=["*"], description="CORS allowed origins")
    rate_limit: str = Field(default="100/minute", description="Rate limit per IP")
    
    # API Authentication
    auth_enabled: bool = Field(default=False, description="Enable API key authentication")
    api_keys: List[str] = Field(default=[], description="Valid API keys (comma-separated or list)")
    api_key_header: str = Field(default="X-API-Key", description="Header name for API key")
    
    # Enhanced Rate Limiting
    rate_limit_per_key: str = Field(default="1000/hour", description="Rate limit per API key")
    rate_limit_per_ip: str = Field(default="100/minute", description="Rate limit per IP (no key)")
    
    # Rate Limit Headers
    enable_rate_limit_headers: bool = Field(default=True, description="Include rate limit info in response headers")
    
    class Config:
        env_prefix = "API_"
        
    @validator('api_keys', pre=True)
    def parse_api_keys(cls, v):
        """Parse API keys from string or list"""
        if isinstance(v, str):
            # Handle comma-separated string
            if v.strip():
                return [key.strip() for key in v.split(',') if key.strip()]
            return []
        return v if isinstance(v, list) else []

class RedisSettings(BaseSettings):
    """Redis configuration for caching and background tasks"""
    host: str = Field(default="localhost", description="Redis host")
    port: int = Field(default=6379, description="Redis port")
    password: Optional[str] = Field(default=None, description="Redis password")
    db: int = Field(default=0, description="Redis database number")
    
    class Config:
        env_prefix = "REDIS_"

class MetricsSettings(BaseSettings):
    """Prometheus metrics configuration"""
    enabled: bool = Field(default=True, description="Enable metrics collection")
    metrics_path: str = Field(default="/metrics", description="Metrics endpoint path")
    enable_internal_metrics: bool = Field(default=True, description="Enable built-in Prometheus process metrics")
    default_labels: Dict[str, str] = Field(default_factory=dict, description="Default labels for all metrics")
    
    class Config:
        env_prefix = "METRICS_"

class SchedulerSettings(BaseSettings):
    """Trading scheduler configuration"""
    enabled: bool = Field(default=False, description="Enable automatic trading scheduler")
    evaluation_interval: int = Field(default=60, description="Strategy evaluation interval (seconds)")
    exit_check_interval: int = Field(default=30, description="Exit condition check interval (seconds)")
    min_confidence: float = Field(default=0.5, description="Minimum confidence to execute trades (0.0-1.0)")
    max_concurrent_trades: int = Field(default=5, description="Maximum concurrent trades")
    require_ibkr_connection: bool = Field(default=True, description="Require IBKR connection to run")
    market_hours_only: bool = Field(default=True, description="Only trade during market hours (9:30 AM - 4:00 PM ET)")
    
    @validator('evaluation_interval', 'exit_check_interval')
    def validate_intervals(cls, v):
        if v < 5:
            raise ValueError('Intervals must be at least 5 seconds')
        return v
    
    @validator('min_confidence')
    def validate_confidence(cls, v):
        if not 0.0 <= v <= 1.0:
            raise ValueError('min_confidence must be between 0.0 and 1.0')
        return v
    
    @validator('max_concurrent_trades')
    def validate_max_trades(cls, v):
        if v < 1:
            raise ValueError('max_concurrent_trades must be at least 1')
        return v
    
    class Config:
        env_prefix = "SCHEDULER_"

class PositionSyncSettings(BaseSettings):
    """Position sync service configuration"""
    enabled: bool = Field(default=True, description="Enable position sync service")
    sync_interval: int = Field(default=300, description="Position sync interval in seconds (5 minutes default)")
    sync_on_trade: bool = Field(default=True, description="Sync positions after trade execution")
    sync_on_position_update: bool = Field(default=True, description="Sync positions on IBKR position update callbacks")
    mark_missing_as_closed: bool = Field(default=False, description="Mark positions as closed if not found in IBKR")
    calculate_realized_pnl: bool = Field(default=True, description="Calculate realized P&L when positions close")
    default_account_id: int = Field(default=1, description="Default account ID for position sync")
    
    @validator('sync_interval')
    def validate_sync_interval(cls, v):
        if v < 10:
            raise ValueError('sync_interval must be at least 10 seconds')
        return v
    
    class Config:
        env_prefix = "POSITION_SYNC_"

class RiskManagementSettings(BaseSettings):
    """Risk Management & Cash Account Rules configuration"""
    # Cash Account Rules
    cash_account_threshold: float = Field(default=25000.0, description="Balance threshold for cash account mode ($25k default)")
    pdt_enforcement_mode: str = Field(default="strict", description="PDT enforcement mode: strict or warning")
    gfv_enforcement_mode: str = Field(default="warning", description="GFV enforcement mode: strict or warning")
    
    # Trade Frequency Limits
    daily_trade_limit: int = Field(default=5, description="Maximum trades per day in cash account mode")
    weekly_trade_limit: int = Field(default=20, description="Maximum trades per week in cash account mode")
    
    # Position Sizing by Confidence
    position_size_low_confidence: float = Field(default=0.01, description="Position size for low confidence (1% of account)")
    position_size_medium_confidence: float = Field(default=0.025, description="Position size for medium confidence (2.5% of account)")
    position_size_high_confidence: float = Field(default=0.04, description="Position size for high confidence (4% of account)")
    max_position_size_pct: float = Field(default=0.10, description="Maximum position size as percentage of account (10% hard cap)")
    
    # Profit Taking Rules
    profit_take_level_1: float = Field(default=0.05, description="First profit taking level (5%)")
    profit_take_level_2: float = Field(default=0.10, description="Second profit taking level (10%)")
    profit_take_level_3: float = Field(default=0.20, description="Third profit taking level (20%)")
    partial_exit_enabled: bool = Field(default=True, description="Enable partial exit strategy")
    partial_exit_level_1_pct: float = Field(default=0.25, description="Partial exit percentage at level 1 (25%)")
    partial_exit_level_2_pct: float = Field(default=0.50, description="Partial exit percentage at level 2 (50%)")
    
    # Settlement Period
    settlement_days: int = Field(default=2, description="Settlement period in business days (T+2 default)")
    
    # Account Monitoring
    balance_check_interval_minutes: int = Field(default=5, description="Interval for checking account balance (minutes)")
    balance_cache_duration_minutes: int = Field(default=5, description="Duration to cache balance (minutes)")
    
    @validator('pdt_enforcement_mode', 'gfv_enforcement_mode')
    def validate_enforcement_mode(cls, v):
        if v not in ['strict', 'warning']:
            raise ValueError('enforcement_mode must be "strict" or "warning"')
        return v
    
    @validator('cash_account_threshold')
    def validate_threshold(cls, v):
        if v < 0:
            raise ValueError('cash_account_threshold must be >= 0')
        return v
    
    @validator('daily_trade_limit', 'weekly_trade_limit')
    def validate_trade_limits(cls, v):
        if v < 1:
            raise ValueError('Trade limits must be >= 1')
        return v
    
    @validator('position_size_low_confidence', 'position_size_medium_confidence', 
               'position_size_high_confidence', 'max_position_size_pct')
    def validate_position_sizes(cls, v):
        if not 0.0 < v <= 1.0:
            raise ValueError('Position sizes must be between 0.0 and 1.0')
        return v
    
    @validator('profit_take_level_1', 'profit_take_level_2', 'profit_take_level_3')
    def validate_profit_levels(cls, v):
        if not 0.0 < v <= 1.0:
            raise ValueError('Profit take levels must be between 0.0 and 1.0')
        return v
    
    @validator('settlement_days')
    def validate_settlement_days(cls, v):
        if not 0 <= v <= 5:
            raise ValueError('settlement_days must be between 0 and 5')
        return v
    
    class Config:
        env_prefix = "RISK_"

class Settings(BaseSettings):
    """Main application settings"""
    
    # Environment
    environment: str = Field(default="development", description="Environment name")
    debug: bool = Field(default=False, description="Debug mode")
    
    # Component settings
    database: DatabaseSettings = DatabaseSettings()
    ibkr: IBKRSettings = IBKRSettings()
    unusual_whales: UnusualWhalesSettings = UnusualWhalesSettings()
    twitter: TwitterSettings = TwitterSettings()
    reddit: RedditSettings = RedditSettings()
    news: NewsSettings = NewsSettings()
    stocktwits: StockTwitsSettings = StockTwitsSettings()
    event_calendar: EventCalendarSettings = EventCalendarSettings()
    google_trends: GoogleTrendsSettings = GoogleTrendsSettings()
    mention_volume: MentionVolumeSettings = MentionVolumeSettings()
    analyst_ratings: AnalystRatingsSettings = AnalystRatingsSettings()
    insider_trading: InsiderTradingSettings = InsiderTradingSettings()
    dark_pool: DarkPoolSettings = DarkPoolSettings()
    websocket: WebSocketSettings = WebSocketSettings()
    sentiment_aggregator: SentimentAggregatorSettings = SentimentAggregatorSettings()
    confluence: ConfluenceSettings = ConfluenceSettings()
    retention: DataRetentionSettings = DataRetentionSettings()
    trading: TradingSettings = TradingSettings()
    logging: LoggingSettings = LoggingSettings()
    api: APISettings = APISettings()
    redis: RedisSettings = RedisSettings()
    metrics: MetricsSettings = MetricsSettings()
    risk: RiskManagementSettings = RiskManagementSettings()
    scheduler: SchedulerSettings = SchedulerSettings()
    position_sync: PositionSyncSettings = PositionSyncSettings()
    
    # Paths
    data_dir: Path = Field(default=Path("./data"), description="Data directory")
    logs_dir: Path = Field(default=Path("./logs"), description="Logs directory")
    
    @validator('environment')
    def validate_environment(cls, v):
        valid_envs = ['development', 'testing', 'staging', 'production']
        if v not in valid_envs:
            raise ValueError(f'Environment must be one of {valid_envs}')
        return v
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Create directories if they don't exist
        self.data_dir.mkdir(exist_ok=True)
        self.logs_dir.mkdir(exist_ok=True)
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False

# Global settings instance
settings = Settings()
