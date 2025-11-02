# WebSocket Real-Time Data Streaming

## Overview

The WebSocket server provides real-time data streaming for:
- **Live Price Updates**: Real-time price streaming for subscribed symbols
- **Trading Signals**: Broadcast trading signals as they're generated
- **Trade Executions**: Real-time trade execution notifications  
- **Portfolio Updates**: Live portfolio position and P&L updates

## Connection

### Endpoint

```
ws://localhost:8000/ws
```

For secure connections:
```
wss://your-domain.com/ws
```

### Client ID (Optional)

You can provide an optional `client_id` query parameter:
```
ws://localhost:8000/ws?client_id=my-client-id
```

If not provided, a UUID will be generated automatically.

## Message Format

### Client → Server

#### Ping
```json
{
  "type": "ping"
}
```

#### Subscribe (Phase 3+)
```json
{
  "type": "subscribe",
  "channel": "price_updates|signals|trades|portfolio",
  "symbols": ["AAPL", "MSFT"]
}
```

#### Unsubscribe (Phase 3+)
```json
{
  "type": "unsubscribe",
  "channel": "price_updates",
  "symbols": ["AAPL"]
}
```

### Server → Client

#### Price Update
```json
{
  "type": "price_update",
  "symbols": {
    "AAPL": {
      "price": 150.25,
      "change": 0.5,
      "change_pct": 0.33,
      "volume": 1000000,
      "high": 151.0,
      "low": 149.5,
      "open": 150.0,
      "close": 150.25
    },
    "MSFT": {
      "price": 380.50,
      "change": -1.2,
      "change_pct": -0.31,
      "volume": 2000000
    }
  },
  "timestamp": "2024-12-19T12:00:00Z"
}
```

#### Trading Signal
```json
{
  "type": "signal",
  "signal_type": "BUY",
  "symbol": "AAPL",
  "price": 150.25,
  "quantity": 10,
  "confidence": 0.85,
  "timestamp": "2024-12-19T12:00:00Z"
}
```

#### Trade Executed
```json
{
  "type": "trade_executed",
  "symbol": "AAPL",
  "side": "BUY",
  "quantity": 10,
  "price": 150.25,
  "timestamp": "2024-12-19T12:00:00Z"
}
```

#### Portfolio Update
```json
{
  "type": "portfolio_update",
  "channel": "portfolio",
  "timestamp": "2024-12-19T12:00:00Z",
  "data": {
    "positions": {
      "AAPL": {
        "symbol": "AAPL",
        "quantity": 10,
        "average_price": 150.25,
        "market_price": 151.50,
        "unrealized_pnl": 12.50,
        "unrealized_pnl_pct": 0.83
      }
    },
    "total_pnl": 12.50,
    "position_count": 1
  }
}
```

#### Pong (Response to Ping)
```json
{
  "type": "pong"
}
```

#### Error
```json
{
  "type": "error",
  "error": "Invalid message format",
  "timestamp": "2024-12-19T12:00:00Z"
}
```

## JavaScript Example

```javascript
class TradingWebSocketClient {
    constructor(url) {
        this.url = url;
        this.ws = null;
        this.reconnectDelay = 5000;
        this.isConnected = false;
    }

    connect() {
        this.ws = new WebSocket(this.url);
        
        this.ws.onopen = () => {
            console.log('WebSocket connected');
            this.isConnected = true;
            this.startPingInterval();
        };
        
        this.ws.onmessage = (event) => {
            const data = JSON.parse(event.data);
            this.handleMessage(data);
        };
        
        this.ws.onclose = () => {
            console.log('WebSocket disconnected');
            this.isConnected = false;
            // Reconnect after delay
            setTimeout(() => this.connect(), this.reconnectDelay);
        };
        
        this.ws.onerror = (error) => {
            console.error('WebSocket error:', error);
        };
    }

    handleMessage(data) {
        switch (data.type) {
            case 'price_update':
                this.onPriceUpdate(data.symbols);
                break;
            case 'signal':
                this.onSignal(data);
                break;
            case 'trade_executed':
                this.onTradeExecuted(data);
                break;
            case 'portfolio_update':
                this.onPortfolioUpdate(data.data);
                break;
            case 'pong':
                console.log('Pong received');
                break;
            case 'error':
                console.error('Server error:', data.error);
                break;
        }
    }

    onPriceUpdate(symbols) {
        for (const [symbol, data] of Object.entries(symbols)) {
            console.log(`${symbol}: $${data.price} (${data.change_pct > 0 ? '+' : ''}${data.change_pct}%)`);
        }
    }

    onSignal(signal) {
        console.log(`Signal: ${signal.signal_type} ${signal.symbol} @ $${signal.price} (confidence: ${signal.confidence})`);
    }

    onTradeExecuted(trade) {
        console.log(`Trade: ${trade.side} ${trade.quantity} ${trade.symbol} @ $${trade.price}`);
    }

    onPortfolioUpdate(data) {
        console.log(`Portfolio: ${data.position_count} positions, P&L: $${data.total_pnl}`);
    }

    ping() {
        if (this.isConnected) {
            this.ws.send(JSON.stringify({ type: 'ping' }));
        }
    }

    startPingInterval() {
        setInterval(() => this.ping(), 30000); // Ping every 30 seconds
    }

    disconnect() {
        if (this.ws) {
            this.ws.close();
        }
    }
}

// Usage
const client = new TradingWebSocketClient('ws://localhost:8000/ws');
client.connect();
```

## Configuration

### Environment Variables

```bash
# Enable/disable WebSocket server
WEBSOCKET_ENABLED=true

# Ping interval (seconds)
WEBSOCKET_PING_INTERVAL=30

# Price update interval (seconds)
WEBSOCKET_PRICE_UPDATE_INTERVAL=3

# Portfolio update interval (seconds)
WEBSOCKET_PORTFOLIO_UPDATE_INTERVAL=5

# Maximum concurrent connections
WEBSOCKET_MAX_CONNECTIONS=100
```

### Status Endpoint

Get WebSocket server status:

```bash
GET /websocket/status
```

Response:
```json
{
  "enabled": true,
  "active_connections": 2,
  "max_connections": 100,
  "ping_interval": 30,
  "price_update_interval": 3,
  "portfolio_update_interval": 5,
  "stream_health": {
    "price_updates": {
      "last_update": "2024-12-19T12:00:00Z",
      "error_count": 0,
      "recovery_attempts": 0,
      "is_healthy": true,
      "started_at": "2024-12-19T11:00:00Z"
    },
    "signals": {
      "last_update": "2024-12-19T12:00:05Z",
      "error_count": 0,
      "is_healthy": true
    }
  }
}
```

## Auto-Subscription (MVP)

For MVP, all clients are automatically subscribed to all streams:
- `price_updates`: All price updates
- `signals`: All trading signals
- `trades`: All trade executions
- `portfolio`: Portfolio updates

Future phases will support selective subscriptions per client.

## Error Handling

- Automatic reconnection with exponential backoff
- Graceful error messages for invalid requests
- Health monitoring for stream reliability
- Automatic cleanup of disconnected clients

## Rate Limiting

Price updates are sent at configured intervals (default: 3 seconds) to respect data provider rate limits.

## Best Practices

1. **Reconnection**: Always implement reconnection logic in your client
2. **Ping/Pong**: Use ping messages to keep connection alive
3. **Error Handling**: Handle all message types including errors
4. **Connection Status**: Monitor connection status and handle disconnections gracefully
5. **Message Validation**: Validate all received messages before processing
