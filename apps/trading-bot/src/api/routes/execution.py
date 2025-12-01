"""
Execution Routes (T10: Strategy-to-Execution Pipeline)
======================================================

API routes for signal execution using the OrderExecutor.
Provides endpoints for executing signals, querying execution history,
and managing the execution pipeline.
"""

import json
import logging
from datetime import datetime
from typing import Optional, Dict, Any, List

from fastapi import APIRouter, HTTPException, Depends, Query
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from ...core.executor import (
    OrderExecutor,
    ExecutionContext,
    ExecutionAuditLog,
    ExecutionStatus,
    get_order_executor,
    init_order_executor,
)
from ...core.strategy.base import TradingSignal, SignalType
from ...data.database import get_db
from ...data.database.models import ExecutionLog, ExecutionStatus as DBExecutionStatus
from .trading import get_ibkr_manager

logger = logging.getLogger(__name__)

router = APIRouter()


# Request/Response Models
class SignalExecutionRequest(BaseModel):
    """Request model for signal execution"""
    symbol: str = Field(..., description="Trading symbol (e.g., AAPL)")
    signal_type: str = Field(..., description="Signal type: BUY or SELL")
    quantity: int = Field(..., ge=1, description="Number of shares")
    price: float = Field(..., gt=0, description="Current/limit price")
    confidence: float = Field(default=0.5, ge=0, le=1, description="Signal confidence (0.0-1.0)")
    stop_loss: Optional[float] = Field(default=None, description="Stop loss price")
    take_profit: Optional[float] = Field(default=None, description="Take profit price")
    account_id: int = Field(default=1, description="Account ID")
    strategy_name: str = Field(default="manual", description="Strategy name")
    order_type: str = Field(default="MARKET", description="Order type: MARKET or LIMIT")
    limit_price: Optional[float] = Field(default=None, description="Limit price (for LIMIT orders)")
    dry_run: bool = Field(default=False, description="If true, simulate execution without placing order")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")


class ExecutionResultResponse(BaseModel):
    """Response model for execution result"""
    status: str
    success: bool
    order_id: Optional[int] = None
    final_quantity: int
    final_price: Optional[float] = None
    validation_passed: bool
    risk_check_passed: bool
    risk_score: float = 0.0
    adjusted_quantity: Optional[int] = None
    messages: List[str]
    error: Optional[str] = None
    execution_time_ms: float
    timestamp: str


class ExecutionHistoryItem(BaseModel):
    """Model for execution history item"""
    id: int
    symbol: str
    signal_type: str
    status: str
    strategy_name: str
    signal_quantity: int
    final_quantity: Optional[int]
    signal_price: float
    final_price: Optional[float]
    confidence: Optional[float]
    risk_score: float
    order_id: Optional[int]
    dry_run: bool
    execution_time_ms: float
    created_at: str
    error_message: Optional[str]


@router.post("/signal", response_model=ExecutionResultResponse)
async def execute_signal(
    request: SignalExecutionRequest,
    db: Session = Depends(get_db),
):
    """
    Execute a trading signal through the OrderExecutor pipeline.

    This endpoint provides full signal-to-order execution with:
    - Signal validation
    - Risk management checks (compliance + portfolio risk)
    - Order placement (market or limit)
    - Full audit trail logging

    The execution pipeline:
    1. Validate signal (basic sanity checks)
    2. Risk validation via RiskManager
    3. Place order via IBKR (unless dry_run=True)
    4. Log execution to database

    Returns execution result with full audit information.
    """
    try:
        # Parse signal type
        try:
            signal_type = SignalType[request.signal_type.upper()]
        except KeyError:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid signal_type: {request.signal_type}. Must be BUY or SELL."
            )

        if signal_type == SignalType.HOLD:
            raise HTTPException(
                status_code=400,
                detail="Cannot execute HOLD signal"
            )

        # Create TradingSignal
        signal = TradingSignal(
            signal_type=signal_type,
            symbol=request.symbol.upper(),
            price=request.price,
            quantity=request.quantity,
            timestamp=datetime.now(),
            confidence=request.confidence,
            metadata=request.metadata,
            stop_loss=request.stop_loss,
            take_profit=request.take_profit,
        )

        # Create ExecutionContext
        context = ExecutionContext(
            account_id=request.account_id,
            strategy_name=request.strategy_name,
            dry_run=request.dry_run,
            order_type=request.order_type,
            limit_price=request.limit_price,
            metadata=request.metadata,
        )

        # Get executor and set IBKR client if available
        executor = get_order_executor()

        # Try to get IBKR client if connected
        ibkr_manager = get_ibkr_manager()
        if ibkr_manager and ibkr_manager.is_connected:
            try:
                client = await ibkr_manager.get_client()
                executor.set_ibkr_client(client)
            except Exception as e:
                logger.warning(f"Could not get IBKR client: {e}")

        # Execute signal
        audit_log = await executor.execute(signal, context)

        # Save to database
        try:
            _save_execution_log(db, audit_log)
        except Exception as e:
            logger.warning(f"Failed to save execution log to database: {e}")

        # Build response
        success = audit_log.status == ExecutionStatus.SUCCESS
        if not success and audit_log.status == ExecutionStatus.REJECTED_DRY_RUN:
            # Dry-run is not a failure
            success = True

        return ExecutionResultResponse(
            status=audit_log.status.value,
            success=success,
            order_id=audit_log.order_id,
            final_quantity=audit_log.final_quantity,
            final_price=audit_log.final_price,
            validation_passed=audit_log.validation_passed,
            risk_check_passed=audit_log.risk_check_passed,
            risk_score=audit_log.risk_score,
            adjusted_quantity=audit_log.adjusted_quantity,
            messages=audit_log.validation_messages,
            error=audit_log.error_message,
            execution_time_ms=audit_log.execution_time_ms,
            timestamp=audit_log.timestamp.isoformat(),
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Signal execution error: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Execution error: {str(e)}"
        )


@router.get("/history")
async def get_execution_history(
    account_id: int = Query(default=1, description="Account ID"),
    symbol: Optional[str] = Query(default=None, description="Filter by symbol"),
    strategy_name: Optional[str] = Query(default=None, description="Filter by strategy"),
    status: Optional[str] = Query(default=None, description="Filter by status (comma-separated for multiple)"),
    dry_run: Optional[bool] = Query(default=None, description="Filter by dry_run"),
    limit: int = Query(default=50, ge=1, le=500, description="Number of records to return"),
    offset: int = Query(default=0, ge=0, description="Number of records to skip"),
    db: Session = Depends(get_db),
):
    """
    Get execution history from the database.

    Supports filtering by:
    - account_id (required)
    - symbol (optional)
    - strategy_name (optional)
    - status (optional, comma-separated for multiple)
    - dry_run (optional)

    Returns paginated execution logs ordered by created_at descending,
    along with summary stats.
    """
    try:
        query = db.query(ExecutionLog).filter(ExecutionLog.account_id == account_id)

        if symbol:
            query = query.filter(ExecutionLog.symbol == symbol.upper())

        if strategy_name:
            query = query.filter(ExecutionLog.strategy_name == strategy_name)

        if status:
            # Support comma-separated status values
            status_list = [s.strip().upper() for s in status.split(",")]
            status_enums = []
            for s in status_list:
                try:
                    status_enums.append(DBExecutionStatus[s])
                except KeyError:
                    pass  # Skip invalid statuses
            if status_enums:
                from sqlalchemy import or_
                query = query.filter(or_(*[ExecutionLog.status == se for se in status_enums]))

        if dry_run is not None:
            query = query.filter(ExecutionLog.dry_run == dry_run)

        # Order by created_at descending and apply pagination
        logs = query.order_by(ExecutionLog.created_at.desc()).offset(offset).limit(limit).all()

        # Build logs list
        logs_list = [
            {
                "id": log.id,
                "symbol": log.symbol,
                "signal_type": log.signal_type,
                "status": log.status.value if log.status else "unknown",
                "strategy_name": log.strategy_name,
                "signal_quantity": log.signal_quantity,
                "quantity": log.final_quantity or log.signal_quantity,
                "final_quantity": log.final_quantity,
                "signal_price": log.signal_price,
                "fill_price": log.final_price,
                "final_price": log.final_price,
                "confidence": log.signal_confidence,
                "risk_score": log.risk_score or 0.0,
                "order_id": log.order_id,
                "dry_run": log.dry_run or False,
                "execution_time_ms": log.execution_time_ms or 0.0,
                "created_at": log.created_at.isoformat() if log.created_at else "",
                "rejection_reason": log.error_message,
                "error_message": log.error_message,
            }
            for log in logs
        ]

        # Calculate quick stats from fetched logs
        total = len(logs_list)
        success_count = sum(1 for l in logs_list if l["status"] == "success")
        rejected_count = sum(1 for l in logs_list if l["status"].startswith("rejected"))
        failed_count = sum(1 for l in logs_list if l["status"].startswith("failed"))

        return {
            "logs": logs_list,
            "stats": {
                "total": total,
                "success": success_count,
                "rejected": rejected_count,
                "failed": failed_count,
            }
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching execution history: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Error fetching execution history: {str(e)}"
        )


@router.get("/history/{execution_id}")
async def get_execution_detail(
    execution_id: int,
    db: Session = Depends(get_db),
):
    """
    Get detailed execution log by ID.

    Returns full audit data including validation messages,
    risk check details, and order information.
    """
    try:
        log = db.query(ExecutionLog).filter(ExecutionLog.id == execution_id).first()

        if not log:
            raise HTTPException(
                status_code=404,
                detail=f"Execution log {execution_id} not found"
            )

        # Parse JSON fields
        validation_messages = []
        if log.validation_messages:
            try:
                validation_messages = json.loads(log.validation_messages)
            except json.JSONDecodeError:
                validation_messages = [log.validation_messages]

        compliance_details = {}
        if log.compliance_details:
            try:
                compliance_details = json.loads(log.compliance_details)
            except json.JSONDecodeError:
                pass

        portfolio_risk_details = {}
        if log.portfolio_risk_details:
            try:
                portfolio_risk_details = json.loads(log.portfolio_risk_details)
            except json.JSONDecodeError:
                pass

        audit_data = {}
        if log.audit_data:
            audit_data = log.audit_data

        return {
            "id": log.id,
            "account_id": log.account_id,
            "symbol": log.symbol,
            "signal": {
                "type": log.signal_type,
                "quantity": log.signal_quantity,
                "price": log.signal_price,
                "confidence": log.signal_confidence,
                "stop_loss": log.signal_stop_loss,
                "take_profit": log.signal_take_profit,
            },
            "context": {
                "strategy_name": log.strategy_name,
                "order_type": log.order_type,
                "limit_price": log.limit_price,
                "dry_run": log.dry_run,
            },
            "status": log.status.value if log.status else "unknown",
            "validation": {
                "passed": log.validation_passed,
                "messages": validation_messages,
            },
            "risk": {
                "passed": log.risk_check_passed,
                "score": log.risk_score,
                "adjusted_quantity": log.adjusted_quantity,
                "compliance_details": compliance_details,
                "portfolio_risk_details": portfolio_risk_details,
            },
            "order": {
                "placed": log.order_placed,
                "order_id": log.order_id,
                "final_quantity": log.final_quantity,
                "final_price": log.final_price,
            },
            "error_message": log.error_message,
            "execution_time_ms": log.execution_time_ms,
            "created_at": log.created_at.isoformat() if log.created_at else None,
            "audit_data": audit_data,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching execution detail: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Error fetching execution detail: {str(e)}"
        )


@router.get("/stats")
async def get_execution_stats(
    account_id: int = Query(default=1, description="Account ID"),
    strategy_name: Optional[str] = Query(default=None, description="Filter by strategy"),
    days: int = Query(default=7, ge=1, le=365, description="Number of days to analyze"),
    db: Session = Depends(get_db),
):
    """
    Get execution statistics for the specified period.

    Returns aggregated statistics including:
    - Total executions by status
    - Success rate
    - Average execution time
    - Risk rejection rate
    - Strategy breakdown
    """
    try:
        from datetime import timedelta
        from sqlalchemy import func

        cutoff_date = datetime.now() - timedelta(days=days)

        query = db.query(ExecutionLog).filter(
            ExecutionLog.account_id == account_id,
            ExecutionLog.created_at >= cutoff_date,
        )

        if strategy_name:
            query = query.filter(ExecutionLog.strategy_name == strategy_name)

        logs = query.all()

        if not logs:
            return {
                "period_days": days,
                "total_executions": 0,
                "by_status": {},
                "success_rate": 0.0,
                "average_execution_time_ms": 0.0,
                "risk_rejection_rate": 0.0,
                "by_strategy": {},
            }

        # Count by status
        status_counts = {}
        for log in logs:
            status = log.status.value if log.status else "unknown"
            status_counts[status] = status_counts.get(status, 0) + 1

        # Calculate success rate
        success_count = status_counts.get("success", 0) + status_counts.get("rejected_dry_run", 0)
        total = len(logs)
        success_rate = success_count / total if total > 0 else 0.0

        # Calculate risk rejection rate
        risk_rejections = (
            status_counts.get("rejected_compliance", 0) +
            status_counts.get("rejected_risk", 0)
        )
        risk_rejection_rate = risk_rejections / total if total > 0 else 0.0

        # Average execution time
        exec_times = [log.execution_time_ms for log in logs if log.execution_time_ms]
        avg_exec_time = sum(exec_times) / len(exec_times) if exec_times else 0.0

        # Count by strategy
        strategy_counts = {}
        for log in logs:
            strategy = log.strategy_name or "unknown"
            strategy_counts[strategy] = strategy_counts.get(strategy, 0) + 1

        return {
            "period_days": days,
            "total_executions": total,
            "by_status": status_counts,
            "success_rate": round(success_rate, 4),
            "average_execution_time_ms": round(avg_exec_time, 2),
            "risk_rejection_rate": round(risk_rejection_rate, 4),
            "by_strategy": strategy_counts,
        }

    except Exception as e:
        logger.error(f"Error calculating execution stats: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Error calculating execution stats: {str(e)}"
        )


def _save_execution_log(db: Session, audit_log: ExecutionAuditLog):
    """Save execution audit log to database"""
    try:
        # Map ExecutionStatus to DB enum
        status_map = {
            ExecutionStatus.SUCCESS: DBExecutionStatus.SUCCESS,
            ExecutionStatus.REJECTED_VALIDATION: DBExecutionStatus.REJECTED_VALIDATION,
            ExecutionStatus.REJECTED_COMPLIANCE: DBExecutionStatus.REJECTED_COMPLIANCE,
            ExecutionStatus.REJECTED_RISK: DBExecutionStatus.REJECTED_RISK,
            ExecutionStatus.REJECTED_DRY_RUN: DBExecutionStatus.REJECTED_DRY_RUN,
            ExecutionStatus.FAILED_ORDER: DBExecutionStatus.FAILED_ORDER,
            ExecutionStatus.FAILED_BROKER: DBExecutionStatus.FAILED_BROKER,
        }

        # Build compliance details if available
        compliance_details = None
        if audit_log.risk_validation and audit_log.risk_validation.compliance_check:
            compliance_details = json.dumps({
                "result": audit_log.risk_validation.compliance_check.result.value,
                "message": audit_log.risk_validation.compliance_check.message,
                "details": audit_log.risk_validation.compliance_check.details,
            })

        # Build portfolio risk details if available
        portfolio_risk_details = None
        if audit_log.risk_validation and audit_log.risk_validation.portfolio_risk:
            pr = audit_log.risk_validation.portfolio_risk
            portfolio_risk_details = json.dumps({
                "approved": pr.approved,
                "reason": pr.reason,
                "risk_score": pr.risk_score,
                "market_regime": pr.market_regime.value,
                "adjusted_size": pr.adjusted_size,
            })

        log = ExecutionLog(
            account_id=audit_log.context.account_id,
            symbol=audit_log.signal.symbol,
            signal_type=audit_log.signal.signal_type.value,
            signal_price=audit_log.signal.price,
            signal_quantity=audit_log.signal.quantity,
            signal_confidence=audit_log.signal.confidence,
            signal_stop_loss=audit_log.signal.stop_loss,
            signal_take_profit=audit_log.signal.take_profit,
            strategy_name=audit_log.context.strategy_name,
            order_type=audit_log.context.order_type,
            limit_price=audit_log.context.limit_price,
            dry_run=audit_log.context.dry_run,
            status=status_map.get(audit_log.status, DBExecutionStatus.FAILED_BROKER),
            validation_passed=audit_log.validation_passed,
            validation_messages=json.dumps(audit_log.validation_messages),
            risk_check_passed=audit_log.risk_check_passed,
            risk_score=audit_log.risk_score,
            adjusted_quantity=audit_log.adjusted_quantity,
            compliance_details=compliance_details,
            portfolio_risk_details=portfolio_risk_details,
            order_placed=audit_log.order_placed,
            order_id=audit_log.order_id,
            final_quantity=audit_log.final_quantity,
            final_price=audit_log.final_price,
            error_message=audit_log.error_message,
            execution_time_ms=audit_log.execution_time_ms,
            audit_data=audit_log.to_dict(),
        )

        db.add(log)
        db.commit()
        logger.info(f"Saved execution log: id={log.id}, status={audit_log.status.value}")

    except Exception as e:
        db.rollback()
        logger.error(f"Failed to save execution log: {e}", exc_info=True)
        raise
