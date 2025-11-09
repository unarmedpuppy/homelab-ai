# IBKR Integration Plan - Wire Dashboard to Real IBKR Data

## Current State

### ✅ Already Integrated:
1. **Portfolio Summary** (`/api/trading/portfolio/summary`) - Uses IBKR when connected
   - Gets account summary (NetLiquidation, TotalCashValue)
   - Gets positions (count, value, P&L)
   - Returns zeros if IBKR not connected

2. **IBKR Connection Endpoints** - Exist and work
   - `POST /api/trading/ibkr/connect` - Connect to IBKR
   - `POST /api/trading/ibkr/disconnect` - Disconnect
   - `GET /api/trading/ibkr/status` - Check connection status
   - `GET /api/trading/ibkr/account` - Get account summary
   - `GET /api/trading/ibkr/positions` - Get positions

### ❌ Missing:
1. **Dashboard UI** - No connect/disconnect buttons
2. **Market Data Quotes** - Uses Yahoo Finance/Alpha Vantage, not IBKR
3. **Real-time Price Updates** - Not using IBKR market data
4. **Connection Status Display** - Shows status but can't connect from UI

## Implementation Plan

### Phase 1: Add IBKR Connection Controls to Dashboard
- [ ] Add "Connect to IBKR" button in header/navigation
- [ ] Add connection status display (already exists, enhance it)
- [ ] Add disconnect button
- [ ] Show connection details (host, port) when connected
- [ ] Handle connection errors gracefully

### Phase 2: Wire Market Data to IBKR
- [ ] Update `/api/market-data/quote/{symbol}` to use IBKR when connected
- [ ] Add IBKR as a provider in DataProviderManager
- [ ] Fallback to Yahoo Finance if IBKR not connected
- [ ] Use IBKR's real-time market data for quotes

### Phase 3: Real-time IBKR Data Streaming
- [ ] Use IBKR's real-time market data subscriptions
- [ ] Stream price updates via WebSocket
- [ ] Update dashboard prices in real-time when IBKR connected

### Phase 4: Verify Full Integration
- [ ] Test portfolio summary with real IBKR connection
- [ ] Test market data quotes from IBKR
- [ ] Test position updates
- [ ] Test account summary display
- [ ] End-to-end test: Connect → View data → Trade

## Technical Details

### IBKR Client Methods Available:
- `get_account_summary()` - Returns account data (NetLiquidation, cash, etc.)
- `get_positions()` - Returns current positions with P&L
- `get_market_data(contract)` - Returns real-time market data for a contract
- `create_contract(symbol)` - Creates IBKR contract object

### IBKR Market Data Structure:
```python
{
    "last": float,  # Last price
    "bid": float,   # Bid price
    "ask": float,   # Ask price
    "volume": int,  # Volume
    "high": float,  # High
    "low": float,   # Low
}
```

### Connection Requirements:
- TWS (Trader Workstation) or IB Gateway must be running
- API connections must be enabled in TWS/Gateway
- Default: host=127.0.0.1, port=7497 (paper) or 7496 (live)

## Next Steps

1. **Start with Phase 1** - Add connection UI so users can connect
2. **Then Phase 2** - Wire market data to use IBKR
3. **Test each phase** - Verify it works before moving on

