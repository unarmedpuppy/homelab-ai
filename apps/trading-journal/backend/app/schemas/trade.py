"""
Trade schemas for API requests and responses.
"""

from __future__ import annotations

from pydantic import BaseModel, Field, field_validator, model_validator, ConfigDict
from typing import Optional, List, TYPE_CHECKING
from datetime import datetime, date as DateType
from decimal import Decimal
from enum import Enum

if TYPE_CHECKING:
    from datetime import date


class TradeType(str, Enum):
    """Trade type enumeration."""
    STOCK = "STOCK"
    OPTION = "OPTION"
    CRYPTO_SPOT = "CRYPTO_SPOT"
    CRYPTO_PERP = "CRYPTO_PERP"
    PREDICTION_MARKET = "PREDICTION_MARKET"


class TradeSide(str, Enum):
    """Trade side enumeration."""
    LONG = "LONG"
    SHORT = "SHORT"


class TradeStatus(str, Enum):
    """Trade status enumeration."""
    OPEN = "open"
    CLOSED = "closed"
    PARTIAL = "partial"


class OptionType(str, Enum):
    """Option type enumeration."""
    CALL = "CALL"
    PUT = "PUT"


# Base schema with common fields
class TradeBase(BaseModel):
    """Base trade schema with common fields."""
    ticker: str = Field(..., min_length=1, max_length=20, description="Ticker symbol")
    trade_type: TradeType = Field(..., description="Type of trade")
    side: TradeSide = Field(..., description="Trade side (LONG or SHORT)")
    
    # Entry details
    entry_price: Decimal = Field(..., gt=0, description="Entry price")
    entry_quantity: Decimal = Field(..., gt=0, description="Entry quantity")
    entry_time: datetime = Field(..., description="Entry timestamp")
    entry_commission: Decimal = Field(default=Decimal("0"), ge=0, description="Entry commission")
    
    # Exit details (optional for open trades)
    exit_price: Optional[Decimal] = Field(None, gt=0, description="Exit price")
    exit_quantity: Optional[Decimal] = Field(None, gt=0, description="Exit quantity")
    exit_time: Optional[datetime] = Field(None, description="Exit timestamp")
    exit_commission: Decimal = Field(default=Decimal("0"), ge=0, description="Exit commission")
    
    # Options specific fields
    strike_price: Optional[Decimal] = Field(None, gt=0, description="Strike price (options only)")
    expiration_date: Optional[DateType] = Field(None, description="Expiration date (options only)")
    option_type: Optional[OptionType] = Field(None, description="Option type (CALL or PUT)")
    delta: Optional[Decimal] = Field(None, description="Delta (options only)")
    gamma: Optional[Decimal] = Field(None, description="Gamma (options only)")
    theta: Optional[Decimal] = Field(None, description="Theta (options only)")
    vega: Optional[Decimal] = Field(None, description="Vega (options only)")
    rho: Optional[Decimal] = Field(None, description="Rho (options only)")
    implied_volatility: Optional[Decimal] = Field(None, ge=0, le=10, description="Implied volatility (options only)")
    volume: Optional[int] = Field(None, ge=0, description="Volume (options only)")
    open_interest: Optional[int] = Field(None, ge=0, description="Open interest (options only)")
    bid_price: Optional[Decimal] = Field(None, ge=0, description="Bid price (options only)")
    ask_price: Optional[Decimal] = Field(None, ge=0, description="Ask price (options only)")
    bid_ask_spread: Optional[Decimal] = Field(None, ge=0, description="Bid-ask spread (options only)")
    
    # Crypto specific fields
    crypto_exchange: Optional[str] = Field(None, max_length=50, description="Crypto exchange (crypto only)")
    crypto_pair: Optional[str] = Field(None, max_length=20, description="Crypto pair (crypto only)")
    
    # Prediction market specific fields
    prediction_market_platform: Optional[str] = Field(None, max_length=50, description="Prediction market platform")
    prediction_outcome: Optional[str] = Field(None, max_length=200, description="Prediction outcome")
    
    # Metadata
    status: TradeStatus = Field(default=TradeStatus.OPEN, description="Trade status")
    playbook: Optional[str] = Field(None, max_length=100, description="Trading playbook/strategy")
    notes: Optional[str] = Field(None, description="Trade notes")
    tags: Optional[List[str]] = Field(None, description="Trade tags")
    
    @field_validator("ticker")
    @classmethod
    def validate_ticker(cls, v: str) -> str:
        """Validate and normalize ticker symbol."""
        return v.upper().strip()
    
    @model_validator(mode='after')
    def validate_exit_after_entry(self):
        """Validate that exit_time is after entry_time."""
        if self.exit_time and self.entry_time:
            if self.exit_time < self.entry_time:
                raise ValueError("Exit time must be after entry time")
        return self
    
    @model_validator(mode='after')
    def validate_exit_quantity(self):
        """Validate that exit_quantity does not exceed entry_quantity."""
        if self.exit_quantity and self.entry_quantity:
            if self.exit_quantity > self.entry_quantity:
                raise ValueError(f"Exit quantity ({self.exit_quantity}) cannot exceed entry quantity ({self.entry_quantity})")
        return self
    
    @model_validator(mode='after')
    def validate_closed_trade_fields(self):
        """Validate that closed trades have all required exit fields."""
        if self.status == TradeStatus.CLOSED:
            if not self.exit_price:
                raise ValueError("Closed trades must have an exit price")
            if not self.exit_quantity:
                raise ValueError("Closed trades must have an exit quantity")
            if not self.exit_time:
                raise ValueError("Closed trades must have an exit time")
        return self
    
    @model_validator(mode='after')
    def validate_options_fields(self):
        """Validate options-specific fields."""
        if self.trade_type == TradeType.OPTION:
            # Strike price is required for options
            if not self.strike_price:
                raise ValueError("Strike price is required for option trades")
            if not self.expiration_date:
                raise ValueError("Expiration date is required for option trades")
            if not self.option_type:
                raise ValueError("Option type (CALL or PUT) is required for option trades")
            
            # Validate Greeks ranges (reasonable bounds)
            if self.delta is not None:
                if abs(self.delta) > 1:
                    raise ValueError(f"Delta must be between -1 and 1, got {self.delta}")
            
            if self.gamma is not None:
                if self.gamma < 0 or self.gamma > 1:
                    raise ValueError(f"Gamma must be between 0 and 1, got {self.gamma}")
            
            if self.vega is not None:
                if self.vega < 0:
                    raise ValueError(f"Vega must be non-negative, got {self.vega}")
            
            if self.theta is not None:
                if self.theta > 0:
                    raise ValueError(f"Theta should typically be negative for long options, got {self.theta}")
            
            # Validate expiration date is in the future for new trades
            if self.expiration_date and self.entry_time:
                if self.expiration_date < self.entry_time.date():
                    raise ValueError("Expiration date must be on or after entry date")
            
            # Validate bid/ask prices
            if self.bid_price is not None and self.ask_price is not None:
                if self.bid_price > self.ask_price:
                    raise ValueError(f"Bid price ({self.bid_price}) cannot exceed ask price ({self.ask_price})")
                
                # Validate bid-ask spread if provided
                if self.bid_ask_spread is not None:
                    calculated_spread = self.ask_price - self.bid_price
                    if abs(self.bid_ask_spread - calculated_spread) > Decimal("0.01"):
                        raise ValueError(f"Bid-ask spread ({self.bid_ask_spread}) does not match calculated spread ({calculated_spread})")
        
        return self
    
    @model_validator(mode='after')
    def validate_trade_type_fields(self):
        """Validate that trade-type-specific fields are only set for appropriate types."""
        # Options fields should only be set for OPTION trades
        if self.trade_type != TradeType.OPTION:
            if any([
                self.strike_price, self.expiration_date, self.option_type,
                self.delta, self.gamma, self.theta, self.vega, self.rho,
                self.implied_volatility, self.volume, self.open_interest,
                self.bid_price, self.ask_price, self.bid_ask_spread
            ]):
                raise ValueError(f"Options-specific fields can only be set for OPTION trade type, but got {self.trade_type}")
        
        # Crypto fields should only be set for crypto trades
        if self.trade_type not in [TradeType.CRYPTO_SPOT, TradeType.CRYPTO_PERP]:
            if self.crypto_exchange or self.crypto_pair:
                raise ValueError(f"Crypto-specific fields can only be set for CRYPTO_SPOT or CRYPTO_PERP trade types, but got {self.trade_type}")
        
        # Prediction market fields should only be set for prediction market trades
        if self.trade_type != TradeType.PREDICTION_MARKET:
            if self.prediction_market_platform or self.prediction_outcome:
                raise ValueError(f"Prediction market fields can only be set for PREDICTION_MARKET trade type, but got {self.trade_type}")
        
        return self


class TradeCreate(TradeBase):
    """Schema for creating a new trade."""
    pass


class TradeUpdate(BaseModel):
    """Schema for updating a trade (all fields optional)."""
    ticker: Optional[str] = Field(None, min_length=1, max_length=20)
    trade_type: Optional[TradeType] = None
    side: Optional[TradeSide] = None
    
    # Entry details
    entry_price: Optional[Decimal] = Field(None, gt=0)
    entry_quantity: Optional[Decimal] = Field(None, gt=0)
    entry_time: Optional[datetime] = None
    entry_commission: Optional[Decimal] = Field(None, ge=0)
    
    # Exit details
    exit_price: Optional[Decimal] = Field(None, gt=0)
    exit_quantity: Optional[Decimal] = Field(None, gt=0)
    exit_time: Optional[datetime] = None
    exit_commission: Optional[Decimal] = Field(None, ge=0)
    
    # Options specific
    strike_price: Optional[Decimal] = Field(None, gt=0)
    expiration_date: Optional[DateType] = None
    option_type: Optional[OptionType] = None
    delta: Optional[Decimal] = None
    gamma: Optional[Decimal] = None
    theta: Optional[Decimal] = None
    vega: Optional[Decimal] = None
    rho: Optional[Decimal] = None
    implied_volatility: Optional[Decimal] = Field(None, ge=0, le=10)
    volume: Optional[int] = Field(None, ge=0)
    open_interest: Optional[int] = Field(None, ge=0)
    bid_price: Optional[Decimal] = Field(None, ge=0)
    ask_price: Optional[Decimal] = Field(None, ge=0)
    bid_ask_spread: Optional[Decimal] = Field(None, ge=0)
    
    # Crypto specific
    crypto_exchange: Optional[str] = Field(None, max_length=50)
    crypto_pair: Optional[str] = Field(None, max_length=20)
    
    # Prediction market specific
    prediction_market_platform: Optional[str] = Field(None, max_length=50)
    prediction_outcome: Optional[str] = Field(None, max_length=200)
    
    # Metadata
    status: Optional[TradeStatus] = None
    playbook: Optional[str] = Field(None, max_length=100)
    notes: Optional[str] = None
    tags: Optional[List[str]] = None
    
    model_config = ConfigDict(extra="forbid")


class TradeResponse(TradeBase):
    """Schema for trade response."""
    id: int
    user_id: int
    net_pnl: Optional[Decimal] = None
    net_roi: Optional[Decimal] = None
    realized_r_multiple: Optional[Decimal] = None
    created_at: datetime
    updated_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


class TradeListResponse(BaseModel):
    """Schema for paginated trade list response."""
    trades: List[TradeResponse]
    total: int
    limit: int
    offset: int
    has_more: bool

