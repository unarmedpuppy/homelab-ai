"""
Account Monitor
===============

Monitors account balance and manages cash account mode state.
"""

import logging
import threading
from typing import Optional, Dict, Any
from datetime import datetime, timedelta
from dataclasses import dataclass

from ...data.database.models import CashAccountState, Account
from ...data.database import SessionLocal
from ...config.settings import settings

logger = logging.getLogger(__name__)


@dataclass
class AccountStatus:
    """Account status information"""
    account_id: int
    balance: float
    is_cash_account_mode: bool
    threshold: float
    available_cash: Optional[float] = None
    last_checked: Optional[datetime] = None


class AccountMonitor:
    """
    Monitor account balance and manage cash account mode
    
    Features:
    - Automatic balance detection from IBKR
    - Cash account mode activation (< $25k threshold)
    - Balance history tracking
    - State persistence in database
    """
    
    def __init__(self, ibkr_client=None):
        """
        Initialize account monitor
        
        Args:
            ibkr_client: Optional IBKR client instance
        """
        self.ibkr_client = ibkr_client
        self.cache_duration = timedelta(minutes=5)  # Cache balance for 5 minutes
        self._cached_status: Optional[AccountStatus] = None
        self._cache_timestamp: Optional[datetime] = None
        self._cache_lock = threading.Lock()  # Thread safety for cache
        
    async def check_account_balance(self, account_id: int) -> AccountStatus:
        """
        Check account balance and update cash account state
        
        Args:
            account_id: Account ID to check
            
        Returns:
            AccountStatus with current balance and cash account mode
        """
        # Check cache first (thread-safe)
        with self._cache_lock:
            if self._cached_status and self._cache_timestamp:
                if (datetime.now() - self._cache_timestamp) < self.cache_duration:
                    if self._cached_status.account_id == account_id:
                        logger.debug(f"Returning cached account status for account {account_id}")
                        return self._cached_status
        
        # Get balance from IBKR if client available
        balance = None
        if self.ibkr_client and self.ibkr_client.connected:
            try:
                account_summary = await self.ibkr_client.get_account_summary()
                # Extract balance from account summary
                # IBKR uses different tags: "TotalCashValue", "NetLiquidation", etc.
                balance = self._extract_balance_from_summary(account_summary)
                logger.debug(f"Retrieved balance from IBKR: ${balance:,.2f}")
            except Exception as e:
                logger.warning(f"Failed to get balance from IBKR: {e}, using cached value")
        
        # Get or create cash account state
        session = SessionLocal()
        try:
            state = session.query(CashAccountState).filter(
                CashAccountState.account_id == account_id
            ).first()
            
            threshold = settings.risk.cash_account_threshold
            
            if not state:
                # Create new state
                state = CashAccountState(
                    account_id=account_id,
                    balance=balance or 0.0,
                    is_cash_account_mode=(balance or 0.0) < threshold if balance else False,
                    threshold=threshold
                )
                session.add(state)
                session.commit()
                logger.info(f"Created cash account state for account {account_id}")
            else:
                # Update existing state
                if balance is not None:
                    old_mode = state.is_cash_account_mode
                    state.balance = balance
                    state.is_cash_account_mode = balance < threshold
                    state.last_checked = datetime.now()
                    
                    # Log mode change
                    if old_mode != state.is_cash_account_mode:
                        mode_str = "enabled" if state.is_cash_account_mode else "disabled"
                        logger.info(
                            f"Cash account mode {mode_str} for account {account_id} "
                            f"(balance: ${balance:,.2f}, threshold: ${threshold:,.2f})"
                        )
                    
                    session.commit()
            
            # Build status object
            status = AccountStatus(
                account_id=state.account_id,
                balance=state.balance,
                is_cash_account_mode=state.is_cash_account_mode,
                threshold=state.threshold,
                last_checked=state.last_checked
            )
            
            # Cache the status (thread-safe)
            with self._cache_lock:
                self._cached_status = status
                self._cache_timestamp = datetime.now()
            
            return status
        except Exception as e:
            session.rollback()
            logger.error(f"Error checking account balance: {e}", exc_info=True)
            raise
        finally:
            session.close()
    
    def _extract_balance_from_summary(self, account_summary: Dict[str, Any]) -> float:
        """
        Extract account balance from IBKR account summary
        
        Args:
            account_summary: Account summary dictionary from IBKR
            
        Returns:
            Account balance as float
        """
        # IBKR account summary tags (prefer NetLiquidation, fallback to TotalCashValue)
        balance_tags = ["NetLiquidation", "TotalCashValue", "AvailableFunds", "BuyingPower"]
        
        for tag in balance_tags:
            if tag in account_summary:
                try:
                    value = account_summary[tag]
                    if isinstance(value, dict):
                        balance = float(value.get("value", 0))
                    else:
                        balance = float(value)
                    
                    if balance > 0:
                        return balance
                except (ValueError, TypeError) as e:
                    logger.warning(f"Failed to parse balance from tag {tag}: {e}")
                    continue
        
        logger.warning("Could not extract balance from account summary")
        return 0.0
    
    async def is_cash_account_mode(self, account_id: int) -> bool:
        """
        Check if account is in cash account mode
        
        Args:
            account_id: Account ID to check
            
        Returns:
            True if in cash account mode, False otherwise
        """
        status = await self.check_account_balance(account_id)
        return status.is_cash_account_mode
    
    async def get_available_cash(self, account_id: int) -> float:
        """
        Get available cash for trading (considering settlements)
        
        Args:
            account_id: Account ID
            
        Returns:
            Available cash amount
        """
        status = await self.check_account_balance(account_id)
        
        # For now, return balance. Will be enhanced in Phase 2 with settlement tracking
        # TODO: Subtract unsettled funds from balance
        return status.balance if status.balance else 0.0
    
    def get_cached_status(self, account_id: int) -> Optional[AccountStatus]:
        """
        Get cached account status without querying IBKR
        
        Args:
            account_id: Account ID
            
        Returns:
            Cached AccountStatus or None if not cached
        """
        with self._cache_lock:
            if (self._cached_status and 
                self._cached_status.account_id == account_id and
                self._cache_timestamp and
                (datetime.now() - self._cache_timestamp) < self.cache_duration):
                return self._cached_status
        return None
    
    def clear_cache(self):
        """Clear cached account status"""
        with self._cache_lock:
            self._cached_status = None
            self._cache_timestamp = None

