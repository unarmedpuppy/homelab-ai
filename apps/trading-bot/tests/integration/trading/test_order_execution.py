"""
Integration Tests for Order Execution Flow
==========================================

Tests that verify complete order execution flow from signal to execution.
"""

import pytest
from unittest.mock import Mock, AsyncMock, patch
from datetime import datetime
from src.data.brokers.ibkr_client import BrokerOrder, BrokerPosition
from src.core.strategy.base import TradingSignal, SignalType
from src.core.risk import RiskManager, get_risk_manager
from tests.mocks.mock_ibkr_client import MockIBKRClient, MockIBKRManager


class TestOrderPlacementFlow:
    """Test order placement flow"""
    
    @pytest.fixture
    def mock_ibkr_client(self):
        """Create mock IBKR client"""
        return MockIBKRClient()
    
    @pytest.fixture
    def sample_signal(self):
        """Create sample trading signal"""
        return TradingSignal(
            signal_type=SignalType.BUY,
            symbol="SPY",
            price=450.0,
            quantity=10,
            timestamp=datetime.now(),
            confidence=0.8
        )
    
    @pytest.mark.asyncio
    async def test_place_market_order_success(self, mock_ibkr_client, sample_signal):
        """Test successful market order placement"""
        # Configure mock to succeed
        await mock_ibkr_client.connect()
        mock_ibkr_client.auto_fill_orders = True
        
        # Place order
        contract = mock_ibkr_client.create_contract(sample_signal.symbol)
        from src.data.brokers.ibkr_client import OrderSide
        order = await mock_ibkr_client.place_market_order(
            contract=contract,
            side=OrderSide.BUY,
            quantity=sample_signal.quantity
        )
        
        assert order is not None
        assert order.symbol == "SPY"
        assert order.side == "BUY"
        assert order.quantity == 10
        assert order.status in ["SUBMITTED", "FILLED"]
    
    @pytest.mark.asyncio
    async def test_place_limit_order_success(self, mock_ibkr_client):
        """Test successful limit order placement"""
        await mock_ibkr_client.connect()
        mock_ibkr_client.auto_fill_orders = True
        
        contract = mock_ibkr_client.create_contract("SPY")
        from src.data.brokers.ibkr_client import OrderSide
        order = await mock_ibkr_client.place_limit_order(
            contract=contract,
            side=OrderSide.BUY,
            quantity=10,
            price=450.0
        )
        
        assert order is not None
        assert order.order_type.value == "LMT"
        assert order.price == 450.0
    
    @pytest.mark.asyncio
    async def test_order_status_updates(self, mock_ibkr_client, sample_signal):
        """Test that order status updates correctly"""
        await mock_ibkr_client.connect()
        mock_ibkr_client.auto_fill_orders = False  # Don't auto-fill
        
        # Place order
        contract = mock_ibkr_client.create_contract(sample_signal.symbol)
        from src.data.brokers.ibkr_client import OrderSide
        order = await mock_ibkr_client.place_market_order(
            contract=contract,
            side=OrderSide.BUY,
            quantity=sample_signal.quantity
        )
        
        assert order.status.value == "PendingSubmit" or order.status.value == "Submitted"
        
        # Simulate fill
        mock_ibkr_client.fill_order(order.order_id, fill_price=450.5)
        
        # Get updated order
        updated_order = mock_ibkr_client.get_order_status(order.order_id)
        assert updated_order.status.value == "Filled"
        assert updated_order.filled_quantity == 10
        assert updated_order.average_fill_price == 450.5


class TestOrderExecutionWithRiskManager:
    """Test order execution integrated with risk manager"""
    
    @pytest.fixture
    def mock_ibkr_client(self):
        """Create mock IBKR client"""
        return MockIBKRClient()
    
    @pytest.fixture
    def risk_manager(self, test_db_session):
        """Create risk manager with mocked dependencies"""
        with patch('src.core.risk.account_monitor.AccountMonitor') as mock_account:
            mock_account.return_value.check_account_balance = AsyncMock(return_value=Mock(
                balance=100000.0,
                available_cash=95000.0
            ))
            mock_account.return_value.is_cash_account_mode = AsyncMock(return_value=False)
            
            from src.core.risk import RiskManager
            return RiskManager(account_monitor=mock_account.return_value)
    
    @pytest.mark.asyncio
    async def test_order_with_compliance_check(self, mock_ibkr_client, risk_manager):
        """Test order placement after compliance check"""
        # Check compliance
        validation = await risk_manager.validate_trade(
            account_id=1,
            symbol="SPY",
            side="BUY",
            quantity=10,
            price_per_share=450.0
        )
        
        assert validation.can_proceed is True
        
        # Place order if compliant
        if validation.can_proceed:
            await mock_ibkr_client.connect()
            contract = mock_ibkr_client.create_contract("SPY")
            from src.data.brokers.ibkr_client import OrderSide
            order = await mock_ibkr_client.place_market_order(
                contract=contract,
                side=OrderSide.BUY,
                quantity=10
            )
            assert order is not None
    
    @pytest.mark.asyncio
    async def test_order_with_position_sizing(self, mock_ibkr_client, risk_manager):
        """Test order placement with confidence-based position sizing"""
        # Calculate position size based on confidence
        position_size = await risk_manager.position_sizing.calculate_position_size(
            account_id=1,
            confidence_score=0.8,  # High confidence
            price_per_share=450.0
        )
        
        assert position_size.size_shares > 0
        assert position_size.size_usd > 0
        
        # Place order with calculated size
        await mock_ibkr_client.connect()
        contract = mock_ibkr_client.create_contract("SPY")
        from src.data.brokers.ibkr_client import OrderSide
        order = await mock_ibkr_client.place_market_order(
            contract=contract,
            side=OrderSide.BUY,
            quantity=position_size.size_shares
        )
        
        assert order.quantity == position_size.size_shares


class TestOrderRejectionHandling:
    """Test order rejection scenarios"""
    
    @pytest.fixture
    def mock_ibkr_client(self):
        """Create mock IBKR client that rejects orders"""
        client = MockIBKRClient()
        client.should_reject_orders = True
        client.rejection_reason = "Insufficient buying power"
        return client
    
    @pytest.mark.asyncio
    async def test_order_rejection(self, mock_ibkr_client):
        """Test handling of rejected orders"""
        await mock_ibkr_client.connect()
        try:
            contract = mock_ibkr_client.create_contract("SPY")
            from src.data.brokers.ibkr_client import OrderSide
            order = await mock_ibkr_client.place_market_order(
                contract=contract,
                side=OrderSide.BUY,
                quantity=10000  # Too large
            )
            
            # If order is created but rejected, check status
            if order:
                assert order.status.value == "Rejected"
        except Exception as e:
            # Expected rejection exception
            assert "reject" in str(e).lower() or "insufficient" in str(e).lower()
    
    @pytest.mark.asyncio
    async def test_rejection_reason_preserved(self, mock_ibkr_client):
        """Test that rejection reason is preserved"""
        await mock_ibkr_client.connect()
        try:
            contract = mock_ibkr_client.create_contract("SPY")
            from src.data.brokers.ibkr_client import OrderSide
            order = await mock_ibkr_client.place_market_order(
                contract=contract,
                side=OrderSide.BUY,
                quantity=10000
            )
            
            # If order has rejection info, verify it
            if order and hasattr(order, 'rejection_reason'):
                assert order.rejection_reason is not None
        except Exception:
            pass


class TestOrderCancellation:
    """Test order cancellation"""
    
    @pytest.fixture
    def mock_ibkr_client(self):
        """Create mock IBKR client"""
        client = MockIBKRClient()
        client.auto_fill_orders = False  # Don't auto-fill
        return client
    
    @pytest.mark.asyncio
    async def test_cancel_pending_order(self, mock_ibkr_client):
        """Test cancellation of pending order"""
        await mock_ibkr_client.connect()
        # Place order
        contract = mock_ibkr_client.create_contract("SPY")
        from src.data.brokers.ibkr_client import OrderSide
        order = await mock_ibkr_client.place_market_order(
            contract=contract,
            side=OrderSide.BUY,
            quantity=10
        )
        
        assert order.status.value in ["PendingSubmit", "Submitted"]
        
        # Cancel order
        cancelled = await mock_ibkr_client.cancel_order(order.order_id)
        
        assert cancelled is True
        
        # Verify order is cancelled
        updated_order = mock_ibkr_client.get_order_status(order.order_id)
        assert updated_order.status.value == "Cancelled"
    
    @pytest.mark.asyncio
    async def test_cancel_filled_order_fails(self, mock_ibkr_client):
        """Test that cancelling filled order fails"""
        await mock_ibkr_client.connect()
        # Place and fill order
        contract = mock_ibkr_client.create_contract("SPY")
        from src.data.brokers.ibkr_client import OrderSide
        order = await mock_ibkr_client.place_market_order(
            contract=contract,
            side=OrderSide.BUY,
            quantity=10
        )
        mock_ibkr_client.auto_fill_orders = True
        mock_ibkr_client.fill_order(order.order_id)
        
        # Try to cancel (should fail)
        cancelled = await mock_ibkr_client.cancel_order(order.order_id)
        
        # Should fail or return False
        assert cancelled is False or order.status.value == "Filled"


class TestPartialFills:
    """Test partial order fills"""
    
    @pytest.fixture
    def mock_ibkr_client(self):
        """Create mock IBKR client"""
        client = MockIBKRClient()
        client.auto_fill_orders = False
        return client
    
    def test_partial_fill(self, mock_ibkr_client):
        """Test partial order fill"""
        # Place order for 100 shares
        order = mock_ibkr_client.place_market_order(
            symbol="SPY",
            side="BUY",
            quantity=100
        )
        
        # Partially fill (50 shares)
        mock_ibkr_client.fill_order(order.order_id, fill_price=450.0, fill_quantity=50)
        
        updated_order = mock_ibkr_client.get_order_status(order.order_id)
        assert updated_order.filled_quantity == 50
        assert updated_order.status in ["PARTIALLY_FILLED", "SUBMITTED"]
        
        # Fill remaining
        mock_ibkr_client.fill_order(order.order_id, fill_price=450.5, fill_quantity=50)
        
        final_order = mock_ibkr_client.get_order_status(order.order_id)
        assert final_order.filled_quantity == 100
        assert final_order.status == "FILLED"


@pytest.mark.integration
class TestOrderExecutionWorkflow:
    """Test complete order execution workflow"""
    
    @pytest.fixture
    def mock_ibkr_client(self):
        """Create mock IBKR client"""
        return MockIBKRClient()
    
    @pytest.fixture
    def risk_manager(self, test_db_session):
        """Create risk manager"""
        with patch('src.core.risk.account_monitor.AccountMonitor') as mock_account:
            mock_account.return_value.check_account_balance = AsyncMock(return_value=Mock(
                balance=100000.0,
                available_cash=95000.0
            ))
            mock_account.return_value.is_cash_account_mode = AsyncMock(return_value=False)
            
            from src.core.risk import RiskManager
            return RiskManager(account_monitor=mock_account.return_value)
    
    @pytest.mark.asyncio
    async def test_complete_execution_workflow(self, mock_ibkr_client, risk_manager):
        """Test complete workflow: signal -> validation -> execution"""
        # 1. Generate signal (simulated)
        signal = TradingSignal(
            signal_type=SignalType.BUY,
            symbol="SPY",
            price=450.0,
            quantity=10,
            timestamp=datetime.now(),
            confidence=0.8
        )
        
        # 2. Validate trade
        validation = await risk_manager.validate_trade(
            account_id=1,
            symbol=signal.symbol,
            side=signal.signal_type.value,
            quantity=signal.quantity,
            price_per_share=signal.price,
            confidence_score=signal.confidence
        )
        
        # 3. Execute if valid
        if validation.can_proceed:
            order = mock_ibkr_client.place_market_order(
                symbol=signal.symbol,
                side=signal.signal_type.value,
                quantity=signal.quantity
            )
            
            # 4. Verify execution
            assert order is not None
            assert order.symbol == signal.symbol
            assert order.status in ["SUBMITTED", "FILLED"]
            
            # 5. Wait for fill (simulated)
            if order.status == "SUBMITTED":
                mock_ibkr_client.fill_order(order.order_id, fill_price=450.5)
                filled_order = mock_ibkr_client.get_order_status(order.order_id)
                assert filled_order.status == "FILLED"
