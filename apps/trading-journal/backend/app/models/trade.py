"""
Trade model for tracking individual trades.

Supports multiple trade types: STOCK, OPTION, CRYPTO_SPOT, CRYPTO_PERP, PREDICTION_MARKET.
"""

from sqlalchemy import String, Numeric, DateTime, Date, Text, Index, func, CheckConstraint
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.orm import Mapped, mapped_column
from datetime import datetime, date
from decimal import Decimal
from typing import Optional, List

from app.database import Base


class Trade(Base):
    """
    Trade model representing a single trade entry.
    
    Supports multiple trade types with type-specific fields.
    Includes calculation methods for P&L, ROI, and R-multiple.
    """
    __tablename__ = "trades"
    
    # Primary key
    id: Mapped[int] = mapped_column(primary_key=True)
    
    # User (single user for MVP)
    user_id: Mapped[int] = mapped_column(nullable=False, server_default="1")
    
    # Basic trade information
    ticker: Mapped[str] = mapped_column(String(20), nullable=False)
    trade_type: Mapped[str] = mapped_column(String(20), nullable=False)  # STOCK, OPTION, CRYPTO_SPOT, CRYPTO_PERP, PREDICTION_MARKET
    side: Mapped[str] = mapped_column(String(10), nullable=False)  # LONG, SHORT
    
    # Entry details
    entry_price: Mapped[Decimal] = mapped_column(Numeric(12, 4), nullable=False)
    entry_quantity: Mapped[Decimal] = mapped_column(Numeric(12, 4), nullable=False)
    entry_time: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    entry_commission: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False, server_default="0")
    
    # Exit details
    exit_price: Mapped[Optional[Decimal]] = mapped_column(Numeric(12, 4), nullable=True)
    exit_quantity: Mapped[Optional[Decimal]] = mapped_column(Numeric(12, 4), nullable=True)
    exit_time: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    exit_commission: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False, server_default="0")
    
    # Options specific fields
    strike_price: Mapped[Optional[Decimal]] = mapped_column(Numeric(12, 4), nullable=True)
    expiration_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    option_type: Mapped[Optional[str]] = mapped_column(String(4), nullable=True)  # CALL, PUT
    
    # Greeks
    delta: Mapped[Optional[Decimal]] = mapped_column(Numeric(8, 4), nullable=True)
    gamma: Mapped[Optional[Decimal]] = mapped_column(Numeric(8, 6), nullable=True)
    theta: Mapped[Optional[Decimal]] = mapped_column(Numeric(8, 4), nullable=True)
    vega: Mapped[Optional[Decimal]] = mapped_column(Numeric(8, 4), nullable=True)
    rho: Mapped[Optional[Decimal]] = mapped_column(Numeric(8, 4), nullable=True)
    
    # Options market data
    implied_volatility: Mapped[Optional[Decimal]] = mapped_column(Numeric(6, 4), nullable=True)
    volume: Mapped[Optional[int]] = mapped_column(nullable=True)
    open_interest: Mapped[Optional[int]] = mapped_column(nullable=True)
    bid_price: Mapped[Optional[Decimal]] = mapped_column(Numeric(12, 4), nullable=True)
    ask_price: Mapped[Optional[Decimal]] = mapped_column(Numeric(12, 4), nullable=True)
    bid_ask_spread: Mapped[Optional[Decimal]] = mapped_column(Numeric(12, 4), nullable=True)
    
    # Crypto specific fields
    crypto_exchange: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    crypto_pair: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    
    # Prediction market specific fields
    prediction_market_platform: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    prediction_outcome: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    
    # Calculated fields (can be computed or stored)
    net_pnl: Mapped[Optional[Decimal]] = mapped_column(Numeric(12, 2), nullable=True)
    net_roi: Mapped[Optional[Decimal]] = mapped_column(Numeric(8, 4), nullable=True)
    realized_r_multiple: Mapped[Optional[Decimal]] = mapped_column(Numeric(8, 4), nullable=True)
    
    # Metadata
    status: Mapped[str] = mapped_column(String(20), nullable=False, server_default="open")  # open, closed, partial
    playbook: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    tags: Mapped[Optional[List[str]]] = mapped_column(ARRAY(Text), nullable=True)
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, server_default=func.current_timestamp())
    updated_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, server_default=func.current_timestamp(), onupdate=func.current_timestamp())
    
    # Indexes (defined in migration, but documented here)
    __table_args__ = (
        Index("idx_trades_entry_time", "entry_time"),
        Index("idx_trades_ticker", "ticker"),
        Index("idx_trades_status", "status"),
        Index("idx_trades_trade_type", "trade_type"),
        Index("idx_trades_expiration_date", "expiration_date"),
        CheckConstraint("side IN ('LONG', 'SHORT')", name="check_trade_side"),
        CheckConstraint("trade_type IN ('STOCK', 'OPTION', 'CRYPTO_SPOT', 'CRYPTO_PERP', 'PREDICTION_MARKET')", name="check_trade_type"),
        CheckConstraint("status IN ('open', 'closed', 'partial')", name="check_trade_status"),
    )
    
    def calculate_net_pnl(self) -> Optional[Decimal]:
        """
        Calculate net P&L for the trade.
        
        Returns:
            Net P&L as Decimal, or None if trade is not closed
        """
        if not self.exit_price or not self.exit_quantity:
            return None
        
        # Use exit_quantity if partial fill, otherwise use entry_quantity
        quantity = self.exit_quantity if self.exit_quantity else self.entry_quantity
        
        # Calculate price difference based on side
        if self.side == "LONG":
            price_diff = self.exit_price - self.entry_price
        else:  # SHORT
            price_diff = self.entry_price - self.exit_price
        
        # Calculate base P&L
        if self.trade_type == "OPTION":
            # Options: multiply by 100 (contract size)
            base_pnl = price_diff * quantity * Decimal("100")
        else:
            # Stocks, crypto, prediction markets
            base_pnl = price_diff * quantity
        
        # Subtract commissions
        net_pnl = base_pnl - self.entry_commission - self.exit_commission
        
        return net_pnl
    
    def calculate_net_roi(self) -> Optional[Decimal]:
        """
        Calculate net ROI (Return on Investment) as a percentage.
        
        Returns:
            ROI as Decimal percentage, or None if trade is not closed
        """
        net_pnl = self.calculate_net_pnl()
        if net_pnl is None:
            return None
        
        # Calculate total cost
        if self.trade_type == "OPTION":
            # Options: multiply by 100 (contract size)
            total_cost = (self.entry_price * self.entry_quantity * Decimal("100")) + self.entry_commission
        else:
            total_cost = (self.entry_price * self.entry_quantity) + self.entry_commission
        
        if total_cost == 0:
            return Decimal("0")
        
        # ROI = (Net P&L / Total Cost) × 100
        roi = (net_pnl / total_cost) * Decimal("100")
        
        return roi
    
    def calculate_r_multiple(self, stop_loss: Optional[Decimal] = None) -> Optional[Decimal]:
        """
        Calculate R-multiple for the trade.
        
        Args:
            stop_loss: Optional stop loss price. If not provided, uses entry price as risk.
        
        Returns:
            R-multiple as Decimal, or None if trade is not closed
        """
        net_pnl = self.calculate_net_pnl()
        if net_pnl is None:
            return None
        
        # Calculate risk amount
        if stop_loss is not None:
            if self.side == "LONG":
                risk_per_unit = self.entry_price - stop_loss
            else:  # SHORT
                risk_per_unit = stop_loss - self.entry_price
        else:
            # Default: use entry price as risk
            risk_per_unit = self.entry_price
        
        # Calculate total risk
        if self.trade_type == "OPTION":
            risk_amount = risk_per_unit * self.entry_quantity * Decimal("100")
        else:
            risk_amount = risk_per_unit * self.entry_quantity
        
        if risk_amount == 0:
            return Decimal("0")
        
        # R-multiple = Net P&L / Risk Amount
        r_multiple = net_pnl / risk_amount
        
        return r_multiple
    
    def update_calculated_fields(self, stop_loss: Optional[Decimal] = None) -> None:
        """
        Update calculated fields (net_pnl, net_roi, realized_r_multiple).
        
        Args:
            stop_loss: Optional stop loss price for R-multiple calculation
        """
        self.net_pnl = self.calculate_net_pnl()
        self.net_roi = self.calculate_net_roi()
        self.realized_r_multiple = self.calculate_r_multiple(stop_loss=stop_loss)
    
    def is_closed(self) -> bool:
        """Check if trade is closed."""
        return self.status == "closed" and self.exit_price is not None
    
    def is_winner(self) -> Optional[bool]:
        """
        Check if trade is a winner.
        
        Returns:
            True if winner, False if loser, None if not closed
        """
        if not self.is_closed():
            return None
        pnl = self.calculate_net_pnl()
        return pnl is not None and pnl > 0
    
    def __repr__(self) -> str:
        """String representation for debugging."""
        return f"<Trade(id={self.id}, ticker={self.ticker}, trade_type={self.trade_type}, side={self.side}, status={self.status})>"

