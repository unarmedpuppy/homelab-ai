"""
Strategy Evaluator
==================

Real-time strategy evaluation engine that manages multiple strategies,
evaluates them against current market data, and generates trading signals.
"""

from typing import Dict, List, Optional, Callable, Any
from datetime import datetime
import pandas as pd
import logging
from dataclasses import dataclass

from ..strategy.base import BaseStrategy, TradingSignal, Position, SignalType
from ..strategy.registry import get_registry
from ..data.providers.market_data import DataProviderManager

logger = logging.getLogger(__name__)


@dataclass
class StrategyState:
    """State tracking for an active strategy"""
    strategy: BaseStrategy
    symbol: str
    enabled: bool
    last_evaluation: Optional[datetime] = None
    last_signal: Optional[TradingSignal] = None
    current_position: Optional[Position] = None
    evaluation_count: int = 0
    signals_generated: int = 0


class StrategyEvaluator:
    """
    Evaluates strategies against real-time market data
    
    Features:
    - Manages multiple active strategies
    - Evaluates strategies on demand or schedule
    - Filters and validates signals
    - Tracks strategy state and performance
    - Integrates with data providers
    """
    
    def __init__(self, data_provider: Optional[DataProviderManager] = None):
        """
        Initialize the strategy evaluator
        
        Args:
            data_provider: Optional data provider manager for fetching market data
        """
        self.data_provider = data_provider
        self.strategies: Dict[str, StrategyState] = {}
        self.registry = get_registry()
        
        # Signal callbacks
        self.signal_callbacks: List[Callable[[TradingSignal], None]] = []
        
        # Evaluation filters
        self.min_confidence = 0.0
        self.require_volume = False
        
        # Sentiment aggregator (optional, lazy-loaded)
        self._sentiment_aggregator = None
        
        logger.info("StrategyEvaluator initialized")
    
    def _get_sentiment_aggregator(self):
        """Lazy-load sentiment aggregator if needed"""
        if self._sentiment_aggregator is None:
            try:
                from ...data.providers.sentiment import SentimentAggregator
                self._sentiment_aggregator = SentimentAggregator(persist_to_db=True)
                logger.debug("Sentiment aggregator initialized")
            except Exception as e:
                logger.warning(f"Failed to initialize sentiment aggregator: {e}")
                return None
        return self._sentiment_aggregator
    
    def _fetch_sentiment(self, symbol: str, hours: int = 24):
        """
        Fetch aggregated sentiment for a symbol
        
        Args:
            symbol: Stock symbol
            hours: Hours of historical data to analyze
            
        Returns:
            AggregatedSentiment object or None
        """
        aggregator = self._get_sentiment_aggregator()
        if aggregator is None:
            return None
        
        try:
            return aggregator.get_aggregated_sentiment(symbol, hours=hours)
        except Exception as e:
            logger.warning(f"Failed to fetch sentiment for {symbol}: {e}")
            return None
    
    def _fetch_confluence(self, symbol: str, market_data: pd.DataFrame, hours: int = 24):
        """
        Fetch confluence score for a symbol
        
        Args:
            symbol: Stock symbol
            market_data: Market data DataFrame
            hours: Hours of sentiment data to analyze
            
        Returns:
            ConfluenceScore object or None
        """
        try:
            from ...core.confluence import ConfluenceCalculator
            calculator = ConfluenceCalculator()
            return calculator.calculate_confluence(symbol, market_data, sentiment_hours=hours)
        except Exception as e:
            logger.warning(f"Failed to fetch confluence for {symbol}: {e}")
            return None
    
    def add_strategy(self, strategy_name: str, config: Dict[str, Any],
                    enabled: bool = True) -> StrategyState:
        """
        Add a strategy to be evaluated
        
        Args:
            strategy_name: Name of strategy (must be registered)
            config: Strategy configuration dictionary
            enabled: Whether strategy is enabled for evaluation
            
        Returns:
            StrategyState object
            
        Raises:
            ValueError: If strategy not found in registry
        """
        if not self.registry.is_registered(strategy_name):
            available = ', '.join(self.registry.list_strategies())
            raise ValueError(
                f"Strategy '{strategy_name}' not found. Available: {available}"
            )
        
        strategy = self.registry.get_strategy(strategy_name, config)
        
        state = StrategyState(
            strategy=strategy,
            symbol=config.get('symbol', 'UNKNOWN'),
            enabled=enabled
        )
        
        strategy_id = f"{strategy_name}_{config.get('symbol', 'UNKNOWN')}"
        self.strategies[strategy_id] = state
        
        logger.info(f"Added strategy: {strategy_id} (enabled: {enabled})")
        return state
    
    def remove_strategy(self, strategy_id: str):
        """Remove a strategy from evaluation"""
        if strategy_id in self.strategies:
            del self.strategies[strategy_id]
            logger.info(f"Removed strategy: {strategy_id}")
        else:
            logger.warning(f"Strategy not found: {strategy_id}")
    
    def enable_strategy(self, strategy_id: str):
        """Enable a strategy for evaluation"""
        if strategy_id in self.strategies:
            self.strategies[strategy_id].enabled = True
            logger.info(f"Enabled strategy: {strategy_id}")
    
    def disable_strategy(self, strategy_id: str):
        """Disable a strategy (keep but don't evaluate)"""
        if strategy_id in self.strategies:
            self.strategies[strategy_id].enabled = False
            logger.info(f"Disabled strategy: {strategy_id}")
    
    async def fetch_market_data(self, symbol: str, timeframe: str,
                               lookback_bars: int = 100) -> pd.DataFrame:
        """
        Fetch market data for a symbol
        
        Args:
            symbol: Stock symbol
            timeframe: Timeframe (e.g., '5m', '1h', '1d')
            lookback_bars: Number of bars to fetch
            
        Returns:
            DataFrame with OHLCV data
        """
        if self.data_provider:
            # Use data provider if available
            try:
                data = await self.data_provider.get_historical_data(
                    symbol=symbol,
                    timeframe=timeframe,
                    lookback=lookback_bars
                )
                return data
            except Exception as e:
                logger.error(f"Error fetching data from provider: {e}")
        
        # Fallback: return empty DataFrame
        logger.warning(f"No data provider available or fetch failed for {symbol}")
        return pd.DataFrame()
    
    def evaluate_strategy(self, strategy_id: str, 
                         data: Optional[pd.DataFrame] = None) -> Optional[TradingSignal]:
        """
        Evaluate a single strategy and generate signal
        
        Args:
            strategy_id: Strategy identifier
            data: Optional market data (will fetch if not provided)
            
        Returns:
            TradingSignal or None if no signal
        """
        if strategy_id not in self.strategies:
            logger.warning(f"Strategy not found: {strategy_id}")
            return None
        
        state = self.strategies[strategy_id]
        
        if not state.enabled:
            return None
        
        # Fetch data if not provided
        if data is None:
            # Note: This is synchronous, but in production you'd want async
            logger.warning(f"No data provided for {strategy_id}, cannot evaluate")
            return None
        
        if len(data) == 0:
            logger.warning(f"Empty data for {strategy_id}")
            return None
        
        try:
            # Fetch sentiment if strategy uses it
            sentiment = None
            if state.strategy.use_sentiment:
                sentiment = self._fetch_sentiment(state.symbol)
            
            # Generate signal
            signal = state.strategy.generate_signal(data, state.current_position, sentiment)
            
            # Apply sentiment filtering if sentiment was used
            if sentiment is not None and hasattr(state.strategy, '_apply_sentiment_filter'):
                signal = state.strategy._apply_sentiment_filter(signal, sentiment)
            
            # Fetch and apply confluence filtering if strategy uses it
            if state.strategy.use_confluence and hasattr(state.strategy, '_apply_confluence_filter'):
                confluence_score = self._fetch_confluence(state.symbol, data)
                if confluence_score is not None:
                    signal = state.strategy._apply_confluence_filter(signal, confluence_score)
            
            # Apply events/earnings filtering if enabled
            if state.strategy.use_events_filter and hasattr(state.strategy, '_apply_events_filter'):
                signal = state.strategy._apply_events_filter(signal)
            
            # Update state
            state.last_evaluation = datetime.now()
            state.evaluation_count += 1
            
            if signal.signal_type != SignalType.HOLD:
                state.signals_generated += 1
                state.last_signal = signal
                
                # Filter signal
                if self._should_execute_signal(signal, state):
                    logger.info(
                        f"Signal generated: {strategy_id} - {signal.signal_type.value} "
                        f"@ ${signal.price:.2f} (confidence: {signal.confidence:.2%})"
                    )
                    return signal
                else:
                    logger.debug(
                        f"Signal filtered: {strategy_id} - {signal.signal_type.value} "
                        f"(confidence: {signal.confidence:.2%} < {self.min_confidence:.2%})"
                    )
            
            return None
            
        except Exception as e:
            logger.error(f"Error evaluating strategy {strategy_id}: {e}", exc_info=True)
            return None
    
    def evaluate_all_strategies(self, 
                               market_data: Optional[Dict[str, pd.DataFrame]] = None) -> List[TradingSignal]:
        """
        Evaluate all enabled strategies
        
        Args:
            market_data: Optional dictionary mapping symbol -> DataFrame
                        If not provided, will fetch data for each strategy
            
        Returns:
            List of TradingSignal objects
        """
        signals = []
        
        for strategy_id, state in self.strategies.items():
            if not state.enabled:
                continue
            
            symbol = state.symbol
            
            # Get data for this symbol
            if market_data and symbol in market_data:
                data = market_data[symbol]
            else:
                # Would need to fetch - skipping for now
                logger.debug(f"No data available for {symbol}, skipping {strategy_id}")
                continue
            
            signal = self.evaluate_strategy(strategy_id, data)
            
            if signal:
                signals.append(signal)
                # Trigger callbacks
                for callback in self.signal_callbacks:
                    try:
                        callback(signal)
                    except Exception as e:
                        logger.error(f"Error in signal callback: {e}")
        
        return signals
    
    def update_position(self, strategy_id: str, position: Optional[Position]):
        """
        Update the current position for a strategy
        
        Args:
            strategy_id: Strategy identifier
            position: Current position or None
        """
        if strategy_id in self.strategies:
            self.strategies[strategy_id].current_position = position
            logger.debug(f"Updated position for {strategy_id}: {position}")
    
    def check_exit_conditions(self, strategy_id: str, 
                             data: Optional[pd.DataFrame] = None) -> Optional[TradingSignal]:
        """
        Check if current position should be exited
        
        Args:
            strategy_id: Strategy identifier
            data: Market data (optional)
            
        Returns:
            SELL signal if exit conditions met, None otherwise
        """
        if strategy_id not in self.strategies:
            return None
        
        state = self.strategies[strategy_id]
        
        if not state.current_position or state.current_position.quantity == 0:
            return None
        
        if data is None or len(data) == 0:
            return None
        
        try:
            should_exit, reason = state.strategy.should_exit(state.current_position, data)
            
            if should_exit:
                current_price = float(data['close'].iloc[-1])
                
                signal = state.strategy._create_sell_signal(
                    price=current_price,
                    quantity=state.current_position.quantity,
                    confidence=1.0,
                    exit_reason=reason,
                    metadata={
                        'exit_reason': reason.value,
                        'entry_price': state.current_position.entry_price,
                        'pnl_pct': state.current_position.unrealized_pnl_pct
                    }
                )
                
                logger.info(
                    f"Exit signal: {strategy_id} - {reason.value} "
                    f"@ ${current_price:.2f}"
                )
                
                return signal
            
            return None
            
        except Exception as e:
            logger.error(f"Error checking exit conditions for {strategy_id}: {e}", exc_info=True)
            return None
    
    def _should_execute_signal(self, signal: TradingSignal, state: StrategyState) -> bool:
        """
        Determine if a signal should be executed based on filters
        
        Args:
            signal: Trading signal
            state: Strategy state
            
        Returns:
            True if signal should be executed
        """
        # Minimum confidence filter
        if signal.confidence < self.min_confidence:
            return False
        
        # Volume confirmation if required
        if self.require_volume:
            # Would check volume data here
            pass
        
        return True
    
    def add_signal_callback(self, callback: Callable[[TradingSignal], None]):
        """
        Add a callback function to be called when signals are generated
        
        Args:
            callback: Function that takes a TradingSignal as argument
        """
        self.signal_callbacks.append(callback)
        logger.debug(f"Added signal callback: {callback}")
    
    def remove_signal_callback(self, callback: Callable[[TradingSignal], None]):
        """Remove a signal callback"""
        if callback in self.signal_callbacks:
            self.signal_callbacks.remove(callback)
    
    def get_strategy_state(self, strategy_id: str) -> Optional[StrategyState]:
        """Get current state of a strategy"""
        return self.strategies.get(strategy_id)
    
    def list_strategies(self) -> List[str]:
        """List all strategy IDs"""
        return list(self.strategies.keys())
    
    def get_evaluation_stats(self) -> Dict[str, Any]:
        """Get evaluation statistics"""
        stats = {
            'total_strategies': len(self.strategies),
            'enabled_strategies': sum(1 for s in self.strategies.values() if s.enabled),
            'total_evaluations': sum(s.evaluation_count for s in self.strategies.values()),
            'total_signals': sum(s.signals_generated for s in self.strategies.values()),
            'strategies': {}
        }
        
        for strategy_id, state in self.strategies.items():
            stats['strategies'][strategy_id] = {
                'enabled': state.enabled,
                'evaluations': state.evaluation_count,
                'signals': state.signals_generated,
                'last_evaluation': state.last_evaluation.isoformat() if state.last_evaluation else None,
                'has_position': state.current_position is not None
            }
        
        return stats

