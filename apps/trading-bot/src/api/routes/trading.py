"""
Trading API Routes
==================

RESTful API endpoints for trading operations.
"""

from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
from datetime import datetime
import logging

from ...core.strategy import StrategyFactory, SMAStrategy
from ...data.database import get_db_session
from ...data.models import Trade, Position, StrategyConfig
from ...api.schemas.trading import (
    TradeRequest, TradeResponse, PositionResponse, 
    StrategyConfigRequest, StrategyConfigResponse,
    SignalResponse, MarketDataResponse
)
from ...utils.logging import get_logger

logger = get_logger(__name__)
router = APIRouter()

@router.post("/signal", response_model=SignalResponse)
async def generate_signal(
    request: TradeRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db_session)
):
    """Generate trading signal for a symbol"""
    try:
        # Get market data (this would be replaced with real data feed)
        market_data = await get_market_data(request.symbol)
        
        # Create strategy instance
        strategy_config = {
            'symbol': request.symbol,
            'entry_threshold': request.entry_threshold,
            'take_profit': request.take_profit,
            'stop_loss': request.stop_loss,
            'default_qty': request.quantity
        }
        
        strategy = StrategyFactory.create_strategy('sma', strategy_config)
        
        # Generate signal
        signal = strategy.generate_signal(market_data)
        
        # Log the signal
        logger.info(f"Generated signal for {request.symbol}: {signal.signal_type.value}")
        
        return SignalResponse(
            signal_type=signal.signal_type.value,
            symbol=signal.symbol,
            price=signal.price,
            quantity=signal.quantity,
            confidence=signal.confidence,
            timestamp=signal.timestamp,
            metadata=signal.metadata
        )
        
    except Exception as e:
        logger.error(f"Error generating signal: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/execute", response_model=TradeResponse)
async def execute_trade(
    request: TradeRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db_session)
):
    """Execute a trade (paper trading mode)"""
    try:
        # Validate request
        if request.quantity <= 0:
            raise HTTPException(status_code=400, detail="Quantity must be positive")
        
        # Create trade record
        trade = Trade(
            symbol=request.symbol,
            side=request.side,
            quantity=request.quantity,
            price=request.price,
            timestamp=datetime.now(),
            status="pending"
        )
        
        db.add(trade)
        db.commit()
        db.refresh(trade)
        
        # Simulate trade execution (replace with real broker integration)
        await simulate_trade_execution(trade, background_tasks)
        
        logger.info(f"Trade executed: {trade.id} - {trade.symbol} {trade.side} {trade.quantity}")
        
        return TradeResponse(
            id=trade.id,
            symbol=trade.symbol,
            side=trade.side,
            quantity=trade.quantity,
            price=trade.price,
            timestamp=trade.timestamp,
            status=trade.status
        )
        
    except Exception as e:
        logger.error(f"Error executing trade: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/positions", response_model=List[PositionResponse])
async def get_positions(db: Session = Depends(get_db_session)):
    """Get current positions"""
    try:
        positions = db.query(Position).filter(Position.status == "open").all()
        
        return [
            PositionResponse(
                id=pos.id,
                symbol=pos.symbol,
                quantity=pos.quantity,
                entry_price=pos.entry_price,
                current_price=pos.current_price,
                unrealized_pnl=pos.unrealized_pnl,
                unrealized_pnl_pct=pos.unrealized_pnl_pct,
                entry_time=pos.entry_time
            )
            for pos in positions
        ]
        
    except Exception as e:
        logger.error(f"Error getting positions: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/trades", response_model=List[TradeResponse])
async def get_trades(
    symbol: Optional[str] = None,
    limit: int = 100,
    db: Session = Depends(get_db_session)
):
    """Get recent trades"""
    try:
        query = db.query(Trade)
        
        if symbol:
            query = query.filter(Trade.symbol == symbol)
        
        trades = query.order_by(Trade.timestamp.desc()).limit(limit).all()
        
        return [
            TradeResponse(
                id=trade.id,
                symbol=trade.symbol,
                side=trade.side,
                quantity=trade.quantity,
                price=trade.price,
                timestamp=trade.timestamp,
                status=trade.status
            )
            for trade in trades
        ]
        
    except Exception as e:
        logger.error(f"Error getting trades: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/strategy/config", response_model=StrategyConfigResponse)
async def update_strategy_config(
    request: StrategyConfigRequest,
    db: Session = Depends(get_db_session)
):
    """Update strategy configuration"""
    try:
        # Get or create strategy config
        config = db.query(StrategyConfig).filter(
            StrategyConfig.strategy_type == request.strategy_type,
            StrategyConfig.symbol == request.symbol
        ).first()
        
        if not config:
            config = StrategyConfig(
                strategy_type=request.strategy_type,
                symbol=request.symbol,
                config_data=request.config_data,
                created_at=datetime.now()
            )
            db.add(config)
        else:
            config.config_data = request.config_data
            config.updated_at = datetime.now()
        
        db.commit()
        db.refresh(config)
        
        logger.info(f"Strategy config updated: {request.strategy_type} for {request.symbol}")
        
        return StrategyConfigResponse(
            id=config.id,
            strategy_type=config.strategy_type,
            symbol=config.symbol,
            config_data=config.config_data,
            created_at=config.created_at,
            updated_at=config.updated_at
        )
        
    except Exception as e:
        logger.error(f"Error updating strategy config: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/market-data/{symbol}", response_model=MarketDataResponse)
async def get_market_data(symbol: str):
    """Get current market data for a symbol"""
    try:
        # This would be replaced with real market data feed
        # For now, return mock data
        mock_data = {
            "AAPL": {"price": 150.25, "change": 0.15, "change_pct": 0.10, "volume": 50000000},
            "MSFT": {"price": 300.50, "change": -0.25, "change_pct": -0.08, "volume": 30000000},
            "NVDA": {"price": 450.75, "change": 2.50, "change_pct": 0.56, "volume": 40000000}
        }
        
        if symbol not in mock_data:
            raise HTTPException(status_code=404, detail=f"Symbol {symbol} not found")
        
        data = mock_data[symbol]
        
        return MarketDataResponse(
            symbol=symbol,
            price=data["price"],
            change=data["change"],
            change_pct=data["change_pct"],
            volume=data["volume"],
            timestamp=datetime.now()
        )
        
    except Exception as e:
        logger.error(f"Error getting market data: {e}")
        raise HTTPException(status_code=500, detail=str(e))

async def simulate_trade_execution(trade: Trade, background_tasks: BackgroundTasks):
    """Simulate trade execution (replace with real broker integration)"""
    # Simulate execution delay
    await asyncio.sleep(0.1)
    
    # Update trade status
    trade.status = "filled"
    trade.executed_at = datetime.now()
    
    # Create position if it's a buy order
    if trade.side == "BUY":
        position = Position(
            symbol=trade.symbol,
            quantity=trade.quantity,
            entry_price=trade.price,
            current_price=trade.price,
            entry_time=trade.timestamp,
            status="open"
        )
        db.add(position)
    
    db.commit()

async def get_market_data(symbol: str) -> pd.DataFrame:
    """Get market data for strategy (mock implementation)"""
    # This would be replaced with real data feed
    import pandas as pd
    import numpy as np
    
    # Generate mock OHLCV data
    dates = pd.date_range(start='2024-01-01', end='2024-01-31', freq='5T')
    np.random.seed(42)  # For reproducible results
    
    base_price = 150.0
    prices = []
    current_price = base_price
    
    for _ in range(len(dates)):
        change = np.random.normal(0, 0.5)
        current_price += change
        prices.append(current_price)
    
    df = pd.DataFrame({
        'open': prices,
        'high': [p + np.random.uniform(0, 1) for p in prices],
        'low': [p - np.random.uniform(0, 1) for p in prices],
        'close': prices,
        'volume': np.random.randint(1000000, 10000000, len(dates))
    }, index=dates)
    
    return df
