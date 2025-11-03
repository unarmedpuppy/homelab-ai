"""
Trading Scheduler
=================

Background scheduler that automatically evaluates strategies, generates signals,
and executes trades on configurable intervals.
"""

import asyncio
import logging
from typing import Dict, List, Optional, Set
from datetime import datetime, time
from enum import Enum
from dataclasses import dataclass

from ...config.settings import settings
from ...core.evaluation import StrategyEvaluator
from ...data.brokers.ibkr_client import IBKRClient, IBKRManager, OrderSide
from ...core.risk import RiskManager, get_risk_manager
from ...data.providers.market_data import DataProviderManager
from ...api.routes.strategies import get_evaluator
from ...api.routes.trading import get_ibkr_manager

logger = logging.getLogger(__name__)


class SchedulerState(Enum):
    """Scheduler state"""
    STOPPED = "stopped"
    RUNNING = "running"
    PAUSED = "paused"
    ERROR = "error"


@dataclass
class SchedulerStats:
    """Scheduler statistics"""
    evaluations_run: int = 0
    signals_generated: int = 0
    trades_executed: int = 0
    trades_rejected: int = 0
    errors: int = 0
    last_evaluation: Optional[datetime] = None
    last_trade: Optional[datetime] = None
    start_time: Optional[datetime] = None


class TradingScheduler:
    """
    Automatic trading scheduler
    
    Features:
    - Periodic strategy evaluation
    - Automatic signal generation
    - Trade execution pipeline
    - Position exit monitoring
    - Error handling and recovery
    - Market hours checking
    """
    
    def __init__(
        self,
        evaluator: Optional[StrategyEvaluator] = None,
        ibkr_manager: Optional[IBKRManager] = None,
        risk_manager: Optional[RiskManager] = None,
        data_provider: Optional[DataProviderManager] = None
    ):
        """
        Initialize trading scheduler
        
        Args:
            evaluator: Strategy evaluator instance
            ibkr_manager: IBKR manager instance
            risk_manager: Risk manager instance
            data_provider: Market data provider manager
        """
        self.config = settings.scheduler
        self.evaluator = evaluator or get_evaluator()
        self.ibkr_manager = ibkr_manager
        self.risk_manager = risk_manager or get_risk_manager()
        self.data_provider = data_provider
        
        # State
        self.state = SchedulerState.STOPPED
        self.stats = SchedulerStats()
        
        # Background tasks
        self._evaluation_task: Optional[asyncio.Task] = None
        self._exit_check_task: Optional[asyncio.Task] = None
        self._running = False
        
        # Active positions being monitored (strategy_id -> symbol)
        self._monitored_positions: Dict[str, str] = {}
        
        logger.info("TradingScheduler initialized")
    
    def _get_ibkr_manager(self) -> Optional[IBKRManager]:
        """Get IBKR manager instance"""
        if self.ibkr_manager:
            return self.ibkr_manager
        try:
            return get_ibkr_manager()
        except Exception as e:
            logger.debug(f"Could not get IBKR manager: {e}")
            return None
    
    def _is_market_hours(self) -> bool:
        """
        Check if current time is within market hours (9:30 AM - 4:00 PM ET)
        
        Returns:
            True if market is open, False otherwise
        """
        if not self.config.market_hours_only:
            return True
        
        # Simple check: 9:30 AM - 4:00 PM ET (13:30 - 20:00 UTC)
        # TODO: Implement proper timezone handling and holiday checking
        now = datetime.now()
        market_open = time(13, 30)  # 9:30 AM ET in UTC
        market_close = time(20, 0)   # 4:00 PM ET in UTC
        current_time = now.time()
        
        # Check if it's a weekday (Monday=0, Sunday=6)
        if now.weekday() >= 5:  # Saturday or Sunday
            return False
        
        return market_open <= current_time <= market_close
    
    def _can_run(self) -> bool:
        """
        Check if scheduler can run
        
        Returns:
            True if conditions are met, False otherwise
        """
        # Check if enabled
        if not self.config.enabled:
            logger.debug("Scheduler is disabled in config")
            return False
        
        # Check IBKR connection if required
        if self.config.require_ibkr_connection:
            ibkr_manager = self._get_ibkr_manager()
            if not ibkr_manager or not ibkr_manager.is_connected:
                logger.debug("IBKR not connected, cannot run scheduler")
                return False
        
        # Check market hours
        if not self._is_market_hours():
            logger.debug("Outside market hours")
            return False
        
        return True
    
    async def _evaluate_strategies(self):
        """
        Evaluate all enabled strategies and execute trades
        
        This is the main evaluation loop that runs periodically.
        """
        if not self._can_run():
            return
        
        try:
            logger.debug("Starting strategy evaluation cycle")
            self.stats.evaluations_run += 1
            self.stats.last_evaluation = datetime.now()
            
            # Get IBKR manager and client
            ibkr_manager = self._get_ibkr_manager()
            if not ibkr_manager:
                logger.warning("IBKR manager not available, skipping evaluation")
                return
            
            client = await ibkr_manager.get_client()
            if not client:
                logger.warning("IBKR client not available, skipping evaluation")
                return
            
            # Get current positions from IBKR
            try:
                positions = await client.get_positions()
                position_map = {pos.symbol: pos for pos in positions}
            except Exception as e:
                logger.warning(f"Error fetching positions: {e}")
                position_map = {}
            
            # Update evaluator with current positions
            for strategy_id, state in self.evaluator.strategies.items():
                if not state.enabled:
                    continue
                
                symbol = state.symbol
                if symbol in position_map:
                    # Convert broker position to strategy position
                    broker_pos = position_map[symbol]
                    from ...core.strategy.base import Position
                    state.current_position = Position(
                        symbol=symbol,
                        quantity=broker_pos.quantity,
                        entry_price=broker_pos.average_price,
                        entry_time=broker_pos.timestamp
                    )
                    self._monitored_positions[strategy_id] = symbol
                else:
                    state.current_position = None
                    self._monitored_positions.pop(strategy_id, None)
            
            # Fetch market data for all active symbols
            symbols = set(state.symbol for state in self.evaluator.strategies.values() if state.enabled)
            market_data: Dict[str, any] = {}
            
            if self.data_provider:
                for symbol in symbols:
                    try:
                        # Fetch historical data for strategy evaluation
                        # Using default timeframe of 5m and 100 bars
                        data = await self.data_provider.get_historical_data(
                            symbol=symbol,
                            timeframe="5m",
                            lookback_bars=100
                        )
                        if data is not None and len(data) > 0:
                            market_data[symbol] = data
                    except Exception as e:
                        logger.warning(f"Error fetching market data for {symbol}: {e}")
            
            # Evaluate all enabled strategies
            signals = []
            for strategy_id, state in self.evaluator.strategies.items():
                if not state.enabled:
                    continue
                
                symbol = state.symbol
                if symbol not in market_data:
                    logger.debug(f"No market data for {symbol}, skipping {strategy_id}")
                    continue
                
                try:
                    signal = self.evaluator.evaluate_strategy(strategy_id, market_data[symbol])
                    if signal and signal.signal_type.value != "HOLD":
                        signals.append((strategy_id, signal))
                        self.stats.signals_generated += 1
                except Exception as e:
                    logger.error(f"Error evaluating strategy {strategy_id}: {e}", exc_info=True)
                    self.stats.errors += 1
            
            # Execute trades for valid signals
            for strategy_id, signal in signals:
                try:
                    # Check confidence threshold
                    if signal.confidence and signal.confidence < self.config.min_confidence:
                        logger.debug(
                            f"Signal confidence {signal.confidence:.2%} below threshold "
                            f"{self.config.min_confidence:.2%}, skipping"
                        )
                        continue
                    
                    # Execute trade
                    await self._execute_signal(strategy_id, signal)
                    
                except Exception as e:
                    logger.error(f"Error executing signal for {strategy_id}: {e}", exc_info=True)
                    self.stats.errors += 1
                    self.stats.trades_rejected += 1
            
        except Exception as e:
            logger.error(f"Error in strategy evaluation cycle: {e}", exc_info=True)
            self.stats.errors += 1
    
    async def _execute_signal(self, strategy_id: str, signal):
        """
        Execute a trading signal
        
        Args:
            strategy_id: Strategy identifier
            signal: TradingSignal to execute
        """
        try:
            ibkr_manager = self._get_ibkr_manager()
            if not ibkr_manager:
                raise RuntimeError("IBKR manager not available")
            
            client = await ibkr_manager.get_client()
            if not client:
                raise RuntimeError("IBKR client not available")
            
            # Get account ID (default to primary account)
            account_id = 1  # TODO: Get from settings or account management
            
            # Prepare trade request
            side = "BUY" if signal.signal_type.value == "BUY" else "SELL"
            
            # Check if we have enough concurrent trades
            if len(self._monitored_positions) >= self.config.max_concurrent_trades:
                logger.warning(
                    f"Max concurrent trades ({self.config.max_concurrent_trades}) reached, "
                    f"skipping signal for {signal.symbol}"
                )
                self.stats.trades_rejected += 1
                return
            
            # Get account ID (default to primary account - TODO: make configurable)
            account_id = 1
            
            # Validate trade with risk manager
            try:
                validation = await self.risk_manager.validate_trade(
                    account_id=account_id,
                    symbol=signal.symbol,
                    side=side,
                    quantity=signal.quantity,
                    price_per_share=signal.price,
                    confidence_score=signal.confidence,
                    will_create_day_trade=False  # TODO: Detect day trades properly
                )
                
                if not validation.can_proceed:
                    logger.warning(
                        f"Trade rejected by risk manager: {side} {signal.quantity} {signal.symbol} - "
                        f"{validation.compliance_check.message}"
                    )
                    self.stats.trades_rejected += 1
                    return
                
                # Use position size from validation if calculated
                quantity = signal.quantity
                if validation.position_size and validation.position_size.size_shares > 0:
                    quantity = validation.position_size.size_shares
                
                if not quantity or quantity <= 0:
                    logger.warning(f"Invalid quantity calculated: {quantity}")
                    self.stats.trades_rejected += 1
                    return
                
            except Exception as e:
                logger.error(f"Error validating trade with risk manager: {e}", exc_info=True)
                self.stats.trades_rejected += 1
                return
            
            # Execute trade via IBKR
            contract = client.create_contract(signal.symbol)
            order_side = OrderSide.BUY if side == "BUY" else OrderSide.SELL
            
            # Place order (use limit if price specified, otherwise market)
            if signal.order_type and hasattr(signal.order_type, 'value') and signal.order_type.value == "LIMIT":
                order = await client.place_limit_order(
                    contract, order_side, quantity, signal.price
                )
            else:
                order = await client.place_market_order(
                    contract, order_side, quantity
                )
            
            logger.info(
                f"Trade executed: {side} {quantity} {signal.symbol} @ ${signal.price:.2f} "
                f"(strategy: {strategy_id}, confidence: {signal.confidence:.2%}, order_id: {order.order_id})"
            )
            
            self.stats.trades_executed += 1
            self.stats.last_trade = datetime.now()
            
            # Update monitored positions
            if side == "BUY":
                self._monitored_positions[strategy_id] = signal.symbol
            
        except Exception as e:
            logger.error(f"Error executing signal: {e}", exc_info=True)
            self.stats.trades_rejected += 1
            raise
    
    async def _check_exit_conditions(self):
        """
        Check exit conditions for all monitored positions
        
        This runs on a separate interval to monitor existing positions.
        """
        if not self._can_run():
            return
        
        try:
            # Get IBKR positions
            ibkr_manager = self._get_ibkr_manager()
            if not ibkr_manager:
                return
            
            client = await ibkr_manager.get_client()
            if not client:
                return
            
            # Check exit conditions for each monitored position
            for strategy_id, symbol in list(self._monitored_positions.items()):
                if strategy_id not in self.evaluator.strategies:
                    continue
                
                state = self.evaluator.strategies[strategy_id]
                if not state.current_position:
                    continue
                
                try:
                    # Fetch latest market data
                    if self.data_provider:
                        data = await self.data_provider.get_historical_data(
                            symbol=symbol,
                            timeframe="5m",
                            lookback_bars=100
                        )
                        
                        if data is not None and len(data) > 0:
                            # Check exit conditions
                            exit_signal = self.evaluator.check_exit_conditions(
                                strategy_id, data
                            )
                            
                            if exit_signal:
                                await self._execute_signal(strategy_id, exit_signal)
                                
                                # Remove from monitored if fully exited
                                if exit_signal.signal_type.value == "SELL" and exit_signal.quantity == state.current_position.quantity:
                                    self._monitored_positions.pop(strategy_id, None)
                    
                except Exception as e:
                    logger.error(f"Error checking exit for {strategy_id}: {e}", exc_info=True)
        
        except Exception as e:
            logger.error(f"Error in exit condition check: {e}", exc_info=True)
    
    async def _evaluation_loop(self):
        """Background task for strategy evaluation"""
        while self._running:
            try:
                await self._evaluate_strategies()
                
                # Sleep for evaluation interval
                await asyncio.sleep(self.config.evaluation_interval)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in evaluation loop: {e}", exc_info=True)
                self.stats.errors += 1
                # Sleep briefly before retrying
                await asyncio.sleep(5)
    
    async def _exit_check_loop(self):
        """Background task for exit condition checking"""
        while self._running:
            try:
                await self._check_exit_conditions()
                
                # Sleep for exit check interval
                await asyncio.sleep(self.config.exit_check_interval)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in exit check loop: {e}", exc_info=True)
                self.stats.errors += 1
                # Sleep briefly before retrying
                await asyncio.sleep(5)
    
    async def start(self):
        """Start the scheduler"""
        if self.state == SchedulerState.RUNNING:
            logger.warning("Scheduler already running")
            return
        
        if not self.config.enabled:
            logger.warning("Scheduler is disabled in configuration")
            return
        
        try:
            self._running = True
            self.state = SchedulerState.RUNNING
            self.stats.start_time = datetime.now()
            
            # Start background tasks
            self._evaluation_task = asyncio.create_task(self._evaluation_loop())
            self._exit_check_task = asyncio.create_task(self._exit_check_loop())
            
            logger.info(
                f"Trading scheduler started (evaluation: {self.config.evaluation_interval}s, "
                f"exit check: {self.config.exit_check_interval}s)"
            )
        
        except Exception as e:
            logger.error(f"Error starting scheduler: {e}", exc_info=True)
            self.state = SchedulerState.ERROR
            self._running = False
            raise
    
    async def stop(self):
        """Stop the scheduler"""
        if self.state == SchedulerState.STOPPED:
            return
        
        try:
            self._running = False
            self.state = SchedulerState.STOPPED
            
            # Cancel background tasks
            if self._evaluation_task:
                self._evaluation_task.cancel()
                try:
                    await self._evaluation_task
                except asyncio.CancelledError:
                    pass
            
            if self._exit_check_task:
                self._exit_check_task.cancel()
                try:
                    await self._exit_check_task
                except asyncio.CancelledError:
                    pass
            
            logger.info("Trading scheduler stopped")
        
        except Exception as e:
            logger.error(f"Error stopping scheduler: {e}", exc_info=True)
    
    async def pause(self):
        """Pause the scheduler (maintains state)"""
        if self.state != SchedulerState.RUNNING:
            logger.warning(f"Cannot pause scheduler in state: {self.state.value}")
            return
        
        self.state = SchedulerState.PAUSED
        logger.info("Trading scheduler paused")
    
    async def resume(self):
        """Resume the scheduler"""
        if self.state != SchedulerState.PAUSED:
            logger.warning(f"Cannot resume scheduler in state: {self.state.value}")
            return
        
        self.state = SchedulerState.RUNNING
        logger.info("Trading scheduler resumed")
    
    def get_status(self) -> Dict:
        """Get scheduler status and statistics"""
        uptime = None
        if self.stats.start_time:
            uptime = (datetime.now() - self.stats.start_time).total_seconds()
        
        return {
            "state": self.state.value,
            "enabled": self.config.enabled,
            "config": {
                "evaluation_interval": self.config.evaluation_interval,
                "exit_check_interval": self.config.exit_check_interval,
                "min_confidence": self.config.min_confidence,
                "max_concurrent_trades": self.config.max_concurrent_trades,
                "market_hours_only": self.config.market_hours_only,
            },
            "stats": {
                "evaluations_run": self.stats.evaluations_run,
                "signals_generated": self.stats.signals_generated,
                "trades_executed": self.stats.trades_executed,
                "trades_rejected": self.stats.trades_rejected,
                "errors": self.stats.errors,
                "monitored_positions": len(self._monitored_positions),
                "last_evaluation": self.stats.last_evaluation.isoformat() if self.stats.last_evaluation else None,
                "last_trade": self.stats.last_trade.isoformat() if self.stats.last_trade else None,
                "uptime_seconds": uptime,
            },
            "can_run": self._can_run(),
            "is_market_hours": self._is_market_hours(),
            "ibkr_connected": self._get_ibkr_manager() and self._get_ibkr_manager().is_connected if self._get_ibkr_manager() else False,
        }


# Global scheduler instance
_scheduler: Optional[TradingScheduler] = None


def get_scheduler() -> TradingScheduler:
    """Get or create global scheduler instance"""
    global _scheduler
    if _scheduler is None:
        _scheduler = TradingScheduler()
    return _scheduler

