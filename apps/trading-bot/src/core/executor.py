"""
Order Executor (T10: Strategy-to-Execution Pipeline)
====================================================

Connects trading signals from strategies to IBKR order execution.
Handles signal validation, risk checks, and order placement with full audit trail.
"""

import logging
from typing import Optional, Dict, Any, List
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum

from .strategy.base import TradingSignal, SignalType
from .risk import RiskManager, PreTradeValidationResult, get_risk_manager
from ..data.brokers.ibkr_client import IBKRClient, OrderSide, BrokerOrder
from ..data.database.models import TradeSide

logger = logging.getLogger(__name__)

# Lazy import for metrics to avoid circular dependencies
_metrics_module = None


def _get_metrics():
    """Lazy load metrics module."""
    global _metrics_module
    if _metrics_module is None:
        try:
            from ..utils import metrics as m
            _metrics_module = m
        except ImportError:
            _metrics_module = None
    return _metrics_module


class ExecutionStatus(Enum):
    """Execution outcome status"""
    SUCCESS = "success"
    REJECTED_VALIDATION = "rejected_validation"  # Signal failed basic validation
    REJECTED_COMPLIANCE = "rejected_compliance"  # Failed compliance checks
    REJECTED_RISK = "rejected_risk"  # Failed portfolio risk checks
    REJECTED_DRY_RUN = "rejected_dry_run"  # Would have executed but dry-run mode
    FAILED_ORDER = "failed_order"  # Order placement failed
    FAILED_BROKER = "failed_broker"  # Broker connection failed


@dataclass
class ExecutionContext:
    """Context for order execution"""
    account_id: int
    strategy_name: str
    dry_run: bool = False
    order_type: str = "MARKET"  # MARKET or LIMIT
    limit_price: Optional[float] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ExecutionAuditLog:
    """
    Complete audit trail for signal execution decision.

    Records the full chain: Signal -> Validation -> Risk Check -> Order -> Result
    """
    # Request info
    signal: TradingSignal
    context: ExecutionContext
    timestamp: datetime = field(default_factory=datetime.now)

    # Validation results
    status: ExecutionStatus = ExecutionStatus.SUCCESS
    validation_passed: bool = False
    validation_messages: List[str] = field(default_factory=list)

    # Risk check results
    risk_check_passed: bool = False
    risk_validation: Optional[PreTradeValidationResult] = None
    risk_score: float = 0.0
    adjusted_quantity: Optional[int] = None

    # Order execution results
    order_placed: bool = False
    broker_order: Optional[BrokerOrder] = None
    order_id: Optional[int] = None

    # Final outcome
    final_quantity: int = 0
    final_price: Optional[float] = None
    error_message: Optional[str] = None
    execution_time_ms: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for logging/storage"""
        return {
            "timestamp": self.timestamp.isoformat(),
            "status": self.status.value,
            "signal": {
                "type": self.signal.signal_type.value,
                "symbol": self.signal.symbol,
                "price": self.signal.price,
                "quantity": self.signal.quantity,
                "confidence": self.signal.confidence,
                "stop_loss": self.signal.stop_loss,
                "take_profit": self.signal.take_profit,
            },
            "context": {
                "account_id": self.context.account_id,
                "strategy_name": self.context.strategy_name,
                "dry_run": self.context.dry_run,
                "order_type": self.context.order_type,
            },
            "validation": {
                "passed": self.validation_passed,
                "messages": self.validation_messages,
            },
            "risk": {
                "passed": self.risk_check_passed,
                "score": self.risk_score,
                "adjusted_quantity": self.adjusted_quantity,
            },
            "order": {
                "placed": self.order_placed,
                "order_id": self.order_id,
                "final_quantity": self.final_quantity,
                "final_price": self.final_price,
            },
            "error": self.error_message,
            "execution_time_ms": self.execution_time_ms,
        }


class OrderExecutor:
    """
    Executes trading signals through IBKR with full risk validation.

    Pipeline:
    1. Validate signal (basic sanity checks)
    2. Risk validation (compliance + portfolio risk via RiskManager)
    3. Place order (market or limit)
    4. Return audit log with full decision chain
    """

    def __init__(
        self,
        ibkr_client: Optional[IBKRClient] = None,
        risk_manager: Optional[RiskManager] = None,
    ):
        """
        Initialize OrderExecutor.

        Args:
            ibkr_client: Optional IBKR client (will use global if not provided)
            risk_manager: Optional RiskManager (will use global if not provided)
        """
        self._ibkr_client = ibkr_client
        self._risk_manager = risk_manager

        logger.info("OrderExecutor initialized (T10: Strategy-to-Execution Pipeline)")

    @property
    def risk_manager(self) -> RiskManager:
        """Get risk manager instance (lazy loading)"""
        if self._risk_manager is None:
            self._risk_manager = get_risk_manager()
        return self._risk_manager

    @property
    def ibkr_client(self) -> Optional[IBKRClient]:
        """Get IBKR client"""
        return self._ibkr_client

    def set_ibkr_client(self, client: IBKRClient):
        """Set IBKR client (for late binding)"""
        self._ibkr_client = client

    async def execute(
        self,
        signal: TradingSignal,
        context: ExecutionContext,
    ) -> ExecutionAuditLog:
        """
        Execute a trading signal with full validation and audit trail.

        Args:
            signal: Trading signal from strategy
            context: Execution context with account info and settings

        Returns:
            ExecutionAuditLog with complete decision chain
        """
        import time
        start_time = time.time()

        audit_log = ExecutionAuditLog(
            signal=signal,
            context=context,
        )

        try:
            # Step 1: Basic signal validation
            validation_result = self._validate_signal(signal)
            audit_log.validation_passed = validation_result["valid"]
            audit_log.validation_messages = validation_result["messages"]

            if not validation_result["valid"]:
                audit_log.status = ExecutionStatus.REJECTED_VALIDATION
                audit_log.error_message = "; ".join(validation_result["messages"])
                self._record_metrics(audit_log)
                return audit_log

            # Step 2: Risk validation (compliance + portfolio risk)
            risk_result = await self._validate_risk(signal, context)
            audit_log.risk_validation = risk_result
            audit_log.risk_score = risk_result.risk_score if risk_result else 0.0

            if risk_result:
                audit_log.risk_check_passed = risk_result.can_proceed
                audit_log.validation_messages.extend(risk_result.messages)

                if risk_result.adjusted_quantity is not None:
                    audit_log.adjusted_quantity = risk_result.adjusted_quantity

                if not risk_result.can_proceed:
                    # Determine if it was compliance or portfolio risk
                    if not risk_result.compliance_check.can_proceed:
                        audit_log.status = ExecutionStatus.REJECTED_COMPLIANCE
                    else:
                        audit_log.status = ExecutionStatus.REJECTED_RISK
                    audit_log.error_message = "; ".join(risk_result.messages)
                    self._record_metrics(audit_log)
                    return audit_log
            else:
                # Risk manager not available, proceed with caution
                audit_log.risk_check_passed = True
                audit_log.validation_messages.append("Warning: Risk validation skipped (manager unavailable)")

            # Determine final quantity (use adjusted if available)
            final_quantity = audit_log.adjusted_quantity or signal.quantity
            audit_log.final_quantity = final_quantity

            # Step 3: Dry-run check
            if context.dry_run:
                audit_log.status = ExecutionStatus.REJECTED_DRY_RUN
                audit_log.validation_messages.append(f"Dry-run: Would execute {signal.signal_type.value} {final_quantity} {signal.symbol}")
                logger.info(f"[DRY-RUN] {signal.signal_type.value} {final_quantity} {signal.symbol} @ {signal.price}")
                self._record_metrics(audit_log)
                return audit_log

            # Step 4: Place order
            order_result = await self._place_order(signal, context, final_quantity)
            audit_log.order_placed = order_result["success"]
            audit_log.broker_order = order_result.get("order")
            audit_log.order_id = order_result.get("order_id")
            audit_log.final_price = order_result.get("price")

            if not order_result["success"]:
                audit_log.status = ExecutionStatus.FAILED_ORDER
                audit_log.error_message = order_result.get("error", "Unknown order error")
                self._record_metrics(audit_log)
                return audit_log

            # Success
            audit_log.status = ExecutionStatus.SUCCESS
            logger.info(
                f"Order executed: {signal.signal_type.value} {final_quantity} {signal.symbol} "
                f"@ {audit_log.final_price or signal.price} (order_id={audit_log.order_id})"
            )

        except Exception as e:
            logger.error(f"Execution error: {e}", exc_info=True)
            audit_log.status = ExecutionStatus.FAILED_BROKER
            audit_log.error_message = str(e)

        finally:
            audit_log.execution_time_ms = (time.time() - start_time) * 1000
            self._record_metrics(audit_log)

        return audit_log

    def _validate_signal(self, signal: TradingSignal) -> Dict[str, Any]:
        """
        Basic signal validation.

        Checks:
        - Signal type is BUY or SELL (not HOLD)
        - Symbol is not empty
        - Quantity is positive
        - Price is positive
        - Confidence is in valid range
        """
        messages = []
        valid = True

        # Signal type check
        if signal.signal_type == SignalType.HOLD:
            messages.append("Cannot execute HOLD signal")
            valid = False

        # Symbol check
        if not signal.symbol or not signal.symbol.strip():
            messages.append("Symbol is required")
            valid = False

        # Quantity check
        if signal.quantity <= 0:
            messages.append(f"Quantity must be positive (got {signal.quantity})")
            valid = False

        # Price check
        if signal.price <= 0:
            messages.append(f"Price must be positive (got {signal.price})")
            valid = False

        # Confidence check (warn but don't fail)
        if signal.confidence < 0 or signal.confidence > 1:
            messages.append(f"Warning: Confidence out of range [0,1] (got {signal.confidence})")

        if valid:
            messages.append("Signal validation passed")

        return {"valid": valid, "messages": messages}

    async def _validate_risk(
        self,
        signal: TradingSignal,
        context: ExecutionContext,
    ) -> Optional[PreTradeValidationResult]:
        """
        Validate signal against risk rules.

        Uses RiskManager.validate_trade() which includes:
        - Compliance checks (PDT, settlement, frequency)
        - Position sizing validation
        - Portfolio risk checks (concentration, correlation, drawdown)
        """
        try:
            # Determine if this would create a day trade
            # For now, assume not a day trade (would need position tracking)
            will_create_day_trade = False

            # Convert signal type to side string
            side = "BUY" if signal.signal_type == SignalType.BUY else "SELL"

            result = await self.risk_manager.validate_trade(
                account_id=context.account_id,
                symbol=signal.symbol,
                side=side,
                quantity=signal.quantity,
                price_per_share=signal.price,
                confidence_score=signal.confidence,
                will_create_day_trade=will_create_day_trade,
            )

            return result

        except Exception as e:
            logger.warning(f"Risk validation error (proceeding with caution): {e}")
            return None

    async def _place_order(
        self,
        signal: TradingSignal,
        context: ExecutionContext,
        quantity: int,
    ) -> Dict[str, Any]:
        """
        Place order with IBKR.

        Args:
            signal: Trading signal
            context: Execution context
            quantity: Final quantity (may be adjusted)

        Returns:
            Dict with success status, order info, or error
        """
        if self._ibkr_client is None:
            return {
                "success": False,
                "error": "IBKR client not configured",
            }

        if not self._ibkr_client.connected:
            return {
                "success": False,
                "error": "IBKR client not connected",
            }

        try:
            # Create contract
            contract = self._ibkr_client.create_contract(signal.symbol)

            # Determine order side
            order_side = OrderSide.BUY if signal.signal_type == SignalType.BUY else OrderSide.SELL

            # Place order based on type
            if context.order_type == "LIMIT" and context.limit_price:
                broker_order = await self._ibkr_client.place_limit_order(
                    contract=contract,
                    side=order_side,
                    quantity=quantity,
                    price=context.limit_price,
                )
            else:
                # Default to market order
                broker_order = await self._ibkr_client.place_market_order(
                    contract=contract,
                    side=order_side,
                    quantity=quantity,
                )

            return {
                "success": True,
                "order": broker_order,
                "order_id": broker_order.order_id,
                "price": broker_order.price or signal.price,
            }

        except Exception as e:
            logger.error(f"Order placement error: {e}", exc_info=True)
            return {
                "success": False,
                "error": str(e),
            }

    def _record_metrics(self, audit_log: ExecutionAuditLog):
        """Record execution metrics to Prometheus and broadcast via WebSocket"""
        metrics = _get_metrics()
        if metrics:
            try:
                # Record execution outcome
                if hasattr(metrics, 'record_execution_outcome'):
                    metrics.record_execution_outcome(
                        strategy=audit_log.context.strategy_name,
                        symbol=audit_log.signal.symbol,
                        side=audit_log.signal.signal_type.value,
                        status=audit_log.status.value,
                    )

                # Record execution duration
                if hasattr(metrics, 'record_execution_duration'):
                    metrics.record_execution_duration(
                        strategy=audit_log.context.strategy_name,
                        duration_ms=audit_log.execution_time_ms,
                    )

                # Record risk score if available
                if audit_log.risk_score > 0 and hasattr(metrics, 'record_portfolio_risk_score'):
                    metrics.record_portfolio_risk_score(audit_log.risk_score)

            except Exception as e:
                logger.debug(f"Error recording execution metrics: {e}")

        # Broadcast execution event via WebSocket
        self._broadcast_execution(audit_log)

    def _broadcast_execution(self, audit_log: ExecutionAuditLog):
        """Broadcast execution event to WebSocket subscribers"""
        try:
            import asyncio
            from ..api.websocket import get_websocket_manager

            manager = get_websocket_manager()
            if manager:
                # Format execution data for WebSocket
                ws_data = {
                    "type": "execution",
                    "channel": "execution",
                    "timestamp": audit_log.timestamp.isoformat(),
                    "data": {
                        "status": audit_log.status.value,
                        "symbol": audit_log.signal.symbol,
                        "signal_type": audit_log.signal.signal_type.value,
                        "strategy_name": audit_log.context.strategy_name,
                        "quantity": audit_log.final_quantity,
                        "fill_price": audit_log.final_price,
                        "signal_price": audit_log.signal.price,
                        "risk_score": audit_log.risk_score,
                        "rejection_reason": audit_log.error_message,
                        "execution_time_ms": audit_log.execution_time_ms,
                    }
                }

                # Schedule async broadcast
                try:
                    loop = asyncio.get_running_loop()
                    asyncio.create_task(manager.broadcast("execution", ws_data))
                except RuntimeError:
                    # No running loop - try to get/create one
                    try:
                        loop = asyncio.get_event_loop()
                        if loop.is_running():
                            asyncio.create_task(manager.broadcast("execution", ws_data))
                        else:
                            asyncio.run_coroutine_threadsafe(
                                manager.broadcast("execution", ws_data), loop
                            )
                    except Exception as e:
                        logger.debug(f"Could not broadcast execution event: {e}")

        except Exception as e:
            logger.debug(f"Error broadcasting execution event: {e}")


# Global executor instance
_executor: Optional[OrderExecutor] = None


def get_order_executor() -> OrderExecutor:
    """Get or create global OrderExecutor instance"""
    global _executor
    if _executor is None:
        _executor = OrderExecutor()
    return _executor


def init_order_executor(
    ibkr_client: Optional[IBKRClient] = None,
    risk_manager: Optional[RiskManager] = None,
) -> OrderExecutor:
    """Initialize global OrderExecutor with dependencies"""
    global _executor
    _executor = OrderExecutor(
        ibkr_client=ibkr_client,
        risk_manager=risk_manager,
    )
    return _executor
