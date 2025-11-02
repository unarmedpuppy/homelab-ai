"""
Position Sizing Manager
=======================

Manages position sizing based on signal confidence and account rules.
"""

import logging
import threading
from typing import Optional, Tuple
from dataclasses import dataclass
from enum import Enum

from ...config.settings import settings
from .account_monitor import AccountMonitor

logger = logging.getLogger(__name__)


class ConfidenceLevel(str, Enum):
    """Signal confidence levels"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


@dataclass
class PositionSizeResult:
    """Result of position size calculation"""
    size_usd: float  # Position size in USD
    size_shares: int  # Position size in shares (rounded down)
    confidence_level: ConfidenceLevel
    base_percentage: float  # Base position size percentage
    actual_percentage: float  # Actual position size percentage (after caps)
    max_size_hit: bool  # Whether max position size cap was hit
    available_cash_used: float  # Percentage of available cash used


class PositionSizingManager:
    """
    Manage position sizing based on confidence and risk rules
    
    Features:
    - Confidence-based position sizing (low/medium/high)
    - Maximum position size caps
    - Account balance consideration
    - Cash account mode awareness
    """
    
    def __init__(self, account_monitor: Optional[AccountMonitor] = None):
        """
        Initialize position sizing manager
        
        Args:
            account_monitor: Optional AccountMonitor instance
        """
        self.account_monitor = account_monitor or AccountMonitor()
        
        # Get position sizing settings
        self.low_confidence_pct = settings.risk.position_size_low_confidence
        self.medium_confidence_pct = settings.risk.position_size_medium_confidence
        self.high_confidence_pct = settings.risk.position_size_high_confidence
        self.max_position_size_pct = settings.risk.max_position_size_pct
    
    def _get_confidence_level(self, confidence_score: float) -> ConfidenceLevel:
        """
        Determine confidence level from score
        
        Args:
            confidence_score: Confidence score (0.0 to 1.0)
            
        Returns:
            ConfidenceLevel enum
        """
        if confidence_score >= 0.7:
            return ConfidenceLevel.HIGH
        elif confidence_score >= 0.4:
            return ConfidenceLevel.MEDIUM
        else:
            return ConfidenceLevel.LOW
    
    def _get_base_position_percentage(self, confidence_level: ConfidenceLevel) -> float:
        """
        Get base position size percentage for confidence level
        
        Args:
            confidence_level: Confidence level
            
        Returns:
            Position size as percentage (0.0 to 1.0)
        """
        if confidence_level == ConfidenceLevel.HIGH:
            return self.high_confidence_pct
        elif confidence_level == ConfidenceLevel.MEDIUM:
            return self.medium_confidence_pct
        else:
            return self.low_confidence_pct
    
    async def calculate_position_size(
        self,
        account_id: int,
        confidence_score: float,
        price_per_share: float,
        min_shares: int = 1
    ) -> PositionSizeResult:
        """
        Calculate position size based on confidence and account balance
        
        Args:
            account_id: Account ID
            confidence_score: Signal confidence score (0.0 to 1.0)
            price_per_share: Price per share for the stock
            min_shares: Minimum number of shares (default: 1)
            
        Returns:
            PositionSizeResult with calculated size
        """
        # Validate inputs
        if confidence_score < 0.0 or confidence_score > 1.0:
            raise ValueError(f"Confidence score must be between 0.0 and 1.0, got {confidence_score}")
        
        if price_per_share <= 0:
            raise ValueError(f"Price per share must be positive, got {price_per_share}")
        
        # Get confidence level
        confidence_level = self._get_confidence_level(confidence_score)
        
        # Get account balance
        account_status = await self.account_monitor.check_account_balance(account_id)
        account_balance = account_status.balance
        
        if account_balance <= 0:
            logger.warning(f"Account {account_id} has zero or negative balance")
            return PositionSizeResult(
                size_usd=0.0,
                size_shares=0,
                confidence_level=confidence_level,
                base_percentage=0.0,
                actual_percentage=0.0,
                max_size_hit=True,
                available_cash_used=0.0
            )
        
        # Get base position size percentage
        base_percentage = self._get_base_position_percentage(confidence_level)
        
        # Calculate base position size in USD
        base_size_usd = account_balance * base_percentage
        
        # Apply maximum position size cap
        max_size_usd = account_balance * self.max_position_size_pct
        max_size_hit = False
        
        if base_size_usd > max_size_usd:
            base_size_usd = max_size_usd
            max_size_hit = True
            logger.debug(
                f"Position size capped at max: ${base_size_usd:,.2f} "
                f"(base: ${account_balance * base_percentage:,.2f}, max: {self.max_position_size_pct * 100:.1f}%)"
            )
        
        # Calculate shares (round down to avoid exceeding)
        size_shares = int(base_size_usd / price_per_share)
        
        # Ensure minimum shares
        if size_shares < min_shares:
            size_shares = 0
            base_size_usd = 0.0
            logger.debug(f"Position size below minimum ({min_shares} shares), setting to 0")
        else:
            # Recalculate USD to match exact share count
            base_size_usd = size_shares * price_per_share
        
        # Calculate actual percentage used
        actual_percentage = (base_size_usd / account_balance) if account_balance > 0 else 0.0
        available_cash_used = actual_percentage * 100
        
        logger.debug(
            f"Position size calculated: {size_shares} shares (${base_size_usd:,.2f}) "
            f"at {confidence_level.value} confidence ({confidence_score:.2f}), "
            f"using {actual_percentage * 100:.2f}% of account"
        )
        
        return PositionSizeResult(
            size_usd=base_size_usd,
            size_shares=size_shares,
            confidence_level=confidence_level,
            base_percentage=base_percentage,
            actual_percentage=actual_percentage,
            max_size_hit=max_size_hit,
            available_cash_used=available_cash_used
        )
    
    async def calculate_position_size_with_settlement(
        self,
        account_id: int,
        confidence_score: float,
        price_per_share: float,
        available_settled_cash: float,
        min_shares: int = 1
    ) -> PositionSizeResult:
        """
        Calculate position size considering only settled cash
        
        This is for cash account mode where only settled funds can be used.
        
        Args:
            account_id: Account ID
            confidence_score: Signal confidence score (0.0 to 1.0)
            price_per_share: Price per share for the stock
            available_settled_cash: Available settled cash amount
            min_shares: Minimum number of shares (default: 1)
            
        Returns:
            PositionSizeResult with calculated size
        """
        # Validate inputs
        if confidence_score < 0.0 or confidence_score > 1.0:
            raise ValueError(f"Confidence score must be between 0.0 and 1.0, got {confidence_score}")
        
        if price_per_share <= 0:
            raise ValueError(f"Price per share must be positive, got {price_per_share}")
        
        if available_settled_cash < 0:
            available_settled_cash = 0.0
        
        # Get confidence level
        confidence_level = self._get_confidence_level(confidence_score)
        
        # Get account balance for percentage calculation
        account_status = await self.account_monitor.check_account_balance(account_id)
        account_balance = account_status.balance
        
        # Get base position size percentage
        base_percentage = self._get_base_position_percentage(confidence_level)
        
        # Calculate base position size based on account balance (for percentage calculation)
        base_size_from_balance = account_balance * base_percentage
        
        # But actual position size is limited by available settled cash
        max_size_from_settled = available_settled_cash
        max_size_usd = account_balance * self.max_position_size_pct
        
        # Take the minimum of: base size, settled cash available, max cap
        base_size_usd = min(base_size_from_balance, max_size_from_settled, max_size_usd)
        max_size_hit = base_size_usd >= max_size_usd
        
        # If we're limited by settled cash, log it
        if base_size_usd < base_size_from_balance:
            if base_size_usd == max_size_from_settled:
                logger.debug(
                    f"Position size limited by settled cash: ${base_size_usd:,.2f} "
                    f"(desired: ${base_size_from_balance:,.2f}, settled: ${available_settled_cash:,.2f})"
                )
        
        # Calculate shares
        size_shares = int(base_size_usd / price_per_share)
        
        # Ensure minimum shares
        if size_shares < min_shares:
            size_shares = 0
            base_size_usd = 0.0
        else:
            # Recalculate USD to match exact share count
            base_size_usd = size_shares * price_per_share
        
        # Calculate actual percentage used
        actual_percentage = (base_size_usd / account_balance) if account_balance > 0 else 0.0
        settled_cash_pct = (base_size_usd / available_settled_cash * 100) if available_settled_cash > 0 else 0.0
        
        logger.debug(
            f"Position size calculated (with settlement): {size_shares} shares (${base_size_usd:,.2f}) "
            f"at {confidence_level.value} confidence, using {settled_cash_pct:.1f}% of settled cash"
        )
        
        return PositionSizeResult(
            size_usd=base_size_usd,
            size_shares=size_shares,
            confidence_level=confidence_level,
            base_percentage=base_percentage,
            actual_percentage=actual_percentage,
            max_size_hit=max_size_hit,
            available_cash_used=settled_cash_pct
        )
    
    def get_position_size_for_confidence(
        self,
        account_balance: float,
        confidence_level: ConfidenceLevel,
        price_per_share: float
    ) -> Tuple[float, int]:
        """
        Simple position size calculation (synchronous, no account lookup)
        
        Useful for quick calculations or testing.
        
        Args:
            account_balance: Account balance
            confidence_level: Confidence level
            price_per_share: Price per share
            
        Returns:
            Tuple of (size_usd, size_shares)
        """
        base_percentage = self._get_base_position_percentage(confidence_level)
        base_size_usd = account_balance * base_percentage
        
        # Apply max cap
        max_size_usd = account_balance * self.max_position_size_pct
        if base_size_usd > max_size_usd:
            base_size_usd = max_size_usd
        
        size_shares = int(base_size_usd / price_per_share)
        actual_size_usd = size_shares * price_per_share
        
        return (actual_size_usd, size_shares)


# Global PositionSizingManager instance (singleton)
_position_sizing_manager: Optional[PositionSizingManager] = None
_position_sizing_manager_lock = threading.Lock()


def get_position_sizing_manager() -> PositionSizingManager:
    """
    Get global PositionSizingManager instance (singleton)
    
    Returns:
        PositionSizingManager instance
    """
    global _position_sizing_manager
    if _position_sizing_manager is None:
        with _position_sizing_manager_lock:
            # Double-check pattern
            if _position_sizing_manager is None:
                _position_sizing_manager = PositionSizingManager()
                logger.info("PositionSizingManager initialized")
    return _position_sizing_manager

