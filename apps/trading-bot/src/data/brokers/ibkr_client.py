"""
Interactive Brokers Integration
==============================

Production-ready IBKR client with proper error handling, reconnection,
and position management.
"""

import asyncio
import logging
import time
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum

try:
    import pandas as pd
except ImportError:
    pd = None

try:
    from ib_insync import IB, util, Stock, MarketOrder, LimitOrder, Contract, Position, Order, Trade, Fill
except ImportError:
    IB = None
    util = None
    Stock = None
    MarketOrder = None
    LimitOrder = None
    Contract = None
    Position = None
    Order = None
    Trade = None
    Fill = None

logger = logging.getLogger(__name__)

class OrderType(Enum):
    """Order types"""
    MARKET = "MKT"
    LIMIT = "LMT"
    STOP = "STP"
    STOP_LIMIT = "STP LMT"

class OrderSide(Enum):
    """Order sides"""
    BUY = "BUY"
    SELL = "SELL"

class OrderStatus(Enum):
    """Order statuses"""
    PENDING = "PendingSubmit"
    SUBMITTED = "Submitted"
    FILLED = "Filled"
    CANCELLED = "Cancelled"
    REJECTED = "Rejected"

@dataclass
class BrokerPosition:
    """Position information"""
    symbol: str
    quantity: int
    average_price: float
    market_price: float
    unrealized_pnl: float
    unrealized_pnl_pct: float
    contract: Contract

@dataclass
class BrokerOrder:
    """Order information"""
    order_id: int
    symbol: str
    side: OrderSide
    quantity: int
    order_type: OrderType
    price: Optional[float]
    status: OrderStatus
    filled_quantity: int
    average_fill_price: float
    timestamp: datetime

class IBKRClient:
    """Interactive Brokers client with async support"""
    
    def __init__(self, host: str = "127.0.0.1", port: int = 7497, client_id: int = 9):
        if IB is None:
            raise ImportError("ib_insync is required for IBKR integration")
        
        self.host = host
        self.port = port
        self.client_id = client_id
        self.ib = None
        self.connected = False
        self.reconnect_attempts = 0
        self.max_reconnect_attempts = 5
        self.reconnect_delay = 5  # seconds
        
        # Event handlers
        self.order_filled_callbacks = []
        self.position_update_callbacks = []
        self.error_callbacks = []
        
        # Track order placement times for fill time metrics
        self.order_placement_times: Dict[int, float] = {}  # order_id -> timestamp
        
        # Import metrics helpers (optional, gracefully handle if metrics disabled)
        try:
            from ...utils.metrics import (
                record_trade_executed,
                record_trade_rejected,
                record_order_fill_time,
                record_slippage,
                update_position_metrics,
                update_broker_connection_status
            )
            self._metrics_available = True
            # Assign methods to instance
            self.record_trade_executed = record_trade_executed
            self.record_trade_rejected = record_trade_rejected
            self.record_order_fill_time = record_order_fill_time
            self.record_slippage = record_slippage
            self.update_position_metrics = update_position_metrics
            self.update_broker_connection_status = update_broker_connection_status
        except ImportError:
            self._metrics_available = False
            logger.debug("Trading metrics helpers not available")
            # Define stub functions if metrics unavailable
            def record_trade_executed(*args, **kwargs): pass
            def record_trade_rejected(*args, **kwargs): pass
            def record_order_fill_time(*args, **kwargs): pass
            def record_slippage(*args, **kwargs): pass
            def update_position_metrics(*args, **kwargs): pass
            def update_broker_connection_status(*args, **kwargs): pass
            
            self.record_trade_executed = record_trade_executed
            self.record_trade_rejected = record_trade_rejected
            self.record_order_fill_time = record_order_fill_time
            self.record_slippage = record_slippage
            self.update_position_metrics = update_position_metrics
            self.update_broker_connection_status = update_broker_connection_status
    
    async def connect(self) -> bool:
        """Connect to IBKR TWS/Gateway"""
        try:
            if self.ib is None:
                self.ib = IB()

            # Note: We don't call util.startLoop() here because:
            # 1. We're already running in an async context (FastAPI/uvicorn)
            # 2. util.startLoop() uses nest_asyncio which is incompatible with uvloop
            # The connectAsync() method works fine without it in an existing event loop

            # Connect
            await self.ib.connectAsync(self.host, self.port, clientId=self.client_id)

            self.connected = True
            self.reconnect_attempts = 0

            # Set up event handlers
            self._setup_event_handlers()

            logger.info(f"Connected to IBKR at {self.host}:{self.port}")
            return True

        except Exception as e:
            logger.error(f"Failed to connect to IBKR: {e}")
            self.connected = False
            return False
    
    async def disconnect(self):
        """Disconnect from IBKR"""
        if self.ib and self.connected:
            try:
                self.ib.disconnect()
                self.connected = False
                logger.info("Disconnected from IBKR")
                
                # Update broker connection status metric
                if self._metrics_available:
                    try:
                        self.update_broker_connection_status(False)
                    except Exception as e:
                        logger.debug(f"Error updating broker connection status metric: {e}")
            except Exception as e:
                logger.error(f"Error disconnecting from IBKR: {e}")
    
    def _setup_event_handlers(self):
        """Set up IBKR event handlers"""
        if not self.ib:
            return

        # Execution details event - fires when order is filled
        # Signature: (trade: Trade, fill: Fill)
        self.ib.execDetailsEvent += self._on_order_filled

        # Position update events
        self.ib.positionEvent += self._on_position_update

        # Error events
        self.ib.errorEvent += self._on_error
    
    def _on_order_filled(self, trade: Trade, fill: Fill):
        """Handle order filled events (execDetailsEvent callback)"""
        logger.info(f"Order filled: {trade}, fill: {fill}")
        
        # Calculate order fill time
        order_id = trade.order.orderId
        fill_time = None
        if order_id in self.order_placement_times:
            fill_time = time.time() - self.order_placement_times[order_id]
            # Clean up tracking
            del self.order_placement_times[order_id]
        
        # Record metrics if available
        if self._metrics_available:
            try:
                symbol = trade.contract.symbol if trade.contract else "unknown"
                side = trade.order.action  # "BUY" or "SELL"
                order_type = trade.order.orderType  # "MKT", "LMT", etc.
                
                # Record order fill time
                if fill_time is not None:
                    self.record_order_fill_time(
                        symbol=symbol,
                        order_type=order_type,
                        fill_time=fill_time
                    )
                
                # Record trade executed (only for fully filled orders)
                if trade.orderStatus.filled > 0:
                    # Note: Strategy name is not available here, will be "unknown"
                    # This could be enhanced by storing strategy info with orders
                    self.record_trade_executed(
                        strategy="unknown",  # Could be enhanced with order metadata
                        symbol=symbol,
                        side=side
                    )
                
                # Calculate and record slippage if limit order
                if hasattr(trade, 'orderStatus') and hasattr(trade.orderStatus, 'avgFillPrice'):
                    if trade.order.price and trade.order.price > 0:  # Limit order
                        expected_price = float(trade.order.price)
                        actual_price = float(trade.orderStatus.avgFillPrice)
                        slippage_pct = ((actual_price - expected_price) / expected_price) * 100
                        self.record_slippage(
                            symbol=symbol,
                            side=side,
                            slippage_pct=slippage_pct
                        )
                        
            except Exception as e:
                logger.warning(f"Error recording order fill metrics: {e}")
        
        # Call callbacks
        for callback in self.order_filled_callbacks:
            try:
                callback(trade)
            except Exception as e:
                logger.error(f"Error in order filled callback: {e}")
    
    def _on_position_update(self, position: Position):
        """Handle position update events"""
        logger.info(f"Position updated: {position}")
        
        # Update position metrics if available
        if self._metrics_available:
            try:
                symbol = position.contract.symbol if position.contract else "unknown"
                quantity = int(position.position)
                # Calculate unrealized P/L if possible
                # Note: This is a simplified calculation, real P/L needs market price
                pnl = 0.0  # Would need market price for accurate P/L
                self.update_position_metrics(
                    symbol=symbol,
                    quantity=quantity,
                    pnl=pnl
                )
            except Exception as e:
                logger.debug(f"Error updating position metrics: {e}")
        
        # Call callbacks
        for callback in self.position_update_callbacks:
            try:
                callback(position)
            except Exception as e:
                logger.error(f"Error in position update callback: {e}")
    
    def _on_error(self, reqId: int, errorCode: int, errorString: str):
        """Handle error events"""
        # Check if this is an order rejection error
        # Common error codes: 201 (Order rejected), 399 (Order rejected - duplicate)
        if errorCode in [201, 399] or "rejected" in errorString.lower():
            # Record trade rejection metric
            if self._metrics_available:
                try:
                    reason = f"error_code_{errorCode}"
                    self.record_trade_rejected(reason=reason)
                except Exception as e:
                    logger.debug(f"Error recording trade rejection metric: {e}")
        logger.error(f"IBKR Error {errorCode}: {errorString}")
        
        # Handle specific error codes
        if errorCode in [502, 504, 1100, 1101, 1102]:  # Connection errors
            logger.warning("Connection error detected, attempting reconnection")
            asyncio.create_task(self._handle_reconnection())
        
        for callback in self.error_callbacks:
            try:
                callback(reqId, errorCode, errorString)
            except Exception as e:
                logger.error(f"Error in error callback: {e}")
    
    async def _handle_reconnection(self):
        """Handle automatic reconnection"""
        if self.reconnect_attempts >= self.max_reconnect_attempts:
            logger.error("Max reconnection attempts reached")
            return
        
        self.reconnect_attempts += 1
        logger.info(f"Attempting reconnection {self.reconnect_attempts}/{self.max_reconnect_attempts}")
        
        await asyncio.sleep(self.reconnect_delay)
        
        if await self.connect():
            logger.info("Reconnection successful")
        else:
            logger.error("Reconnection failed")
    
    def create_contract(self, symbol: str, exchange: str = "SMART", currency: str = "USD") -> Contract:
        """Create a stock contract"""
        return Stock(symbol, exchange, currency)
    
    async def get_market_data(self, contract: Contract) -> Dict[str, Any]:
        """Get current market data for a contract"""
        if not self.connected:
            raise RuntimeError("Not connected to IBKR")
        
        try:
            ticker = self.ib.reqMktData(contract, "", False, False)
            await asyncio.sleep(1)  # Wait for data
            
            return {
                "bid": ticker.bid if ticker.bid else None,
                "ask": ticker.ask if ticker.ask else None,
                "last": ticker.last if ticker.last else None,
                "close": ticker.close if ticker.close else None,
                "volume": ticker.volume if ticker.volume else None,
                "high": ticker.high if ticker.high else None,
                "low": ticker.low if ticker.low else None,
                "open": ticker.open if ticker.open else None
            }
        except Exception as e:
            logger.error(f"Error getting market data for {contract.symbol}: {e}")
            raise
    
    async def get_historical_data(self, contract: Contract, duration: str = "1 D",
                                 bar_size: str = "1 min"):
        """Get historical data for a contract. Returns pandas DataFrame if available."""
        if not self.connected:
            raise RuntimeError("Not connected to IBKR")

        if pd is None:
            raise ImportError("pandas is required for historical data. Install with: pip install pandas")

        try:
            bars = self.ib.reqHistoricalData(
                contract,
                endDateTime="",
                durationStr=duration,
                barSizeSetting=bar_size,
                whatToShow="TRADES",
                useRTH=True,
                formatDate=1
            )

            if not bars:
                raise RuntimeError("No historical data returned")

            df = util.df(bars)
            df.set_index("date", inplace=True)
            df.index = pd.to_datetime(df.index)

            return df
        except Exception as e:
            logger.error(f"Error getting historical data for {contract.symbol}: {e}")
            raise
    
    async def place_market_order(self, contract: Contract, side: OrderSide, 
                               quantity: int) -> BrokerOrder:
        """Place a market order"""
        if not self.connected:
            raise RuntimeError("Not connected to IBKR")
        
        try:
            order_start_time = time.time()
            
            order = MarketOrder(side.value, quantity)
            trade = self.ib.placeOrder(contract, order)
            
            # Track order placement time for fill time metrics
            order_id = trade.order.orderId
            self.order_placement_times[order_id] = order_start_time
            
            return BrokerOrder(
                order_id=trade.order.orderId,
                symbol=contract.symbol,
                side=side,
                quantity=quantity,
                order_type=OrderType.MARKET,
                price=None,
                status=OrderStatus.PENDING,
                filled_quantity=0,
                average_fill_price=0.0,
                timestamp=datetime.now()
            )
        except Exception as e:
            logger.error(f"Error placing market order for {contract.symbol}: {e}")
            raise
    
    async def place_limit_order(self, contract: Contract, side: OrderSide, 
                              quantity: int, price: float) -> BrokerOrder:
        """Place a limit order"""
        if not self.connected:
            raise RuntimeError("Not connected to IBKR")
        
        try:
            order_start_time = time.time()
            
            order = LimitOrder(side.value, quantity, price)
            trade = self.ib.placeOrder(contract, order)
            
            # Track order placement time for fill time metrics
            order_id = trade.order.orderId
            self.order_placement_times[order_id] = order_start_time
            
            return BrokerOrder(
                order_id=trade.order.orderId,
                symbol=contract.symbol,
                side=side,
                quantity=quantity,
                order_type=OrderType.LIMIT,
                price=price,
                status=OrderStatus.PENDING,
                filled_quantity=0,
                average_fill_price=0.0,
                timestamp=datetime.now()
            )
        except Exception as e:
            logger.error(f"Error placing limit order for {contract.symbol}: {e}")
            raise
    
    async def cancel_order(self, order_id: int) -> bool:
        """Cancel an order"""
        if not self.connected:
            raise RuntimeError("Not connected to IBKR")
        
        try:
            self.ib.cancelOrder(order_id)
            logger.info(f"Order {order_id} cancelled")
            return True
        except Exception as e:
            logger.error(f"Error cancelling order {order_id}: {e}")
            return False
    
    async def get_positions(self) -> List[BrokerPosition]:
        """Get current positions"""
        if not self.connected:
            raise RuntimeError("Not connected to IBKR")
        
        try:
            positions = self.ib.positions()
            broker_positions = []
            
            for pos in positions:
                if pos.position != 0:  # Only non-zero positions
                    market_data = await self.get_market_data(pos.contract)
                    market_price = market_data.get("last", pos.avgCost)
                    
                    unrealized_pnl = (market_price - pos.avgCost) * pos.position
                    unrealized_pnl_pct = (market_price / pos.avgCost - 1) if pos.avgCost != 0 else 0
                    
                    broker_positions.append(BrokerPosition(
                        symbol=pos.contract.symbol,
                        quantity=int(pos.position),
                        average_price=pos.avgCost,
                        market_price=market_price,
                        unrealized_pnl=unrealized_pnl,
                        unrealized_pnl_pct=unrealized_pnl_pct,
                        contract=pos.contract
                    ))
            
            return broker_positions
        except Exception as e:
            logger.error(f"Error getting positions: {e}")
            raise
    
    async def get_account_summary(self) -> Dict[str, Any]:
        """Get account summary"""
        if not self.connected:
            raise RuntimeError("Not connected to IBKR")

        try:
            # Use async version to avoid blocking the event loop
            summary = await self.ib.accountSummaryAsync()
            account_data = {}

            for item in summary:
                account_data[item.tag] = {
                    "value": item.value,
                    "currency": item.currency
                }

            return account_data
        except Exception as e:
            logger.error(f"Error getting account summary: {e}")
            raise
    
    def add_order_filled_callback(self, callback):
        """Add callback for order filled events"""
        self.order_filled_callbacks.append(callback)
    
    def add_position_update_callback(self, callback):
        """Add callback for position update events"""
        self.position_update_callbacks.append(callback)
    
    def add_error_callback(self, callback):
        """Add callback for error events"""
        self.error_callbacks.append(callback)
    
    async def __aenter__(self):
        """Async context manager entry"""
        await self.connect()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        await self.disconnect()

class IBKRManager:
    """Manager for IBKR connections with automatic reconnection"""
    
    def __init__(self, host: str = "127.0.0.1", port: int = 7497, client_id: int = 9):
        self.host = host
        self.port = port
        self.client_id = client_id
        self.client = None
        self.connection_task = None
    
    async def start(self):
        """Start the IBKR manager"""
        self.client = IBKRClient(self.host, self.port, self.client_id)
        
        # Set up error handling
        self.client.add_error_callback(self._on_error)
        
        # Connect
        await self.client.connect()
        
        # Start connection monitoring task
        self.connection_task = asyncio.create_task(self._monitor_connection())
    
    async def stop(self):
        """Stop the IBKR manager"""
        if self.connection_task:
            self.connection_task.cancel()
        
        if self.client:
            await self.client.disconnect()
    
    async def _monitor_connection(self):
        """Monitor connection and handle reconnection"""
        while True:
            try:
                if not self.client.connected:
                    logger.warning("IBKR connection lost, attempting reconnection")
                    await self.client.connect()
                
                await asyncio.sleep(30)  # Check every 30 seconds
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in connection monitor: {e}")
                await asyncio.sleep(10)
    
    def _on_error(self, reqId: int, errorCode: int, errorString: str):
        """Handle IBKR errors"""
        logger.error(f"IBKR Error {errorCode}: {errorString}")
    
    @property
    def is_connected(self) -> bool:
        """Check if connected"""
        return self.client and self.client.connected
    
    async def get_client(self) -> IBKRClient:
        """Get the IBKR client"""
        if not self.is_connected:
            raise RuntimeError("IBKR not connected")
        return self.client
