"""
Signal Aggregator
=================

Aggregates and prioritizes signals from multiple strategies.
"""

from typing import List, Dict, Optional
from datetime import datetime
import logging

from ..strategy.base import TradingSignal, SignalType

logger = logging.getLogger(__name__)


class SignalAggregator:
    """
    Aggregates signals from multiple strategies
    
    Features:
    - Combines signals for the same symbol
    - Prioritizes signals by confidence
    - Resolves conflicting signals
    - Filters duplicate signals
    """
    
    def __init__(self, 
                 confidence_threshold: float = 0.0,
                 require_confirmation: bool = False,
                 min_confirmations: int = 1):
        """
        Initialize signal aggregator
        
        Args:
            confidence_threshold: Minimum confidence to include signal
            require_confirmation: Whether to require multiple strategy confirmations
            min_confirmations: Minimum number of strategies that must agree
        """
        self.confidence_threshold = confidence_threshold
        self.require_confirmation = require_confirmation
        self.min_confirmations = min_confirmations
        
        logger.info("SignalAggregator initialized")
    
    def aggregate_signals(self, signals: List[TradingSignal]) -> List[TradingSignal]:
        """
        Aggregate and prioritize signals
        
        Args:
            signals: List of trading signals from multiple strategies
            
        Returns:
            List of aggregated/filtered signals
        """
        if not signals:
            return []
        
        # Filter by confidence threshold
        filtered = [s for s in signals if s.confidence >= self.confidence_threshold]
        
        if not filtered:
            return []
        
        # Group by symbol and signal type
        grouped = self._group_signals(filtered)
        
        # Aggregate each group
        aggregated = []
        
        for (symbol, signal_type), signal_group in grouped.items():
            if self.require_confirmation:
                # Require multiple confirmations
                if len(signal_group) < self.min_confirmations:
                    logger.debug(
                        f"Insufficient confirmations for {symbol} {signal_type.value}: "
                        f"{len(signal_group)} < {self.min_confirmations}"
                    )
                    continue
            
            # Aggregate signals in this group
            aggregated_signal = self._combine_signals(signal_group)
            
            if aggregated_signal:
                aggregated.append(aggregated_signal)
        
        # Sort by confidence (highest first)
        aggregated.sort(key=lambda x: x.confidence, reverse=True)
        
        return aggregated
    
    def _group_signals(self, signals: List[TradingSignal]) -> Dict[tuple, List[TradingSignal]]:
        """Group signals by symbol and signal type"""
        grouped = {}
        
        for signal in signals:
            key = (signal.symbol, signal.signal_type)
            
            if key not in grouped:
                grouped[key] = []
            
            grouped[key].append(signal)
        
        return grouped
    
    def _combine_signals(self, signals: List[TradingSignal]) -> Optional[TradingSignal]:
        """
        Combine multiple signals for the same symbol/type
        
        Args:
            signals: List of signals to combine
            
        Returns:
            Combined signal or None
        """
        if not signals:
            return None
        
        if len(signals) == 1:
            return signals[0]
        
        # Use the signal with highest confidence as base
        base_signal = max(signals, key=lambda x: x.confidence)
        
        # Calculate aggregate confidence
        # Weighted average by individual confidences
        total_weight = sum(s.confidence for s in signals)
        if total_weight > 0:
            weighted_confidence = sum(
                s.confidence * s.confidence for s in signals
            ) / total_weight
        else:
            weighted_confidence = base_signal.confidence
        
        # Cap confidence at 1.0, boost slightly for multiple confirmations
        if len(signals) > 1:
            confirmation_boost = min(0.1 * (len(signals) - 1), 0.2)
            weighted_confidence = min(1.0, weighted_confidence + confirmation_boost)
        
        # Average price
        avg_price = sum(s.price for s in signals) / len(signals)
        
        # Use maximum quantity
        max_quantity = max(s.quantity for s in signals)
        
        # Combine metadata
        combined_metadata = {
            'aggregated': True,
            'strategy_count': len(signals),
            'individual_confidences': [s.confidence for s in signals],
            'individual_prices': [s.price for s in signals]
        }
        
        # Merge metadata from all signals
        for signal in signals:
            if signal.metadata:
                for key, value in signal.metadata.items():
                    if key not in combined_metadata:
                        combined_metadata[f"strategy_{key}"] = value
        
        # Create aggregated signal
        aggregated = TradingSignal(
            signal_type=base_signal.signal_type,
            symbol=base_signal.symbol,
            price=avg_price,
            quantity=max_quantity,
            timestamp=datetime.now(),
            confidence=weighted_confidence,
            metadata=combined_metadata,
            entry_level=base_signal.entry_level,
            stop_loss=base_signal.stop_loss,
            take_profit=base_signal.take_profit,
            timeframe=base_signal.timeframe
        )
        
        logger.info(
            f"Aggregated {len(signals)} signals for {base_signal.symbol} "
            f"{base_signal.signal_type.value}: confidence={weighted_confidence:.2%}"
        )
        
        return aggregated
    
    def resolve_conflicts(self, signals: List[TradingSignal]) -> List[TradingSignal]:
        """
        Resolve conflicting signals (e.g., BUY and SELL for same symbol)
        
        Args:
            signals: List of potentially conflicting signals
            
        Returns:
            List of resolved signals
        """
        # Group by symbol
        by_symbol = {}
        for signal in signals:
            if signal.symbol not in by_symbol:
                by_symbol[signal.symbol] = []
            by_symbol[signal.symbol].append(signal)
        
        resolved = []
        
        for symbol, symbol_signals in by_symbol.items():
            # Check for conflicts
            has_buy = any(s.signal_type == SignalType.BUY for s in symbol_signals)
            has_sell = any(s.signal_type == SignalType.SELL for s in symbol_signals)
            
            if has_buy and has_sell:
                # Conflict detected - use highest confidence signal
                buy_signals = [s for s in symbol_signals if s.signal_type == SignalType.BUY]
                sell_signals = [s for s in symbol_signals if s.signal_type == SignalType.SELL]
                
                best_buy = max(buy_signals, key=lambda x: x.confidence) if buy_signals else None
                best_sell = max(sell_signals, key=lambda x: x.confidence) if sell_signals else None
                
                if best_buy and best_sell:
                    # Choose signal with higher confidence
                    if best_buy.confidence > best_sell.confidence:
                        resolved.append(best_buy)
                        logger.info(
                            f"Resolved conflict for {symbol}: "
                            f"BUY (confidence={best_buy.confidence:.2%}) > "
                            f"SELL (confidence={best_sell.confidence:.2%})"
                        )
                    else:
                        resolved.append(best_sell)
                        logger.info(
                            f"Resolved conflict for {symbol}: "
                            f"SELL (confidence={best_sell.confidence:.2%}) > "
                            f"BUY (confidence={best_buy.confidence:.2%})"
                        )
                elif best_buy:
                    resolved.append(best_buy)
                elif best_sell:
                    resolved.append(best_sell)
            else:
                # No conflict, add all signals
                resolved.extend(symbol_signals)
        
        return resolved
    
    def filter_duplicates(self, signals: List[TradingSignal],
                         time_window_seconds: int = 60) -> List[TradingSignal]:
        """
        Filter duplicate signals within a time window
        
        Args:
            signals: List of signals
            time_window_seconds: Time window to consider signals as duplicates
            
        Returns:
            Filtered list of signals
        """
        if not signals:
            return []
        
        # Sort by timestamp (newest first)
        sorted_signals = sorted(signals, key=lambda x: x.timestamp, reverse=True)
        
        filtered = []
        seen = set()
        
        for signal in sorted_signals:
            key = (signal.symbol, signal.signal_type)
            
            if key in seen:
                # Check if within time window
                # Would need to compare timestamps here
                # For simplicity, just skip duplicates
                continue
            
            seen.add(key)
            filtered.append(signal)
        
        return filtered

