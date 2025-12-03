"""
Risk Manager
============

Unified interface for all risk management components.
Coordinates account monitoring, compliance, position sizing, profit taking,
and portfolio-level risk checks (T17: Risk Manager Agent).
"""

import logging
from typing import Optional, Dict, Any, List
from dataclasses import dataclass, field

from .account_monitor import AccountMonitor, AccountStatus
from .compliance import ComplianceManager, ComplianceCheck, ComplianceResult
from .position_sizing import PositionSizingManager, PositionSizeResult, ConfidenceLevel
from .profit_taking import ProfitTakingManager, ProfitExitPlan, ProfitCheckResult
from .portfolio_risk import (
    PortfolioRiskChecker,
    PortfolioRiskDecision,
    PortfolioRiskSettings,
    RiskCheck,
    RiskCheckResult,
    MarketRegime,
)

# Lazy import for metrics to avoid circular dependencies
_metrics_module = None


def _get_metrics():
    """Lazy load metrics module."""
    global _metrics_module
    if _metrics_module is None:
        try:
            from ...utils import metrics as m
            _metrics_module = m
        except ImportError:
            _metrics_module = None
    return _metrics_module


logger = logging.getLogger(__name__)


@dataclass
class PreTradeValidationResult:
    """Result of pre-trade validation"""
    is_valid: bool
    can_proceed: bool
    compliance_check: ComplianceCheck
    position_size: Optional[PositionSizeResult] = None
    portfolio_risk: Optional[PortfolioRiskDecision] = None
    messages: List[str] = field(default_factory=list)
    risk_score: float = 0.0
    market_regime: MarketRegime = MarketRegime.UNKNOWN
    adjusted_quantity: Optional[int] = None  # Reduced quantity from portfolio risk


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
    # Portfolio risk status (T17)
    portfolio_risk_enabled: bool = True
    circuit_breaker_triggered: bool = False
    market_regime: MarketRegime = MarketRegime.UNKNOWN
    portfolio_risk_summary: Optional[Dict[str, Any]] = None


class RiskManager:
    """
    Unified risk management interface

    Coordinates:
    - Account monitoring and cash account mode detection
    - Compliance checks (PDT, settlement, frequency)
    - Position sizing based on confidence
    - Profit taking rules
    - Portfolio-level risk checks (T17: Risk Manager Agent)
    """

    def __init__(
        self,
        account_monitor: Optional[AccountMonitor] = None,
        compliance_manager: Optional[ComplianceManager] = None,
        position_sizing_manager: Optional[PositionSizingManager] = None,
        profit_taking_manager: Optional[ProfitTakingManager] = None,
        portfolio_risk_checker: Optional[PortfolioRiskChecker] = None,
        ibkr_client: Optional[Any] = None,
    ):
        """
        Initialize risk manager

        Args:
            account_monitor: Optional AccountMonitor instance
            compliance_manager: Optional ComplianceManager instance
            position_sizing_manager: Optional PositionSizingManager instance
            profit_taking_manager: Optional ProfitTakingManager instance
            portfolio_risk_checker: Optional PortfolioRiskChecker instance
            ibkr_client: Optional IBKR client for live data
        """
        # Initialize or use provided instances
        self.account_monitor = account_monitor or AccountMonitor()
        self.compliance = compliance_manager or ComplianceManager(account_monitor=self.account_monitor)
        self.position_sizing = position_sizing_manager or PositionSizingManager(account_monitor=self.account_monitor)
        self.profit_taking = profit_taking_manager or ProfitTakingManager()

        # T17: Portfolio Risk Checker
        self.portfolio_risk = portfolio_risk_checker or PortfolioRiskChecker(ibkr_client=ibkr_client)
        self._ibkr_client = ibkr_client

        logger.info("RiskManager initialized with portfolio risk checks enabled")
    
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

        # 3. Portfolio risk checks (T17: Risk Manager Agent)
        portfolio_risk_decision = None
        adjusted_quantity = None
        risk_score = 0.0
        market_regime = MarketRegime.UNKNOWN

        if quantity and price_per_share:
            portfolio_risk_decision = await self.portfolio_risk.evaluate(
                symbol=symbol,
                side=side if isinstance(side, str) else side.value,
                quantity=quantity,
                price=price_per_share,
                account_id=account_id,
            )

            risk_score = portfolio_risk_decision.risk_score
            market_regime = portfolio_risk_decision.market_regime

            # Record metrics for portfolio risk evaluation
            metrics = _get_metrics()
            if metrics:
                try:
                    metrics.record_portfolio_risk_evaluation(portfolio_risk_decision)
                except Exception as e:
                    logger.debug(f"Error recording portfolio risk metrics: {e}")

            if not portfolio_risk_decision.approved:
                messages.append(f"Portfolio risk check failed: {portfolio_risk_decision.reason}")
                return PreTradeValidationResult(
                    is_valid=False,
                    can_proceed=False,
                    compliance_check=compliance_check,
                    position_size=position_size,
                    portfolio_risk=portfolio_risk_decision,
                    messages=messages,
                    risk_score=risk_score,
                    market_regime=market_regime,
                )

            # Check if position size should be adjusted
            if portfolio_risk_decision.adjusted_size is not None:
                adjusted_quantity = portfolio_risk_decision.adjusted_size
                messages.append(
                    f"Position size adjusted from {quantity} to {adjusted_quantity} shares "
                    f"due to portfolio risk ({portfolio_risk_decision.reason})"
                )

            # Add warning messages from portfolio risk checks
            for check in portfolio_risk_decision.warning_checks:
                messages.append(f"Portfolio risk warning: {check.message}")

            messages.append(
                f"Portfolio risk check passed (score: {risk_score:.2f}, regime: {market_regime.value})"
            )

        return PreTradeValidationResult(
            is_valid=True,
            can_proceed=True,
            compliance_check=compliance_check,
            position_size=position_size,
            portfolio_risk=portfolio_risk_decision,
            messages=messages,
            risk_score=risk_score,
            market_regime=market_regime,
            adjusted_quantity=adjusted_quantity,
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

        # Get portfolio risk status (T17)
        portfolio_risk_status = self.portfolio_risk.get_status()

        return RiskStatus(
            account_id=account_id,
            account_status=account_status,
            is_cash_account_mode=account_status.is_cash_account_mode,
            available_settled_cash=available_settled,
            day_trade_count=day_trade_count,
            daily_trade_count=daily_count,
            weekly_trade_count=weekly_count,
            compliance_summary=compliance_summary,
            portfolio_risk_enabled=portfolio_risk_status.get("enabled", True),
            circuit_breaker_triggered=portfolio_risk_status.get("circuit_breaker_triggered", False),
            market_regime=MarketRegime(portfolio_risk_status.get("market_regime", "unknown")),
            portfolio_risk_summary=portfolio_risk_status,
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

