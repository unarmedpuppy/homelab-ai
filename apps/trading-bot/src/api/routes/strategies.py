"""
Strategy Management Routes
==========================

API endpoints for managing and evaluating trading strategies.
"""

from fastapi import APIRouter, HTTPException, Depends
from typing import List, Dict, Any, Optional
from pydantic import BaseModel
import logging

from ...core.strategy.registry import get_registry
from ...core.evaluation import StrategyEvaluator
from ...config.settings import settings

logger = logging.getLogger(__name__)

router = APIRouter()

# Global evaluator instance
_evaluator: Optional[StrategyEvaluator] = None


def get_evaluator() -> StrategyEvaluator:
    """Get or create global evaluator instance"""
    global _evaluator
    if _evaluator is None:
        # Initialize without data provider for now
        # In production, you'd pass a configured data provider
        _evaluator = StrategyEvaluator()
    return _evaluator


class StrategyConfig(BaseModel):
    """Strategy configuration model"""
    name: str
    symbol: str
    timeframe: str = "5m"
    entry: Dict[str, Any] = {}
    exit: Dict[str, Any] = {}
    risk_management: Dict[str, Any] = {}


class StrategyRequest(BaseModel):
    """Request to add/evaluate a strategy"""
    strategy_type: str
    config: Dict[str, Any]
    enabled: bool = True


class EvaluateRequest(BaseModel):
    """Request to evaluate strategies"""
    symbols: Optional[List[str]] = None  # If None, evaluate all
    fetch_data: bool = False  # Whether to fetch fresh data


@router.get("/strategies")
async def list_strategies():
    """List all available strategy types"""
    registry = get_registry()
    strategies = registry.list_strategies()
    
    result = []
    for strategy_name in strategies:
        info = registry.get_strategy_info(strategy_name)
        result.append({
            'name': strategy_name,
            'description': info.get('description', ''),
            'metadata': info
        })
    
    return {
        "status": "success",
        "strategies": result
    }


@router.get("/strategies/{strategy_name}")
async def get_strategy_info(strategy_name: str):
    """Get information about a strategy type"""
    registry = get_registry()
    
    if not registry.is_registered(strategy_name):
        raise HTTPException(
            status_code=404,
            detail=f"Strategy '{strategy_name}' not found"
        )
    
    info = registry.get_strategy_info(strategy_name)
    
    return {
        "status": "success",
        "strategy": {
            'name': strategy_name,
            **info
        }
    }


@router.post("/strategies/add")
async def add_strategy(request: StrategyRequest):
    """Add a strategy to the evaluator"""
    evaluator = get_evaluator()
    
    try:
        strategy_id = f"{request.strategy_type}_{request.config.get('symbol', 'UNKNOWN')}"
        
        state = evaluator.add_strategy(
            strategy_name=request.strategy_type,
            config=request.config,
            enabled=request.enabled
        )
        
        return {
            "status": "success",
            "message": f"Strategy added: {strategy_id}",
            "strategy_id": strategy_id,
            "enabled": state.enabled
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error adding strategy: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error adding strategy: {str(e)}")


@router.get("/strategies/active")
async def list_active_strategies():
    """List all active strategies in the evaluator"""
    evaluator = get_evaluator()
    strategy_ids = evaluator.list_strategies()
    
    strategies = []
    for strategy_id in strategy_ids:
        state = evaluator.get_strategy_state(strategy_id)
        if state:
            strategies.append({
                'strategy_id': strategy_id,
                'symbol': state.symbol,
                'enabled': state.enabled,
                'evaluations': state.evaluation_count,
                'signals_generated': state.signals_generated,
                'last_evaluation': state.last_evaluation.isoformat() if state.last_evaluation else None,
                'has_position': state.current_position is not None
            })
    
    return {
        "status": "success",
        "strategies": strategies
    }


@router.post("/strategies/{strategy_id}/enable")
async def enable_strategy(strategy_id: str):
    """Enable a strategy"""
    evaluator = get_evaluator()
    
    if strategy_id not in evaluator.list_strategies():
        raise HTTPException(
            status_code=404,
            detail=f"Strategy '{strategy_id}' not found"
        )
    
    evaluator.enable_strategy(strategy_id)
    
    return {
        "status": "success",
        "message": f"Strategy {strategy_id} enabled"
    }


@router.post("/strategies/{strategy_id}/disable")
async def disable_strategy(strategy_id: str):
    """Disable a strategy"""
    evaluator = get_evaluator()
    
    if strategy_id not in evaluator.list_strategies():
        raise HTTPException(
            status_code=404,
            detail=f"Strategy '{strategy_id}' not found"
        )
    
    evaluator.disable_strategy(strategy_id)
    
    return {
        "status": "success",
        "message": f"Strategy {strategy_id} disabled"
    }


@router.delete("/strategies/{strategy_id}")
async def remove_strategy(strategy_id: str):
    """Remove a strategy from evaluator"""
    evaluator = get_evaluator()
    
    if strategy_id not in evaluator.list_strategies():
        raise HTTPException(
            status_code=404,
            detail=f"Strategy '{strategy_id}' not found"
        )
    
    evaluator.remove_strategy(strategy_id)
    
    return {
        "status": "success",
        "message": f"Strategy {strategy_id} removed"
    }


@router.post("/strategies/evaluate")
async def evaluate_strategies(request: EvaluateRequest):
    """
    Evaluate all active strategies
    
    Note: This is a simplified endpoint. In production, you'd want to:
    - Fetch real market data
    - Handle async data fetching
    - Return more detailed results
    """
    evaluator = get_evaluator()
    
    # This would need market data to evaluate
    # For now, return evaluation stats
    stats = evaluator.get_evaluation_stats()
    
    return {
        "status": "success",
        "message": "Evaluation would be performed with market data",
        "stats": stats
    }


@router.get("/strategies/stats")
async def get_evaluation_stats():
    """Get evaluation statistics"""
    evaluator = get_evaluator()
    stats = evaluator.get_evaluation_stats()
    
    return {
        "status": "success",
        "stats": stats
    }

