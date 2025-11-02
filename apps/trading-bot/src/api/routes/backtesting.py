"""
Backtesting Routes
==================

API routes for backtesting operations with performance metrics.
"""

from fastapi import APIRouter, HTTPException, Depends
from typing import Dict, Any, Optional, List
from pydantic import BaseModel
from datetime import datetime
import logging

from ...core.backtesting.service import BacktestingService
from ...core.backtesting.metrics import BacktestMetrics
from ...data.database.models import Backtest, BacktestTrade
from ...data.database import get_db
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)

router = APIRouter()


class BacktestRequest(BaseModel):
    """Request model for backtest execution"""
    strategy: str
    symbol: str
    start_date: datetime
    end_date: datetime
    initial_capital: float = 10000.0
    parameters: Dict[str, Any] = {}
    risk_free_rate: float = 0.0


class BacktestResponse(BaseModel):
    """Response model for backtest results"""
    backtest_id: int
    status: str
    metrics: Optional[Dict[str, Any]] = None
    message: Optional[str] = None


def get_backtesting_service() -> BacktestingService:
    """Get backtesting service instance"""
    return BacktestingService(risk_free_rate=0.0)


@router.post("/run", response_model=BacktestResponse)
async def run_backtest(
    request: BacktestRequest,
    db: Session = Depends(get_db),
    service: BacktestingService = Depends(get_backtesting_service)
):
    """
    Run a backtest strategy
    
    Note: This endpoint currently returns a placeholder. Full backtest execution
    will be implemented when the backtesting engine is complete.
    """
    logger.info(f"Backtest request: strategy={request.strategy}, symbol={request.symbol}")
    
    # TODO: Implement full backtest execution
    # For now, return placeholder response
    return BacktestResponse(
        backtest_id=0,
        status="pending",
        message="Backtesting execution not yet fully implemented. Metrics calculator is available."
    )


@router.get("/{backtest_id}/metrics")
async def get_backtest_metrics(
    backtest_id: int,
    db: Session = Depends(get_db),
    service: BacktestingService = Depends(get_backtesting_service)
):
    """
    Get detailed performance metrics for a completed backtest
    
    Args:
        backtest_id: ID of the backtest
        
    Returns:
        Detailed metrics including Sharpe ratio, drawdown, win rate, etc.
    """
    # Fetch backtest from database
    backtest = db.query(Backtest).filter(Backtest.id == backtest_id).first()
    
    if not backtest:
        raise HTTPException(status_code=404, detail=f"Backtest {backtest_id} not found")
    
    # Get metrics (calculate if not already done)
    metrics = service.get_metrics_from_backtest(backtest)
    
    if metrics is None:
        # Calculate metrics
        metrics = service.calculate_and_store_metrics(backtest, include_equity_curve=False)
        db.commit()
    
    # Convert to dict for JSON response
    metrics_dict = {
        "basic": {
            "initial_capital": metrics.initial_capital,
            "final_capital": metrics.final_capital,
            "total_return": metrics.total_return,
            "total_return_pct": metrics.total_return_pct,
        },
        "trades": {
            "total_trades": metrics.total_trades,
            "winning_trades": metrics.winning_trades,
            "losing_trades": metrics.losing_trades,
            "win_rate": metrics.win_rate,
        },
        "profit_loss": {
            "total_profit": metrics.total_profit,
            "total_loss": metrics.total_loss,
            "profit_factor": metrics.profit_factor,
            "average_win": metrics.average_win,
            "average_loss": metrics.average_loss,
            "largest_win": metrics.largest_win,
            "largest_loss": metrics.largest_loss,
        },
        "risk": {
            "max_drawdown": metrics.max_drawdown,
            "max_drawdown_pct": metrics.max_drawdown_pct,
            "max_drawdown_start": metrics.max_drawdown_start.isoformat() if metrics.max_drawdown_start else None,
            "max_drawdown_end": metrics.max_drawdown_end.isoformat() if metrics.max_drawdown_end else None,
            "recovery_time_days": metrics.recovery_time_days,
        },
        "risk_adjusted": {
            "sharpe_ratio": metrics.sharpe_ratio,
            "sortino_ratio": metrics.sortino_ratio,
            "calmar_ratio": metrics.calmar_ratio,
        },
        "additional": {
            "average_trade_return": metrics.average_trade_return,
            "expectancy": metrics.expectancy,
            "total_bars": metrics.total_bars,
        },
        "period": {
            "start_date": metrics.start_date.isoformat(),
            "end_date": metrics.end_date.isoformat(),
        }
    }
    
    return {
        "backtest_id": backtest_id,
        "metrics": metrics_dict
    }


@router.post("/optimize")
async def optimize_parameters(
    request: Dict[str, Any],
    db: Session = Depends(get_db),
    service: BacktestingService = Depends(get_backtesting_service)
):
    """
    Run parameter optimization for a strategy
    
    Note: This endpoint currently returns a placeholder. Full optimization
    will be implemented when the backtesting engine is complete.
    
    Request body should include:
    - strategy: Strategy name
    - symbol: Symbol to backtest
    - start_date: Start date
    - end_date: End date
    - initial_capital: Starting capital
    - parameter_space: Dict of parameter ranges
    - objective: Optimization objective (sharpe_ratio, total_return, etc.)
    - max_workers: Number of parallel workers (default 4)
    """
    logger.info(f"Optimization request: {request}")
    
    # TODO: Implement full optimization
    # For now, return placeholder response
    return {
        "status": "pending",
        "message": "Parameter optimization not yet fully implemented. Optimization engine is available."
    }


@router.get("/strategies")
async def get_strategies():
    """Get available backtesting strategies"""
    from ...core.strategy.registry import StrategyRegistry
    
    registry = StrategyRegistry()
    strategy_names = registry.list_strategies()
    
    strategies = []
    for name in strategy_names:
        try:
            info = registry.get_strategy_info(name)
            strategies.append({
                "name": name,
                "description": info.get('description', f"{name} strategy"),
                "class": info.get('class', '')
            })
        except Exception as e:
            logger.warning(f"Error getting info for strategy {name}: {e}")
            strategies.append({
                "name": name,
                "description": f"{name} strategy",
                "class": ""
            })
    
    return {
        "strategies": strategies
    }
