"""
Backtesting Module
==================

Core backtesting functionality including performance metrics calculation
and parameter optimization.
"""

from .metrics import MetricsCalculator, BacktestMetrics
from .service import BacktestingService
from .engine import BacktestEngine
from .parameter_space import ParameterRange, ParameterSpace
from .optimizer import OptimizationEngine, OptimizationResult

__all__ = [
    'MetricsCalculator',
    'BacktestMetrics',
    'BacktestingService',
    'BacktestEngine',
    'ParameterRange',
    'ParameterSpace',
    'OptimizationEngine',
    'OptimizationResult',
]

