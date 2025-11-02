"""
Trading Routes
==============

API routes for trading operations and IBKR connection management.
"""

from fastapi import APIRouter, HTTPException, Depends
from typing import List, Dict, Any, Optional
import logging
from pydantic import BaseModel

from ...data.brokers.ibkr_client import IBKRClient, IBKRManager
from ...config.settings import settings

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
        
        return {
            "status": "success",
            "positions": [
                {
                    "symbol": pos.symbol,
                    "quantity": pos.quantity,
                    "average_price": pos.average_price,
                    "market_price": pos.market_price,
                    "unrealized_pnl": pos.unrealized_pnl,
                    "unrealized_pnl_pct": pos.unrealized_pnl_pct
                }
                for pos in positions
            ]
        }
    except Exception as e:
        logger.error(f"Error getting positions: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Error retrieving positions: {str(e)}"
        )

@router.post("/live-trade")
async def live_trade(trade_request: Dict[str, Any]):
    """Execute a live trade"""
    logger.info(f"Live trade request: {trade_request}")
    
    # TODO: Implement live trading logic
    return {
        "status": "success",
        "message": "Live trading not yet implemented",
        "trade_id": "placeholder"
    }

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