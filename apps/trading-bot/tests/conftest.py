"""
Pytest Configuration and Fixtures
==================================
"""

import pytest
import pandas as pd
import numpy as np
from unittest.mock import Mock, MagicMock, patch, AsyncMock
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List

# Mock database session fixture
@pytest.fixture
def mock_db_session():
    """Mock database session"""
    session = Mock()
    session.query = Mock()
    session.add = Mock()
    session.commit = Mock()
    session.rollback = Mock()
    session.refresh = Mock()
    session.close = Mock()
    session.delete = Mock()
    return session

# Mock Twitter client fixture
@pytest.fixture
def mock_twitter_client():
    """Mock Twitter API client"""
    client = Mock()
    client.is_available = Mock(return_value=True)
    client.search_tweets = Mock(return_value=[])
    client.get_user_info = Mock(return_value={
        'follower_count': 10000,
        'following_count': 500,
        'tweet_count': 5000,
        'verified': True
    })
    return client

# Mock sentiment analyzer fixture
@pytest.fixture
def mock_sentiment_analyzer():
    """Mock sentiment analyzer"""
    analyzer = Mock()
    analyzer.analyze_tweet = Mock(return_value=Mock(
        sentiment_score=0.5,
        confidence=0.8,
        sentiment_level=Mock(value='bullish'),
        vader_scores={'compound': 0.5, 'pos': 0.6, 'neu': 0.3, 'neg': 0.1},
        engagement_score=0.7,
        influencer_weight=1.0,
        weighted_score=0.35,
        timestamp=datetime.now()
    ))
    analyzer._calculate_engagement_score = Mock(return_value=0.7)
    analyzer.calculate_engagement_weight = Mock(return_value=1.0)
    analyzer._score_to_level = Mock(return_value=Mock(value='bullish'))
    return analyzer

# Mock cache manager fixture
@pytest.fixture
def mock_cache_manager():
    """Mock CacheManager"""
    cache = Mock()
    cache.get = Mock(return_value=None)
    cache.set = Mock()
    cache.delete = Mock()
    cache.exists = Mock(return_value=False)
    cache.get_ttl = Mock(return_value=None)
    return cache

# Mock rate limiter fixture
@pytest.fixture
def mock_rate_limiter():
    """Mock RateLimiter"""
    limiter = Mock()
    limiter.check_rate_limit = Mock(return_value=(True, Mock(is_limited=False)))
    limiter.wait_if_needed = Mock(return_value=Mock(is_limited=False))
    limiter.get_status = Mock(return_value=Mock(
        allowed=100,
        used=50,
        remaining=50,
        reset_at=datetime.now() + timedelta(minutes=15),
        is_limited=False
    ))
    return limiter

# Mock usage monitor fixture
@pytest.fixture
def mock_usage_monitor():
    """Mock UsageMonitor"""
    monitor = Mock()
    monitor.record_request = Mock()
    monitor.get_metrics = Mock(return_value=Mock(
        total_requests=100,
        successful_requests=95,
        failed_requests=5,
        cached_requests=50,
        avg_response_time=0.5
    ))
    return monitor

# Mock yfinance fixture
@pytest.fixture
def mock_yfinance():
    """Mock yfinance module"""
    mock_yf = Mock()
    mock_ticker = Mock()
    mock_ticker.info = {}
    mock_yf.Ticker = Mock(return_value=mock_ticker)
    mock_yf.Tickers = Mock(return_value=Mock(tickers={}))
    return mock_yf

# Mock httpx fixture for async clients
@pytest.fixture
def mock_httpx_client():
    """Mock httpx.AsyncClient"""
    client = AsyncMock()
    response = Mock()
    response.status_code = 200
    response.json = Mock(return_value={})
    client.get = AsyncMock(return_value=response)
    client.post = AsyncMock(return_value=response)
    return client

# Sample sentiment data fixtures
@pytest.fixture
def sample_symbol_sentiment():
    """Sample SymbolSentiment for testing"""
    from src.data.providers.sentiment.models import SymbolSentiment, SentimentLevel
    
    return SymbolSentiment(
        symbol="AAPL",
        timestamp=datetime.now(),
        mention_count=10,
        average_sentiment=0.6,
        weighted_sentiment=0.6,
        sentiment_level=SentimentLevel.BULLISH,
        confidence=0.8,
        volume_trend="up"
    )

@pytest.fixture
def sample_tweet():
    """Sample Tweet for testing"""
    from src.data.providers.sentiment.models import Tweet
    
    return Tweet(
        tweet_id="123",
        text="$AAPL is looking bullish today!",
        author_id="user123",
        author_username="trader1",
        created_at=datetime.now(),
        symbols_mentioned=["AAPL"]
    )

# ============================================================================
# Market Data Fixtures
# ============================================================================

@pytest.fixture
def sample_ohlcv_data():
    """Sample OHLCV market data for testing"""
    dates = pd.date_range(start='2024-01-01', periods=100, freq='5min')
    
    # Generate realistic price data
    np.random.seed(42)
    base_price = 100.0
    returns = np.random.randn(100) * 0.01  # 1% volatility
    prices = base_price * (1 + returns).cumprod()
    
    data = pd.DataFrame({
        'open': prices * (1 + np.random.randn(100) * 0.002),
        'high': prices * (1 + abs(np.random.randn(100)) * 0.005),
        'low': prices * (1 - abs(np.random.randn(100)) * 0.005),
        'close': prices,
        'volume': np.random.randint(100000, 1000000, 100)
    }, index=dates)
    
    # Ensure high >= close >= low and high >= open >= low
    data['high'] = data[['open', 'high', 'close', 'low']].max(axis=1)
    data['low'] = data[['open', 'high', 'close', 'low']].min(axis=1)
    
    return data

@pytest.fixture
def sample_ohlcv_data_near_pdh():
    """Sample OHLCV data where price is near Previous Day High"""
    dates = pd.date_range(start='2024-01-01', periods=100, freq='5min')
    
    base_price = 100.0
    pdh_price = 105.0
    current_price = pdh_price * 0.999  # 0.1% below PDH
    
    data = pd.DataFrame({
        'open': [current_price] * 100,
        'high': [current_price * 1.002] * 100,
        'low': [current_price * 0.998] * 100,
        'close': [current_price] * 100,
        'volume': [500000] * 100
    }, index=dates)
    
    # Set previous day's high in earlier data
    prev_day_idx = 50
    data.iloc[prev_day_idx:prev_day_idx+10, data.columns.get_loc('high')] = pdh_price
    data.iloc[prev_day_idx:prev_day_idx+10, data.columns.get_loc('close')] = pdh_price
    
    return data

@pytest.fixture
def sample_ohlcv_data_near_pdl():
    """Sample OHLCV data where price is near Previous Day Low"""
    dates = pd.date_range(start='2024-01-01', periods=100, freq='5min')
    
    base_price = 100.0
    pdl_price = 95.0
    current_price = pdl_price * 1.001  # 0.1% above PDL
    
    data = pd.DataFrame({
        'open': [current_price] * 100,
        'high': [current_price * 1.002] * 100,
        'low': [current_price * 0.998] * 100,
        'close': [current_price] * 100,
        'volume': [500000] * 100
    }, index=dates)
    
    # Set previous day's low in earlier data
    prev_day_idx = 50
    data.iloc[prev_day_idx:prev_day_idx+10, data.columns.get_loc('low')] = pdl_price
    data.iloc[prev_day_idx:prev_day_idx+10, data.columns.get_loc('close')] = pdl_price
    
    return data

@pytest.fixture
def sample_price_level():
    """Sample PriceLevel for testing"""
    from src.core.strategy.levels import PriceLevel, LevelType
    
    return PriceLevel(
        price=100.0,
        level_type=LevelType.PREVIOUS_DAY_HIGH,
        strength=0.9,
        timeframe="1d",
        timestamp=datetime.now(),
        touches=0,
        metadata={}
    )

@pytest.fixture
def sample_price_levels():
    """Sample list of PriceLevels for testing"""
    from src.core.strategy.levels import PriceLevel, LevelType
    
    return [
        PriceLevel(
            price=105.0,
            level_type=LevelType.PREVIOUS_DAY_HIGH,
            strength=0.9,
            timeframe="1d",
            timestamp=datetime.now(),
            touches=0
        ),
        PriceLevel(
            price=95.0,
            level_type=LevelType.PREVIOUS_DAY_LOW,
            strength=0.9,
            timeframe="1d",
            timestamp=datetime.now(),
            touches=0
        )
    ]

# ============================================================================
# Strategy Fixtures
# ============================================================================

@pytest.fixture
def sample_strategy_config():
    """Sample strategy configuration"""
    return {
        "name": "test_strategy",
        "symbol": "SPY",
        "timeframe": "5m",
        "entry": {
            "levels": ["previous_day_high", "previous_day_low"],
            "proximity_threshold": 0.001,
            "volume_confirmation": False
        },
        "exit": {
            "stop_loss_pct": 0.005,
            "take_profit_type": "opposite_level",
            "take_profit_threshold": 0.002
        },
        "risk_management": {
            "max_position_size": 100,
            "risk_per_trade": 0.02,
            "default_qty": 10
        }
    }

@pytest.fixture
def mock_strategy():
    """Mock strategy instance"""
    strategy = Mock()
    strategy.config = {"symbol": "SPY", "timeframe": "5m"}
    strategy.symbol = "SPY"
    strategy.timeframe = "5m"
    strategy.generate_signal = Mock(return_value=None)
    strategy.evaluate_entry_conditions = Mock(return_value={})
    strategy.evaluate_exit_conditions = Mock(return_value={})
    strategy.calculate_position_size = Mock(return_value=10)
    return strategy

@pytest.fixture
def mock_data_provider(sample_ohlcv_data):
    """Mock data provider for strategies"""
    provider = Mock()
    provider.get_historical_data = Mock(return_value=sample_ohlcv_data)
    
    async def async_get_historical_data(*args, **kwargs):
        return sample_ohlcv_data
    
    provider.get_historical_data_async = AsyncMock(side_effect=async_get_historical_data)
    return provider

# ============================================================================
# Trading Signal & Position Fixtures
# ============================================================================

@pytest.fixture
def sample_trading_signal_buy():
    """Sample BUY trading signal"""
    from src.core.strategy.base import TradingSignal, SignalType
    
    return TradingSignal(
        signal_type=SignalType.BUY,
        symbol="SPY",
        price=100.0,
        quantity=10,
        timestamp=datetime.now(),
        confidence=0.75,
        metadata={}
    )

@pytest.fixture
def sample_trading_signal_sell():
    """Sample SELL trading signal"""
    from src.core.strategy.base import TradingSignal, SignalType
    
    return TradingSignal(
        signal_type=SignalType.SELL,
        symbol="SPY",
        price=105.0,
        quantity=10,
        timestamp=datetime.now(),
        confidence=0.75,
        metadata={}
    )

@pytest.fixture
def sample_position():
    """Sample Position for testing"""
    from src.core.strategy.base import Position
    
    return Position(
        symbol="SPY",
        quantity=10,
        entry_price=100.0,
        entry_time=datetime.now(),
        current_price=102.0,
        unrealized_pnl=20.0,
        unrealized_pnl_pct=0.02
    )

@pytest.fixture
def sample_position_with_levels():
    """Sample Position with price levels"""
    from src.core.strategy.base import Position
    from src.core.strategy.levels import PriceLevel, LevelType
    
    entry_level = PriceLevel(
        price=100.0,
        level_type=LevelType.PREVIOUS_DAY_LOW,
        strength=0.9,
        timeframe="1d",
        timestamp=datetime.now()
    )
    
    return Position(
        symbol="SPY",
        quantity=10,
        entry_price=100.0,
        entry_time=datetime.now(),
        current_price=102.0,
        unrealized_pnl=20.0,
        unrealized_pnl_pct=0.02,
        entry_level=entry_level,
        stop_loss=99.5,
        take_profit=105.0
    )

# ============================================================================
# Broker & Trading Fixtures
# ============================================================================

@pytest.fixture
def mock_ibkr_client():
    """
    Simple mock IBKR client fixture for basic tests
    
    For more complex tests, use MockIBKRClient from tests.mocks.mock_ibkr_client
    """
    client = AsyncMock()
    client.connected = True
    client.host = "127.0.0.1"
    client.port = 7497
    client.client_id = 9
    
    # Connection methods
    client.connect = AsyncMock(return_value=True)
    client.disconnect = AsyncMock(return_value=None)
    # Note: IBKRClient uses .connected property, not is_connected() method
    
    # Order methods (using actual IBKRClient method names)
    from src.data.brokers.ibkr_client import BrokerOrder, OrderSide, OrderType, OrderStatus
    mock_order = BrokerOrder(
        order_id=1,
        symbol="SPY",
        side=OrderSide.BUY,
        quantity=10,
        order_type=OrderType.MARKET,
        price=None,
        status=OrderStatus.SUBMITTED,
        filled_quantity=0,
        average_fill_price=0.0,
        timestamp=datetime.now()
    )
    client.place_market_order = AsyncMock(return_value=mock_order)
    client.place_limit_order = AsyncMock(return_value=mock_order)
    client.cancel_order = AsyncMock(return_value=True)
    
    # Position methods
    client.get_positions = AsyncMock(return_value=[])
    client.get_position = AsyncMock(return_value=None)
    
    # Account methods
    client.get_account_summary = AsyncMock(return_value={
        "total_value": 100000.0,
        "available_funds": 50000.0,
        "buying_power": 100000.0
    })
    
    return client

@pytest.fixture
def mock_ibkr_client_full():
    """
    Full MockIBKRClient instance for integration tests
    
    Provides more realistic behavior and configurable responses
    """
    from tests.mocks.mock_ibkr_client import MockIBKRClient
    
    client = MockIBKRClient()
    # Configure for typical test scenarios
    client.configure(
        connect_success=True,
        place_order_success=True,
        auto_fill_orders=True
    )
    return client

@pytest.fixture
def sample_broker_order():
    """Sample broker order"""
    from src.data.brokers.ibkr_client import BrokerOrder, OrderSide, OrderType, OrderStatus
    
    return BrokerOrder(
        order_id=1,
        symbol="SPY",
        side=OrderSide.BUY,
        quantity=10,
        order_type=OrderType.MARKET,
        price=None,
        status=OrderStatus.FILLED,
        filled_quantity=10,
        average_fill_price=100.0,
        timestamp=datetime.now()
    )

@pytest.fixture
def sample_broker_position():
    """Sample broker position"""
    from src.data.brokers.ibkr_client import BrokerPosition
    from ib_insync import Stock, Contract
    
    contract = Mock(spec=Contract)
    contract.symbol = "SPY"
    
    return BrokerPosition(
        symbol="SPY",
        quantity=10,
        average_price=100.0,
        market_price=102.0,
        unrealized_pnl=20.0,
        unrealized_pnl_pct=0.02,
        contract=contract
    )

# ============================================================================
# Risk Management Fixtures
# ============================================================================

@pytest.fixture
def sample_account_balance():
    """Sample account balance for risk management tests"""
    return {
        "total_value": 100000.0,
        "available_funds": 50000.0,
        "buying_power": 100000.0,
        "cash": 50000.0,
        "margin_used": 0.0
    }

@pytest.fixture
def sample_account_balance_under_25k():
    """Sample account balance under $25k (cash account)"""
    return {
        "total_value": 20000.0,
        "available_funds": 20000.0,
        "buying_power": 20000.0,
        "cash": 20000.0,
        "margin_used": 0.0
    }

@pytest.fixture
def sample_risk_limits():
    """Sample risk management limits"""
    return {
        "max_position_size_pct": 0.04,  # 4% of account
        "max_open_positions": 5,
        "max_daily_loss_pct": 0.02,  # 2% daily loss limit
        "stop_loss_pct": 0.005,  # 0.5% stop loss
        "take_profit_pct": 0.02,  # 2% take profit
        "confidence_sizing": {
            "low": 0.01,      # 1% for low confidence
            "medium": 0.02,   # 2% for medium confidence
            "high": 0.04      # 4% for high confidence
        }
    }

# ============================================================================
# Evaluation & Strategy Evaluator Fixtures
# ============================================================================

@pytest.fixture
def mock_strategy_evaluator():
    """Mock strategy evaluator"""
    evaluator = Mock()
    evaluator.strategies = {}
    evaluator.add_strategy = Mock(return_value=Mock())
    evaluator.evaluate_strategy = Mock(return_value=None)
    evaluator.evaluate_all_strategies = Mock(return_value=[])
    evaluator.update_position = Mock()
    evaluator.check_exit_conditions = Mock(return_value=None)
    return evaluator

# ============================================================================
# Helper Functions
# ============================================================================

def create_sample_ohlcv_data(
    start_date: str = '2024-01-01',
    periods: int = 100,
    freq: str = '5min',
    base_price: float = 100.0,
    volatility: float = 0.01
) -> pd.DataFrame:
    """Helper to create custom OHLCV data"""
    dates = pd.date_range(start=start_date, periods=periods, freq=freq)
    
    np.random.seed(42)
    returns = np.random.randn(periods) * volatility
    prices = base_price * (1 + returns).cumprod()
    
    data = pd.DataFrame({
        'open': prices * (1 + np.random.randn(periods) * 0.002),
        'high': prices * (1 + abs(np.random.randn(periods)) * 0.005),
        'low': prices * (1 - abs(np.random.randn(periods)) * 0.005),
        'close': prices,
        'volume': np.random.randint(100000, 1000000, periods)
    }, index=dates)
    
    data['high'] = data[['open', 'high', 'close', 'low']].max(axis=1)
    data['low'] = data[['open', 'high', 'close', 'low']].min(axis=1)
    
    return data

# ============================================================================
# Test Database Fixtures
# ============================================================================

@pytest.fixture(scope="function")
def test_db_engine():
    """Create a test database engine (SQLite in-memory)"""
    from sqlalchemy import create_engine
    from src.data.database.models import Base
    
    # Use in-memory SQLite for fast tests
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        echo=False
    )
    
    # Create all tables
    Base.metadata.create_all(bind=engine)
    
    yield engine
    
    # Cleanup: Drop all tables
    Base.metadata.drop_all(bind=engine)
    engine.dispose()

@pytest.fixture(scope="function")
def test_db_session(test_db_engine):
    """Create a test database session with automatic cleanup"""
    from sqlalchemy.orm import sessionmaker
    from src.data.database.models import Base
    
    # Create session factory
    TestSessionLocal = sessionmaker(
        autocommit=False,
        autoflush=False,
        bind=test_db_engine
    )
    
    # Create session
    session = TestSessionLocal()
    
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()

@pytest.fixture(scope="function")
def test_db_session_with_rollback(test_db_engine):
    """
    Create a test database session that automatically rolls back
    
    Useful for tests that need to verify database operations without
    committing changes (isolation between tests)
    """
    from sqlalchemy.orm import sessionmaker
    
    TestSessionLocal = sessionmaker(
        autocommit=False,
        autoflush=False,
        bind=test_db_engine
    )
    
    session = TestSessionLocal()
    
    try:
        yield session
    finally:
        session.rollback()
        session.close()

