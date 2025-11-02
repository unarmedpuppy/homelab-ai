"""
Mock IBKR Client for Testing
=============================

Mock implementation of IBKRClient that allows configurable responses
for testing scenarios without requiring a real IBKR connection.
"""

import asyncio
from typing import Dict, List, Optional, Any, Callable
from datetime import datetime
from unittest.mock import Mock, AsyncMock
import pandas as pd

from src.data.brokers.ibkr_client import (
    BrokerOrder,
    BrokerPosition,
    OrderSide,
    OrderType,
    OrderStatus
)


class MockIBKRClient:
    """
    Mock IBKR client with same interface as IBKRClient
    
    Allows configurable responses for different test scenarios:
    - Connection success/failure
    - Order placement success/rejection
    - Position data
    - Account summary
    - Market data
    
    Note: This is a mock implementation for testing. It does not require
    a real IBKR connection and allows configuring responses for various scenarios.
    """
    
    def __init__(self, host: str = "127.0.0.1", port: int = 7497, client_id: int = 9):
        """Initialize mock client"""
        self.host = host
        self.port = port
        self.client_id = client_id
        self.connected = False
        self.reconnect_attempts = 0
        
        # Event handlers (same interface as real client)
        self.order_filled_callbacks: List[Callable] = []
        self.position_update_callbacks: List[Callable] = []
        self.error_callbacks: List[Callable] = []
        
        # Configurable responses for testing
        self._config = {
            'connect_success': True,
            'connect_delay': 0.0,
            'connection_error': None,
            'place_order_success': True,
            'order_fill_delay': 0.0,
            'order_rejection_reason': None,
            'positions': [],
            'account_summary': {
                'TotalCashValue': {'value': '50000.0', 'currency': 'USD'},
                'BuyingPower': {'value': '100000.0', 'currency': 'USD'},
                'NetLiquidation': {'value': '100000.0', 'currency': 'USD'},
                'AvailableFunds': {'value': '50000.0', 'currency': 'USD'}
            },
            'market_data': {},
            'historical_data': None,
            'auto_fill_orders': True,  # Automatically fill orders after delay
            'fill_price_offset': 0.0,  # Price offset for fills (for slippage testing)
        }
        
        # Internal state
        self._orders: Dict[int, BrokerOrder] = {}
        self._next_order_id = 1
        self._contracts: Dict[str, Mock] = {}
    
    def configure(self, **kwargs):
        """Configure mock behavior"""
        self._config.update(kwargs)
    
    def reset(self):
        """Reset mock to initial state"""
        self.connected = False
        self._orders = {}
        self._next_order_id = 1
        self._contracts = {}
        self._config['positions'] = []
    
    async def connect(self) -> bool:
        """Connect to IBKR (mock)"""
        if self._config['connect_delay'] > 0:
            await asyncio.sleep(self._config['connect_delay'])
        
        if self._config['connection_error']:
            error = self._config['connection_error']
            if isinstance(error, Exception):
                raise error
            raise RuntimeError(str(error))
        
        self.connected = self._config['connect_success']
        self.reconnect_attempts = 0
        return self.connected
    
    async def disconnect(self):
        """Disconnect from IBKR (mock)"""
        self.connected = False
    
    def create_contract(self, symbol: str, exchange: str = "SMART", currency: str = "USD") -> Mock:
        """Create a mock contract"""
        if symbol not in self._contracts:
            contract = Mock()
            contract.symbol = symbol
            contract.exchange = exchange
            contract.currency = currency
            self._contracts[symbol] = contract
        return self._contracts[symbol]
    
    async def get_market_data(self, contract: Mock) -> Dict[str, Any]:
        """Get mock market data"""
        if not self.connected:
            raise RuntimeError("Not connected to IBKR")
        
        symbol = contract.symbol if hasattr(contract, 'symbol') else str(contract)
        
        # Check if custom market data configured
        if symbol in self._config['market_data']:
            return self._config['market_data'][symbol]
        
        # Default mock market data
        base_price = 100.0
        return {
            "bid": base_price - 0.01,
            "ask": base_price + 0.01,
            "last": base_price,
            "close": base_price,
            "volume": 1000000,
            "high": base_price * 1.01,
            "low": base_price * 0.99,
            "open": base_price
        }
    
    async def get_historical_data(self, contract: Mock, duration: str = "1 D", 
                                 bar_size: str = "1 min") -> pd.DataFrame:
        """Get mock historical data"""
        if not self.connected:
            raise RuntimeError("Not connected to IBKR")
        
        # Check if custom historical data configured
        if self._config['historical_data'] is not None:
            return self._config['historical_data']
        
        # Default mock historical data
        dates = pd.date_range(start='2024-01-01', periods=100, freq='5min')
        base_price = 100.0
        
        data = pd.DataFrame({
            'open': [base_price] * 100,
            'high': [base_price * 1.01] * 100,
            'low': [base_price * 0.99] * 100,
            'close': [base_price] * 100,
            'volume': [1000000] * 100
        }, index=dates)
        
        return data
    
    async def place_market_order(self, contract: Mock, side: OrderSide, 
                               quantity: int) -> BrokerOrder:
        """Place a mock market order"""
        if not self.connected:
            raise RuntimeError("Not connected to IBKR")
        
        if not self._config['place_order_success']:
            if self._config['order_rejection_reason']:
                raise RuntimeError(self._config['order_rejection_reason'])
            raise RuntimeError("Order rejected by broker")
        
        symbol = contract.symbol if hasattr(contract, 'symbol') else str(contract)
        
        # Get current market price
        market_data = await self.get_market_data(contract)
        fill_price = market_data['last'] + self._config['fill_price_offset']
        
        # Create order
        order_id = self._next_order_id
        self._next_order_id += 1
        
        order = BrokerOrder(
            order_id=order_id,
            symbol=symbol,
            side=side,
            quantity=quantity,
            order_type=OrderType.MARKET,
            price=None,
            status=OrderStatus.PENDING,
            filled_quantity=0,
            average_fill_price=0.0,
            timestamp=datetime.now()
        )
        
        self._orders[order_id] = order
        
        # Auto-fill if configured
        if self._config['auto_fill_orders']:
            if self._config['order_fill_delay'] > 0:
                await asyncio.sleep(self._config['order_fill_delay'])
            
            # Update order to filled
            order.status = OrderStatus.FILLED
            order.filled_quantity = quantity
            order.average_fill_price = fill_price
            
            # Trigger callback
            for callback in self.order_filled_callbacks:
                try:
                    # Create mock Trade object for callback
                    mock_trade = Mock()
                    mock_trade.order = Mock()
                    mock_trade.order.orderId = order_id
                    mock_trade.order.totalQuantity = quantity
                    callback(mock_trade)
                except Exception as e:
                    print(f"Error in order filled callback: {e}")
        
        return order
    
    async def place_limit_order(self, contract: Mock, side: OrderSide, 
                              quantity: int, price: float) -> BrokerOrder:
        """Place a mock limit order"""
        if not self.connected:
            raise RuntimeError("Not connected to IBKR")
        
        if not self._config['place_order_success']:
            if self._config['order_rejection_reason']:
                raise RuntimeError(self._config['order_rejection_reason'])
            raise RuntimeError("Order rejected by broker")
        
        symbol = contract.symbol if hasattr(contract, 'symbol') else str(contract)
        
        # Create order
        order_id = self._next_order_id
        self._next_order_id += 1
        
        order = BrokerOrder(
            order_id=order_id,
            symbol=symbol,
            side=side,
            quantity=quantity,
            order_type=OrderType.LIMIT,
            price=price,
            status=OrderStatus.PENDING,
            filled_quantity=0,
            average_fill_price=0.0,
            timestamp=datetime.now()
        )
        
        self._orders[order_id] = order
        
        # Auto-fill if configured and price is reasonable
        if self._config['auto_fill_orders']:
            market_data = await self.get_market_data(contract)
            market_price = market_data['last']
            
            # Check if limit order should fill
            should_fill = False
            if side == OrderSide.BUY and price >= market_price:
                should_fill = True
            elif side == OrderSide.SELL and price <= market_price:
                should_fill = True
            
            if should_fill:
                if self._config['order_fill_delay'] > 0:
                    await asyncio.sleep(self._config['order_fill_delay'])
                
                # Update order to filled
                order.status = OrderStatus.FILLED
                order.filled_quantity = quantity
                order.average_fill_price = price + self._config['fill_price_offset']
                
                # Trigger callback
                for callback in self.order_filled_callbacks:
                    try:
                        mock_trade = Mock()
                        mock_trade.order = Mock()
                        mock_trade.order.orderId = order_id
                        mock_trade.order.totalQuantity = quantity
                        callback(mock_trade)
                    except Exception as e:
                        print(f"Error in order filled callback: {e}")
        
        return order
    
    async def cancel_order(self, order_id: int) -> bool:
        """Cancel a mock order"""
        if not self.connected:
            raise RuntimeError("Not connected to IBKR")
        
        if order_id in self._orders:
            self._orders[order_id].status = OrderStatus.CANCELLED
            return True
        
        return False
    
    def get_order(self, order_id: int) -> Optional[BrokerOrder]:
        """Get order by ID (helper method for testing)"""
        return self._orders.get(order_id)
    
    def get_order_status(self, order_id: int) -> Optional[BrokerOrder]:
        """Get order status by ID (alias for get_order for testing compatibility)"""
        return self.get_order(order_id)
    
    def fill_order(self, order_id: int, fill_price: Optional[float] = None, fill_quantity: Optional[int] = None) -> bool:
        """Manually fill an order (helper for testing)"""
        if order_id not in self._orders:
            return False
        
        order = self._orders[order_id]
        if order.status == OrderStatus.CANCELLED or order.status == OrderStatus.FILLED:
            return False
        
        # Use provided fill price or calculate from market
        if fill_price is None:
            # Would need market data, use order's expected price
            fill_price = order.price if order.price else 100.0
        
        fill_qty = fill_quantity if fill_quantity is not None else order.quantity
        
        order.status = OrderStatus.FILLED
        order.filled_quantity = fill_qty
        order.average_fill_price = fill_price
        
        # Trigger callbacks
        for callback in self.order_filled_callbacks:
            try:
                mock_trade = Mock()
                mock_trade.order = Mock()
                mock_trade.order.orderId = order_id
                mock_trade.order.totalQuantity = fill_qty
                callback(mock_trade)
            except Exception as e:
                print(f"Error in order filled callback: {e}")
        
        return True
    
    def update_position_price(self, symbol: str, current_price: float) -> bool:
        """Update position price (helper for testing)"""
        # Find position for symbol
        for pos in self._config['positions']:
            if pos.symbol == symbol:
                # Update unrealized P/L if position has avg_cost
                if hasattr(pos, 'avg_cost') and pos.avg_cost > 0:
                    pnl = (current_price - pos.avg_cost) * pos.quantity
                    pnl_pct = ((current_price - pos.avg_cost) / pos.avg_cost) * 100 if pos.avg_cost > 0 else 0.0
                    
                    if hasattr(pos, 'unrealized_pnl'):
                        pos.unrealized_pnl = pnl
                    if hasattr(pos, 'unrealized_pnl_pct'):
                        pos.unrealized_pnl_pct = pnl_pct
                    
                    # Update current price if attribute exists
                    if hasattr(pos, 'current_price'):
                        pos.current_price = current_price
                
                return True
        
        return False
    
    @property
    def auto_fill_orders(self) -> bool:
        """Get auto_fill_orders setting"""
        return self._config.get('auto_fill_orders', True)
    
    @auto_fill_orders.setter
    def auto_fill_orders(self, value: bool):
        """Set auto_fill_orders setting"""
        self._config['auto_fill_orders'] = value
    
    @property
    def should_reject_orders(self) -> bool:
        """Get should_reject_orders setting"""
        return not self._config.get('place_order_success', True)
    
    @should_reject_orders.setter
    def should_reject_orders(self, value: bool):
        """Set should_reject_orders setting"""
        self._config['place_order_success'] = not value
        if value:
            self._config['order_rejection_reason'] = "Order rejected for testing"
    
    @property
    def default_fill_price(self) -> float:
        """Get default fill price"""
        return self._config.get('default_fill_price', 100.0)
    
    @default_fill_price.setter
    def default_fill_price(self, value: float):
        """Set default fill price"""
        self._config['default_fill_price'] = value
        # Also update market data if needed
        # This is a simplified approach - in real tests you might want more control
    
    async def get_positions(self) -> List[BrokerPosition]:
        """Get mock positions"""
        if not self.connected:
            raise RuntimeError("Not connected to IBKR")
        
        return self._config['positions'].copy()
    
    async def get_account_summary(self) -> Dict[str, Any]:
        """Get mock account summary"""
        if not self.connected:
            raise RuntimeError("Not connected to IBKR")
        
        return self._config['account_summary'].copy()
    
    def add_order_filled_callback(self, callback: Callable):
        """Add callback for order filled events"""
        self.order_filled_callbacks.append(callback)
    
    def add_position_update_callback(self, callback: Callable):
        """Add callback for position update events"""
        self.position_update_callbacks.append(callback)
    
    def add_error_callback(self, callback: Callable):
        """Add callback for error events"""
        self.error_callbacks.append(callback)
    
    async def __aenter__(self):
        """Async context manager entry"""
        await self.connect()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        await self.disconnect()


class MockIBKRManager:
    """
    Mock IBKRManager for testing
    
    Provides same interface as IBKRManager but uses MockIBKRClient
    """
    
    def __init__(self, host: str = "127.0.0.1", port: int = 7497, client_id: int = 9):
        """Initialize mock manager"""
        self.host = host
        self.port = port
        self.client_id = client_id
        self.client: Optional[MockIBKRClient] = None
        self._monitoring_task: Optional[asyncio.Task] = None
        self._running = False
    
    @property
    def is_connected(self) -> bool:
        """Check if connected"""
        return self.client is not None and self.client.connected
    
    async def start(self):
        """Start the manager"""
        self.client = MockIBKRClient(self.host, self.port, self.client_id)
        await self.client.connect()
        self._running = True
    
    async def stop(self):
        """Stop the manager"""
        self._running = False
        if self.client:
            await self.client.disconnect()
            self.client = None
    
    async def get_client(self) -> MockIBKRClient:
        """Get the client"""
        if not self.is_connected:
            raise RuntimeError("IBKR not connected")
        return self.client

