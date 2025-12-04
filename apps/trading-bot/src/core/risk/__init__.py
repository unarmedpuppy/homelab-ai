"""
Risk Management Module
======================

Comprehensive risk management system for cash account rules,
compliance, position sizing, profit taking, and portfolio-level risk checks.
"""

from typing import Optional

from .account_monitor import AccountMonitor, AccountStatus
from .compliance import ComplianceManager, ComplianceCheck, ComplianceResult
from .position_sizing import (
    PositionSizingManager,
    PositionSizeResult,
    ConfidenceLevel,
    get_position_sizing_manager
)
from .profit_taking import (
    ProfitTakingManager,
    ProfitExitPlan,
    ProfitCheckResult,
    ProfitLevel,
    get_profit_taking_manager
)
from .portfolio_risk import (
    PortfolioRiskChecker,
    PortfolioRiskDecision,
    PortfolioRiskSettings,
    RiskCheck,
    RiskCheckResult,
    MarketRegime,
    get_portfolio_risk_checker,
)

from .manager import RiskManager, PreTradeValidationResult, RiskStatus

# Global risk manager instance
_risk_manager: Optional[RiskManager] = None


def get_risk_manager() -> RiskManager:
    """Get or create global risk manager instance"""
    global _risk_manager
    if _risk_manager is None:
        _risk_manager = RiskManager()
    return _risk_manager


__all__ = [
    # Account Monitor
    'AccountMonitor',
    'AccountStatus',
    # Compliance
    'ComplianceManager',
    'ComplianceCheck',
    'ComplianceResult',
    # Position Sizing
    'PositionSizingManager',
    'PositionSizeResult',
    'ConfidenceLevel',
    'get_position_sizing_manager',
    # Profit Taking
    'ProfitTakingManager',
    'ProfitExitPlan',
    'ProfitCheckResult',
    'ProfitLevel',
    'get_profit_taking_manager',
    # Portfolio Risk (T17)
    'PortfolioRiskChecker',
    'PortfolioRiskDecision',
    'PortfolioRiskSettings',
    'RiskCheck',
    'RiskCheckResult',
    'MarketRegime',
    'get_portfolio_risk_checker',
    # Risk Manager
    'RiskManager',
    'PreTradeValidationResult',
    'RiskStatus',
    'get_risk_manager',
]

