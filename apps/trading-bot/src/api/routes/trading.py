"""
Trading Routes
==============

API routes for trading operations and IBKR connection management.
"""

from fastapi import APIRouter, HTTPException, Depends
from typing import List, Dict, Any, Optional
import logging
from pydantic import BaseModel
from datetime import datetime

from ...data.brokers.ibkr_client import IBKRClient, IBKRManager, OrderSide
from ...data.database.models import Trade, TradeSide, OrderStatus, Account
from ...data.database import SessionLocal
from ...config.settings import settings
from ...utils.metrics_integration import update_portfolio_metrics_from_positions
from ...core.risk import get_risk_manager, RiskManager

logger = logging.getLogger(__name__)

router = APIRouter()

# Global IBKR manager instance
_ibkr_manager: Optional[IBKRManager] = None

class ConnectionTestRequest(BaseModel):
    """Connection test request model"""
    host: Optional[str] = None
    port: Optional[int] = None
    client_id: Optional[int] = None

class ConnectionResponse(BaseModel):
    """Connection status response model"""
    connected: bool
    host: str
    port: int
    client_id: int
    message: str

def get_ibkr_manager() -> Optional[IBKRManager]:
    """Get or create IBKR manager instance"""
    global _ibkr_manager
    if _ibkr_manager is None:
        _ibkr_manager = IBKRManager(
            host=settings.ibkr.host,
            port=settings.ibkr.port,
            client_id=settings.ibkr.client_id
        )
    return _ibkr_manager

@router.get("/ibkr/status", response_model=ConnectionResponse)
async def ibkr_connection_status():
    """Get current IBKR connection status"""
    manager = get_ibkr_manager()
    
    if not manager:
        return ConnectionResponse(
            connected=False,
            host=settings.ibkr.host,
            port=settings.ibkr.port,
            client_id=settings.ibkr.client_id,
            message="IBKR manager not initialized"
        )
    
    is_connected = manager.is_connected
    
    # Update broker connection status metric
    try:
        from ...utils.metrics_trading import update_broker_connection_status
        update_broker_connection_status(is_connected)
    except Exception:
        pass
    
    return ConnectionResponse(
        connected=is_connected,
        host=settings.ibkr.host,
        port=settings.ibkr.port,
        client_id=settings.ibkr.client_id,
        message="Connected" if is_connected else "Not connected"
    )

@router.post("/ibkr/connect")
async def ibkr_connect(request: Optional[ConnectionTestRequest] = None):
    """Connect to IBKR"""
    global _ibkr_manager
    
    # Use provided values or defaults
    host = request.host if request and request.host else settings.ibkr.host
    port = request.port if request and request.port else settings.ibkr.port
    client_id = request.client_id if request and request.client_id else settings.ibkr.client_id
    
    try:
        # Create new manager with specified config
        _ibkr_manager = IBKRManager(host=host, port=port, client_id=client_id)
        await _ibkr_manager.start()
        
        if _ibkr_manager.is_connected:
            return {
                "status": "success",
                "message": "Successfully connected to IBKR",
                "host": host,
                "port": port,
                "client_id": client_id
            }
        else:
            raise HTTPException(
                status_code=500,
                detail="Failed to connect to IBKR. Make sure TWS/Gateway is running and API is enabled."
            )
    except Exception as e:
        logger.error(f"Error connecting to IBKR: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Connection error: {str(e)}"
        )

@router.post("/ibkr/disconnect")
async def ibkr_disconnect():
    """Disconnect from IBKR"""
    global _ibkr_manager
    
    if _ibkr_manager:
        try:
            await _ibkr_manager.stop()
            _ibkr_manager = None
            return {
                "status": "success",
                "message": "Disconnected from IBKR"
            }
        except Exception as e:
            logger.error(f"Error disconnecting from IBKR: {e}")
            raise HTTPException(
                status_code=500,
                detail=f"Disconnect error: {str(e)}"
            )
    else:
        return {
            "status": "success",
            "message": "Already disconnected"
        }

@router.post("/ibkr/test")
async def ibkr_test_connection(request: Optional[ConnectionTestRequest] = None):
    """Test IBKR connection with detailed diagnostics"""
    # Use provided values or defaults
    host = request.host if request and request.host else settings.ibkr.host
    port = request.port if request and request.port else settings.ibkr.port
    client_id = request.client_id if request and request.client_id else settings.ibkr.client_id
    
    client = None
    results = {
        "connected": False,
        "host": host,
        "port": port,
        "client_id": client_id,
        "tests": {}
    }
    
    try:
        logger.info(f"Testing IBKR connection to {host}:{port} (client_id: {client_id})")
        
        client = IBKRClient(host=host, port=port, client_id=client_id)
        connected = await client.connect()
        
        results["connected"] = connected
        
        if not connected:
            results["error"] = "Failed to connect. Make sure TWS/Gateway is running and API connections are enabled."
            return results
        
        # Test account access
        try:
            account_summary = await client.get_account_summary()
            results["tests"]["account_access"] = {
                "success": True,
                "fields_retrieved": len(account_summary)
            }
        except Exception as e:
            results["tests"]["account_access"] = {
                "success": False,
                "error": str(e)
            }
        
        # Test market data access
        try:
            contract = client.create_contract("AAPL")
            market_data = await client.get_market_data(contract)
            results["tests"]["market_data"] = {
                "success": True,
                "sample_symbol": "AAPL",
                "data_keys": list(market_data.keys())
            }
        except Exception as e:
            results["tests"]["market_data"] = {
                "success": False,
                "error": str(e)
            }
        
        # Test position access
        try:
            positions = await client.get_positions()
            results["tests"]["positions"] = {
                "success": True,
                "position_count": len(positions)
            }
        except Exception as e:
            results["tests"]["positions"] = {
                "success": False,
                "error": str(e)
            }
        
        results["message"] = "Connection test completed successfully"
        
    except Exception as e:
        logger.error(f"Error testing IBKR connection: {e}")
        results["error"] = str(e)
        
    finally:
        if client:
            await client.disconnect()
    
    return results

@router.get("/ibkr/account")
async def ibkr_account_summary():
    """Get IBKR account summary"""
    manager = get_ibkr_manager()
    
    if not manager or not manager.is_connected:
        raise HTTPException(
            status_code=503,
            detail="IBKR not connected. Please connect first using /api/trading/ibkr/connect"
        )
    
    try:
        client = await manager.get_client()
        account_summary = await client.get_account_summary()
        return {
            "status": "success",
            "account_data": account_summary
        }
    except Exception as e:
        logger.error(f"Error getting account summary: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Error retrieving account data: {str(e)}"
        )

@router.get("/ibkr/positions")
async def ibkr_positions():
    """Get current IBKR positions"""
    manager = get_ibkr_manager()
    
    if not manager or not manager.is_connected:
        raise HTTPException(
            status_code=503,
            detail="IBKR not connected. Please connect first using /api/trading/ibkr/connect"
        )
    
    try:
        client = await manager.get_client()
        positions = await client.get_positions()
        
        positions_list = []
        for pos in positions:
            positions_list.append({
                "symbol": pos.symbol,
                "quantity": pos.quantity,
                "average_price": pos.average_price,
                "market_price": pos.market_price,
                "unrealized_pnl": pos.unrealized_pnl,
                "unrealized_pnl_pct": pos.unrealized_pnl_pct
            })
            
            # Update position metrics
            try:
                from ...utils.metrics_trading import update_position_metrics
                update_position_metrics(
                    symbol=pos.symbol,
                    quantity=pos.quantity,
                    pnl=pos.unrealized_pnl
                )
            except Exception:
                pass
        
        # Update portfolio-level metrics
        try:
            update_portfolio_metrics_from_positions(positions_list)
        except Exception:
            pass
        
        return {
            "status": "success",
            "positions": positions_list
        }
    except Exception as e:
        logger.error(f"Error getting positions: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Error retrieving positions: {str(e)}"
        )

@router.post("/execute")
async def execute_trade(
    trade_request: Dict[str, Any],
    risk_manager: RiskManager = Depends(lambda: get_risk_manager())
):
    """
    Execute a trade with risk management validation
    
    Required fields:
    - account_id: Account ID
    - symbol: Stock symbol
    - side: "BUY" or "SELL"
    - quantity: Number of shares (optional if confidence_score provided)
    - price_per_share: Price per share (required)
    - confidence_score: Optional confidence score (0.0-1.0) for position sizing
    
    Optional fields:
    - strategy_id: Strategy ID that generated this trade
    - will_create_day_trade: Whether this will create a day trade
    """
    try:
        # Extract request parameters
        account_id = trade_request.get("account_id")
        symbol = trade_request.get("symbol")
        side_str = trade_request.get("side", "BUY").upper()
        quantity = trade_request.get("quantity")
        price_per_share = trade_request.get("price_per_share")
        confidence_score = trade_request.get("confidence_score")
        strategy_id = trade_request.get("strategy_id")
        will_create_day_trade = trade_request.get("will_create_day_trade", False)
        
        # Validate required fields
        if not account_id:
            raise HTTPException(status_code=400, detail="account_id is required")
        if not symbol:
            raise HTTPException(status_code=400, detail="symbol is required")
        if not price_per_share:
            raise HTTPException(status_code=400, detail="price_per_share is required")
        if side_str not in ["BUY", "SELL"]:
            raise HTTPException(status_code=400, detail="side must be 'BUY' or 'SELL'")
        
        # Convert side to enum
        trade_side = TradeSide.BUY if side_str == "BUY" else TradeSide.SELL
        
        # 1. Pre-trade validation with risk management
        logger.info(f"Validating trade: {side_str} {quantity or 'auto'} {symbol} @ ${price_per_share:.2f}")
        
        validation = await risk_manager.validate_trade(
            account_id=account_id,
            symbol=symbol,
            side=side_str,
            quantity=quantity,
            price_per_share=price_per_share,
            confidence_score=confidence_score,
            will_create_day_trade=will_create_day_trade
        )
        
        if not validation.can_proceed:
            logger.warning(
                f"Trade rejected: {side_str} {quantity or 'auto'} {symbol} - {validation.compliance_check.message}"
            )
            raise HTTPException(
                status_code=403,
                detail={
                    "error": "Trade rejected by risk management",
                    "reason": validation.compliance_check.result.value,
                    "message": validation.compliance_check.message,
                    "compliance_details": validation.compliance_check.details
                }
            )
        
        # 2. Use position size from validation if calculated
        if validation.position_size and validation.position_size.size_shares > 0:
            quantity = validation.position_size.size_shares
            logger.info(
                f"Using calculated position size: {quantity} shares "
                f"({validation.position_size.confidence_level.value} confidence)"
            )
        
        if not quantity or quantity <= 0:
            raise HTTPException(
                status_code=400,
                detail="Quantity must be specified or confidence_score provided for auto-sizing"
            )
        
        # 3. Get IBKR manager and client
        manager = get_ibkr_manager()
        if not manager or not manager.is_connected:
            raise HTTPException(
                status_code=503,
                detail="IBKR not connected. Please connect first using /api/trading/ibkr/connect"
            )
        
        client = await manager.get_client()
        
        # 4. Create contract and place order
        contract = client.create_contract(symbol)
        ibkr_side = OrderSide.BUY if trade_side == TradeSide.BUY else OrderSide.SELL
        
        # For now, use market orders (can be enhanced to support limit orders)
        broker_order = await client.place_market_order(contract, ibkr_side, quantity)
        
        logger.info(
            f"Order placed: {side_str} {quantity} {symbol} @ market "
            f"(order_id: {broker_order.order_id})"
        )
        
        # 5. Record trade in database
        session = SessionLocal()
        try:
            # Get account (verify it exists)
            account = session.query(Account).filter(Account.id == account_id).first()
            if not account:
                raise HTTPException(status_code=404, detail=f"Account {account_id} not found")
            
            # Create trade record
            trade = Trade(
                account_id=account_id,
                strategy_id=strategy_id,
                symbol=symbol,
                side=trade_side,
                quantity=quantity,
                price=price_per_share,
                order_type="market",
                status=OrderStatus.SUBMITTED,
                filled_quantity=0,
                confidence_score=confidence_score
            )
            session.add(trade)
            session.flush()  # Get trade ID
            
            # Record settlement for this trade
            trade_amount = quantity * price_per_share
            settlement_amount = -trade_amount if trade_side == TradeSide.BUY else trade_amount
            risk_manager.compliance.record_settlement(
                account_id=account_id,
                trade_id=trade.id,
                trade_date=datetime.now(),
                amount=settlement_amount
            )
            
            # Calculate and store settlement date
            trade.settlement_date = risk_manager.compliance.calculate_settlement_date(datetime.now())
            
            # Increment trade frequency
            risk_manager.compliance.increment_trade_frequency(account_id, datetime.now())
            
            # Check for day trade (for SELL orders)
            if trade_side == TradeSide.SELL:
                day_trade = risk_manager.compliance.detect_day_trade(
                    account_id=account_id,
                    symbol=symbol,
                    side=trade_side,
                    trade_date=datetime.now(),
                    trade_id=trade.id
                )
                if day_trade:
                    buy_trade_id, sell_trade_id = day_trade
                    risk_manager.compliance.record_day_trade(
                        account_id=account_id,
                        symbol=symbol,
                        buy_trade_id=buy_trade_id,
                        sell_trade_id=sell_trade_id,
                        trade_date=datetime.now()
                    )
                    trade.is_day_trade = True
                    logger.info(f"Day trade detected and recorded for {symbol}")
            
            session.commit()
            session.refresh(trade)
            
            logger.info(f"Trade recorded in database: trade_id={trade.id}")
            
            return {
                "status": "success",
                "message": "Trade executed successfully",
                "trade_id": trade.id,
                "broker_order_id": broker_order.order_id,
                "symbol": symbol,
                "side": side_str,
                "quantity": quantity,
                "price": price_per_share,
                "order_status": "submitted",
                "validation": {
                    "passed": True,
                    "compliance_result": validation.compliance_check.result.value,
                    "position_size": {
                        "size_shares": validation.position_size.size_shares if validation.position_size else quantity,
                        "size_usd": validation.position_size.size_usd if validation.position_size else quantity * price_per_share,
                        "confidence_level": validation.position_size.confidence_level.value if validation.position_size else None
                    } if validation.position_size else None
                }
            }
        except HTTPException:
            session.rollback()
            raise
        except Exception as e:
            session.rollback()
            logger.error(f"Error recording trade: {e}", exc_info=True)
            raise HTTPException(status_code=500, detail=f"Error recording trade: {str(e)}")
        finally:
            session.close()
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error executing trade: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Trade execution error: {str(e)}")


@router.post("/live-trade")
async def live_trade(trade_request: Dict[str, Any]):
    """
    Execute a live trade (legacy endpoint, redirects to /execute)
    
    Deprecated: Use /execute instead
    """
    logger.warning("/live-trade endpoint is deprecated, use /execute instead")
    return await execute_trade(trade_request)

@router.post("/backtest")
async def backtest(backtest_request: Dict[str, Any]):
    """Run a backtest"""
    logger.info(f"Backtest request: {backtest_request}")
    
    # TODO: Implement backtesting logic
    return {
        "status": "success",
        "message": "Backtesting not yet implemented",
        "results": {}
    }

@router.get("/status")
async def trading_status():
    """Get trading bot status"""
    manager = get_ibkr_manager()
    ibkr_connected = manager.is_connected if manager else False
    
    return {
        "status": "running",
        "ibkr_connected": ibkr_connected,
        "active_strategies": 0,
        "open_positions": 0,
        "last_trade": None
    }