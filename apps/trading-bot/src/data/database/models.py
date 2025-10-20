"""
Database Models
===============

SQLAlchemy models for the trading bot database.
"""

from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, Text, ForeignKey, Enum
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
    
    # Relationships
    account = relationship("Account", back_populates="trades")
    strategy = relationship("Strategy", back_populates="trades")
    position = relationship("Position", back_populates="trades")

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
    
    # Relationships
    account = relationship("Account", back_populates="positions")
    trades = relationship("Trade", back_populates="position")

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
    symbol = Column(String(20), nullable=False)
    strike = Column(Float, nullable=False)
    expiry = Column(DateTime, nullable=False)
    option_type = Column(String(10), nullable=False)  # call, put
    volume = Column(Integer, nullable=False)
    premium = Column(Float, nullable=False)
    direction = Column(String(20), nullable=False)  # bullish, bearish
    unusual = Column(Boolean, default=False)
    sentiment_score = Column(Float)
    timestamp = Column(DateTime, server_default=func.now())
    provider = Column(String(50), default="unusual_whales")

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
