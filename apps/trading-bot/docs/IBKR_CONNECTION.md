# Interactive Brokers Connection Guide

This guide explains how to set up and manage the connection to Interactive Brokers (IBKR) for live trading.

## Table of Contents

- [Overview](#overview)
- [Prerequisites](#prerequisites)
- [Initial Setup](#initial-setup)
- [Configuration](#configuration)
- [Testing the Connection](#testing-the-connection)
- [API Endpoints](#api-endpoints)
- [Troubleshooting](#troubleshooting)
- [Advanced Usage](#advanced-usage)

## Overview

The trading bot integrates with Interactive Brokers using the `ib_insync` library. This allows you to:
- Connect to TWS (Trader Workstation) or IB Gateway
- Execute trades
- Monitor positions
- Access market data
- Retrieve account information

## Prerequisites

### 1. Interactive Brokers Account

You need an Interactive Brokers account. You can use:
- **Paper Trading Account**: Free test account with virtual money (recommended for testing)
- **Live Account**: Real trading account with real money

### 2. Install TWS or IB Gateway

Download and install one of the following:

**Trader Workstation (TWS)**:
- Full-featured desktop application
- Download: https://www.interactivebrokers.com/en/index.php?f=16042
- Available for Windows, macOS, and Linux

**IB Gateway** (Recommended for automated trading):
- Lightweight, headless application
- Download: https://www.interactivebrokers.com/en/index.php?f=16457
- Better for server environments

### 3. Enable API Connections

Before the bot can connect, you must enable API connections in TWS/Gateway:

1. **Open TWS or IB Gateway**
2. **Go to**: `Edit → Global Configuration → API → Settings`
3. **Enable**:
   - ✅ **Enable ActiveX and Socket Clients**
   - ✅ **Read-Only API**: Unchecked (needed for trading)
   - Set **Socket Port**: 
     - `7497` for Paper Trading
     - `7496` for Live Trading
4. **Click Apply** and restart TWS/Gateway

⚠️ **Important**: The port configuration must match your environment settings.

### 4. Python Dependencies

The required dependencies are already included in `requirements.txt`:
```bash
ib-insync==0.9.86
```

Install with:
```bash
pip install -r requirements.txt
# or
pip install -r requirements/base.txt
```

## Configuration

### Environment Variables

Configure IBKR connection settings via environment variables or `.env` file:

```env
# Interactive Brokers Configuration
IBKR_HOST=127.0.0.1          # TWS/Gateway host (localhost)
IBKR_PORT=7497               # 7497 for paper, 7496 for live
IBKR_CLIENT_ID=9             # Unique client ID (avoid conflicts)
IBKR_TIMEOUT=10              # Connection timeout in seconds
```

### Configuration Notes

- **Host**: Usually `127.0.0.1` (localhost) when TWS/Gateway is on the same machine
- **Port**: 
  - Paper Trading: `7497` (default)
  - Live Trading: `7496` (default)
- **Client ID**: A unique integer (1-99). Each application connecting to TWS needs a unique ID.
  - Default: `9`
  - Change if you have multiple applications connecting simultaneously

### Docker Configuration

When running in Docker, use `host.docker.internal` to connect to TWS/Gateway on the host machine:

```yaml
environment:
  IBKR_HOST: host.docker.internal
  IBKR_PORT: 7497
  IBKR_CLIENT_ID: 9
```

The `docker-compose.yml` already includes this configuration.

## Testing the Connection

### Method 1: Command Line Script (Recommended)

Use the provided test script to verify your connection:

```bash
cd apps/trading-bot
python scripts/test_ibkr_connection.py
```

This script will:
- ✅ Check if `ib_insync` is installed
- ✅ Test connection to TWS/Gateway
- ✅ Verify account access
- ✅ Test market data retrieval
- ✅ Check position access

**Expected Output**:
```
============================================================
Interactive Brokers Connection Test
============================================================

📋 Configuration:
   Host: 127.0.0.1
   Port: 7497
   Client ID: 9

✅ ib_insync is installed
🔌 Attempting to connect to IBKR...
   Make sure TWS or IB Gateway is running!

✅ Successfully connected to IBKR!

📊 Testing account access...
✅ Account access successful!
   Retrieved 50 account fields

📈 Testing market data access...
✅ Market data access successful!
   AAPL Quote:
      Last: $175.50
      Bid: $175.49
      Ask: $175.51

💼 Testing position access...
✅ Position access successful!
   Current positions: 0

============================================================
✅ Connection test completed successfully!
============================================================
```

### Method 2: API Endpoint

If the API server is running, test via HTTP:

```bash
# Test connection
curl -X POST http://localhost:8000/api/trading/ibkr/test

# Check connection status
curl http://localhost:8000/api/trading/ibkr/status
```

See [API Endpoints](#api-endpoints) section for more details.

### Method 3: Python Interactive

Test in Python directly:

```python
import asyncio
from src.data.brokers.ibkr_client import IBKRClient
from src.config.settings import settings

async def test():
    client = IBKRClient(
        host=settings.ibkr.host,
        port=settings.ibkr.port,
        client_id=settings.ibkr.client_id
    )
    
    connected = await client.connect()
    if connected:
        print("✅ Connected!")
        
        # Test market data
        contract = client.create_contract("AAPL")
        data = await client.get_market_data(contract)
        print(f"AAPL: ${data['last']:.2f}")
        
        await client.disconnect()
    else:
        print("❌ Connection failed")

asyncio.run(test())
```

## API Endpoints

The trading bot provides several API endpoints for managing the IBKR connection:

### Connection Status

```http
GET /api/trading/ibkr/status
```

Returns current connection status:
```json
{
  "connected": true,
  "host": "127.0.0.1",
  "port": 7497,
  "client_id": 9,
  "message": "Connected"
}
```

### Connect

```http
POST /api/trading/ibkr/connect
Content-Type: application/json

{
  "host": "127.0.0.1",  // Optional, uses default if omitted
  "port": 7497,         // Optional
  "client_id": 9        // Optional
}
```

Establishes connection to IBKR. The connection persists until manually disconnected.

### Disconnect

```http
POST /api/trading/ibkr/disconnect
```

Disconnects from IBKR.

### Test Connection

```http
POST /api/trading/ibkr/test
Content-Type: application/json

{
  "host": "127.0.0.1",  // Optional
  "port": 7497,         // Optional
  "client_id": 9        // Optional
}
```

Comprehensive connection test with diagnostics:
```json
{
  "connected": true,
  "host": "127.0.0.1",
  "port": 7497,
  "client_id": 9,
  "tests": {
    "account_access": {
      "success": true,
      "fields_retrieved": 50
    },
    "market_data": {
      "success": true,
      "sample_symbol": "AAPL",
      "data_keys": ["bid", "ask", "last", "volume"]
    },
    "positions": {
      "success": true,
      "position_count": 0
    }
  },
  "message": "Connection test completed successfully"
}
```

### Get Account Summary

```http
GET /api/trading/ibkr/account
```

Retrieves account summary (requires connection):
```json
{
  "status": "success",
  "account_data": {
    "NetLiquidation": {
      "value": "100000.00",
      "currency": "USD"
    },
    "TotalCashValue": {
      "value": "100000.00",
      "currency": "USD"
    },
    ...
  }
}
```

### Get Positions

```http
GET /api/trading/ibkr/positions
```

Returns current positions:
```json
{
  "status": "success",
  "positions": [
    {
      "symbol": "AAPL",
      "quantity": 10,
      "average_price": 150.25,
      "market_price": 175.50,
      "unrealized_pnl": 252.50,
      "unrealized_pnl_pct": 0.1681
    }
  ]
}
```

## Troubleshooting

### Connection Failed

**Error**: `Failed to connect to IBKR`

**Solutions**:
1. ✅ Verify TWS or IB Gateway is running
2. ✅ Check API connections are enabled in TWS/Gateway settings
3. ✅ Verify port number matches (7497 for paper, 7496 for live)
4. ✅ Check firewall isn't blocking the connection
5. ✅ Try a different client ID if multiple apps are connected
6. ✅ Restart TWS/Gateway after changing settings

### Client ID Conflict

**Error**: `Client Already Connected` or connection refused

**Solution**: Change the `IBKR_CLIENT_ID` to a different number (1-99) that isn't in use.

### Market Data Not Available

**Error**: `Could not get market data` or missing price data

**Possible Causes**:
- Market data subscription not enabled for the symbol
- Market is closed
- Symbol doesn't exist or incorrect exchange

**Solutions**:
- Subscribe to market data in IBKR account management
- For testing, use major symbols like AAPL, MSFT, TSLA
- Verify symbol format (e.g., "AAPL" not "AAPL.US")

### Account Summary Access Denied

**Error**: `Could not get account summary`

**Possible Causes**:
- Read-only API is enabled in TWS settings
- Insufficient permissions
- Account doesn't exist

**Solution**: 
- Disable "Read-Only API" in TWS/Gateway settings
- Verify account credentials

### Docker Connection Issues

**Error**: Cannot connect from Docker container

**Solutions**:
1. Use `host.docker.internal` as host (already configured)
2. Ensure TWS/Gateway allows connections from Docker network
3. On Linux, may need to add `--network host` to docker run

### Connection Timeout

**Error**: Connection timeout after 10 seconds

**Solutions**:
- Verify TWS/Gateway is actually running
- Check network connectivity
- Increase timeout: `IBKR_TIMEOUT=30`
- Ensure no firewall is blocking

### Automatic Reconnection

The bot includes automatic reconnection logic:
- Reconnects automatically if connection is lost
- Monitors connection every 30 seconds
- Attempts up to 5 reconnections with 5-second delays

This is handled automatically by the `IBKRManager` class.

## Advanced Usage

### Custom Connection Settings

Override default settings per connection:

```python
from src.data.brokers.ibkr_client import IBKRClient

# Connect with custom settings
client = IBKRClient(
    host="192.168.1.100",  # Remote TWS
    port=7497,
    client_id=5
)

await client.connect()
```

### Event Handlers

Subscribe to events:

```python
def on_order_filled(trade):
    print(f"Order filled: {trade}")

def on_position_update(position):
    print(f"Position updated: {position}")

def on_error(reqId, errorCode, errorString):
    print(f"Error {errorCode}: {errorString}")

client = IBKRClient()
client.add_order_filled_callback(on_order_filled)
client.add_position_update_callback(on_position_update)
client.add_error_callback(on_error)

await client.connect()
```

### Async Context Manager

Use as async context manager for automatic cleanup:

```python
async with IBKRClient() as client:
    # Use client
    positions = await client.get_positions()
    # Automatically disconnected on exit
```

### IBKRManager for Persistent Connection

Use `IBKRManager` for long-running applications:

```python
from src.data.brokers.ibkr_client import IBKRManager

manager = IBKRManager()
await manager.start()  # Connects and monitors

# Use throughout application
client = await manager.get_client()
positions = await client.get_positions()

# When done
await manager.stop()
```

## Additional Resources

- [IBKR API Documentation](https://interactivebrokers.github.io/tws-api/)
- [ib_insync Documentation](https://ib-insync.readthedocs.io/)
- [IBKR Paper Trading Guide](https://www.interactivebrokers.com/en/index.php?f=4588)

## Support

If you encounter issues:
1. Check this troubleshooting guide
2. Review the test script output
3. Check TWS/Gateway logs
4. Verify API settings in TWS/Gateway
5. Open an issue on GitHub with:
   - Error message
   - Configuration (without sensitive data)
   - Test script output

---

**⚠️ Important**: Always test with paper trading first before using real money!

