"""
Risk Management Module
======================

Comprehensive risk management system for cash account rules,
compliance, position sizing, and profit taking.
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
    'AccountMonitor',
    'AccountStatus',
    'ComplianceManager',
    'ComplianceCheck',
    'ComplianceResult',
    'PositionSizingManager',
    'PositionSizeResult',
    'ConfidenceLevel',
    'ProfitTakingManager',
    'ProfitExitPlan',
    'ProfitCheckResult',
    'ProfitLevel',
    'get_profit_taking_manager',
    'RiskManager',
    'PreTradeValidationResult',
    'RiskStatus',
    'get_risk_manager',
]

