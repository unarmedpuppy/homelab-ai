"""
Compliance Manager
==================

Manages cash account compliance rules:
- Pattern Day Trader (PDT) tracking and prevention
- T+2 settlement period tracking
- Trade frequency limits
- Good Faith Violation (GFV) prevention
"""

import logging
from typing import Optional, Dict, Any, Tuple, List
from datetime import datetime, timedelta, date
from dataclasses import dataclass
from enum import Enum

from ...data.database.models import (
    DayTrade, SettlementTracking, TradeFrequencyTracking, Trade, TradeSide, OrderStatus
)
from ...data.database import SessionLocal
from ...config.settings import settings
from .account_monitor import AccountMonitor

logger = logging.getLogger(__name__)


class ComplianceResult(str, Enum):
    """Compliance check results"""
    ALLOWED = "allowed"
    BLOCKED_PDT = "blocked_pdt"
    BLOCKED_SETTLEMENT = "blocked_settlement"
    BLOCKED_FREQUENCY = "blocked_frequency"
    BLOCKED_GFV = "blocked_gfv"
    WARNING = "warning"


@dataclass
class ComplianceCheck:
    """Result of a compliance check"""
    result: ComplianceResult
    message: str
    details: Optional[Dict[str, Any]] = None
    can_proceed: bool = True


class ComplianceManager:
    """
    Manage cash account compliance rules
    
    Features:
    - PDT violation prevention (max 3 day trades in 5 days)
    - T+2 settlement tracking
    - Trade frequency limits
    - GFV prevention
    """
    
    def __init__(self, account_monitor: Optional[AccountMonitor] = None):
        """
        Initialize compliance manager
        
        Args:
            account_monitor: Optional AccountMonitor instance
        """
        self.account_monitor = account_monitor or AccountMonitor()
        self.settlement_days = settings.risk.settlement_days
        self.pdt_enforcement = settings.risk.pdt_enforcement_mode
        self.gfv_enforcement_mode = settings.risk.gfv_enforcement_mode
        self.daily_limit = settings.risk.daily_trade_limit
        self.weekly_limit = settings.risk.weekly_trade_limit
    
    def calculate_settlement_date(self, trade_date: datetime) -> datetime:
        """
        Calculate settlement date (T+2 business days)
        
        Args:
            trade_date: Date of the trade
            
        Returns:
            Settlement date (trade date + 2 business days)
        """
        settlement_date = trade_date.date()
        business_days_added = 0
        
        while business_days_added < self.settlement_days:
            settlement_date += timedelta(days=1)
            # Skip weekends (Saturday = 5, Sunday = 6)
            if settlement_date.weekday() < 5:  # Monday-Friday
                business_days_added += 1
        
        # TODO: Add holiday calendar support (exclude market holidays)
        # For now, just skip weekends
        
        return datetime.combine(settlement_date, datetime.min.time())
    
    def is_business_day(self, check_date: date) -> bool:
        """
        Check if a date is a business day (Monday-Friday)
        
        Args:
            check_date: Date to check
            
        Returns:
            True if business day, False otherwise
        """
        return check_date.weekday() < 5  # Monday = 0, Friday = 4
    
    def get_day_trade_count(self, account_id: int, lookback_days: int = 5) -> int:
        """
        Get count of day trades in the last N business days
        
        Args:
            account_id: Account ID
            lookback_days: Number of business days to look back (default: 5)
            
        Returns:
            Count of day trades
        """
        session = SessionLocal()
        try:
            # Calculate cutoff date (N business days ago)
            now = datetime.now()
            cutoff_date = now
            business_days_back = 0
            
            # Go back day by day until we've counted N business days
            while business_days_back < lookback_days:
                cutoff_date -= timedelta(days=1)
                if self.is_business_day(cutoff_date.date()):
                    business_days_back += 1
            
            # Count day trades since cutoff (only count trades on or after cutoff date)
            count = session.query(DayTrade).filter(
                DayTrade.account_id == account_id,
                DayTrade.trade_date >= cutoff_date
            ).count()
            
            return count
        except (OSError, IOError) as e:
            # Database file access errors
            logger.error(f"Database I/O error getting day trade count: {e}", exc_info=True)
            return 0
        finally:
            session.close()
    
    async def check_pdt_compliance(
        self, 
        account_id: int, 
        symbol: str, 
        side: TradeSide,
        will_create_day_trade: bool = False
    ) -> ComplianceCheck:
        """
        Check if trade would violate PDT rules
        
        Args:
            account_id: Account ID
            symbol: Trading symbol
            side: Trade side (BUY or SELL)
            will_create_day_trade: Whether this trade would create a day trade
            
        Returns:
            ComplianceCheck result
        """
        # Check if account is in cash account mode
        try:
            is_cash_account = await self.account_monitor.is_cash_account_mode(account_id)
            if not is_cash_account:
                return ComplianceCheck(
                    result=ComplianceResult.ALLOWED,
                    message="Account not in cash account mode, PDT rules don't apply",
                    can_proceed=True
                )
        except (RuntimeError, ConnectionError, TimeoutError) as e:
            # IBKR/network errors checking account mode
            logger.warning(f"Could not check cash account mode (network error): {e}")
            # Continue with PDT check anyway
        except (KeyError, AttributeError) as e:
            # Account data structure errors
            logger.warning(f"Could not check cash account mode (data error): {e}")
            # Continue with PDT check anyway
        
        # Get current day trade count
        current_count = self.get_day_trade_count(account_id, lookback_days=5)
        
        # If this would create a day trade, increment count
        if will_create_day_trade:
            current_count += 1
        
        # Check if limit exceeded (max 3 day trades in 5 business days)
        if current_count >= 3:
            if self.pdt_enforcement == "strict":
                return ComplianceCheck(
                    result=ComplianceResult.BLOCKED_PDT,
                    message=f"PDT violation: {current_count} day trades in last 5 business days (limit: 3)",
                    details={"current_count": current_count, "limit": 3},
                    can_proceed=False
                )
            else:
                # Warning mode
                return ComplianceCheck(
                    result=ComplianceResult.WARNING,
                    message=f"PDT warning: {current_count} day trades in last 5 business days (limit: 3)",
                    details={"current_count": current_count, "limit": 3},
                    can_proceed=True
                )
        
        return ComplianceCheck(
            result=ComplianceResult.ALLOWED,
            message=f"PDT check passed: {current_count}/3 day trades used",
            details={"current_count": current_count, "limit": 3},
            can_proceed=True
        )
    
    def record_day_trade(
        self,
        account_id: int,
        symbol: str,
        buy_trade_id: int,
        sell_trade_id: int,
        trade_date: datetime
    ):
        """
        Record a day trade
        
        Args:
            account_id: Account ID
            symbol: Trading symbol
            buy_trade_id: ID of the buy trade
            sell_trade_id: ID of the sell trade
            trade_date: Date of the day trade
        """
        session = SessionLocal()
        try:
            day_trade = DayTrade(
                account_id=account_id,
                symbol=symbol,
                buy_trade_id=buy_trade_id,
                sell_trade_id=sell_trade_id,
                trade_date=trade_date
            )
            session.add(day_trade)
            session.commit()
            logger.info(f"Recorded day trade for {symbol} on account {account_id}")
        except Exception as e:
            session.rollback()
            logger.error(f"Error recording day trade: {e}", exc_info=True)
            raise
        finally:
            session.close()
    
    async def get_available_settled_cash(self, account_id: int) -> float:
        """
        Get available settled cash (cash that has settled T+2)
        
        Args:
            account_id: Account ID
            
        Returns:
            Available settled cash amount
        """
        session = SessionLocal()
        try:
            now = datetime.now()
            
            # Get total cash from account monitor
            account_status = await self.account_monitor.check_account_balance(account_id)
            total_cash = account_status.balance
            
            # Update settlement status first (inline to avoid creating another session)
            unsettled_to_settle = session.query(SettlementTracking).filter(
                SettlementTracking.account_id == account_id,
                SettlementTracking.is_settled == False,
                SettlementTracking.settlement_date <= now
            ).all()
            
            for settlement in unsettled_to_settle:
                settlement.is_settled = True
                settlement.settled_at = now
            
            if unsettled_to_settle:
                session.commit()
                logger.debug(f"Marked {len(unsettled_to_settle)} settlements as settled for account {account_id}")
            
            # Get all unsettled trades (settlement_date > now)
            unsettled_trades = session.query(SettlementTracking).filter(
                SettlementTracking.account_id == account_id,
                SettlementTracking.is_settled == False,
                SettlementTracking.settlement_date > now
            ).all()
            
            # Calculate total unsettled amounts
            # For SELL trades, amount is positive (cash received, but not settled for T+2)
            # For BUY trades, amount is negative (cash used, not yet settled)
            
            # Cash tied up in unsettled BUY trades (not available for new purchases)
            unsettled_buy_amount = sum(abs(st.amount) for st in unsettled_trades if st.amount < 0)
            
            # Unsettled SELL proceeds (cash received but not yet settled for T+2)
            # These are in the account balance but are not "settled" until T+2
            # While they can be used to buy securities, they shouldn't count as "settled cash"
            unsettled_sell_amount = sum(st.amount for st in unsettled_trades if st.amount > 0)
            
            # Available SETTLED cash = total cash - unsettled buy amounts - unsettled sell proceeds
            # This gives us only the cash that has fully settled (T+2 complete)
            available = max(0.0, total_cash - unsettled_buy_amount - unsettled_sell_amount)
            
            return available
        except Exception as e:
            logger.error(f"Error getting available settled cash: {e}", exc_info=True)
            # Fallback: return account balance
            try:
                account_status = await self.account_monitor.check_account_balance(account_id)
                return account_status.balance or 0.0
            except:
                return 0.0
        finally:
            session.close()
    
    async def check_settled_cash_available(
        self, 
        account_id: int, 
        required_amount: float
    ) -> Tuple[bool, float]:
        """
        Check if sufficient settled cash is available
        
        Args:
            account_id: Account ID
            required_amount: Amount needed
            
        Returns:
            Tuple of (is_available, available_amount)
        """
        available = await self.get_available_settled_cash(account_id)
        return available >= required_amount, available
    
    def record_settlement(
        self,
        account_id: int,
        trade_id: int,
        trade_date: datetime,
        amount: float
    ) -> SettlementTracking:
        """
        Record a trade for settlement tracking
        
        Args:
            account_id: Account ID
            trade_id: Trade ID
            trade_date: Date of the trade
            amount: Cash amount from trade (positive for sell, negative for buy)
            
        Returns:
            SettlementTracking record
        """
        session = SessionLocal()
        try:
            settlement_date = self.calculate_settlement_date(trade_date)
            
            settlement = SettlementTracking(
                account_id=account_id,
                trade_id=trade_id,
                trade_date=trade_date,
                settlement_date=settlement_date,
                amount=amount,
                is_settled=False
            )
            session.add(settlement)
            session.commit()
            
            logger.debug(
                f"Recorded settlement for trade {trade_id}: "
                f"trade_date={trade_date.date()}, settlement_date={settlement_date.date()}, amount=${amount:,.2f}"
            )
            
            return settlement
        except Exception as e:
            session.rollback()
            logger.error(f"Error recording settlement: {e}", exc_info=True)
            raise
        finally:
            session.close()
    
    def update_settled_status(self, account_id: int):
        """
        Update settlement status for trades that have settled
        
        Args:
            account_id: Account ID
        """
        session = SessionLocal()
        try:
            now = datetime.now()
            
            # Find all settlements that should be marked as settled
            unsettled = session.query(SettlementTracking).filter(
                SettlementTracking.account_id == account_id,
                SettlementTracking.is_settled == False,
                SettlementTracking.settlement_date <= now
            ).all()
            
            for settlement in unsettled:
                settlement.is_settled = True
                settlement.settled_at = now
            
            if unsettled:
                session.commit()
                logger.info(f"Marked {len(unsettled)} settlements as settled for account {account_id}")
        except Exception as e:
            session.rollback()
            logger.error(f"Error updating settlement status: {e}", exc_info=True)
        finally:
            session.close()
    
    async def check_trade_frequency(self, account_id: int) -> ComplianceCheck:
        """
        Check if trade frequency limits are exceeded
        
        Args:
            account_id: Account ID
            
        Returns:
            ComplianceCheck result
        """
        # Check if account is in cash account mode
        try:
            is_cash_account = await self.account_monitor.is_cash_account_mode(account_id)
            if not is_cash_account:
                return ComplianceCheck(
                    result=ComplianceResult.ALLOWED,
                    message="Account not in cash account mode, frequency limits don't apply",
                    can_proceed=True
                )
        except Exception as e:
            logger.warning(f"Could not check cash account mode: {e}")
        
        session = SessionLocal()
        try:
            now = datetime.now()
            today_start = datetime.combine(now.date(), datetime.min.time())
            
            # Get today's tracking record
            today_record = session.query(TradeFrequencyTracking).filter(
                TradeFrequencyTracking.account_id == account_id,
                TradeFrequencyTracking.date >= today_start
            ).first()
            
            # Get week start (Monday of current week)
            week_start = now - timedelta(days=now.weekday())
            week_start = datetime.combine(week_start.date(), datetime.min.time())
            
            # Get weekly tracking
            week_record = session.query(TradeFrequencyTracking).filter(
                TradeFrequencyTracking.account_id == account_id,
                TradeFrequencyTracking.week_start_date == week_start
            ).first()
            
            daily_count = today_record.daily_count if today_record else 0
            weekly_count = week_record.weekly_count if week_record else 0
            
            # Check limits
            if daily_count >= self.daily_limit:
                return ComplianceCheck(
                    result=ComplianceResult.BLOCKED_FREQUENCY,
                    message=f"Daily trade limit exceeded: {daily_count}/{self.daily_limit} trades",
                    details={"daily_count": daily_count, "daily_limit": self.daily_limit},
                    can_proceed=False
                )
            
            if weekly_count >= self.weekly_limit:
                return ComplianceCheck(
                    result=ComplianceResult.BLOCKED_FREQUENCY,
                    message=f"Weekly trade limit exceeded: {weekly_count}/{self.weekly_limit} trades",
                    details={"weekly_count": weekly_count, "weekly_limit": self.weekly_limit},
                    can_proceed=False
                )
            
            return ComplianceCheck(
                result=ComplianceResult.ALLOWED,
                message=f"Frequency check passed: {daily_count}/{self.daily_limit} daily, {weekly_count}/{self.weekly_limit} weekly",
                details={"daily_count": daily_count, "weekly_count": weekly_count},
                can_proceed=True
            )
        except Exception as e:
            logger.error(f"Error checking trade frequency: {e}", exc_info=True)
            # Allow trade if check fails (fail open)
            return ComplianceCheck(
                result=ComplianceResult.ALLOWED,
                message=f"Frequency check error, allowing trade: {e}",
                can_proceed=True
            )
        finally:
            session.close()
    
    def increment_trade_frequency(self, account_id: int, trade_date: datetime):
        """
        Increment trade frequency counters
        
        Args:
            account_id: Account ID
            trade_date: Date of the trade
        """
        session = SessionLocal()
        try:
            # Use trade_date or now
            now = trade_date if trade_date else datetime.now()
            today_start = datetime.combine(now.date(), datetime.min.time())
            
            # Get or create today's record
            today_record = session.query(TradeFrequencyTracking).filter(
                TradeFrequencyTracking.account_id == account_id,
                TradeFrequencyTracking.date >= today_start
            ).first()
            
            if not today_record:
                # Calculate week start (Monday)
                week_start = now - timedelta(days=now.weekday())
                week_start = datetime.combine(week_start.date(), datetime.min.time())
                
                today_record = TradeFrequencyTracking(
                    account_id=account_id,
                    date=today_start,
                    daily_count=0,
                    weekly_count=0,
                    week_start_date=week_start,
                    last_trade_at=now
                )
                session.add(today_record)
                session.flush()  # Flush to get the ID
            
            # Increment daily count
            today_record.daily_count += 1
            today_record.last_trade_at = now
            
            # Find or create week record (using week_start_date)
            week_record = session.query(TradeFrequencyTracking).filter(
                TradeFrequencyTracking.account_id == account_id,
                TradeFrequencyTracking.week_start_date == today_record.week_start_date,
                TradeFrequencyTracking.id != today_record.id  # Different from today's record
            ).first()
            
            # If no separate week record, use today's record for weekly count too
            # (weekly_count tracks across the week)
            if not week_record:
                # Check if today's record is the week start day
                if today_record.date.date() == today_record.week_start_date.date():
                    # Today IS the week start, use this record
                    today_record.weekly_count += 1
                else:
                    # Create a week record for tracking
                    week_record = TradeFrequencyTracking(
                        account_id=account_id,
                        date=today_record.week_start_date,
                        daily_count=0,
                        weekly_count=1,  # Start with 1 for this trade
                        week_start_date=today_record.week_start_date,
                        last_trade_at=now
                    )
                    session.add(week_record)
            else:
                week_record.weekly_count += 1
                week_record.last_trade_at = now
            
            session.commit()
            logger.debug(f"Incremented trade frequency for account {account_id}")
        except Exception as e:
            session.rollback()
            logger.error(f"Error incrementing trade frequency: {e}", exc_info=True)
            raise
        finally:
            session.close()
    
    def detect_day_trade(
        self,
        account_id: int,
        symbol: str,
        side: TradeSide,
        trade_date: datetime,
        trade_id: Optional[int] = None
    ) -> Optional[Tuple[int, int]]:
        """
        Detect if a trade creates a day trade
        
        A day trade occurs when:
        - A SELL happens on the same day as a BUY of the same symbol
        
        Args:
            account_id: Account ID
            symbol: Trading symbol
            side: Trade side (BUY or SELL)
            trade_date: Date of the trade
            trade_id: Optional trade ID (if trade already saved, must be filled)
            
        Returns:
            Tuple of (buy_trade_id, sell_trade_id) if day trade detected, None otherwise
        """
        if side == TradeSide.BUY:
            # For BUY, we can't detect day trade yet (need to wait for SELL)
            return None
        
        # For SELL, check if there was a BUY of same symbol today
        # Note: trade_id should only be provided if the SELL trade is already filled
        if not trade_id:
            logger.debug(f"Cannot detect day trade: trade_id not provided for SELL trade")
            return None
        
        session = SessionLocal()
        try:
            trade_date_start = datetime.combine(trade_date.date(), datetime.min.time())
            trade_date_end = datetime.combine(trade_date.date(), datetime.max.time())
            
            # Verify the SELL trade is filled
            sell_trade = session.query(Trade).filter(Trade.id == trade_id).first()
            if not sell_trade or sell_trade.status != OrderStatus.FILLED:
                logger.debug(f"SELL trade {trade_id} is not filled, cannot detect day trade")
                return None
            
            # Find BUY trades of same symbol on same day (only filled trades)
            buy_trades = session.query(Trade).filter(
                Trade.account_id == account_id,
                Trade.symbol == symbol,
                Trade.side == TradeSide.BUY,
                Trade.timestamp >= trade_date_start,
                Trade.timestamp <= trade_date_end,
                Trade.status == OrderStatus.FILLED  # Only filled trades
            ).order_by(Trade.timestamp.desc()).all()  # Most recent first
            
            if buy_trades:
                # Found a matching BUY on same day - this is a day trade
                # Use the most recent BUY trade
                buy_trade = buy_trades[0]
                return (buy_trade.id, trade_id)
            
            return None
        except Exception as e:
            logger.error(f"Error detecting day trade: {e}", exc_info=True)
            return None
        finally:
            session.close()
    
    async def check_gfv_prevention(
        self,
        account_id: int,
        symbol: str,
        side: TradeSide,
        amount: float
    ) -> ComplianceCheck:
        """
        Check for Good Faith Violation (GFV) prevention
        
        GFV occurs when:
        - Buying a security with unsettled funds from a sale
        - Then selling that security before the funds from the original sale have settled (T+2)
        - This creates a "free ride" violation
        
        Logic:
        - For BUY orders: Check if using unsettled funds
        - For SELL orders: Check if selling a position that was bought with unsettled funds
                          before those funds have settled
        
        Args:
            account_id: Account ID
            symbol: Trading symbol
            side: Trade side (BUY or SELL)
            amount: Trade amount (positive for sell, negative for buy)
            
        Returns:
            ComplianceCheck result
        """
        # Only check in cash account mode
        try:
            is_cash_account = await self.account_monitor.is_cash_account_mode(account_id)
            if not is_cash_account:
                return ComplianceCheck(
                    result=ComplianceResult.ALLOWED,
                    message="Account not in cash account mode, GFV checks skipped",
                    can_proceed=True
                )
        except Exception as e:
            logger.warning(f"Could not check cash account mode for GFV: {e}")
            # Proceed with checks if we can't determine mode
        
        session = SessionLocal()
        try:
            now = datetime.now()
            trade_amount = abs(amount)
            
            if side == TradeSide.BUY:
                # For BUY orders: Check if we're using unsettled funds
                # GFV scenario: Buying with funds from a sale that hasn't settled yet
                
                # Get available settled cash
                available_settled = await self.get_available_settled_cash(account_id)
                
                # Check if we have enough settled cash
                if available_settled >= trade_amount:
                    # We have enough settled cash, no GFV risk
                    return ComplianceCheck(
                        result=ComplianceResult.ALLOWED,
                        message=f"Sufficient settled cash available: ${available_settled:,.2f}",
                        can_proceed=True
                    )
                
                # We don't have enough settled cash - check if we're using unsettled funds
                # Get recent SELL trades that haven't settled yet
                unsettled_sells = session.query(SettlementTracking).join(Trade).filter(
                    SettlementTracking.account_id == account_id,
                    SettlementTracking.is_settled == False,
                    SettlementTracking.settlement_date > now,
                    SettlementTracking.amount > 0,  # Positive amount = SELL trade
                    Trade.status == OrderStatus.FILLED  # Only filled trades
                ).order_by(SettlementTracking.settlement_date).all()
                
                # Calculate total unsettled funds from sales
                total_unsettled_from_sales = sum(st.amount for st in unsettled_sells)
                
                # Check if we would be using unsettled funds
                shortfall = trade_amount - available_settled
                if shortfall > 0 and total_unsettled_from_sales >= shortfall:
                    # We're using unsettled funds - check if we have any positions in this symbol
                    # that were bought with unsettled funds (to detect potential GFV on future sell)
                    
                    # Get positions in this symbol that might have been bought with unsettled funds
                    # Check if we have any recent BUY trades in this symbol that haven't settled
                    recent_unsettled_buys = session.query(Trade).join(SettlementTracking).filter(
                        Trade.account_id == account_id,
                        Trade.symbol == symbol,
                        Trade.side == TradeSide.BUY,
                        Trade.status == OrderStatus.FILLED,
                        SettlementTracking.is_settled == False,
                        SettlementTracking.settlement_date > now,
                        SettlementTracking.amount < 0  # Negative amount = BUY trade
                    ).all()
                    
                    if recent_unsettled_buys:
                        # We already have unsettled BUY positions in this symbol
                        # This is a warning - if we buy more and then sell before settlement, it's a GFV
                        logger.warning(
                            f"GFV Risk: Buying {symbol} with unsettled funds while already holding "
                            f"unsettled BUY positions. If sold before settlement, this would be a GFV."
                        )
                        
                        # For now, allow but warn (could be made stricter)
                        return ComplianceCheck(
                            result=ComplianceResult.WARNING,
                            message=f"GFV Risk: Buying with unsettled funds. "
                                   f"Available settled: ${available_settled:,.2f}, "
                                   f"Unsettled from sales: ${total_unsettled_from_sales:,.2f}, "
                                   f"Need: ${trade_amount:,.2f}. "
                                   f"Warning: If you sell before funds settle (T+2), this may be a GFV.",
                            can_proceed=True
                        )
                    
                    # Using unsettled funds but no existing unsettled positions in this symbol
                    # This is acceptable - just track that we're using unsettled funds
                    return ComplianceCheck(
                        result=ComplianceResult.ALLOWED,
                        message=f"Using unsettled funds (${shortfall:,.2f}), but no existing unsettled positions. "
                               f"Available settled: ${available_settled:,.2f}",
                        can_proceed=True
                    )
                else:
                    # Not enough cash at all (neither settled nor unsettled)
                    return ComplianceCheck(
                        result=ComplianceResult.BLOCKED_SETTLEMENT,
                        message=f"Insufficient cash: need ${trade_amount:,.2f}, "
                               f"have ${available_settled:,.2f} settled + "
                               f"${total_unsettled_from_sales:,.2f} unsettled",
                        can_proceed=False
                    )
            
            elif side == TradeSide.SELL:
                # For SELL orders: Check if selling a position bought with unsettled funds
                # GFV scenario: Selling a security before the funds used to buy it have settled
                
                # Find recent BUY trades in this symbol that haven't settled yet
                unsettled_buys = session.query(Trade).join(SettlementTracking).filter(
                    Trade.account_id == account_id,
                    Trade.symbol == symbol,
                    Trade.side == TradeSide.BUY,
                    Trade.status == OrderStatus.FILLED,
                    SettlementTracking.is_settled == False,
                    SettlementTracking.settlement_date > now,
                    SettlementTracking.amount < 0  # Negative amount = BUY trade
                ).order_by(Trade.timestamp.desc()).all()
                
                if not unsettled_buys:
                    # No unsettled BUY positions, safe to sell
                    return ComplianceCheck(
                        result=ComplianceResult.ALLOWED,
                        message="No unsettled BUY positions in this symbol, GFV check passed",
                        can_proceed=True
                    )
                
                # Calculate total quantity bought with unsettled funds
                total_unsettled_quantity = sum(trade.quantity for trade in unsettled_buys)
                
                # Check if we're trying to sell more than we can without GFV
                # We can only sell the quantity that wasn't bought with unsettled funds
                # OR wait until funds settle
                
                # Get earliest settlement date
                settlement_dates = []
                for trade in unsettled_buys:
                    st = session.query(SettlementTracking).filter(
                        SettlementTracking.trade_id == trade.id
                    ).first()
                    if st:
                        settlement_dates.append(st.settlement_date)
                
                if not settlement_dates:
                    # No settlement tracking found, allow trade
                    return ComplianceCheck(
                        result=ComplianceResult.ALLOWED,
                        message="No settlement tracking found for unsettled buys, GFV check passed",
                        can_proceed=True
                    )
                
                earliest_settlement = min(settlement_dates)
                
                # Calculate how many shares we can sell without GFV
                # This is complex - we'd need to track which shares were bought with which funds
                # For now, block if we're trying to sell more than we have that's settled
                
                # Simplified check: If we have any unsettled buys and we're selling,
                # it's a potential GFV. Block if we're selling more than settled quantity.
                # We'll use a conservative approach: block if selling any amount when we have
                # unsettled buys (unless the sell quantity is less than settled quantity)
                
                # Get total positions (we'd need position tracking for this to be accurate)
                # For now, issue a warning if we have unsettled buys and are selling
                
                logger.warning(
                    f"GFV Risk: Attempting to sell {symbol} (amount: ${trade_amount:,.2f}) "
                    f"while holding {total_unsettled_quantity:.0f} shares bought with unsettled funds. "
                    f"Earliest settlement: {earliest_settlement}. "
                    f"This may be a Good Faith Violation if sold before settlement."
                )
                
                # For strict mode, block the trade
                # For warning mode, allow but warn
                if self.gfv_enforcement_mode == "strict":
                    return ComplianceCheck(
                        result=ComplianceResult.BLOCKED_GFV,
                        message=f"GFV Prevention: Cannot sell {symbol} before funds settle. "
                               f"Unsettled BUY quantity: {total_unsettled_quantity:.0f} shares. "
                               f"Earliest settlement date: {earliest_settlement.strftime('%Y-%m-%d')}. "
                               f"Wait until funds settle to avoid Good Faith Violation.",
                        details={
                            "unsettled_quantity": total_unsettled_quantity,
                            "earliest_settlement": earliest_settlement.isoformat()
                        },
                        can_proceed=False
                    )
                else:
                    # Warning mode - allow but warn
                    return ComplianceCheck(
                        result=ComplianceResult.WARNING,
                        message=f"GFV Warning: Selling {symbol} with unsettled BUY positions. "
                               f"Unsettled quantity: {total_unsettled_quantity:.0f} shares. "
                               f"Settlement date: {earliest_settlement.strftime('%Y-%m-%d')}. "
                               f"Proceed at your own risk - this may result in a Good Faith Violation.",
                        details={
                            "unsettled_quantity": total_unsettled_quantity,
                            "earliest_settlement": earliest_settlement.isoformat()
                        },
                        can_proceed=True
                    )
            
            # Default: allow
            return ComplianceCheck(
                result=ComplianceResult.ALLOWED,
                message="GFV check passed",
                can_proceed=True
            )
            
        except Exception as e:
            logger.error(f"Error checking GFV prevention: {e}", exc_info=True)
            # Fail open - allow trade if check fails
            return ComplianceCheck(
                result=ComplianceResult.ALLOWED,
                message=f"GFV check error, allowing trade: {e}",
                can_proceed=True
            )
        finally:
            session.close()
    
    async def _get_current_price(self, symbol: str) -> Optional[float]:
        """
        Helper method to get current price for a symbol
        Used for calculating quantities from amounts
        
        Args:
            symbol: Trading symbol
            
        Returns:
            Current price or None if unavailable
        """
        # TODO: Integrate with market data provider
        # For now, return None - callers should handle this
        return None
    
    async def check_compliance(
        self,
        account_id: int,
        symbol: str,
        side: TradeSide,
        amount: float,
        will_create_day_trade: bool = False
    ) -> ComplianceCheck:
        """
        Comprehensive compliance check before trade
        
        Args:
            account_id: Account ID
            symbol: Trading symbol
            side: Trade side (BUY or SELL)
            amount: Trade amount
            will_create_day_trade: Whether this would create a day trade
            
        Returns:
            ComplianceCheck result (first violation found, or ALLOWED)
        """
        # Check if in cash account mode
        try:
            is_cash_account = await self.account_monitor.is_cash_account_mode(account_id)
            if not is_cash_account:
                return ComplianceCheck(
                    result=ComplianceResult.ALLOWED,
                    message="Account not in cash account mode, compliance checks skipped",
                    can_proceed=True
                )
        except Exception as e:
            logger.warning(f"Could not check cash account mode: {e}, proceeding with checks")
        
        # 1. Check PDT compliance
        pdt_check = await self.check_pdt_compliance(
            account_id, symbol, side, will_create_day_trade
        )
        if not pdt_check.can_proceed:
            return pdt_check
        
        # 2. Check trade frequency
        freq_check = await self.check_trade_frequency(account_id)
        if not freq_check.can_proceed:
            return freq_check
        
        # 3. Check settled cash (for BUY orders)
        if side == TradeSide.BUY:
            has_settled, available = await self.check_settled_cash_available(account_id, abs(amount))
            if not has_settled:
                return ComplianceCheck(
                    result=ComplianceResult.BLOCKED_SETTLEMENT,
                    message=f"Insufficient settled cash: need ${abs(amount):,.2f}, have ${available:,.2f}",
                    details={"required": abs(amount), "available": available},
                    can_proceed=False
                )
        
        # 4. Check GFV prevention
        gfv_check = await self.check_gfv_prevention(account_id, symbol, side, amount)
        if not gfv_check.can_proceed:
            return gfv_check
        
        # All checks passed
        return ComplianceCheck(
            result=ComplianceResult.ALLOWED,
            message="All compliance checks passed",
            can_proceed=True
        )

