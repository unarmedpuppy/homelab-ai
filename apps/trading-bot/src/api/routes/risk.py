"""
Risk Management API Routes
==========================

API endpoints for risk management, compliance, and account monitoring.
"""

from fastapi import APIRouter, HTTPException, Depends, Query
from typing import Optional, Dict, Any
from pydantic import BaseModel
import logging

from ...core.risk import RiskManager, PreTradeValidationResult, RiskStatus
from ...data.database.models import TradeSide

logger = logging.getLogger(__name__)

router = APIRouter()

# Global risk manager instance
_risk_manager: Optional[RiskManager] = None


def get_risk_manager() -> RiskManager:
    """Get or create risk manager instance"""
    global _risk_manager
    if _risk_manager is None:
        _risk_manager = RiskManager()
    return _risk_manager


class TradeValidationRequest(BaseModel):
    """Request model for trade validation"""
    account_id: int
    symbol: str
    side: str  # "BUY" or "SELL"
    quantity: Optional[int] = None
    price_per_share: Optional[float] = None
    confidence_score: Optional[float] = None
    will_create_day_trade: bool = False


class TradeValidationResponse(BaseModel):
    """Response model for trade validation"""
    is_valid: bool
    can_proceed: bool
    compliance_result: str
    compliance_message: str
    position_size: Optional[Dict[str, Any]] = None
    messages: list = []
    
    class Config:
        from_attributes = True


@router.post("/validate-trade", response_model=TradeValidationResponse)
async def validate_trade(
    request: TradeValidationRequest,
    risk_manager: RiskManager = Depends(get_risk_manager)
):
    """
    Validate a trade before execution
    
    Performs comprehensive pre-trade validation including:
    - Compliance checks (PDT, settlement, frequency limits)
    - Position sizing (if confidence score provided)
    - Cash account mode detection
    """
    try:
        result = await risk_manager.validate_trade(
            account_id=request.account_id,
            symbol=request.symbol,
            side=request.side,
            quantity=request.quantity,
            price_per_share=request.price_per_share,
            confidence_score=request.confidence_score,
            will_create_day_trade=request.will_create_day_trade
        )
        
        # Build response
        position_size_dict = None
        if result.position_size:
            position_size_dict = {
                "size_usd": result.position_size.size_usd,
                "size_shares": result.position_size.size_shares,
                "confidence_level": result.position_size.confidence_level.value,
                "base_percentage": result.position_size.base_percentage,
                "actual_percentage": result.position_size.actual_percentage,
                "max_size_hit": result.position_size.max_size_hit
            }
        
        return TradeValidationResponse(
            is_valid=result.is_valid,
            can_proceed=result.can_proceed,
            compliance_result=result.compliance_check.result.value,
            compliance_message=result.compliance_check.message,
            position_size=position_size_dict,
            messages=result.messages
        )
    except Exception as e:
        logger.error(f"Error validating trade: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Trade validation error: {str(e)}")


@router.get("/status")
async def get_risk_status(
    account_id: int = Query(..., description="Account ID"),
    risk_manager: RiskManager = Depends(get_risk_manager)
):
    """
    Get current risk management status for an account
    
    Returns:
    - Account balance and cash account mode
    - Compliance status (PDT, trade frequency)
    - Available settled cash
    """
    try:
        status = await risk_manager.get_risk_status(account_id)
        
        return {
            "account_id": status.account_id,
            "account_balance": status.account_status.balance,
            "is_cash_account_mode": status.is_cash_account_mode,
            "threshold": status.account_status.threshold,
            "available_settled_cash": status.available_settled_cash,
            "compliance": {
                "day_trades_last_5_days": status.day_trade_count,
                "day_trade_limit": status.compliance_summary["pdt_limit"],
                "daily_trades": status.daily_trade_count,
                "daily_limit": status.compliance_summary["daily_limit"],
                "weekly_trades": status.weekly_trade_count,
                "weekly_limit": status.compliance_summary["weekly_limit"]
            },
            "last_checked": status.account_status.last_checked.isoformat() if status.account_status.last_checked else None
        }
    except Exception as e:
        logger.error(f"Error getting risk status: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error getting risk status: {str(e)}")


@router.get("/compliance")
async def get_compliance_status(
    account_id: int = Query(..., description="Account ID"),
    risk_manager: RiskManager = Depends(get_risk_manager)
):
    """
    Get detailed compliance status
    
    Returns detailed compliance information including:
    - PDT status
    - Trade frequency limits
    - Settlement tracking
    """
    try:
        status = await risk_manager.get_risk_status(account_id)
        
        # Get additional compliance details
        day_trade_count = risk_manager.compliance.get_day_trade_count(account_id, lookback_days=5)
        
        return {
            "account_id": account_id,
            "cash_account_mode": status.is_cash_account_mode,
            "pdt": {
                "day_trades_count": day_trade_count,
                "limit": 3,
                "can_trade": day_trade_count < 3,
                "remaining_day_trades": max(0, 3 - day_trade_count)
            },
            "trade_frequency": {
                "daily": {
                    "count": status.daily_trade_count,
                    "limit": status.compliance_summary["daily_limit"],
                    "remaining": max(0, status.compliance_summary["daily_limit"] - status.daily_trade_count)
                },
                "weekly": {
                    "count": status.weekly_trade_count,
                    "limit": status.compliance_summary["weekly_limit"],
                    "remaining": max(0, status.compliance_summary["weekly_limit"] - status.weekly_trade_count)
                }
            },
            "settlement": {
                "available_settled_cash": status.available_settled_cash,
                "settlement_period_days": risk_manager.compliance.settlement_days
            }
        }
    except Exception as e:
        logger.error(f"Error getting compliance status: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error getting compliance status: {str(e)}")


@router.get("/account-mode")
async def get_account_mode(
    account_id: int = Query(..., description="Account ID"),
    risk_manager: RiskManager = Depends(get_risk_manager)
):
    """
    Check if account is in cash account mode
    
    Returns cash account mode status and threshold information.
    """
    try:
        is_cash_mode = await risk_manager.is_cash_account_mode(account_id)
        status = await risk_manager.get_risk_status(account_id)
        
        return {
            "account_id": account_id,
            "is_cash_account_mode": is_cash_mode,
            "account_balance": status.account_status.balance,
            "threshold": status.account_status.threshold,
            "balance_vs_threshold": {
                "difference": status.account_status.balance - status.account_status.threshold,
                "percentage": (status.account_status.balance / status.account_status.threshold * 100) if status.account_status.threshold > 0 else 0
            },
            "last_checked": status.account_status.last_checked.isoformat() if status.account_status.last_checked else None
        }
    except Exception as e:
        logger.error(f"Error getting account mode: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error getting account mode: {str(e)}")

