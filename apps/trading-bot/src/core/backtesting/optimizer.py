"""
Parameter Optimization Engine
=============================

Grid search optimization for strategy parameters.
"""

from typing import Dict, List, Any, Optional, Type, Callable, Tuple
from dataclasses import dataclass
from datetime import datetime
import asyncio
from concurrent.futures import ThreadPoolExecutor, as_completed
import logging
import pandas as pd

from .parameter_space import ParameterSpace
from .metrics import MetricsCalculator, BacktestMetrics
from ..strategy.base import BaseStrategy

logger = logging.getLogger(__name__)


@dataclass
class OptimizationResult:
    """Result of parameter optimization"""
    best_params: Dict[str, Any]
    best_metrics: BacktestMetrics
    best_objective_value: float
    all_results: List[Tuple[Dict[str, Any], BacktestMetrics, float]]  # (params, metrics, objective_value)
    optimization_time_seconds: float
    total_combinations: int
    combinations_tested: int
    objective_name: str


class OptimizationEngine:
    """
    Parameter optimization engine using grid search
    """
    
    # Supported optimization objectives
    OBJECTIVES = {
        'sharpe_ratio': lambda m: m.sharpe_ratio,
        'total_return': lambda m: m.total_return_pct,
        'win_rate': lambda m: m.win_rate,
        'profit_factor': lambda m: m.profit_factor if m.profit_factor != float('inf') else 0.0,
        'calmar_ratio': lambda m: m.calmar_ratio if m.calmar_ratio != float('inf') else 0.0,
        'sortino_ratio': lambda m: m.sortino_ratio if m.sortino_ratio != float('inf') else 0.0,
    }
    
    def __init__(
        self,
        strategy_class: Type[BaseStrategy],
        parameter_space: ParameterSpace,
        initial_capital: float,
        data: pd.DataFrame,
        risk_free_rate: float = 0.0
    ):
        """
        Initialize optimization engine
        
        Args:
            strategy_class: Strategy class to optimize
            parameter_space: Parameter space to search
            initial_capital: Starting capital for backtests
            data: Market data DataFrame (OHLCV)
            risk_free_rate: Risk-free rate for metrics calculation
        """
        self.strategy_class = strategy_class
        self.parameter_space = parameter_space
        self.initial_capital = initial_capital
        self.data = data
        self.metrics_calculator = MetricsCalculator(risk_free_rate=risk_free_rate)
        
        # Validate strategy class
        if not issubclass(strategy_class, BaseStrategy):
            raise ValueError(f"Strategy class must inherit from BaseStrategy: {strategy_class}")
    
    async def optimize(
        self,
        objective: str = 'sharpe_ratio',
        max_workers: int = 4,
        progress_callback: Optional[Callable[[int, int], None]] = None
    ) -> OptimizationResult:
        """
        Run parameter optimization using grid search
        
        Args:
            objective: Optimization objective (one of: sharpe_ratio, total_return, win_rate, etc.)
            max_workers: Maximum number of parallel workers
            progress_callback: Optional callback function(completed, total) for progress updates
            
        Returns:
            OptimizationResult with best parameters and all results
        """
        if objective not in self.OBJECTIVES:
            raise ValueError(
                f"Unknown objective '{objective}'. "
                f"Supported objectives: {list(self.OBJECTIVES.keys())}"
            )
        
        objective_func = self.OBJECTIVES[objective]
        
        # Generate all parameter combinations
        combinations = self.parameter_space.generate_combinations()
        total_combinations = len(combinations)
        
        logger.info(
            f"Starting optimization with {total_combinations} combinations, "
            f"objective: {objective}, max_workers: {max_workers}"
        )
        
        start_time = datetime.now()
        results = []
        best_metrics = None
        best_params = None
        best_objective_value = float('-inf')
        
        # Run optimizations in parallel
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            # Submit all tasks
            future_to_params = {
                executor.submit(self._run_single_backtest, params): params
                for params in combinations
            }
            
            # Process completed tasks
            completed = 0
            for future in as_completed(future_to_params):
                params = future_to_params[future]
                completed += 1
                
                try:
                    metrics = future.result()
                    if metrics is None:
                        logger.warning(f"Backtest failed for parameters {params}")
                        continue
                    
                    # Calculate objective value
                    objective_value = objective_func(metrics)
                    
                    results.append((params, metrics, objective_value))
                    
                    # Update best if better
                    if objective_value > best_objective_value:
                        best_objective_value = objective_value
                        best_metrics = metrics
                        best_params = params
                        logger.debug(
                            f"New best ({objective}={objective_value:.4f}): {best_params}"
                        )
                    
                    # Progress callback
                    if progress_callback:
                        progress_callback(completed, total_combinations)
                    
                except Exception as e:
                    logger.error(f"Error evaluating parameters {params}: {e}", exc_info=True)
                    continue
        
        # Sort results by objective value (descending)
        results.sort(key=lambda x: x[2], reverse=True)
        
        optimization_time = (datetime.now() - start_time).total_seconds()
        
        if best_params is None:
            raise RuntimeError("No successful backtests found during optimization")
        
        logger.info(
            f"Optimization completed in {optimization_time:.2f}s. "
            f"Best {objective}: {best_objective_value:.4f} with params: {best_params}"
        )
        
        return OptimizationResult(
            best_params=best_params,
            best_metrics=best_metrics,
            best_objective_value=best_objective_value,
            all_results=results,
            optimization_time_seconds=optimization_time,
            total_combinations=total_combinations,
            combinations_tested=len(results),
            objective_name=objective
        )
    
    def _run_single_backtest(self, params: Dict[str, Any]) -> Optional[BacktestMetrics]:
        """
        Run a single backtest with given parameters
        
        Args:
            params: Parameter dictionary
            
        Returns:
            BacktestMetrics or None if backtest fails
        """
        try:
            # Create strategy instance with parameters
            config = params.copy()
            
            # Add required config fields if not present
            if 'symbol' not in config:
                config['symbol'] = 'UNKNOWN'
            if 'timeframe' not in config:
                config['timeframe'] = '5m'
            
            strategy = self.strategy_class(config)
            
            # Run backtest using backtesting engine
            from .engine import BacktestEngine
            
            engine = BacktestEngine(
                strategy=strategy,
                initial_capital=self.initial_capital,
                commission_per_trade=0.0,  # Can be configured
                slippage=0.0  # Can be configured
            )
            
            # Run backtest
            trades, metrics = engine.run(
                data=self.data,
                start_date=None,  # Use all data
                end_date=None,
                sentiment_data=None  # Can be added if needed
            )
            
            return metrics
            
        except Exception as e:
            logger.error(f"Error running backtest with params {params}: {e}", exc_info=True)
            return None
    
    def _evaluate_objective(
        self,
        metrics: BacktestMetrics,
        objective: str
    ) -> float:
        """
        Evaluate objective function for given metrics
        
        Args:
            metrics: Calculated metrics
            objective: Objective name
            
        Returns:
            Objective value
        """
        if objective not in self.OBJECTIVES:
            raise ValueError(f"Unknown objective: {objective}")
        
        objective_func = self.OBJECTIVES[objective]
        return objective_func(metrics)
    
    @classmethod
    def register_objective(cls, name: str, func: Callable[[BacktestMetrics], float]):
        """
        Register a custom objective function
        
        Args:
            name: Objective name
            func: Function that takes BacktestMetrics and returns a float
        """
        cls.OBJECTIVES[name] = func
        logger.info(f"Registered custom objective: {name}")

