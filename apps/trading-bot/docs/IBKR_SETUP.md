# Interactive Brokers (IBKR) Setup Guide

This guide covers the required setup, permissions, and configuration for using Interactive Brokers with the trading bot.

## Prerequisites

1. **Interactive Brokers Account**
   - Paper trading account for testing
   - Live account for production (with appropriate funding)

2. **TWS or IB Gateway**
   - Download from: https://www.interactivebrokers.com/en/trading/tws.php
   - IB Gateway is recommended for automated trading (more stable, lower resource usage)

3. **Python Dependencies**
   ```bash
   pip install ib-insync
   ```

## TWS/Gateway Configuration

### Enable API Access

1. Open TWS or IB Gateway
2. Navigate to: **Edit → Global Configuration → API → Settings**
3. Configure the following:

| Setting | Value | Notes |
|---------|-------|-------|
| Enable ActiveX and Socket Clients | ✓ Checked | Required for API access |
| Read-Only API | ☐ Unchecked | Uncheck to allow trading |
| Socket Port | 7497 (paper) / 7496 (live) | See port table below |
| Allow connections from localhost only | ✓ Recommended | Security best practice |
| Trusted IPs | 127.0.0.1 | Add if needed |

### Port Configuration

| Environment | TWS Port | Gateway Port |
|-------------|----------|--------------|
| Paper Trading | 7497 | 4002 |
| Live Trading | 7496 | 4001 |

### API Precautions

In **Edit → Global Configuration → API → Precautions**:
- Set up order confirmations as needed
- Configure order size limits
- Enable/disable specific order types

## Required Permissions

### Minimum Permissions for Trading Bot

1. **Market Data**
   - Delayed market data (free) - minimum for basic functionality
   - Real-time market data (subscription required) - recommended

2. **Trading Permissions**
   - US stocks (for default symbols like AAPL, MSFT)
   - Enable specific asset classes as needed

3. **API Permissions**
   - Socket API access
   - Order submission
   - Position queries
   - Account data

### Market Data Subscriptions

For real-time data, subscribe to appropriate market data packages:

| Data Package | Coverage | Notes |
|--------------|----------|-------|
| US Securities Snapshot Bundle | NYSE, NASDAQ, AMEX | Recommended for US stocks |
| US Equity Level 1 | Basic quotes | Lower cost option |

Check available subscriptions at: Account Management → Settings → Market Data Subscriptions

## Environment Configuration

Create or update `.env` file:

```env
# IBKR Connection Settings
IBKR_HOST=127.0.0.1
IBKR_PORT=7497          # Use 7497 for paper, 7496 for live
IBKR_CLIENT_ID=9        # Unique ID for this connection

# Trading Mode
TRADING_MODE=paper      # 'paper' or 'live'
```

## Connection Testing

### Basic Connection Test

```bash
cd apps/trading-bot
python scripts/test_ibkr_connection.py
```

### Paper Trading Integration Tests

```bash
python scripts/test_ibkr_paper_trading.py

# Skip order tests (read-only)
python scripts/test_ibkr_paper_trading.py --skip-orders

# Test with specific symbol
python scripts/test_ibkr_paper_trading.py --symbol MSFT
```

## Troubleshooting

### Common Issues

#### "Not connected to IBKR"
1. Ensure TWS/Gateway is running
2. Check API is enabled in settings
3. Verify port number matches configuration
4. Check for firewall blocking

#### "Client ID already in use"
- Another application is using the same client ID
- Change `IBKR_CLIENT_ID` in `.env` to a unique value

#### "No market data permissions"
- Subscribe to market data packages in Account Management
- Wait 24 hours for subscription to activate
- Use delayed data if real-time not available

#### Connection Drops
- Enable auto-restart in Gateway settings
- Implement reconnection logic (built into IBKRManager)
- Check internet connection stability

### Debug Logging

Enable verbose logging:

```python
import logging
logging.getLogger('ib_insync').setLevel(logging.DEBUG)
```

## Security Best Practices

1. **Use Paper Trading for Development**
   - Always test new code in paper mode first
   - Port 7497 (TWS) or 4002 (Gateway)

2. **Limit API Permissions**
   - Only enable permissions you need
   - Use Read-Only API when not actively trading

3. **Network Security**
   - Allow connections from localhost only
   - Don't expose API ports to the internet
   - Use firewall rules if needed

4. **Order Safety**
   - Set maximum order sizes in API Precautions
   - Implement position limits in code
   - Use risk management checks before order submission

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                      Trading Bot                             │
├─────────────────────────────────────────────────────────────┤
│  IBKRManager                                                 │
│  ├── Connection monitoring                                   │
│  ├── Auto-reconnection                                       │
│  └── Client lifecycle                                        │
├─────────────────────────────────────────────────────────────┤
│  IBKRClient                                                  │
│  ├── Order placement (market, limit)                         │
│  ├── Position queries                                        │
│  ├── Market data                                             │
│  ├── Historical data                                         │
│  └── Event callbacks                                         │
├─────────────────────────────────────────────────────────────┤
│  PositionSyncService                                         │
│  ├── IBKR → Database sync                                    │
│  ├── P&L tracking                                            │
│  └── Position lifecycle                                      │
└─────────────────────────────────────────────────────────────┘
            │
            │ ib_insync (async)
            ▼
┌─────────────────────────────────────────────────────────────┐
│           TWS / IB Gateway (Port 7497/7496)                  │
└─────────────────────────────────────────────────────────────┘
            │
            │ FIX Protocol
            ▼
┌─────────────────────────────────────────────────────────────┐
│              Interactive Brokers Servers                     │
└─────────────────────────────────────────────────────────────┘
```

## File Structure

```
src/data/brokers/
├── ibkr_client.py      # IBKRClient and IBKRManager classes
└── __init__.py

src/core/sync/
├── position_sync.py    # Position sync service
└── __init__.py

scripts/
├── test_ibkr_connection.py      # Basic connection test
└── test_ibkr_paper_trading.py   # Comprehensive integration tests

tests/
├── mocks/
│   └── mock_ibkr_client.py      # Mock client for unit tests
└── integration/
    └── brokers/
        └── test_ibkr_integration.py  # Integration tests
```

## API Reference

### IBKRClient

```python
from src.data.brokers.ibkr_client import IBKRClient, OrderSide

async with IBKRClient(host="127.0.0.1", port=7497, client_id=9) as client:
    # Get market data
    contract = client.create_contract("AAPL")
    data = await client.get_market_data(contract)

    # Place order
    order = await client.place_market_order(
        contract=contract,
        side=OrderSide.BUY,
        quantity=10
    )

    # Get positions
    positions = await client.get_positions()

    # Get account summary
    summary = await client.get_account_summary()
```

### IBKRManager

```python
from src.data.brokers.ibkr_client import IBKRManager

manager = IBKRManager(host="127.0.0.1", port=7497, client_id=9)
await manager.start()

# Manager handles reconnection automatically
client = await manager.get_client()

# Clean shutdown
await manager.stop()
```

## Next Steps

1. Run connection test to verify setup
2. Run paper trading tests to verify functionality
3. Test with small positions in paper mode
4. Review risk management settings before live trading
5. Monitor logs during initial live trading
