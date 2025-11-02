"""
Risk Manager
============

Unified interface for all risk management components.
Coordinates account monitoring, compliance, position sizing, and profit taking.
"""

import logging
from typing import Optional, Dict, Any
from dataclasses import dataclass

from .account_monitor import AccountMonitor, AccountStatus
from .compliance import ComplianceManager, ComplianceCheck, ComplianceResult
from .position_sizing import PositionSizingManager, PositionSizeResult, ConfidenceLevel
from .profit_taking import ProfitTakingManager, ProfitExitPlan, ProfitCheckResult

logger = logging.getLogger(__name__)


@dataclass
class PreTradeValidationResult:
    """Result of pre-trade validation"""
    is_valid: bool
    can_proceed: bool
    compliance_check: ComplianceCheck
    position_size: Optional[PositionSizeResult] = None
    messages: list = None
    
    def __post_init__(self):
        if self.messages is None:
            self.messages = []


@dataclass
class RiskStatus:
    """Current risk management status"""
    account_id: int
    account_status: AccountStatus
    is_cash_account_mode: bool
    available_settled_cash: float
    day_trade_count: int
    daily_trade_count: int
    weekly_trade_count: int
    compliance_summary: Dict[str, Any]


class RiskManager:
    """
    Unified risk management interface
    
    Coordinates:
    - Account monitoring and cash account mode detection
    - Compliance checks (PDT, settlement, frequency)
    - Position sizing based on confidence
    - Profit taking rules
    """
    
    def __init__(
        self,
        account_monitor: Optional[AccountMonitor] = None,
        compliance_manager: Optional[ComplianceManager] = None,
        position_sizing_manager: Optional[PositionSizingManager] = None,
        profit_taking_manager: Optional[ProfitTakingManager] = None
    ):
        """
        Initialize risk manager
        
        Args:
            account_monitor: Optional AccountMonitor instance
            compliance_manager: Optional ComplianceManager instance
            position_sizing_manager: Optional PositionSizingManager instance
            profit_taking_manager: Optional ProfitTakingManager instance
        """
        # Initialize or use provided instances
        self.account_monitor = account_monitor or AccountMonitor()
        self.compliance = compliance_manager or ComplianceManager(account_monitor=self.account_monitor)
        self.position_sizing = position_sizing_manager or PositionSizingManager(account_monitor=self.account_monitor)
        self.profit_taking = profit_taking_manager or ProfitTakingManager()
        
        logger.info("RiskManager initialized")
    
    async def validate_trade(
        self,
        account_id: int,
        symbol: str,
        side: str,
        quantity: Optional[int] = None,
        price_per_share: Optional[float] = None,
        confidence_score: Optional[float] = None,
        will_create_day_trade: bool = False
    ) -> PreTradeValidationResult:
        """
        Comprehensive pre-trade validation
        
        Args:
            account_id: Account ID
            symbol: Trading symbol
            side: Trade side ("BUY" or "SELL")
            quantity: Optional quantity (will calculate if not provided)
            price_per_share: Price per share (required if quantity not provided)
            confidence_score: Optional confidence score for position sizing
            will_create_day_trade: Whether this trade would create a day trade
            
        Returns:
            PreTradeValidationResult with validation details
        """
        from ...data.database.models import TradeSide
        
        # Convert side string to enum
        if isinstance(side, str):
            trade_side = TradeSide.BUY if side.upper() == "BUY" else TradeSide.SELL
        else:
            trade_side = side
        
        messages = []
        
        # 1. Compliance check
        trade_amount = 0.0
        if quantity and price_per_share:
            trade_amount = quantity * price_per_share
        elif quantity is None and price_per_share and confidence_score is not None:
            # Calculate position size first to get trade amount
            position_size = await self.position_sizing.calculate_position_size(
                account_id=account_id,
                confidence_score=confidence_score,
                price_per_share=price_per_share
            )
            trade_amount = position_size.size_usd
            quantity = position_size.size_shares
        
        compliance_check = await self.compliance.check_compliance(
            account_id=account_id,
            symbol=symbol,
            side=trade_side,
            amount=-trade_amount if trade_side == TradeSide.BUY else trade_amount,
            will_create_day_trade=will_create_day_trade
        )
        
        if not compliance_check.can_proceed:
            messages.append(f"Compliance check failed: {compliance_check.message}")
            return PreTradeValidationResult(
                is_valid=False,
                can_proceed=False,
                compliance_check=compliance_check,
                messages=messages
            )
        
        messages.append(f"Compliance check passed: {compliance_check.message}")
        
        # 2. Position sizing (for BUY orders with confidence score)
        position_size = None
        if trade_side == TradeSide.BUY and confidence_score is not None and price_per_share:
            # Check if in cash account mode for settled cash
            is_cash_account = await self.account_monitor.is_cash_account_mode(account_id)
            
            if is_cash_account:
                # Use settled cash calculation
                available_settled = await self.compliance.get_available_settled_cash(account_id)
                position_size = await self.position_sizing.calculate_position_size_with_settlement(
                    account_id=account_id,
                    confidence_score=confidence_score,
                    price_per_share=price_per_share,
                    available_settled_cash=available_settled
                )
            else:
                # Regular position sizing
                position_size = await self.position_sizing.calculate_position_size(
                    account_id=account_id,
                    confidence_score=confidence_score,
                    price_per_share=price_per_share
                )
            
            messages.append(
                f"Position size calculated: {position_size.size_shares} shares "
                f"(${position_size.size_usd:,.2f}) at {position_size.confidence_level.value} confidence"
            )
            
            # If quantity was provided, validate it doesn't exceed calculated size
            if quantity and quantity > position_size.size_shares:
                messages.append(
                    f"Warning: Requested quantity ({quantity}) exceeds recommended size "
                    f"({position_size.size_shares} shares)"
                )
        
        return PreTradeValidationResult(
            is_valid=True,
            can_proceed=True,
            compliance_check=compliance_check,
            position_size=position_size,
            messages=messages
        )
    
    async def get_risk_status(self, account_id: int) -> RiskStatus:
        """
        Get current risk management status
        
        Args:
            account_id: Account ID
            
        Returns:
            RiskStatus with current state
        """
        # Get account status
        account_status = await self.account_monitor.check_account_balance(account_id)
        
        # Get available settled cash
        available_settled = await self.compliance.get_available_settled_cash(account_id)
        
        # Get day trade count
        day_trade_count = self.compliance.get_day_trade_count(account_id, lookback_days=5)
        
        # Get trade frequency
        freq_check = await self.compliance.check_trade_frequency(account_id)
        daily_count = freq_check.details.get("daily_count", 0) if freq_check.details else 0
        weekly_count = freq_check.details.get("weekly_count", 0) if freq_check.details else 0
        
        # Build compliance summary
        compliance_summary = {
            "pdt_day_trades": day_trade_count,
            "pdt_limit": 3,
            "daily_trades": daily_count,
            "daily_limit": self.compliance.daily_limit,
            "weekly_trades": weekly_count,
            "weekly_limit": self.compliance.weekly_limit,
            "available_settled_cash": available_settled
        }
        
        return RiskStatus(
            account_id=account_id,
            account_status=account_status,
            is_cash_account_mode=account_status.is_cash_account_mode,
            available_settled_cash=available_settled,
            day_trade_count=day_trade_count,
            daily_trade_count=daily_count,
            weekly_trade_count=weekly_count,
            compliance_summary=compliance_summary
        )
    
    async def calculate_position_size(
        self,
        account_id: int,
        confidence_score: float,
        price_per_share: float
    ) -> PositionSizeResult:
        """
        Calculate position size (convenience method)
        
        Args:
            account_id: Account ID
            confidence_score: Signal confidence (0.0-1.0)
            price_per_share: Price per share
            
        Returns:
            PositionSizeResult
        """
        # Check if in cash account mode
        is_cash_account = await self.account_monitor.is_cash_account_mode(account_id)
        
        if is_cash_account:
            available_settled = await self.compliance.get_available_settled_cash(account_id)
            return await self.position_sizing.calculate_position_size_with_settlement(
                account_id=account_id,
                confidence_score=confidence_score,
                price_per_share=price_per_share,
                available_settled_cash=available_settled
            )
        else:
            return await self.position_sizing.calculate_position_size(
                account_id=account_id,
                confidence_score=confidence_score,
                price_per_share=price_per_share
            )
    
    def create_profit_exit_plan(
        self,
        entry_price: float,
        quantity: int,
        custom_levels: Optional[tuple] = None,
        custom_exit_pcts: Optional[tuple] = None
    ) -> ProfitExitPlan:
        """
        Create profit exit plan (convenience method)
        
        Args:
            entry_price: Entry price
            quantity: Position quantity
            custom_levels: Optional custom profit levels
            custom_exit_pcts: Optional custom exit percentages
            
        Returns:
            ProfitExitPlan
        """
        return self.profit_taking.create_exit_plan(
            entry_price=entry_price,
            quantity=quantity,
            custom_levels=custom_levels,
            custom_exit_pcts=custom_exit_pcts
        )
    
    def check_profit_levels(
        self,
        current_price: float,
        exit_plan: ProfitExitPlan,
        current_quantity: int
    ) -> ProfitCheckResult:
        """
        Check profit levels (convenience method)
        
        Args:
            current_price: Current market price
            exit_plan: Profit exit plan
            current_quantity: Current position quantity
            
        Returns:
            ProfitCheckResult
        """
        return self.profit_taking.check_profit_levels(
            current_price=current_price,
            exit_plan=exit_plan,
            current_quantity=current_quantity
        )
    
    async def is_cash_account_mode(self, account_id: int) -> bool:
        """
        Check if account is in cash account mode (convenience method)
        
        Args:
            account_id: Account ID
            
        Returns:
            True if in cash account mode
        """
        return await self.account_monitor.is_cash_account_mode(account_id)

