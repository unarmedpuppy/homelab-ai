"""
Profit Taking Manager
=====================

Manages aggressive profit taking strategies with partial exits.
"""

import logging
import threading
from typing import Optional, List, Tuple
from dataclasses import dataclass
from enum import Enum
from datetime import datetime

from ...config.settings import settings
from ...data.database.models import Position, Trade

logger = logging.getLogger(__name__)


class ProfitLevel(str, Enum):
    """Profit taking levels"""
    LEVEL_1 = "level_1"  # 5% profit
    LEVEL_2 = "level_2"  # 10% profit
    LEVEL_3 = "level_3"  # 20% profit


@dataclass
class ProfitExitPlan:
    """Profit exit plan for a position"""
    entry_price: float
    level_1_price: float  # 5% profit
    level_2_price: float  # 10% profit
    level_3_price: float  # 20% profit
    level_1_exit_pct: float  # Percentage to exit at level 1 (default 25%)
    level_2_exit_pct: float  # Percentage to exit at level 2 (default 50%)
    level_3_exit_pct: float  # Percentage to exit at level 3 (remaining)
    levels_hit: List[ProfitLevel] = None
    
    def __post_init__(self):
        if self.levels_hit is None:
            self.levels_hit = []


@dataclass
class ProfitCheckResult:
    """Result of checking profit levels"""
    should_exit: bool
    exit_quantity: int  # Number of shares to sell (0 = no exit)
    profit_level: Optional[ProfitLevel] = None
    profit_pct: float = 0.0
    remaining_shares: int = 0
    message: str = ""


class ProfitTakingManager:
    """
    Manage aggressive profit taking with partial exits
    
    Features:
    - Multiple profit levels (5%, 10%, 20%)
    - Partial exit strategy
    - Strategy-driven coordination
    - Position tracking
    """
    
    def __init__(self):
        """Initialize profit taking manager"""
        # Get profit taking settings
        self.profit_level_1 = settings.risk.profit_take_level_1  # 5%
        self.profit_level_2 = settings.risk.profit_take_level_2  # 10%
        self.profit_level_3 = settings.risk.profit_take_level_3  # 20%
        self.partial_exit_enabled = settings.risk.partial_exit_enabled
        self.partial_exit_level_1_pct = settings.risk.partial_exit_level_1_pct  # 25%
        self.partial_exit_level_2_pct = settings.risk.partial_exit_level_2_pct  # 50%
    
    def create_exit_plan(
        self,
        entry_price: float,
        quantity: int,
        custom_levels: Optional[Tuple[float, float, float]] = None,
        custom_exit_pcts: Optional[Tuple[float, float]] = None
    ) -> ProfitExitPlan:
        """
        Create a profit exit plan for a position
        
        Args:
            entry_price: Entry price of the position
            quantity: Total quantity of shares
            custom_levels: Optional custom profit levels (level_1, level_2, level_3) as decimals
            custom_exit_pcts: Optional custom exit percentages (level_1_pct, level_2_pct)
            
        Returns:
            ProfitExitPlan with exit prices and percentages
        """
        # Use custom levels if provided, otherwise use defaults
        if custom_levels:
            level_1_pct, level_2_pct, level_3_pct = custom_levels
        else:
            level_1_pct = self.profit_level_1
            level_2_pct = self.profit_level_2
            level_3_pct = self.profit_level_3
        
        # Use custom exit percentages if provided
        if custom_exit_pcts:
            level_1_exit_pct, level_2_exit_pct = custom_exit_pcts
        else:
            level_1_exit_pct = self.partial_exit_level_1_pct
            level_2_exit_pct = self.partial_exit_level_2_pct
        
        # Calculate exit prices
        level_1_price = entry_price * (1 + level_1_pct)
        level_2_price = entry_price * (1 + level_2_pct)
        level_3_price = entry_price * (1 + level_3_pct)
        
        # Level 3 exits remaining shares (after level 1 and 2)
        level_3_exit_pct = 1.0 - level_1_exit_pct - level_2_exit_pct
        
        plan = ProfitExitPlan(
            entry_price=entry_price,
            level_1_price=level_1_price,
            level_2_price=level_2_price,
            level_3_price=level_3_price,
            level_1_exit_pct=level_1_exit_pct,
            level_2_exit_pct=level_2_exit_pct,
            level_3_exit_pct=level_3_exit_pct,
            levels_hit=[]
        )
        
        logger.debug(
            f"Created exit plan: entry=${entry_price:.2f}, "
            f"L1=${level_1_price:.2f} ({level_1_pct*100:.1f}%, exit {level_1_exit_pct*100:.0f}%), "
            f"L2=${level_2_price:.2f} ({level_2_pct*100:.1f}%, exit {level_2_exit_pct*100:.0f}%), "
            f"L3=${level_3_price:.2f} ({level_3_pct*100:.1f}%, exit {level_3_exit_pct*100:.0f}%)"
        )
        
        return plan
    
    def check_profit_levels(
        self,
        current_price: float,
        exit_plan: ProfitExitPlan,
        current_quantity: int
    ) -> ProfitCheckResult:
        """
        Check if any profit levels have been hit
        
        Args:
            current_price: Current market price
            exit_plan: Profit exit plan for the position
            current_quantity: Current quantity of shares held
            
        Returns:
            ProfitCheckResult indicating if exit should occur and how many shares
        """
        if current_quantity <= 0:
            return ProfitCheckResult(
                should_exit=False,
                exit_quantity=0,
                remaining_shares=0,
                message="No shares to exit"
            )
        
        profit_pct = ((current_price - exit_plan.entry_price) / exit_plan.entry_price) if exit_plan.entry_price > 0 else 0.0
        
        # Check levels from highest to lowest (so we exit at the highest level reached)
        # But track which levels have been hit
        
        # Level 3 (20%)
        if current_price >= exit_plan.level_3_price and ProfitLevel.LEVEL_3 not in exit_plan.levels_hit:
            exit_plan.levels_hit.append(ProfitLevel.LEVEL_3)
            # Exit remaining shares (whatever is left after level 1 and 2)
            exit_quantity = current_quantity
            return ProfitCheckResult(
                should_exit=True,
                exit_quantity=exit_quantity,
                profit_level=ProfitLevel.LEVEL_3,
                profit_pct=profit_pct,
                remaining_shares=0,
                message=f"Level 3 ({profit_pct*100:.1f}% profit) reached, exiting remaining {exit_quantity} shares"
            )
        
        # Level 2 (10%)
        if current_price >= exit_plan.level_2_price and ProfitLevel.LEVEL_2 not in exit_plan.levels_hit:
            exit_plan.levels_hit.append(ProfitLevel.LEVEL_2)
            if self.partial_exit_enabled:
                # Calculate exit quantity for level 2
                # We need to exit level_2_pct of ORIGINAL quantity, but account for what's already been sold
                # For simplicity, exit level_2_pct of current quantity (or use original if tracked)
                exit_quantity = int(current_quantity * exit_plan.level_2_exit_pct)
            else:
                # Full exit at level 2
                exit_quantity = current_quantity
            
            remaining = current_quantity - exit_quantity
            return ProfitCheckResult(
                should_exit=True,
                exit_quantity=exit_quantity,
                profit_level=ProfitLevel.LEVEL_2,
                profit_pct=profit_pct,
                remaining_shares=remaining,
                message=f"Level 2 ({profit_pct*100:.1f}% profit) reached, exiting {exit_quantity} shares ({remaining} remaining)"
            )
        
        # Level 1 (5%)
        if current_price >= exit_plan.level_1_price and ProfitLevel.LEVEL_1 not in exit_plan.levels_hit:
            exit_plan.levels_hit.append(ProfitLevel.LEVEL_1)
            if self.partial_exit_enabled:
                # Calculate exit quantity for level 1
                exit_quantity = int(current_quantity * exit_plan.level_1_exit_pct)
            else:
                # Full exit at level 1
                exit_quantity = current_quantity
            
            remaining = current_quantity - exit_quantity
            return ProfitCheckResult(
                should_exit=True,
                exit_quantity=exit_quantity,
                profit_level=ProfitLevel.LEVEL_1,
                profit_pct=profit_pct,
                remaining_shares=remaining,
                message=f"Level 1 ({profit_pct*100:.1f}% profit) reached, exiting {exit_quantity} shares ({remaining} remaining)"
            )
        
        # No level reached
        return ProfitCheckResult(
            should_exit=False,
            exit_quantity=0,
            profit_pct=profit_pct,
            remaining_shares=current_quantity,
            message=f"Current profit: {profit_pct*100:.2f}%, no exit levels reached"
        )
    
    def check_profit_for_position(
        self,
        position: Position,
        current_price: float,
        exit_plan: Optional[ProfitExitPlan] = None
    ) -> ProfitCheckResult:
        """
        Check profit levels for a database Position model
        
        Args:
            position: Position database model
            current_price: Current market price
            exit_plan: Optional exit plan (will create if not provided)
            
        Returns:
            ProfitCheckResult
        """
        if not exit_plan:
            # Create exit plan from position entry price
            exit_plan = self.create_exit_plan(
                entry_price=position.average_price,
                quantity=position.quantity
            )
        
        return self.check_profit_levels(
            current_price=current_price,
            exit_plan=exit_plan,
            current_quantity=position.quantity
        )
    
    def should_take_profit(
        self,
        entry_price: float,
        current_price: float,
        quantity: int,
        exit_plan: Optional[ProfitExitPlan] = None
    ) -> Tuple[bool, int, Optional[ProfitLevel]]:
        """
        Simplified check for profit taking (returns tuple for compatibility)
        
        Args:
            entry_price: Entry price
            current_price: Current price
            quantity: Current quantity
            exit_plan: Optional exit plan
            
        Returns:
            Tuple of (should_exit, exit_quantity, profit_level)
        """
        if not exit_plan:
            exit_plan = self.create_exit_plan(entry_price, quantity)
        
        result = self.check_profit_levels(current_price, exit_plan, quantity)
        return (result.should_exit, result.exit_quantity, result.profit_level)
    
    def get_profit_pct(self, entry_price: float, current_price: float) -> float:
        """
        Calculate profit percentage
        
        Args:
            entry_price: Entry price
            current_price: Current price
            
        Returns:
            Profit percentage (e.g., 0.05 for 5% profit)
        """
        if entry_price <= 0:
            return 0.0
        return ((current_price - entry_price) / entry_price)
    
    def get_profit_level_prices(
        self,
        entry_price: float,
        custom_levels: Optional[Tuple[float, float, float]] = None
    ) -> Tuple[float, float, float]:
        """
        Get profit level prices for entry price
        
        Args:
            entry_price: Entry price
            custom_levels: Optional custom levels
            
        Returns:
            Tuple of (level_1_price, level_2_price, level_3_price)
        """
        if custom_levels:
            level_1_pct, level_2_pct, level_3_pct = custom_levels
        else:
            level_1_pct = self.profit_level_1
            level_2_pct = self.profit_level_2
            level_3_pct = self.profit_level_3
        
        return (
            entry_price * (1 + level_1_pct),
            entry_price * (1 + level_2_pct),
            entry_price * (1 + level_3_pct)
        )


# Global ProfitTakingManager instance (singleton)
_profit_taking_manager: Optional[ProfitTakingManager] = None
_profit_taking_manager_lock = threading.Lock()


def get_profit_taking_manager() -> ProfitTakingManager:
    """
    Get global ProfitTakingManager instance (singleton)
    
    Returns:
        ProfitTakingManager instance
    """
    global _profit_taking_manager
    if _profit_taking_manager is None:
        with _profit_taking_manager_lock:
            # Double-check pattern
            if _profit_taking_manager is None:
                _profit_taking_manager = ProfitTakingManager()
                logger.info("ProfitTakingManager initialized")
    return _profit_taking_manager

