"""
Options chain schemas for API requests and responses.
"""

from __future__ import annotations

from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List
from datetime import date, datetime
from decimal import Decimal
from enum import Enum


class OptionType(str, Enum):
    """Option type enumeration."""
    CALL = "CALL"
    PUT = "PUT"


class OptionChainEntry(BaseModel):
    """Single option contract in the chain."""
    strike_price: Decimal = Field(..., description="Strike price")
    expiration_date: date = Field(..., description="Expiration date")
    option_type: OptionType = Field(..., description="Option type (CALL or PUT)")
    
    # Greeks
    delta: Optional[Decimal] = Field(None, description="Delta")
    gamma: Optional[Decimal] = Field(None, description="Gamma")
    theta: Optional[Decimal] = Field(None, description="Theta")
    vega: Optional[Decimal] = Field(None, description="Vega")
    rho: Optional[Decimal] = Field(None, description="Rho")
    
    # Market data
    implied_volatility: Optional[Decimal] = Field(None, ge=0, le=10, description="Implied volatility (0-10 = 0-1000%)")
    volume: Optional[int] = Field(None, ge=0, description="Volume")
    open_interest: Optional[int] = Field(None, ge=0, description="Open interest")
    
    # Pricing
    bid_price: Optional[Decimal] = Field(None, ge=0, description="Bid price")
    ask_price: Optional[Decimal] = Field(None, ge=0, description="Ask price")
    bid_ask_spread: Optional[Decimal] = Field(None, ge=0, description="Bid-ask spread")
    last_price: Optional[Decimal] = Field(None, ge=0, description="Last traded price")
    
    # Calculated fields
    mid_price: Optional[Decimal] = Field(None, description="Mid price (bid + ask) / 2")
    intrinsic_value: Optional[Decimal] = Field(None, description="Intrinsic value")
    time_value: Optional[Decimal] = Field(None, description="Time value")
    
    model_config = ConfigDict(from_attributes=True)


class OptionChainResponse(BaseModel):
    """Options chain response for a ticker."""
    ticker: str = Field(..., description="Ticker symbol")
    expiration_date: Optional[date] = Field(None, description="Expiration date filter (if specific expiration requested)")
    option_type: Optional[OptionType] = Field(None, description="Option type filter (if specific type requested)")
    chain: List[OptionChainEntry] = Field(default_factory=list, description="List of option contracts")
    as_of: datetime = Field(default_factory=datetime.now, description="Timestamp of data")
    
    model_config = ConfigDict(from_attributes=True)


class GreeksResponse(BaseModel):
    """Greeks data response for a ticker."""
    ticker: str = Field(..., description="Ticker symbol")
    strike_price: Optional[Decimal] = Field(None, description="Strike price filter (if specific strike requested)")
    expiration_date: Optional[date] = Field(None, description="Expiration date filter (if specific expiration requested)")
    greeks: List[OptionChainEntry] = Field(default_factory=list, description="List of Greeks data")
    as_of: datetime = Field(default_factory=datetime.now, description="Timestamp of data")
    
    model_config = ConfigDict(from_attributes=True)

