"""
Backtesting Engine
==================

Core backtesting engine that simulates trading using historical data.
"""

from typing import List, Optional, Dict, Any, Tuple
from datetime import datetime
import pandas as pd
import logging

from ..strategy.base import BaseStrategy, TradingSignal, Position, SignalType, ExitReason
from .metrics import MetricsCalculator, BacktestMetrics
from ...data.database.models import BacktestTrade, TradeSide

logger = logging.getLogger(__name__)


class BacktestEngine:
    """
    Backtesting engine that simulates trading on historical data
    """
    
    def __init__(
        self,
        strategy: BaseStrategy,
        initial_capital: float,
        commission_per_trade: float = 0.0,
        slippage: float = 0.0
    ):
        """
        Initialize backtesting engine
        
        Args:
            strategy: Strategy instance to test
            initial_capital: Starting capital
            commission_per_trade: Commission per trade (default 0.0)
            slippage: Slippage as percentage (default 0.0, e.g., 0.001 for 0.1%)
        """
        self.strategy = strategy
        self.initial_capital = initial_capital
        self.commission_per_trade = commission_per_trade
        self.slippage = slippage
        
        self.metrics_calculator = MetricsCalculator()
    
    def run(
        self,
        data: pd.DataFrame,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        sentiment_data: Optional[Any] = None
    ) -> Tuple[List[BacktestTrade], BacktestMetrics]:
        """
        Run backtest on historical data
        
        Args:
            data: DataFrame with OHLCV data, indexed by datetime
            start_date: Optional start date (filters data)
            end_date: Optional end date (filters data)
            sentiment_data: Optional sentiment data for strategy
            
        Returns:
            Tuple of (list of trades, metrics)
        """
        # Filter data by date range if provided
        if start_date:
            data = data[data.index >= pd.to_datetime(start_date)]
        if end_date:
            data = data[data.index <= pd.to_datetime(end_date)]
        
        if len(data) == 0:
            logger.warning("No data available for backtest period")
            return [], self.metrics_calculator._empty_metrics(
                self.initial_capital,
                start_date or data.index[0] if len(data) > 0 else datetime.now(),
                end_date or data.index[-1] if len(data) > 0 else datetime.now()
            )
        
        # Initialize state
        cash = self.initial_capital
        position: Optional[Position] = None
        trades: List[Dict[str, Any]] = []  # Store as dicts, convert to BacktestTrade when saving
        equity_history: List[float] = []
        equity_timestamps: List[datetime] = []
        
        # Track current price for position valuation
        current_price = float(data['close'].iloc[0])
        
        # Iterate through historical data
        for idx, row in data.iterrows():
            timestamp = idx if isinstance(idx, datetime) else pd.to_datetime(idx).to_pydatetime()
            current_price = float(row['close'])
            
            # Create current data slice up to this point
            current_data = data.loc[:idx]
            
            # Check for exit conditions if we have a position
            if position:
                should_exit, exit_reason = self.strategy.should_exit(position, current_data)
                
                if should_exit:
                    # Exit position
                    exit_price = self._apply_slippage(current_price, position.quantity > 0)
                    pnl = self._calculate_pnl(position, exit_price)
                    
                    trade = {
                        'symbol': self.strategy.symbol,
                        'side': TradeSide.SELL if position.quantity > 0 else TradeSide.BUY,
                        'quantity': abs(position.quantity),
                        'price': exit_price,
                        'timestamp': timestamp,
                        'pnl': pnl,
                        'pnl_pct': (pnl / (position.entry_price * abs(position.quantity))) * 100 if position.entry_price > 0 else 0.0,
                        'exit_reason': exit_reason.value if exit_reason else None
                    }
                    trades.append(trade)
                    
                    # Update cash
                    cash += (exit_price * abs(position.quantity)) - self.commission_per_trade
                    position = None
            
            # Generate entry signal if no position
            if position is None:
                try:
                    signal = self.strategy.generate_signal(
                        current_data,
                        position=None,
                        sentiment=sentiment_data
                    )
                    
                    if signal.signal_type in [SignalType.BUY, SignalType.SELL]:
                        # Calculate position size
                        account_value = cash  # For simplicity, use cash (could add position value if multi-position)
                        quantity = self.strategy.calculate_position_size(signal, account_value)
                        
                        if quantity > 0:
                            # Execute entry
                            entry_price = self._apply_slippage(current_price, signal.signal_type == SignalType.BUY)
                            cost = entry_price * quantity + self.commission_per_trade
                            
                            if cost <= cash:
                                # Create position
                                position = Position(
                                    symbol=self.strategy.symbol,
                                    quantity=quantity if signal.signal_type == SignalType.BUY else -quantity,
                                    entry_price=entry_price,
                                    entry_time=timestamp,
                                    current_price=entry_price,
                                    unrealized_pnl=0.0,
                                    unrealized_pnl_pct=0.0,
                                    stop_loss=signal.stop_loss,
                                    take_profit=signal.take_profit
                                )
                                
                                # Update cash
                                cash -= cost
                                
                                # Create entry trade record (optional - could track separately)
                                # Entry trades are tracked for completeness but excluded from metrics
                                entry_trade = {
                                    'symbol': self.strategy.symbol,
                                    'side': TradeSide.BUY if signal.signal_type == SignalType.BUY else TradeSide.SELL,
                                    'quantity': quantity,
                                    'price': entry_price,
                                    'timestamp': timestamp,
                                    'pnl': 0.0,  # Entry trade has no P&L
                                    'pnl_pct': 0.0,
                                    'exit_reason': None
                                }
                                trades.append(entry_trade)
                
                except Exception as e:
                    logger.warning(f"Error generating signal at {timestamp}: {e}")
                    continue
            
            # Update position current price
            if position:
                position.current_price = current_price
                position.unrealized_pnl = (current_price - position.entry_price) * position.quantity
                if position.entry_price > 0:
                    position.unrealized_pnl_pct = ((current_price - position.entry_price) / position.entry_price) * 100
            
            # Track equity (cash + position value at current price)
            if position:
                position_value = current_price * position.quantity
                equity = cash + position_value
            else:
                equity = cash
            equity_history.append(equity)
            equity_timestamps.append(timestamp)
        
        # Close any open position at end
        if position:
            exit_price = current_price
            pnl = self._calculate_pnl(position, exit_price)
            
            final_timestamp = data.index[-1] if isinstance(data.index[-1], datetime) else pd.to_datetime(data.index[-1]).to_pydatetime()
            
            trade = {
                'symbol': self.strategy.symbol,
                'side': TradeSide.SELL if position.quantity > 0 else TradeSide.BUY,
                'quantity': abs(position.quantity),
                'price': exit_price,
                'timestamp': final_timestamp,
                'pnl': pnl,
                'pnl_pct': (pnl / (position.entry_price * abs(position.quantity))) * 100 if position.entry_price > 0 else 0.0,
                'exit_reason': "end_of_backtest"
            }
            trades.append(trade)
            
            cash += (exit_price * abs(position.quantity)) - self.commission_per_trade
        
        # Filter out entry trades (they have 0 P&L, we only want exits for metrics)
        # Actually, let's keep all trades but mark entry/exit pairs
        # For now, filter entry trades for metrics calculation
        exit_trades = [t for t in trades if t.pnl != 0.0]
        
        # Calculate metrics
        start_dt = start_date or data.index[0]
        end_dt = end_date or data.index[-1]
        
        metrics = self.metrics_calculator.calculate(
            trades=exit_trades,
            initial_capital=self.initial_capital,
            start_date=start_dt if isinstance(start_dt, datetime) else pd.to_datetime(start_dt).to_pydatetime(),
            end_date=end_dt if isinstance(end_dt, datetime) else pd.to_datetime(end_dt).to_pydatetime(),
            include_equity_curve=True
        )
        
        logger.info(
            f"Backtest completed: {len(exit_trades)} trades, "
            f"Return: {metrics.total_return_pct:.2f}%, "
            f"Sharpe: {metrics.sharpe_ratio:.2f}"
        )
        
        return trades, metrics
    
    def _apply_slippage(self, price: float, is_buy: bool) -> float:
        """
        Apply slippage to price
        
        Args:
            price: Base price
            is_buy: True if buying (slippage adds), False if selling (slippage subtracts)
            
        Returns:
            Price with slippage applied
        """
        if self.slippage == 0.0:
            return price
        
        slippage_amount = price * self.slippage
        if is_buy:
            return price + slippage_amount
        else:
            return price - slippage_amount
    
    def _calculate_pnl(self, position: Position, exit_price: float) -> float:
        """
        Calculate profit/loss for closing a position
        
        Args:
            position: Position to close
            exit_price: Exit price
            
        Returns:
            P&L amount
        """
        return (exit_price - position.entry_price) * position.quantity - self.commission_per_trade

