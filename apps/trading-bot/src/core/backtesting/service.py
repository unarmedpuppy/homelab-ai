"""
Backtesting Service
===================

Service layer for orchestrating backtesting operations including
metrics calculation and integration with database models.
"""

from typing import List, Optional, Dict, Any
from datetime import datetime
import logging
import json
import pandas as pd

from .metrics import MetricsCalculator, BacktestMetrics
from ...data.database.models import Backtest, BacktestTrade

logger = logging.getLogger(__name__)


class BacktestingService:
    """Service for backtesting operations"""
    
    def __init__(self, risk_free_rate: float = 0.0):
        """
        Initialize backtesting service
        
        Args:
            risk_free_rate: Annual risk-free rate for metrics calculation
        """
        self.metrics_calculator = MetricsCalculator(risk_free_rate=risk_free_rate)
    
    def calculate_and_store_metrics(
        self,
        backtest: Backtest,
        trades: Optional[List[BacktestTrade]] = None,
        include_equity_curve: bool = False
    ) -> BacktestMetrics:
        """
        Calculate metrics for a backtest and store in database
        
        Args:
            backtest: Backtest database model instance
            trades: List of backtest trades (if None, will fetch from database)
            include_equity_curve: Whether to include equity curve in results
            
        Returns:
            BacktestMetrics object
        """
        # Fetch trades if not provided
        if trades is None:
            trades = backtest.backtest_trades
        
        # Calculate metrics
        metrics = self.metrics_calculator.calculate(
            trades=trades,
            initial_capital=backtest.initial_capital,
            start_date=backtest.start_date,
            end_date=backtest.end_date,
            include_equity_curve=include_equity_curve
        )
        
        # Update backtest model with metrics
        self._update_backtest_model(backtest, metrics, include_equity_curve)
        
        logger.info(
            f"Calculated metrics for backtest {backtest.id}: "
            f"Sharpe={metrics.sharpe_ratio:.2f}, "
            f"Return={metrics.total_return_pct:.2f}%, "
            f"MaxDD={metrics.max_drawdown_pct:.2f}%, "
            f"WinRate={metrics.win_rate:.2f}%"
        )
        
        return metrics
    
    def _update_backtest_model(
        self,
        backtest: Backtest,
        metrics: BacktestMetrics,
        include_equity_curve: bool = False
    ) -> None:
        """
        Update backtest database model with calculated metrics
        
        Args:
            backtest: Backtest model instance
            metrics: Calculated metrics
            include_equity_curve: Whether equity curve was included
        """
        # Update basic metrics
        backtest.final_capital = metrics.final_capital
        backtest.total_return = metrics.total_return
        backtest.total_return_pct = metrics.total_return_pct
        backtest.max_drawdown = metrics.max_drawdown
        backtest.sharpe_ratio = metrics.sharpe_ratio
        backtest.win_rate = metrics.win_rate
        backtest.total_trades = metrics.total_trades
        backtest.winning_trades = metrics.winning_trades
        backtest.losing_trades = metrics.losing_trades
        
        # Store detailed results in JSON field
        results_dict = {
            'profit_factor': metrics.profit_factor,
            'average_win': metrics.average_win,
            'average_loss': metrics.average_loss,
            'largest_win': metrics.largest_win,
            'largest_loss': metrics.largest_loss,
            'max_drawdown_pct': metrics.max_drawdown_pct,
            'max_drawdown_start': metrics.max_drawdown_start.isoformat() if metrics.max_drawdown_start else None,
            'max_drawdown_end': metrics.max_drawdown_end.isoformat() if metrics.max_drawdown_end else None,
            'recovery_time_days': metrics.recovery_time_days,
            'sortino_ratio': metrics.sortino_ratio,
            'calmar_ratio': metrics.calmar_ratio,
            'average_trade_return': metrics.average_trade_return,
            'expectancy': metrics.expectancy,
            'total_profit': metrics.total_profit,
            'total_loss': metrics.total_loss,
            'total_bars': metrics.total_bars,
        }
        
        # Optionally include equity curve (can be large)
        if include_equity_curve and metrics.equity_curve is not None:
            # Store equity curve as list of [timestamp, value] pairs
            equity_data = [
                [idx.isoformat(), float(val)]
                for idx, val in metrics.equity_curve.items()
            ]
            results_dict['equity_curve'] = equity_data
        
        backtest.results = json.dumps(results_dict)
        
        logger.debug(f"Updated backtest {backtest.id} with metrics")
    
    def get_metrics_from_backtest(self, backtest: Backtest) -> Optional[BacktestMetrics]:
        """
        Retrieve metrics from backtest model (if already calculated)
        
        Args:
            backtest: Backtest model instance
            
        Returns:
            BacktestMetrics object or None if metrics not calculated
        """
        if backtest.sharpe_ratio is None and backtest.results is None:
            return None
        
        # Reconstruct metrics from stored values
        results_dict = {}
        if backtest.results:
            try:
                results_dict = json.loads(backtest.results)
            except (json.JSONDecodeError, TypeError):
                logger.warning(f"Failed to parse results JSON for backtest {backtest.id}")
                results_dict = {}
        
        # Build metrics object from stored values
        metrics = BacktestMetrics(
            initial_capital=backtest.initial_capital,
            final_capital=backtest.final_capital or backtest.initial_capital,
            total_return=backtest.total_return or 0.0,
            total_return_pct=backtest.total_return_pct or 0.0,
            total_trades=backtest.total_trades or 0,
            winning_trades=backtest.winning_trades or 0,
            losing_trades=backtest.losing_trades or 0,
            win_rate=backtest.win_rate or 0.0,
            total_profit=results_dict.get('total_profit', 0.0),
            total_loss=results_dict.get('total_loss', 0.0),
            profit_factor=results_dict.get('profit_factor', 0.0),
            average_win=results_dict.get('average_win', 0.0),
            average_loss=results_dict.get('average_loss', 0.0),
            largest_win=results_dict.get('largest_win', 0.0),
            largest_loss=results_dict.get('largest_loss', 0.0),
            max_drawdown=backtest.max_drawdown or 0.0,
            max_drawdown_pct=results_dict.get('max_drawdown_pct', 0.0),
            max_drawdown_start=pd.to_datetime(results_dict['max_drawdown_start']).to_pydatetime() if results_dict.get('max_drawdown_start') else None,
            max_drawdown_end=pd.to_datetime(results_dict['max_drawdown_end']).to_pydatetime() if results_dict.get('max_drawdown_end') else None,
            recovery_time_days=results_dict.get('recovery_time_days'),
            sharpe_ratio=backtest.sharpe_ratio or 0.0,
            sortino_ratio=results_dict.get('sortino_ratio', 0.0),
            calmar_ratio=results_dict.get('calmar_ratio', 0.0),
            average_trade_return=results_dict.get('average_trade_return', 0.0),
            expectancy=results_dict.get('expectancy', 0.0),
            total_bars=results_dict.get('total_bars', 0),
            start_date=backtest.start_date,
            end_date=backtest.end_date,
            equity_curve=None,  # Don't reconstruct equity curve from JSON
            monthly_returns=None,
            daily_returns=None,
        )
        
        return metrics

