"""
Database Models
===============

SQLAlchemy models for the trading bot database.
"""

from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, Text, ForeignKey, Enum, JSON, Index
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from datetime import datetime
from enum import Enum as PyEnum
from typing import Optional

Base = declarative_base()

class TradeSide(PyEnum):
    """Trade side enumeration"""
    BUY = "BUY"
    SELL = "SELL"

class OrderStatus(PyEnum):
    """Order status enumeration"""
    PENDING = "pending"
    SUBMITTED = "submitted"
    FILLED = "filled"
    CANCELLED = "cancelled"
    REJECTED = "rejected"

class PositionStatus(PyEnum):
    """Position status enumeration"""
    OPEN = "open"
    CLOSED = "closed"

class StrategyType(PyEnum):
    """Strategy type enumeration"""
    SMA = "sma"
    MOMENTUM = "momentum"
    MEAN_REVERSION = "mean_reversion"
    BREAKOUT = "breakout"

class BacktestStatus(PyEnum):
    """Backtest status enumeration"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"

# User and Account Management
class User(Base):
    """User model"""
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True)
    username = Column(String(50), unique=True, nullable=False)
    email = Column(String(100), unique=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    
    # Relationships
    accounts = relationship("Account", back_populates="user")
    strategies = relationship("Strategy", back_populates="user")

class Account(Base):
    """Trading account model"""
    __tablename__ = "accounts"
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    name = Column(String(100), nullable=False)
    account_type = Column(String(20), nullable=False)  # paper, live
    broker = Column(String(50), nullable=False)  # ibkr, alpaca, etc.
    broker_account_id = Column(String(100))
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    
    # Relationships
    user = relationship("User", back_populates="accounts")
    positions = relationship("Position", back_populates="account")
    trades = relationship("Trade", back_populates="account")
    backtests = relationship("Backtest", back_populates="account")
    cash_account_state = relationship("CashAccountState", back_populates="account", uselist=False)

# Trading Models
class Strategy(Base):
    """Trading strategy model"""
    __tablename__ = "strategies"
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    name = Column(String(100), nullable=False)
    strategy_type = Column(Enum(StrategyType), nullable=False)
    description = Column(Text)
    config = Column(Text)  # JSON configuration
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    
    # Relationships
    user = relationship("User", back_populates="strategies")
    trades = relationship("Trade", back_populates="strategy")
    backtests = relationship("Backtest", back_populates="strategy")

class Trade(Base):
    """Trade model"""
    __tablename__ = "trades"
    
    id = Column(Integer, primary_key=True)
    account_id = Column(Integer, ForeignKey("accounts.id"), nullable=False)
    strategy_id = Column(Integer, ForeignKey("strategies.id"))
    symbol = Column(String(20), nullable=False)
    side = Column(Enum(TradeSide), nullable=False)
    quantity = Column(Integer, nullable=False)
    price = Column(Float, nullable=False)
    order_type = Column(String(20), nullable=False)  # market, limit, stop
    status = Column(Enum(OrderStatus), default=OrderStatus.PENDING)
    filled_quantity = Column(Integer, default=0)
    average_fill_price = Column(Float)
    commission = Column(Float, default=0.0)
    timestamp = Column(DateTime, server_default=func.now())
    executed_at = Column(DateTime)
    cancelled_at = Column(DateTime)
    
    # Risk management fields
    settlement_date = Column(DateTime)  # T+2 settlement date
    is_day_trade = Column(Boolean, default=False, index=True)  # Flag for day trades
    confidence_score = Column(Float)  # Signal confidence (0.0-1.0) for position sizing
    
    # Relationships
    account = relationship("Account", back_populates="trades")
    strategy = relationship("Strategy", back_populates="trades")
    # Note: Position relationship removed - no foreign key exists
    # If needed, query positions separately by symbol/account_id

class Position(Base):
    """Position model"""
    __tablename__ = "positions"
    
    id = Column(Integer, primary_key=True)
    account_id = Column(Integer, ForeignKey("accounts.id"), nullable=False)
    symbol = Column(String(20), nullable=False)
    quantity = Column(Integer, nullable=False)
    average_price = Column(Float, nullable=False)
    current_price = Column(Float)
    unrealized_pnl = Column(Float, default=0.0)
    unrealized_pnl_pct = Column(Float, default=0.0)
    status = Column(Enum(PositionStatus), default=PositionStatus.OPEN)
    opened_at = Column(DateTime, server_default=func.now())
    closed_at = Column(DateTime)
    
    # Position sync fields
    last_synced_at = Column(DateTime, nullable=True, index=True)  # When position was last synced from IBKR
    realized_pnl = Column(Float, nullable=True)  # Realized P&L when position fully closes (sum of all partial closes)
    
    # Relationships
    account = relationship("Account", back_populates="positions")
    position_closes = relationship("PositionClose", back_populates="position", cascade="all, delete-orphan")
    # Note: Trade relationship removed - no foreign key exists
    # If needed, query trades separately by symbol/account_id

class PositionClose(Base):
    """Position close model - tracks partial and full closes"""
    __tablename__ = "position_closes"
    
    id = Column(Integer, primary_key=True)
    position_id = Column(Integer, ForeignKey("positions.id"), nullable=False, index=True)
    account_id = Column(Integer, ForeignKey("accounts.id"), nullable=False, index=True)
    symbol = Column(String(20), nullable=False, index=True)
    quantity_closed = Column(Integer, nullable=False)  # Quantity closed in this transaction
    entry_price = Column(Float, nullable=False)  # Average entry price at time of close
    exit_price = Column(Float, nullable=False)  # Exit price for this close
    realized_pnl = Column(Float, nullable=False)  # Realized P&L for this close
    realized_pnl_pct = Column(Float, nullable=False)  # Realized P&L percentage
    closed_at = Column(DateTime, server_default=func.now(), nullable=False, index=True)
    is_full_close = Column(Boolean, default=False, index=True)  # True if this was a full position close
    
    # Relationships
    position = relationship("Position", back_populates="position_closes")
    account = relationship("Account")

# Market Data Models
class MarketData(Base):
    """Market data model"""
    __tablename__ = "market_data"
    
    id = Column(Integer, primary_key=True)
    symbol = Column(String(20), nullable=False)
    timestamp = Column(DateTime, nullable=False)
    open = Column(Float)
    high = Column(Float)
    low = Column(Float)
    close = Column(Float)
    volume = Column(Integer)
    provider = Column(String(50))  # yahoo, alpha_vantage, etc.
    
    # Index for efficient queries
    __table_args__ = (
        {"mysql_engine": "InnoDB"},
    )

class OptionsFlow(Base):
    """Options flow data model"""
    __tablename__ = "options_flow"
    
    id = Column(Integer, primary_key=True)
    symbol = Column(String(20), nullable=False, index=True)
    strike = Column(Float, nullable=False)
    expiry = Column(DateTime, nullable=False, index=True)
    option_type = Column(String(10), nullable=False)  # call, put
    volume = Column(Integer, nullable=False)
    premium = Column(Float, nullable=False)
    direction = Column(String(20), nullable=False)  # bullish, bearish
    unusual = Column(Boolean, default=False)
    sentiment_score = Column(Float)
    timestamp = Column(DateTime, server_default=func.now(), index=True)
    provider = Column(String(50), default="unusual_whales")
    
    # Enhanced fields for pattern detection
    is_sweep = Column(Boolean, default=False, index=True)
    is_block = Column(Boolean, default=False, index=True)
    pattern_type = Column(String(50))  # "sweep", "block", "spread", etc.
    sweep_strength = Column(Float)  # 0.0 to 1.0
    open_interest = Column(Integer)
    implied_volatility = Column(Float)
    
    # Indexes for common queries
    __table_args__ = (
        Index('idx_options_flow_symbol_timestamp', 'symbol', 'timestamp'),
        Index('idx_options_flow_patterns', 'symbol', 'pattern_type', 'timestamp'),
    )

class OptionsChainSnapshot(Base):
    """Options chain snapshot for analysis"""
    __tablename__ = "options_chain_snapshots"
    
    id = Column(Integer, primary_key=True)
    symbol = Column(String(20), nullable=False, index=True)
    snapshot_time = Column(DateTime, nullable=False, server_default=func.now(), index=True)
    
    # Chain-wide metrics
    max_pain = Column(Float)  # Max pain strike price
    total_call_volume = Column(Integer, default=0)
    total_put_volume = Column(Integer, default=0)
    total_call_oi = Column(Integer, default=0)
    total_put_oi = Column(Integer, default=0)
    gamma_exposure = Column(Float)  # Total GEX
    put_call_ratio_volume = Column(Float)
    put_call_ratio_premium = Column(Float)
    put_call_ratio_oi = Column(Float)
    
    # Strike concentration (JSON field for flexibility)
    strike_concentration = Column(JSON)  # {strike: {call_oi, put_oi, volume}}
    
    # Metadata
    underlying_price = Column(Float)
    snapshot_data = Column(JSON)  # Full snapshot data if needed
    
    __table_args__ = (
        Index('idx_chain_snapshot_symbol_time', 'symbol', 'snapshot_time'),
    )


class OptionsPattern(Base):
    """Detected options flow patterns (sweeps, blocks, spreads)"""
    __tablename__ = "options_patterns"
    
    id = Column(Integer, primary_key=True)
    symbol = Column(String(20), nullable=False, index=True)
    pattern_type = Column(String(50), nullable=False, index=True)  # "sweep", "block", "spread", etc.
    detected_at = Column(DateTime, nullable=False, server_default=func.now(), index=True)
    
    # Pattern details
    strength = Column(Float)  # 0.0 to 1.0
    direction = Column(String(20))  # "bullish", "bearish", "neutral"
    total_premium = Column(Float)
    total_volume = Column(Integer)
    strike_count = Column(Integer)  # Number of strikes involved
    
    # Pattern metadata
    flows = Column(JSON)  # Array of flow IDs or flow details
    pattern_data = Column(JSON)  # Additional pattern-specific data
    
    # Timestamps
    expiry_date = Column(DateTime)  # Target expiry if applicable
    
    __table_args__ = (
        Index('idx_pattern_symbol_type_time', 'symbol', 'pattern_type', 'detected_at'),
        Index('idx_pattern_strength', 'symbol', 'strength', 'detected_at'),
    )


# Backtesting Models
class Backtest(Base):
    """Backtest model"""
    __tablename__ = "backtests"
    
    id = Column(Integer, primary_key=True)
    account_id = Column(Integer, ForeignKey("accounts.id"), nullable=False)
    strategy_id = Column(Integer, ForeignKey("strategies.id"), nullable=False)
    name = Column(String(100), nullable=False)
    symbol = Column(String(20), nullable=False)
    start_date = Column(DateTime, nullable=False)
    end_date = Column(DateTime, nullable=False)
    initial_capital = Column(Float, nullable=False)
    final_capital = Column(Float)
    total_return = Column(Float)
    total_return_pct = Column(Float)
    max_drawdown = Column(Float)
    sharpe_ratio = Column(Float)
    win_rate = Column(Float)
    total_trades = Column(Integer)
    winning_trades = Column(Integer)
    losing_trades = Column(Integer)
    status = Column(Enum(BacktestStatus), default=BacktestStatus.PENDING)
    config = Column(Text)  # JSON configuration
    results = Column(Text)  # JSON results
    created_at = Column(DateTime, server_default=func.now())
    completed_at = Column(DateTime)
    
    # Relationships
    account = relationship("Account", back_populates="backtests")
    strategy = relationship("Strategy", back_populates="backtests")
    backtest_trades = relationship("BacktestTrade", back_populates="backtest")

class BacktestTrade(Base):
    """Backtest trade model"""
    __tablename__ = "backtest_trades"
    
    id = Column(Integer, primary_key=True)
    backtest_id = Column(Integer, ForeignKey("backtests.id"), nullable=False)
    symbol = Column(String(20), nullable=False)
    side = Column(Enum(TradeSide), nullable=False)
    quantity = Column(Integer, nullable=False)
    price = Column(Float, nullable=False)
    timestamp = Column(DateTime, nullable=False)
    pnl = Column(Float)
    pnl_pct = Column(Float)
    exit_reason = Column(String(50))  # take_profit, stop_loss, etc.
    
    # Relationships
    backtest = relationship("Backtest", back_populates="backtest_trades")

# Screening Models
class ScreenerRun(Base):
    """Screener run model"""
    __tablename__ = "screener_runs"
    
    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    universe = Column(Text)  # JSON array of symbols
    filters = Column(Text)  # JSON filter configuration
    pass_rate = Column(Float)
    total_symbols = Column(Integer)
    passed_symbols = Column(Integer)
    created_at = Column(DateTime, server_default=func.now())
    
    # Relationships
    screener_results = relationship("ScreenerResult", back_populates="run")

class ScreenerResult(Base):
    """Screener result model"""
    __tablename__ = "screener_results"
    
    id = Column(Integer, primary_key=True)
    run_id = Column(Integer, ForeignKey("screener_runs.id"), nullable=False)
    symbol = Column(String(20), nullable=False)
    passed = Column(Boolean, nullable=False)
    metrics = Column(Text)  # JSON metrics data
    score = Column(Float)
    
    # Relationships
    run = relationship("ScreenerRun", back_populates="screener_results")

# Risk Management Models
class CashAccountState(Base):
    """Cash account state tracking"""
    __tablename__ = "cash_account_state"
    
    id = Column(Integer, primary_key=True)
    account_id = Column(Integer, ForeignKey("accounts.id"), nullable=False, unique=True, index=True)
    balance = Column(Float, nullable=False)
    is_cash_account_mode = Column(Boolean, default=False, nullable=False, index=True)
    threshold = Column(Float, nullable=False, default=25000.0)  # Default $25k threshold
    last_checked = Column(DateTime, nullable=False, server_default=func.now())
    last_updated = Column(DateTime, nullable=False, server_default=func.now(), onupdate=func.now())
    
    # Relationships
    account = relationship("Account", back_populates="cash_account_state")
    
    # Indexes
    __table_args__ = (
        Index('idx_cash_account_mode', 'is_cash_account_mode'),
        {"mysql_engine": "InnoDB"},
    )

class DayTrade(Base):
    """Day trade tracking for PDT compliance"""
    __tablename__ = "day_trades"
    
    id = Column(Integer, primary_key=True)
    account_id = Column(Integer, ForeignKey("accounts.id"), nullable=False, index=True)
    symbol = Column(String(20), nullable=False, index=True)
    buy_trade_id = Column(Integer, ForeignKey("trades.id"), nullable=False)
    sell_trade_id = Column(Integer, ForeignKey("trades.id"), nullable=False)
    trade_date = Column(DateTime, nullable=False, index=True)  # Date of the day trade
    created_at = Column(DateTime, server_default=func.now())
    
    # Relationships
    account = relationship("Account")
    buy_trade = relationship("Trade", foreign_keys=[buy_trade_id])
    sell_trade = relationship("Trade", foreign_keys=[sell_trade_id])
    
    # Indexes
    __table_args__ = (
        Index('idx_day_trade_account_date', 'account_id', 'trade_date'),
        {"mysql_engine": "InnoDB"},
    )

class SettlementTracking(Base):
    """Track trade settlements for T+2 compliance"""
    __tablename__ = "settlement_tracking"
    
    id = Column(Integer, primary_key=True)
    account_id = Column(Integer, ForeignKey("accounts.id"), nullable=False, index=True)
    trade_id = Column(Integer, ForeignKey("trades.id"), nullable=False, unique=True, index=True)
    trade_date = Column(DateTime, nullable=False, index=True)
    settlement_date = Column(DateTime, nullable=False, index=True)
    amount = Column(Float, nullable=False)  # Cash amount from trade
    is_settled = Column(Boolean, default=False, nullable=False, index=True)
    settled_at = Column(DateTime)
    created_at = Column(DateTime, server_default=func.now())
    
    # Relationships
    account = relationship("Account")
    trade = relationship("Trade")
    
    # Indexes
    __table_args__ = (
        Index('idx_settlement_account_date', 'account_id', 'settlement_date'),
        Index('idx_settlement_is_settled', 'is_settled'),
        {"mysql_engine": "InnoDB"},
    )

class TradeFrequencyTracking(Base):
    """Track daily and weekly trade frequency"""
    __tablename__ = "trade_frequency_tracking"
    
    id = Column(Integer, primary_key=True)
    account_id = Column(Integer, ForeignKey("accounts.id"), nullable=False, index=True)
    date = Column(DateTime, nullable=False, index=True)  # Date of the trading day
    daily_count = Column(Integer, default=0, nullable=False)
    weekly_count = Column(Integer, default=0, nullable=False)  # Count for current week
    week_start_date = Column(DateTime, nullable=False)  # Start of the week (Monday)
    last_trade_at = Column(DateTime)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    
    # Relationships
    account = relationship("Account")
    
    # Unique constraint: one record per account per day
    __table_args__ = (
        Index('idx_frequency_account_date', 'account_id', 'date', unique=True),
        Index('idx_frequency_week_start', 'account_id', 'week_start_date'),
        {"mysql_engine": "InnoDB"},
    )

class RiskLimits(Base):
    """Risk limits model"""
    __tablename__ = "risk_limits"
    
    id = Column(Integer, primary_key=True)
    account_id = Column(Integer, ForeignKey("accounts.id"), nullable=False)
    max_position_size = Column(Float)
    max_daily_loss = Column(Float)
    max_drawdown = Column(Float)
    max_trades_per_day = Column(Integer)
    max_correlation = Column(Float)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    
    # Relationships
    account = relationship("Account")

class RiskAlert(Base):
    """Risk alert model"""
    __tablename__ = "risk_alerts"
    
    id = Column(Integer, primary_key=True)
    account_id = Column(Integer, ForeignKey("accounts.id"), nullable=False)
    alert_type = Column(String(50), nullable=False)  # position_size, daily_loss, etc.
    message = Column(Text, nullable=False)
    severity = Column(String(20), nullable=False)  # low, medium, high, critical
    is_resolved = Column(Boolean, default=False)
    created_at = Column(DateTime, server_default=func.now())
    resolved_at = Column(DateTime)
    
    # Relationships
    account = relationship("Account")

# System Models
class SystemLog(Base):
    """System log model"""
    __tablename__ = "system_logs"
    
    id = Column(Integer, primary_key=True)
    level = Column(String(20), nullable=False)  # DEBUG, INFO, WARNING, ERROR, CRITICAL
    message = Column(Text, nullable=False)
    module = Column(String(100))
    function = Column(String(100))
    line_number = Column(Integer)
    timestamp = Column(DateTime, server_default=func.now())
    extra_data = Column(Text)  # JSON extra data

class APILog(Base):
    """API log model"""
    __tablename__ = "api_logs"
    
    id = Column(Integer, primary_key=True)
    method = Column(String(10), nullable=False)
    path = Column(String(255), nullable=False)
    status_code = Column(Integer, nullable=False)
    response_time = Column(Float)  # milliseconds
    user_id = Column(Integer, ForeignKey("users.id"))
    ip_address = Column(String(45))
    user_agent = Column(String(500))
    timestamp = Column(DateTime, server_default=func.now())
    
    # Relationships
    user = relationship("User")

# Performance Models
class PerformanceMetrics(Base):
    """Performance metrics model"""
    __tablename__ = "performance_metrics"
    
    id = Column(Integer, primary_key=True)
    account_id = Column(Integer, ForeignKey("accounts.id"), nullable=False)
    date = Column(DateTime, nullable=False)
    total_value = Column(Float, nullable=False)
    cash_balance = Column(Float, nullable=False)
    total_pnl = Column(Float, nullable=False)
    total_pnl_pct = Column(Float, nullable=False)
    daily_pnl = Column(Float, nullable=False)
    daily_pnl_pct = Column(Float, nullable=False)
    open_positions = Column(Integer, default=0)
    total_trades = Column(Integer, default=0)
    winning_trades = Column(Integer, default=0)
    losing_trades = Column(Integer, default=0)
    win_rate = Column(Float, default=0.0)
    
    # Relationships
    account = relationship("Account")

# Sentiment Data Models
class Tweet(Base):
    """Twitter tweet data model"""
    __tablename__ = "tweets"
    
    id = Column(Integer, primary_key=True)
    tweet_id = Column(String(50), unique=True, nullable=False, index=True)  # Twitter tweet ID
    text = Column(Text, nullable=False)
    author_id = Column(String(50), nullable=False, index=True)
    author_username = Column(String(100), nullable=False)
    created_at = Column(DateTime, nullable=False, index=True)
    like_count = Column(Integer, default=0)
    retweet_count = Column(Integer, default=0)
    reply_count = Column(Integer, default=0)
    quote_count = Column(Integer, default=0)
    is_retweet = Column(Boolean, default=False)
    is_quote = Column(Boolean, default=False)
    is_reply = Column(Boolean, default=False)
    language = Column(String(10))
    symbols_mentioned = Column(Text)  # JSON array of symbols
    raw_data = Column(Text)  # JSON raw API response
    stored_at = Column(DateTime, server_default=func.now())
    
    # Relationships
    sentiments = relationship("TweetSentiment", back_populates="tweet")
    
    # Indexes for efficient queries
    __table_args__ = (
        {"mysql_engine": "InnoDB"},
    )

class TweetSentiment(Base):
    """Sentiment analysis result for a tweet"""
    __tablename__ = "tweet_sentiments"
    
    id = Column(Integer, primary_key=True)
    tweet_id = Column(Integer, ForeignKey("tweets.id"), nullable=False, index=True)
    symbol = Column(String(20), nullable=False, index=True)
    sentiment_score = Column(Float, nullable=False)  # -1.0 to 1.0
    confidence = Column(Float, nullable=False)  # 0.0 to 1.0
    sentiment_level = Column(String(20), nullable=False)  # very_bearish, bearish, neutral, bullish, very_bullish
    vader_compound = Column(Float)
    vader_pos = Column(Float)
    vader_neu = Column(Float)
    vader_neg = Column(Float)
    engagement_score = Column(Float, default=0.0)
    influencer_weight = Column(Float, default=1.0)
    weighted_score = Column(Float, default=0.0)
    analyzed_at = Column(DateTime, server_default=func.now(), index=True)
    
    # Relationships
    tweet = relationship("Tweet", back_populates="sentiments")
    
    # Composite index for symbol + timestamp queries
    __table_args__ = (
        {"mysql_engine": "InnoDB"},
    )

class SymbolSentiment(Base):
    """Aggregated sentiment for a symbol over time"""
    __tablename__ = "symbol_sentiments"
    
    id = Column(Integer, primary_key=True)
    symbol = Column(String(20), nullable=False, index=True)
    timestamp = Column(DateTime, nullable=False, index=True)
    mention_count = Column(Integer, nullable=False, default=0)
    average_sentiment = Column(Float, nullable=False)  # -1.0 to 1.0
    weighted_sentiment = Column(Float, nullable=False)  # -1.0 to 1.0
    influencer_sentiment = Column(Float)
    engagement_score = Column(Float, default=0.0)
    sentiment_level = Column(String(20), nullable=False)  # very_bearish, bearish, neutral, bullish, very_bullish
    confidence = Column(Float, default=0.0)
    volume_trend = Column(String(20), default="stable")  # up, down, stable
    tweet_ids = Column(Text)  # JSON array of tweet IDs used in aggregation
    aggregated_at = Column(DateTime, server_default=func.now())
    
    # Composite index for symbol + timestamp queries
    __table_args__ = (
        {"mysql_engine": "InnoDB"},
    )

class Influencer(Base):
    """Twitter influencer/trader account"""
    __tablename__ = "influencers"
    
    id = Column(Integer, primary_key=True)
    user_id = Column(String(50), unique=True, nullable=False, index=True)  # Twitter user ID
    username = Column(String(100), unique=True, nullable=False, index=True)
    display_name = Column(String(200))
    follower_count = Column(Integer, default=0)
    following_count = Column(Integer, default=0)
    tweet_count = Column(Integer, default=0)
    is_verified = Column(Boolean, default=False)
    is_protected = Column(Boolean, default=False)
    category = Column(String(50), default="unknown")  # trader, analyst, news, education, etc.
    weight_multiplier = Column(Float, default=1.5)
    is_active = Column(Boolean, default=True, index=True)
    added_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    
    __table_args__ = (
        {"mysql_engine": "InnoDB"},
    )

# Reddit Sentiment Data Models
class RedditPost(Base):
    """Reddit post/comment data model"""
    __tablename__ = "reddit_posts"
    
    id = Column(Integer, primary_key=True)
    post_id = Column(String(50), unique=True, nullable=False, index=True)  # Reddit post/comment ID
    text = Column(Text, nullable=False)
    author = Column(String(100), nullable=False, index=True)
    created_at = Column(DateTime, nullable=False, index=True)
    score = Column(Integer, default=0)
    upvote_ratio = Column(Float, default=1.0)
    num_comments = Column(Integer, default=0)
    subreddit = Column(String(100), nullable=False, index=True)
    is_post = Column(Boolean, default=True)  # True for post, False for comment
    parent_id = Column(String(50))  # Parent post/comment ID if this is a comment
    symbols_mentioned = Column(Text)  # JSON array of symbols
    raw_data = Column(Text)  # JSON raw API response
    stored_at = Column(DateTime, server_default=func.now())
    
    # Relationships
    sentiments = relationship("RedditSentiment", back_populates="post")
    
    # Indexes for efficient queries
    __table_args__ = (
        {"mysql_engine": "InnoDB"},
    )

class RedditSentiment(Base):
    """Sentiment analysis result for a Reddit post/comment"""
    __tablename__ = "reddit_sentiments"
    
    id = Column(Integer, primary_key=True)
    post_id = Column(Integer, ForeignKey("reddit_posts.id"), nullable=False, index=True)
    symbol = Column(String(20), nullable=False, index=True)
    sentiment_score = Column(Float, nullable=False)  # -1.0 to 1.0
    confidence = Column(Float, nullable=False)  # 0.0 to 1.0
    sentiment_level = Column(String(20), nullable=False)  # very_bearish, bearish, neutral, bullish, very_bullish
    vader_compound = Column(Float)
    vader_pos = Column(Float)
    vader_neu = Column(Float)
    vader_neg = Column(Float)
    engagement_score = Column(Float, default=0.0)
    weighted_score = Column(Float, default=0.0)
    analyzed_at = Column(DateTime, server_default=func.now(), index=True)
    
    # Relationships
    post = relationship("RedditPost", back_populates="sentiments")
    
    # Composite index for symbol + timestamp queries
    __table_args__ = (
        {"mysql_engine": "InnoDB"},
    )

# Aggregated Sentiment Models (cross-source aggregation)
class AggregatedSentiment(Base):
    """Aggregated sentiment across multiple sources (Twitter, Reddit, News, etc.)"""
    __tablename__ = "aggregated_sentiments"
    
    id = Column(Integer, primary_key=True)
    symbol = Column(String(20), nullable=False, index=True)
    timestamp = Column(DateTime, nullable=False, index=True)
    unified_sentiment = Column(Float, nullable=False)  # -1.0 to 1.0
    confidence = Column(Float, nullable=False)  # 0.0 to 1.0
    sentiment_level = Column(String(20), nullable=False)  # very_bearish, bearish, neutral, bullish, very_bullish
    source_count = Column(Integer, nullable=False, default=0)  # Number of sources used
    provider_count = Column(Integer, nullable=False, default=0)  # Number of providers used
    total_mention_count = Column(Integer, nullable=False, default=0)
    divergence_detected = Column(Boolean, default=False)
    divergence_score = Column(Float, default=0.0)  # 0.0 to 1.0
    volume_trend = Column(String(20), default="stable")  # up, down, stable
    
    # Source-specific sentiment scores
    twitter_sentiment = Column(Float)  # -1.0 to 1.0
    reddit_sentiment = Column(Float)  # -1.0 to 1.0
    news_sentiment = Column(Float)  # -1.0 to 1.0
    options_flow_sentiment = Column(Float)  # -1.0 to 1.0
    
    # Source breakdown (JSON): {"twitter": 45.2, "reddit": 32.1, ...}
    source_breakdown = Column(Text)  # JSON dict of source -> contribution percentage
    
    # Providers used (JSON array): ["twitter", "reddit", "news"]
    providers_used = Column(Text)  # JSON array
    
    aggregated_at = Column(DateTime, server_default=func.now())
    
    # Composite indexes for efficient queries
    __table_args__ = (
        Index('idx_aggregated_sentiment_symbol_timestamp', 'symbol', 'timestamp'),
        {"mysql_engine": "InnoDB"},
    )

# Confluence Models
class ConfluenceScore(Base):
    """Confluence score combining technical indicators, sentiment, and options flow"""
    __tablename__ = "confluence_scores"
    
    id = Column(Integer, primary_key=True)
    symbol = Column(String(20), nullable=False, index=True)
    timestamp = Column(DateTime, nullable=False, index=True)
    confluence_score = Column(Float, nullable=False)  # 0.0 to 1.0 (confluence strength)
    directional_bias = Column(Float, nullable=False)  # -1.0 to 1.0 (bullish/bearish)
    confluence_level = Column(String(20), nullable=False)  # very_low, low, moderate, high, very_high
    confidence = Column(Float, nullable=False, default=0.0)  # 0.0 to 1.0
    
    # Component scores (raw values before weighting)
    technical_score = Column(Float)  # -1.0 to 1.0
    sentiment_score = Column(Float)  # -1.0 to 1.0
    options_flow_score = Column(Float)  # -1.0 to 1.0
    
    # Component contributions (weighted contributions to final score)
    technical_contribution = Column(Float)  # 0.0 to 1.0
    sentiment_contribution = Column(Float)  # 0.0 to 1.0
    options_flow_contribution = Column(Float)  # 0.0 to 1.0
    
    # Technical breakdown (JSON): {"rsi_score": 0.5, "sma_trend_score": 0.3, ...}
    technical_breakdown = Column(Text)  # JSON dict
    
    # Components used (JSON array): ["technical", "sentiment", "options_flow"]
    components_used = Column(Text)  # JSON array
    
    # Threshold checks
    meets_minimum_threshold = Column(Boolean, default=False, index=True)
    meets_high_threshold = Column(Boolean, default=False, index=True)
    
    volume_trend = Column(String(20), default="stable")  # up, down, stable
    
    calculated_at = Column(DateTime, server_default=func.now())
    
    # Composite indexes for efficient queries
    __table_args__ = (
        Index('idx_confluence_symbol_timestamp', 'symbol', 'timestamp'),
        Index('idx_confluence_meets_thresholds', 'meets_minimum_threshold', 'meets_high_threshold'),
        {"mysql_engine": "InnoDB"},
    )


# Execution Logging Models (T10: Strategy-to-Execution Pipeline)
class ExecutionStatus(PyEnum):
    """Execution outcome status"""
    SUCCESS = "success"
    REJECTED_VALIDATION = "rejected_validation"
    REJECTED_COMPLIANCE = "rejected_compliance"
    REJECTED_RISK = "rejected_risk"
    REJECTED_DRY_RUN = "rejected_dry_run"
    FAILED_ORDER = "failed_order"
    FAILED_BROKER = "failed_broker"


class ExecutionLog(Base):
    """
    Execution audit log for signal-to-order pipeline (T10).

    Records the full decision chain: Signal -> Validation -> Risk Check -> Order -> Result
    """
    __tablename__ = "execution_logs"

    id = Column(Integer, primary_key=True)
    account_id = Column(Integer, ForeignKey("accounts.id"), nullable=False, index=True)

    # Signal information
    symbol = Column(String(20), nullable=False, index=True)
    signal_type = Column(String(10), nullable=False)  # BUY, SELL
    signal_price = Column(Float, nullable=False)
    signal_quantity = Column(Integer, nullable=False)
    signal_confidence = Column(Float)
    signal_stop_loss = Column(Float)
    signal_take_profit = Column(Float)

    # Context information
    strategy_name = Column(String(100), nullable=False, index=True)
    order_type = Column(String(20), default="MARKET")  # MARKET, LIMIT
    limit_price = Column(Float)
    dry_run = Column(Boolean, default=False, index=True)

    # Execution status
    status = Column(Enum(ExecutionStatus), nullable=False, index=True)

    # Validation results
    validation_passed = Column(Boolean, default=False)
    validation_messages = Column(Text)  # JSON array of messages

    # Risk check results
    risk_check_passed = Column(Boolean, default=False)
    risk_score = Column(Float, default=0.0)
    adjusted_quantity = Column(Integer)  # If position was reduced by risk checks
    compliance_details = Column(Text)  # JSON compliance check details
    portfolio_risk_details = Column(Text)  # JSON portfolio risk details

    # Order execution results
    order_placed = Column(Boolean, default=False)
    order_id = Column(Integer)  # IBKR order ID
    final_quantity = Column(Integer)
    final_price = Column(Float)

    # Error information
    error_message = Column(Text)

    # Timing
    execution_time_ms = Column(Float, default=0.0)
    created_at = Column(DateTime, nullable=False, server_default=func.now(), index=True)

    # Full audit data (JSON blob for complete context)
    audit_data = Column(JSON)  # Full ExecutionAuditLog.to_dict() output

    # Relationships
    account = relationship("Account")

    # Indexes for common queries
    __table_args__ = (
        Index('idx_execution_account_timestamp', 'account_id', 'created_at'),
        Index('idx_execution_symbol_timestamp', 'symbol', 'created_at'),
        Index('idx_execution_strategy_timestamp', 'strategy_name', 'created_at'),
        Index('idx_execution_status_timestamp', 'status', 'created_at'),
        {"mysql_engine": "InnoDB"},
    )
