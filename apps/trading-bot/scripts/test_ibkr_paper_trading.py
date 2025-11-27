#!/usr/bin/env python3
"""
IBKR Paper Trading Integration Tests
====================================

Comprehensive test script for IBKR paper trading functionality.
Tests order submission, modification, cancellation, position sync, and error handling.

Requirements:
- TWS or IB Gateway running in paper trading mode
- Port 7497 (paper trading default)
- API access enabled in TWS/Gateway settings

Usage:
    python scripts/test_ibkr_paper_trading.py [--skip-orders] [--symbol SYMBOL]
"""

import asyncio
import argparse
import sys
import os
import time
import logging
from pathlib import Path
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
from dataclasses import dataclass
from enum import Enum

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv

# Load environment variables
env_file = Path(__file__).parent.parent / ".env"
if env_file.exists():
    load_dotenv(env_file)

from src.data.brokers.ibkr_client import (
    IBKRClient,
    IBKRManager,
    OrderSide,
    OrderType,
    OrderStatus,
    BrokerOrder,
    BrokerPosition
)
from src.core.sync.position_sync import PositionSyncService
from src.config.settings import settings

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class TestResult(Enum):
    """Test result status"""
    PASS = "PASS"
    FAIL = "FAIL"
    SKIP = "SKIP"
    WARN = "WARN"


@dataclass
class TestCase:
    """Test case result"""
    name: str
    result: TestResult
    duration: float
    message: str = ""
    details: Optional[Dict[str, Any]] = None


class IBKRPaperTradingTests:
    """IBKR Paper Trading Integration Tests"""

    def __init__(self, test_symbol: str = "AAPL", skip_orders: bool = False):
        """
        Initialize test suite

        Args:
            test_symbol: Symbol to use for testing (default: AAPL)
            skip_orders: Skip order placement tests (useful for read-only testing)
        """
        self.test_symbol = test_symbol
        self.skip_orders = skip_orders
        self.client: Optional[IBKRClient] = None
        self.manager: Optional[IBKRManager] = None
        self.results: List[TestCase] = []
        self.test_orders: List[int] = []  # Track orders for cleanup

    async def setup(self) -> bool:
        """Set up test environment"""
        logger.info("=" * 60)
        logger.info("IBKR Paper Trading Integration Tests")
        logger.info("=" * 60)
        logger.info("")
        logger.info(f"Test Symbol: {self.test_symbol}")
        logger.info(f"Skip Orders: {self.skip_orders}")
        logger.info(f"IBKR Host: {settings.ibkr.host}")
        logger.info(f"IBKR Port: {settings.ibkr.port}")
        logger.info("")

        # Verify paper trading port
        if settings.ibkr.port not in [7497, 4002]:
            logger.warning(
                f"Port {settings.ibkr.port} is not a standard paper trading port. "
                f"Paper trading typically uses 7497 (TWS) or 4002 (Gateway)."
            )
            logger.warning("Continuing anyway - ensure you're in paper trading mode!")
            logger.warning("")

        return True

    async def teardown(self):
        """Clean up test environment"""
        # Cancel any test orders that weren't cancelled
        if self.client and self.client.connected and self.test_orders:
            logger.info("Cleaning up test orders...")
            for order_id in self.test_orders:
                try:
                    await self.client.cancel_order(order_id)
                    logger.info(f"  Cancelled order {order_id}")
                except Exception as e:
                    logger.warning(f"  Could not cancel order {order_id}: {e}")

        # Disconnect
        if self.client:
            await self.client.disconnect()
            logger.info("Disconnected from IBKR")

    def record_result(self, name: str, result: TestResult, duration: float,
                     message: str = "", details: Optional[Dict[str, Any]] = None):
        """Record a test result"""
        test_case = TestCase(
            name=name,
            result=result,
            duration=duration,
            message=message,
            details=details
        )
        self.results.append(test_case)

        # Log result
        status_emoji = {
            TestResult.PASS: "✅",
            TestResult.FAIL: "❌",
            TestResult.SKIP: "⏭️",
            TestResult.WARN: "⚠️"
        }
        emoji = status_emoji.get(result, "?")
        logger.info(f"{emoji} {name}: {result.value} ({duration:.2f}s)")
        if message:
            logger.info(f"   {message}")

    # =========================================================================
    # Connection Tests
    # =========================================================================

    async def test_connection(self) -> TestResult:
        """Test IBKR connection"""
        start = time.time()

        try:
            self.client = IBKRClient(
                host=settings.ibkr.host,
                port=settings.ibkr.port,
                client_id=settings.ibkr.client_id
            )

            connected = await self.client.connect()
            duration = time.time() - start

            if connected and self.client.connected:
                self.record_result(
                    "Connection",
                    TestResult.PASS,
                    duration,
                    f"Connected to IBKR at {settings.ibkr.host}:{settings.ibkr.port}"
                )
                return TestResult.PASS
            else:
                self.record_result(
                    "Connection",
                    TestResult.FAIL,
                    duration,
                    "Failed to connect to IBKR"
                )
                return TestResult.FAIL

        except Exception as e:
            duration = time.time() - start
            self.record_result(
                "Connection",
                TestResult.FAIL,
                duration,
                f"Connection error: {str(e)}"
            )
            return TestResult.FAIL

    async def test_reconnection(self) -> TestResult:
        """Test reconnection after disconnect"""
        start = time.time()

        if not self.client or not self.client.connected:
            self.record_result(
                "Reconnection",
                TestResult.SKIP,
                0,
                "Skipped: No initial connection"
            )
            return TestResult.SKIP

        try:
            # Disconnect
            await self.client.disconnect()
            await asyncio.sleep(1)

            # Reconnect
            connected = await self.client.connect()
            duration = time.time() - start

            if connected:
                self.record_result(
                    "Reconnection",
                    TestResult.PASS,
                    duration,
                    "Successfully reconnected after disconnect"
                )
                return TestResult.PASS
            else:
                self.record_result(
                    "Reconnection",
                    TestResult.FAIL,
                    duration,
                    "Failed to reconnect"
                )
                return TestResult.FAIL

        except Exception as e:
            duration = time.time() - start
            self.record_result(
                "Reconnection",
                TestResult.FAIL,
                duration,
                f"Reconnection error: {str(e)}"
            )
            return TestResult.FAIL

    # =========================================================================
    # Account Tests
    # =========================================================================

    async def test_account_summary(self) -> TestResult:
        """Test account summary retrieval"""
        start = time.time()

        if not self.client or not self.client.connected:
            self.record_result(
                "Account Summary",
                TestResult.SKIP,
                0,
                "Skipped: Not connected"
            )
            return TestResult.SKIP

        try:
            summary = await self.client.get_account_summary()
            duration = time.time() - start

            if summary:
                # Check for key account fields
                key_fields = ['TotalCashValue', 'BuyingPower', 'NetLiquidation']
                found_fields = [f for f in key_fields if f in summary]

                self.record_result(
                    "Account Summary",
                    TestResult.PASS,
                    duration,
                    f"Retrieved {len(summary)} fields (key fields: {len(found_fields)}/{len(key_fields)})",
                    {"fields_count": len(summary), "key_fields": found_fields}
                )
                return TestResult.PASS
            else:
                self.record_result(
                    "Account Summary",
                    TestResult.FAIL,
                    duration,
                    "No account summary returned"
                )
                return TestResult.FAIL

        except Exception as e:
            duration = time.time() - start
            self.record_result(
                "Account Summary",
                TestResult.FAIL,
                duration,
                f"Error: {str(e)}"
            )
            return TestResult.FAIL

    # =========================================================================
    # Market Data Tests
    # =========================================================================

    async def test_market_data(self) -> TestResult:
        """Test market data retrieval"""
        start = time.time()

        if not self.client or not self.client.connected:
            self.record_result(
                "Market Data",
                TestResult.SKIP,
                0,
                "Skipped: Not connected"
            )
            return TestResult.SKIP

        try:
            contract = self.client.create_contract(self.test_symbol)
            market_data = await self.client.get_market_data(contract)
            duration = time.time() - start

            if market_data:
                # Check for price data
                has_price = any([
                    market_data.get('last'),
                    market_data.get('bid'),
                    market_data.get('ask')
                ])

                if has_price:
                    self.record_result(
                        "Market Data",
                        TestResult.PASS,
                        duration,
                        f"{self.test_symbol}: Last=${market_data.get('last', 'N/A')}, "
                        f"Bid=${market_data.get('bid', 'N/A')}, Ask=${market_data.get('ask', 'N/A')}",
                        market_data
                    )
                    return TestResult.PASS
                else:
                    self.record_result(
                        "Market Data",
                        TestResult.WARN,
                        duration,
                        "Market data returned but no prices (market might be closed or no subscription)",
                        market_data
                    )
                    return TestResult.WARN
            else:
                self.record_result(
                    "Market Data",
                    TestResult.FAIL,
                    duration,
                    "No market data returned"
                )
                return TestResult.FAIL

        except Exception as e:
            duration = time.time() - start
            self.record_result(
                "Market Data",
                TestResult.FAIL,
                duration,
                f"Error: {str(e)}"
            )
            return TestResult.FAIL

    async def test_historical_data(self) -> TestResult:
        """Test historical data retrieval"""
        start = time.time()

        if not self.client or not self.client.connected:
            self.record_result(
                "Historical Data",
                TestResult.SKIP,
                0,
                "Skipped: Not connected"
            )
            return TestResult.SKIP

        try:
            contract = self.client.create_contract(self.test_symbol)
            df = await self.client.get_historical_data(contract, duration="1 D", bar_size="5 mins")
            duration = time.time() - start

            if df is not None and not df.empty:
                self.record_result(
                    "Historical Data",
                    TestResult.PASS,
                    duration,
                    f"Retrieved {len(df)} bars for {self.test_symbol}",
                    {"bars": len(df), "columns": list(df.columns)}
                )
                return TestResult.PASS
            else:
                self.record_result(
                    "Historical Data",
                    TestResult.FAIL,
                    duration,
                    "No historical data returned"
                )
                return TestResult.FAIL

        except ImportError as e:
            duration = time.time() - start
            self.record_result(
                "Historical Data",
                TestResult.SKIP,
                duration,
                f"Skipped: {str(e)}"
            )
            return TestResult.SKIP

        except Exception as e:
            duration = time.time() - start
            self.record_result(
                "Historical Data",
                TestResult.FAIL,
                duration,
                f"Error: {str(e)}"
            )
            return TestResult.FAIL

    # =========================================================================
    # Position Tests
    # =========================================================================

    async def test_get_positions(self) -> TestResult:
        """Test position retrieval"""
        start = time.time()

        if not self.client or not self.client.connected:
            self.record_result(
                "Get Positions",
                TestResult.SKIP,
                0,
                "Skipped: Not connected"
            )
            return TestResult.SKIP

        try:
            positions = await self.client.get_positions()
            duration = time.time() - start

            # Positions can be empty, that's valid
            self.record_result(
                "Get Positions",
                TestResult.PASS,
                duration,
                f"Retrieved {len(positions)} positions",
                {"count": len(positions), "symbols": [p.symbol for p in positions]}
            )
            return TestResult.PASS

        except Exception as e:
            duration = time.time() - start
            self.record_result(
                "Get Positions",
                TestResult.FAIL,
                duration,
                f"Error: {str(e)}"
            )
            return TestResult.FAIL

    async def test_position_sync(self) -> TestResult:
        """Test position sync service"""
        start = time.time()

        if not self.client or not self.client.connected:
            self.record_result(
                "Position Sync",
                TestResult.SKIP,
                0,
                "Skipped: Not connected"
            )
            return TestResult.SKIP

        try:
            # Create a mock manager for testing
            # Note: In real usage, this would use the global manager

            # For now, just test that the service initializes correctly
            sync_service = PositionSyncService()
            stats = sync_service.get_stats()
            duration = time.time() - start

            self.record_result(
                "Position Sync",
                TestResult.PASS,
                duration,
                "Position sync service initialized successfully",
                stats
            )
            return TestResult.PASS

        except Exception as e:
            duration = time.time() - start
            self.record_result(
                "Position Sync",
                TestResult.FAIL,
                duration,
                f"Error: {str(e)}"
            )
            return TestResult.FAIL

    # =========================================================================
    # Order Tests
    # =========================================================================

    async def test_limit_order_placement(self) -> TestResult:
        """Test limit order placement (far from market to avoid fill)"""
        start = time.time()

        if self.skip_orders:
            self.record_result(
                "Limit Order Placement",
                TestResult.SKIP,
                0,
                "Skipped: --skip-orders flag set"
            )
            return TestResult.SKIP

        if not self.client or not self.client.connected:
            self.record_result(
                "Limit Order Placement",
                TestResult.SKIP,
                0,
                "Skipped: Not connected"
            )
            return TestResult.SKIP

        try:
            # Get current price
            contract = self.client.create_contract(self.test_symbol)
            market_data = await self.client.get_market_data(contract)

            current_price = market_data.get('last') or market_data.get('bid') or 100.0

            # Place limit order far below market (won't fill)
            limit_price = round(current_price * 0.5, 2)  # 50% below market

            order = await self.client.place_limit_order(
                contract=contract,
                side=OrderSide.BUY,
                quantity=1,
                price=limit_price
            )

            duration = time.time() - start

            if order and order.order_id:
                self.test_orders.append(order.order_id)

                self.record_result(
                    "Limit Order Placement",
                    TestResult.PASS,
                    duration,
                    f"Order {order.order_id} placed: BUY 1 {self.test_symbol} @ ${limit_price}",
                    {
                        "order_id": order.order_id,
                        "symbol": order.symbol,
                        "side": order.side.value,
                        "quantity": order.quantity,
                        "price": order.price,
                        "status": order.status.value
                    }
                )
                return TestResult.PASS
            else:
                self.record_result(
                    "Limit Order Placement",
                    TestResult.FAIL,
                    duration,
                    "Order placement returned no order ID"
                )
                return TestResult.FAIL

        except Exception as e:
            duration = time.time() - start
            self.record_result(
                "Limit Order Placement",
                TestResult.FAIL,
                duration,
                f"Error: {str(e)}"
            )
            return TestResult.FAIL

    async def test_order_cancellation(self) -> TestResult:
        """Test order cancellation"""
        start = time.time()

        if self.skip_orders:
            self.record_result(
                "Order Cancellation",
                TestResult.SKIP,
                0,
                "Skipped: --skip-orders flag set"
            )
            return TestResult.SKIP

        if not self.client or not self.client.connected:
            self.record_result(
                "Order Cancellation",
                TestResult.SKIP,
                0,
                "Skipped: Not connected"
            )
            return TestResult.SKIP

        if not self.test_orders:
            self.record_result(
                "Order Cancellation",
                TestResult.SKIP,
                0,
                "Skipped: No test orders to cancel"
            )
            return TestResult.SKIP

        try:
            order_id = self.test_orders[-1]
            cancelled = await self.client.cancel_order(order_id)
            duration = time.time() - start

            if cancelled:
                self.test_orders.remove(order_id)
                self.record_result(
                    "Order Cancellation",
                    TestResult.PASS,
                    duration,
                    f"Order {order_id} cancelled successfully"
                )
                return TestResult.PASS
            else:
                self.record_result(
                    "Order Cancellation",
                    TestResult.FAIL,
                    duration,
                    f"Failed to cancel order {order_id}"
                )
                return TestResult.FAIL

        except Exception as e:
            duration = time.time() - start
            self.record_result(
                "Order Cancellation",
                TestResult.FAIL,
                duration,
                f"Error: {str(e)}"
            )
            return TestResult.FAIL

    async def test_market_order_small(self) -> TestResult:
        """Test small market order (PAPER TRADING ONLY - will execute!)"""
        start = time.time()

        if self.skip_orders:
            self.record_result(
                "Market Order (Small)",
                TestResult.SKIP,
                0,
                "Skipped: --skip-orders flag set"
            )
            return TestResult.SKIP

        if not self.client or not self.client.connected:
            self.record_result(
                "Market Order (Small)",
                TestResult.SKIP,
                0,
                "Skipped: Not connected"
            )
            return TestResult.SKIP

        # Double-check we're on paper trading port
        if settings.ibkr.port not in [7497, 4002]:
            self.record_result(
                "Market Order (Small)",
                TestResult.SKIP,
                0,
                f"Skipped: Port {settings.ibkr.port} is not a paper trading port"
            )
            return TestResult.SKIP

        try:
            contract = self.client.create_contract(self.test_symbol)

            # Place small market order (1 share)
            order = await self.client.place_market_order(
                contract=contract,
                side=OrderSide.BUY,
                quantity=1
            )

            duration = time.time() - start

            if order and order.order_id:
                self.record_result(
                    "Market Order (Small)",
                    TestResult.PASS,
                    duration,
                    f"Order {order.order_id} placed: BUY 1 {self.test_symbol} @ MARKET",
                    {
                        "order_id": order.order_id,
                        "symbol": order.symbol,
                        "side": order.side.value,
                        "quantity": order.quantity,
                        "status": order.status.value
                    }
                )
                return TestResult.PASS
            else:
                self.record_result(
                    "Market Order (Small)",
                    TestResult.FAIL,
                    duration,
                    "Market order placement returned no order ID"
                )
                return TestResult.FAIL

        except Exception as e:
            duration = time.time() - start
            self.record_result(
                "Market Order (Small)",
                TestResult.FAIL,
                duration,
                f"Error: {str(e)}"
            )
            return TestResult.FAIL

    # =========================================================================
    # Error Handling Tests
    # =========================================================================

    async def test_invalid_symbol(self) -> TestResult:
        """Test error handling for invalid symbol"""
        start = time.time()

        if not self.client or not self.client.connected:
            self.record_result(
                "Invalid Symbol Handling",
                TestResult.SKIP,
                0,
                "Skipped: Not connected"
            )
            return TestResult.SKIP

        try:
            # Try to get market data for invalid symbol
            contract = self.client.create_contract("INVALID_SYMBOL_XYZ123")

            try:
                await self.client.get_market_data(contract)
                duration = time.time() - start

                # If no error, that's unexpected but not necessarily wrong
                self.record_result(
                    "Invalid Symbol Handling",
                    TestResult.WARN,
                    duration,
                    "No error raised for invalid symbol (might return empty data)"
                )
                return TestResult.WARN

            except Exception as inner_e:
                duration = time.time() - start

                # Error is expected for invalid symbol
                self.record_result(
                    "Invalid Symbol Handling",
                    TestResult.PASS,
                    duration,
                    f"Correctly handled invalid symbol: {type(inner_e).__name__}"
                )
                return TestResult.PASS

        except Exception as e:
            duration = time.time() - start
            self.record_result(
                "Invalid Symbol Handling",
                TestResult.FAIL,
                duration,
                f"Unexpected error: {str(e)}"
            )
            return TestResult.FAIL

    async def test_disconnected_operation(self) -> TestResult:
        """Test error handling for operations when disconnected"""
        start = time.time()

        if not self.client:
            self.record_result(
                "Disconnected Operation Handling",
                TestResult.SKIP,
                0,
                "Skipped: No client"
            )
            return TestResult.SKIP

        try:
            # Temporarily disconnect
            was_connected = self.client.connected
            if was_connected:
                await self.client.disconnect()

            # Try operation while disconnected
            try:
                contract = self.client.create_contract(self.test_symbol)
                await self.client.get_market_data(contract)

                duration = time.time() - start

                # Should have raised an error
                self.record_result(
                    "Disconnected Operation Handling",
                    TestResult.FAIL,
                    duration,
                    "No error raised for operation while disconnected"
                )
                result = TestResult.FAIL

            except RuntimeError as e:
                duration = time.time() - start

                if "not connected" in str(e).lower():
                    self.record_result(
                        "Disconnected Operation Handling",
                        TestResult.PASS,
                        duration,
                        "Correctly raised error for disconnected operation"
                    )
                    result = TestResult.PASS
                else:
                    self.record_result(
                        "Disconnected Operation Handling",
                        TestResult.WARN,
                        duration,
                        f"Error raised but unexpected message: {e}"
                    )
                    result = TestResult.WARN

            # Reconnect if was connected
            if was_connected:
                await self.client.connect()

            return result

        except Exception as e:
            duration = time.time() - start
            self.record_result(
                "Disconnected Operation Handling",
                TestResult.FAIL,
                duration,
                f"Unexpected error: {str(e)}"
            )
            return TestResult.FAIL

    # =========================================================================
    # Event Handler Tests
    # =========================================================================

    async def test_callback_registration(self) -> TestResult:
        """Test callback registration"""
        start = time.time()

        if not self.client:
            self.record_result(
                "Callback Registration",
                TestResult.SKIP,
                0,
                "Skipped: No client"
            )
            return TestResult.SKIP

        try:
            callback_data = {"called": False}

            def test_callback(*args):
                callback_data["called"] = True

            # Register callbacks
            self.client.add_order_filled_callback(test_callback)
            self.client.add_position_update_callback(test_callback)
            self.client.add_error_callback(test_callback)

            duration = time.time() - start

            # Verify callbacks are registered
            has_order_callback = test_callback in self.client.order_filled_callbacks
            has_position_callback = test_callback in self.client.position_update_callbacks
            has_error_callback = test_callback in self.client.error_callbacks

            if has_order_callback and has_position_callback and has_error_callback:
                self.record_result(
                    "Callback Registration",
                    TestResult.PASS,
                    duration,
                    "All callbacks registered successfully"
                )
                return TestResult.PASS
            else:
                self.record_result(
                    "Callback Registration",
                    TestResult.FAIL,
                    duration,
                    f"Callbacks: order={has_order_callback}, position={has_position_callback}, error={has_error_callback}"
                )
                return TestResult.FAIL

        except Exception as e:
            duration = time.time() - start
            self.record_result(
                "Callback Registration",
                TestResult.FAIL,
                duration,
                f"Error: {str(e)}"
            )
            return TestResult.FAIL

    # =========================================================================
    # Run All Tests
    # =========================================================================

    async def run_all_tests(self) -> bool:
        """Run all tests and return success status"""
        if not await self.setup():
            return False

        try:
            # Connection tests
            logger.info("\n--- Connection Tests ---")
            await self.test_connection()
            await self.test_reconnection()

            # Account tests
            logger.info("\n--- Account Tests ---")
            await self.test_account_summary()

            # Market data tests
            logger.info("\n--- Market Data Tests ---")
            await self.test_market_data()
            await self.test_historical_data()

            # Position tests
            logger.info("\n--- Position Tests ---")
            await self.test_get_positions()
            await self.test_position_sync()

            # Order tests
            logger.info("\n--- Order Tests ---")
            await self.test_limit_order_placement()
            await self.test_order_cancellation()
            # Market order is commented out by default - enable with care
            # await self.test_market_order_small()

            # Error handling tests
            logger.info("\n--- Error Handling Tests ---")
            await self.test_invalid_symbol()
            await self.test_disconnected_operation()

            # Event handler tests
            logger.info("\n--- Event Handler Tests ---")
            await self.test_callback_registration()

        finally:
            await self.teardown()

        # Print summary
        self.print_summary()

        # Return success if no failures
        failures = sum(1 for r in self.results if r.result == TestResult.FAIL)
        return failures == 0

    def print_summary(self):
        """Print test summary"""
        logger.info("")
        logger.info("=" * 60)
        logger.info("TEST SUMMARY")
        logger.info("=" * 60)

        # Count results
        counts = {
            TestResult.PASS: 0,
            TestResult.FAIL: 0,
            TestResult.SKIP: 0,
            TestResult.WARN: 0
        }

        total_duration = 0
        for result in self.results:
            counts[result.result] += 1
            total_duration += result.duration

        logger.info(f"Total Tests: {len(self.results)}")
        logger.info(f"  ✅ Passed:  {counts[TestResult.PASS]}")
        logger.info(f"  ❌ Failed:  {counts[TestResult.FAIL]}")
        logger.info(f"  ⏭️  Skipped: {counts[TestResult.SKIP]}")
        logger.info(f"  ⚠️  Warnings: {counts[TestResult.WARN]}")
        logger.info(f"Total Duration: {total_duration:.2f}s")
        logger.info("")

        # List failures
        failures = [r for r in self.results if r.result == TestResult.FAIL]
        if failures:
            logger.info("FAILURES:")
            for f in failures:
                logger.info(f"  - {f.name}: {f.message}")

        logger.info("=" * 60)


async def main():
    """Main function"""
    parser = argparse.ArgumentParser(description="IBKR Paper Trading Integration Tests")
    parser.add_argument(
        "--skip-orders",
        action="store_true",
        help="Skip order placement tests"
    )
    parser.add_argument(
        "--symbol",
        type=str,
        default="AAPL",
        help="Symbol to use for testing (default: AAPL)"
    )
    args = parser.parse_args()

    tests = IBKRPaperTradingTests(
        test_symbol=args.symbol,
        skip_orders=args.skip_orders
    )

    try:
        success = await tests.run_all_tests()
        return 0 if success else 1
    except KeyboardInterrupt:
        logger.info("\n\nTests interrupted by user")
        return 1
    except Exception as e:
        logger.error(f"\n\nUnexpected error: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
