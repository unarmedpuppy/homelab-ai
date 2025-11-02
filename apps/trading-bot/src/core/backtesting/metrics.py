"""
Performance Metrics Calculator
==============================

Calculate comprehensive performance metrics from backtest trades including
Sharpe ratio, maximum drawdown, win rate, profit factor, and more.
"""

from dataclasses import dataclass
from typing import List, Tuple, Optional
from datetime import datetime
import pandas as pd
import numpy as np
import logging

logger = logging.getLogger(__name__)


@dataclass
class BacktestMetrics:
    """Comprehensive backtest performance metrics"""
    # Basic metrics
    initial_capital: float
    final_capital: float
    total_return: float
    total_return_pct: float
    
    # Trade statistics
    total_trades: int
    winning_trades: int
    losing_trades: int
    win_rate: float
    
    # Profit/Loss metrics
    total_profit: float
    total_loss: float
    profit_factor: float
    average_win: float
    average_loss: float
    largest_win: float
    largest_loss: float
    
    # Risk metrics
    max_drawdown: float
    max_drawdown_pct: float
    max_drawdown_start: Optional[datetime]
    max_drawdown_end: Optional[datetime]
    recovery_time_days: Optional[float]
    
    # Risk-adjusted returns
    sharpe_ratio: float
    sortino_ratio: float
    calmar_ratio: float
    
    # Additional metrics
    average_trade_return: float
    expectancy: float  # Average expected return per trade
    total_bars: int
    start_date: datetime
    end_date: datetime
    
    # Equity curve data (optional, for detailed analysis)
    equity_curve: Optional[pd.Series] = None
    monthly_returns: Optional[pd.Series] = None
    daily_returns: Optional[pd.Series] = None


class MetricsCalculator:
    """
    Calculate comprehensive performance metrics from backtest trades
    """
    
    def __init__(self, risk_free_rate: float = 0.0, trading_days_per_year: int = 252):
        """
        Initialize metrics calculator
        
        Args:
            risk_free_rate: Annual risk-free rate (default 0.0)
            trading_days_per_year: Trading days per year for annualization (default 252)
        """
        self.risk_free_rate = risk_free_rate
        self.trading_days_per_year = trading_days_per_year
    
    def calculate(
        self,
        trades: List,  # List of BacktestTrade objects or dicts with trade data
        initial_capital: float,
        start_date: datetime,
        end_date: datetime,
        include_equity_curve: bool = True
    ) -> BacktestMetrics:
        """
        Calculate comprehensive performance metrics from trades
        
        Args:
            trades: List of backtest trades
            initial_capital: Starting capital
            start_date: Backtest start date
            end_date: Backtest end date
            include_equity_curve: Whether to calculate equity curve (default True)
            
        Returns:
            BacktestMetrics object with all calculated metrics
        """
        if not trades:
            return self._empty_metrics(initial_capital, start_date, end_date)
        
        # Convert trades to DataFrame for easier processing
        trades_df = self._trades_to_dataframe(trades)
        
        # Calculate basic metrics
        final_capital = initial_capital + trades_df['pnl'].sum()
        total_return = final_capital - initial_capital
        total_return_pct = (total_return / initial_capital) * 100 if initial_capital > 0 else 0.0
        
        # Trade statistics
        winning_trades = trades_df[trades_df['pnl'] > 0]
        losing_trades = trades_df[trades_df['pnl'] < 0]
        total_trades = len(trades_df)
        win_rate = (len(winning_trades) / total_trades * 100) if total_trades > 0 else 0.0
        
        # Profit/Loss metrics
        total_profit = winning_trades['pnl'].sum() if len(winning_trades) > 0 else 0.0
        total_loss = abs(losing_trades['pnl'].sum()) if len(losing_trades) > 0 else 0.0
        profit_factor = total_profit / total_loss if total_loss > 0 else (float('inf') if total_profit > 0 else 0.0)
        
        average_win = winning_trades['pnl'].mean() if len(winning_trades) > 0 else 0.0
        average_loss = losing_trades['pnl'].mean() if len(losing_trades) > 0 else 0.0
        largest_win = winning_trades['pnl'].max() if len(winning_trades) > 0 else 0.0
        largest_loss = losing_trades['pnl'].min() if len(losing_trades) > 0 else 0.0
        
        # Equity curve and drawdown
        if include_equity_curve:
            equity_curve = self.build_equity_curve(trades, initial_capital, start_date, end_date)
            max_dd, max_dd_pct, dd_start, dd_end = self.calculate_max_drawdown(equity_curve)
            
            # Calculate recovery time
            recovery_time = self._calculate_recovery_time(equity_curve, max_dd, dd_start)
            
            # Calculate returns for risk-adjusted metrics
            daily_returns = self._calculate_daily_returns(equity_curve)
            monthly_returns = self._calculate_monthly_returns(equity_curve)
        else:
            equity_curve = None
            daily_returns = None
            monthly_returns = None
            max_dd = 0.0
            max_dd_pct = 0.0
            dd_start = None
            dd_end = None
            recovery_time = None
        
        # Risk-adjusted returns
        sharpe_ratio = self.calculate_sharpe_ratio(
            daily_returns if daily_returns is not None else pd.Series(dtype=float)
        )
        sortino_ratio = self.calculate_sortino_ratio(
            daily_returns if daily_returns is not None else pd.Series(dtype=float)
        )
        # Annualize return for Calmar ratio (rough approximation from period)
        days_in_period = (end_date - start_date).days
        if days_in_period > 0:
            annual_return = (total_return_pct / 100) * (365 / days_in_period)
        else:
            annual_return = 0.0
        calmar_ratio = self.calculate_calmar_ratio(annual_return, max_dd_pct / 100)
        
        # Additional metrics
        average_trade_return = trades_df['pnl'].mean()
        expectancy = (win_rate / 100 * average_win) + ((100 - win_rate) / 100 * average_loss)
        
        # Calculate total bars (approximate from date range)
        total_bars = self._estimate_bars(start_date, end_date)
        
        return BacktestMetrics(
            initial_capital=initial_capital,
            final_capital=final_capital,
            total_return=total_return,
            total_return_pct=total_return_pct,
            total_trades=total_trades,
            winning_trades=len(winning_trades),
            losing_trades=len(losing_trades),
            win_rate=win_rate,
            total_profit=total_profit,
            total_loss=total_loss,
            profit_factor=profit_factor,
            average_win=average_win,
            average_loss=average_loss,
            largest_win=largest_win,
            largest_loss=largest_loss,
            max_drawdown=max_dd,
            max_drawdown_pct=max_dd_pct,
            max_drawdown_start=dd_start,
            max_drawdown_end=dd_end,
            recovery_time_days=recovery_time,
            sharpe_ratio=sharpe_ratio,
            sortino_ratio=sortino_ratio,
            calmar_ratio=calmar_ratio,
            average_trade_return=average_trade_return,
            expectancy=expectancy,
            total_bars=total_bars,
            start_date=start_date,
            end_date=end_date,
            equity_curve=equity_curve,
            monthly_returns=monthly_returns,
            daily_returns=daily_returns,
        )
    
    def calculate_sharpe_ratio(self, returns: pd.Series, risk_free_rate: Optional[float] = None) -> float:
        """
        Calculate Sharpe ratio (annualized)
        
        Args:
            returns: Series of returns (daily, monthly, etc.)
            risk_free_rate: Annual risk-free rate (uses instance default if None)
            
        Returns:
            Sharpe ratio (annualized)
        """
        if returns.empty or len(returns) < 2:
            return 0.0
        
        risk_free = risk_free_rate if risk_free_rate is not None else self.risk_free_rate
        
        # Calculate excess returns
        excess_returns = returns - (risk_free / self.trading_days_per_year)
        
        # Annualize if daily returns
        if len(returns) > 0:
            # Estimate if daily (assuming ~252 trading days)
            mean_return = excess_returns.mean()
            std_return = excess_returns.std()
            
            if std_return == 0:
                return 0.0
            
            # Annualize
            sharpe = (mean_return * np.sqrt(self.trading_days_per_year)) / std_return
            return float(sharpe)
        
        return 0.0
    
    def calculate_sortino_ratio(self, returns: pd.Series, risk_free_rate: Optional[float] = None) -> float:
        """
        Calculate Sortino ratio (annualized)
        Similar to Sharpe but only considers downside deviation
        
        Args:
            returns: Series of returns
            risk_free_rate: Annual risk-free rate
            
        Returns:
            Sortino ratio (annualized)
        """
        if returns.empty or len(returns) < 2:
            return 0.0
        
        risk_free = risk_free_rate if risk_free_rate is not None else self.risk_free_rate
        excess_returns = returns - (risk_free / self.trading_days_per_year)
        
        # Calculate downside deviation (only negative returns)
        downside_returns = excess_returns[excess_returns < 0]
        
        if len(downside_returns) == 0:
            # No downside, return high ratio
            return 999.0
        
        downside_std = downside_returns.std()
        
        if downside_std == 0:
            return 0.0
        
        mean_return = excess_returns.mean()
        sortino = (mean_return * np.sqrt(self.trading_days_per_year)) / downside_std
        
        return float(sortino)
    
    def calculate_max_drawdown(self, equity_curve: pd.Series) -> Tuple[float, float, Optional[datetime], Optional[datetime]]:
        """
        Calculate maximum drawdown
        
        Args:
            equity_curve: Series of portfolio values over time (indexed by datetime)
            
        Returns:
            Tuple of (max_drawdown_value, max_drawdown_pct, start_date, end_date)
        """
        if equity_curve.empty or len(equity_curve) < 2:
            return 0.0, 0.0, None, None
        
        # Calculate running maximum
        running_max = equity_curve.expanding().max()
        
        # Calculate drawdown
        drawdown = equity_curve - running_max
        drawdown_pct = (drawdown / running_max) * 100
        
        # Find maximum drawdown
        max_dd_idx = drawdown.idxmin()
        max_dd_value = float(drawdown.min())
        max_dd_pct_value = float(drawdown_pct.min())
        
        # Find drawdown start (peak before max drawdown)
        peak_before_dd = running_max.loc[:max_dd_idx].idxmax()
        dd_start = peak_before_dd if pd.notna(peak_before_dd) else equity_curve.index[0]
        
        # Find drawdown end (recovery point)
        dd_end = max_dd_idx
        
        return max_dd_value, max_dd_pct_value, dd_start, dd_end
    
    def calculate_win_rate(self, trades: List) -> float:
        """
        Calculate win rate percentage
        
        Args:
            trades: List of trade objects/dicts
            
        Returns:
            Win rate as percentage (0-100)
        """
        if not trades:
            return 0.0
        
        trades_df = self._trades_to_dataframe(trades)
        winning_trades = len(trades_df[trades_df['pnl'] > 0])
        total_trades = len(trades_df)
        
        return (winning_trades / total_trades * 100) if total_trades > 0 else 0.0
    
    def calculate_profit_factor(self, trades: List) -> float:
        """
        Calculate profit factor (gross profit / gross loss)
        
        Args:
            trades: List of trade objects/dicts
            
        Returns:
            Profit factor (infinity if no losses, 0 if no profits)
        """
        if not trades:
            return 0.0
        
        trades_df = self._trades_to_dataframe(trades)
        total_profit = trades_df[trades_df['pnl'] > 0]['pnl'].sum()
        total_loss = abs(trades_df[trades_df['pnl'] < 0]['pnl'].sum())
        
        if total_loss == 0:
            return float('inf') if total_profit > 0 else 0.0
        
        return float(total_profit / total_loss)
    
    def calculate_calmar_ratio(self, annual_return: float, max_drawdown: float) -> float:
        """
        Calculate Calmar ratio (annual return / maximum drawdown)
        
        Args:
            annual_return: Annualized return (as decimal, e.g., 0.15 for 15%)
            max_drawdown: Maximum drawdown (as decimal, e.g., 0.20 for 20%)
            
        Returns:
            Calmar ratio
        """
        if max_drawdown == 0:
            return 0.0 if annual_return <= 0 else float('inf')
        
        return float(annual_return / abs(max_drawdown))
    
    def build_equity_curve(
        self,
        trades: List,
        initial_capital: float,
        start_date: datetime,
        end_date: datetime
    ) -> pd.Series:
        """
        Build equity curve from trades
        
        Args:
            trades: List of trade objects/dicts
            initial_capital: Starting capital
            start_date: Backtest start date
            end_date: Backtest end date
            
        Returns:
            Series of portfolio values indexed by datetime
        """
        if not trades:
            # Return single point equity curve
            return pd.Series([initial_capital], index=[start_date])
        
        trades_df = self._trades_to_dataframe(trades)
        
        # Sort by timestamp
        trades_df = trades_df.sort_values('timestamp')
        
        # Calculate cumulative P&L
        cumulative_pnl = trades_df['pnl'].cumsum()
        equity_values = initial_capital + cumulative_pnl
        
        # Set index to timestamps
        equity_curve = pd.Series(equity_values.values, index=trades_df['timestamp'].values)
        
        # Add start and end points if not present
        if equity_curve.index[0] != start_date:
            equity_curve = pd.concat([
                pd.Series([initial_capital], index=[start_date]),
                equity_curve
            ])
        
        if equity_curve.index[-1] != end_date:
            final_value = equity_curve.iloc[-1]
            equity_curve = pd.concat([
                equity_curve,
                pd.Series([final_value], index=[end_date])
            ])
        
        # Sort by index to ensure chronological order
        equity_curve = equity_curve.sort_index()
        
        return equity_curve
    
    def _trades_to_dataframe(self, trades: List) -> pd.DataFrame:
        """Convert list of trades to DataFrame"""
        trade_data = []
        
        for trade in trades:
            # Handle both dict and object access
            if isinstance(trade, dict):
                pnl = trade.get('pnl', 0.0)
                timestamp = trade.get('timestamp')
                if timestamp is None:
                    logger.warning("Trade missing timestamp, using current time")
                    timestamp = datetime.now()
                elif isinstance(timestamp, str):
                    timestamp = pd.to_datetime(timestamp)
            else:
                # Object access
                pnl = getattr(trade, 'pnl', 0.0)
                timestamp = getattr(trade, 'timestamp', None)
                if timestamp is None:
                    # Try to get from relationship
                    timestamp = datetime.now()
            
            trade_data.append({
                'pnl': float(pnl) if pnl is not None else 0.0,
                'timestamp': timestamp if timestamp else datetime.now()
            })
        
        df = pd.DataFrame(trade_data)
        if 'timestamp' in df.columns:
            df['timestamp'] = pd.to_datetime(df['timestamp'])
        
        return df
    
    def _calculate_daily_returns(self, equity_curve: pd.Series) -> pd.Series:
        """Calculate daily returns from equity curve"""
        if equity_curve.empty or len(equity_curve) < 2:
            return pd.Series(dtype=float)
        
        # Calculate percentage returns
        returns = equity_curve.pct_change().dropna()
        
        return returns
    
    def _calculate_monthly_returns(self, equity_curve: pd.Series) -> pd.Series:
        """Calculate monthly returns from equity curve"""
        if equity_curve.empty or len(equity_curve) < 2:
            return pd.Series(dtype=float)
        
        # Resample to monthly and calculate returns
        monthly_equity = equity_curve.resample('M').last()
        returns = monthly_equity.pct_change().dropna()
        
        return returns
    
    def _calculate_recovery_time(self, equity_curve: pd.Series, max_drawdown: float, dd_start: datetime) -> Optional[float]:
        """Calculate time to recover from maximum drawdown (in days)"""
        if dd_start is None or equity_curve.empty:
            return None
        
        # Find when equity recovers to the peak value before drawdown
        peak_value = equity_curve.loc[:dd_start].max() if dd_start in equity_curve.index else equity_curve.iloc[0]
        
        # Find recovery point (when equity returns to peak)
        after_dd = equity_curve.loc[dd_start:]
        recovery_idx = after_dd[after_dd >= peak_value].first_valid_index()
        
        if recovery_idx is None:
            # Never recovered
            return None
        
        # Calculate days
        recovery_time = (recovery_idx - dd_start).total_seconds() / (24 * 3600)
        
        return float(recovery_time)
    
    def _estimate_bars(self, start_date: datetime, end_date: datetime) -> int:
        """Estimate total number of bars from date range (approximate)"""
        days = (end_date - start_date).days
        # Approximate: assume ~252 trading days per year, ~6.5 hours per day, ~390 minutes
        # For 5-minute bars: ~78 bars per day
        bars_per_day = 78  # Conservative estimate for 5-minute bars
        return max(1, int(days * bars_per_day))
    
    def _empty_metrics(self, initial_capital: float, start_date: datetime, end_date: datetime) -> BacktestMetrics:
        """Return empty metrics for backtest with no trades"""
        return BacktestMetrics(
            initial_capital=initial_capital,
            final_capital=initial_capital,
            total_return=0.0,
            total_return_pct=0.0,
            total_trades=0,
            winning_trades=0,
            losing_trades=0,
            win_rate=0.0,
            total_profit=0.0,
            total_loss=0.0,
            profit_factor=0.0,
            average_win=0.0,
            average_loss=0.0,
            largest_win=0.0,
            largest_loss=0.0,
            max_drawdown=0.0,
            max_drawdown_pct=0.0,
            max_drawdown_start=None,
            max_drawdown_end=None,
            recovery_time_days=None,
            sharpe_ratio=0.0,
            sortino_ratio=0.0,
            calmar_ratio=0.0,
            average_trade_return=0.0,
            expectancy=0.0,
            total_bars=self._estimate_bars(start_date, end_date),
            start_date=start_date,
            end_date=end_date,
            equity_curve=None,
            monthly_returns=None,
            daily_returns=None,
        )

