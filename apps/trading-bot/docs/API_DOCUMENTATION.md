# Trading Bot API Documentation

## Overview

The Trading Bot API provides comprehensive endpoints for trading operations, sentiment analysis, options flow, and confluence scoring. This document provides detailed information about all available endpoints, request/response formats, and usage examples.

## Base URL

```
http://localhost:8000
```

## Authentication

### API Key Authentication (Optional)

API key authentication is **disabled by default**. To enable:

1. Set `API_AUTH_ENABLED=true` in your environment
2. Add valid API keys: `API_KEYS=key1,key2,key3` (comma-separated)
3. Include API key in requests: `X-API-Key: your-api-key`

**Example:**
```bash
curl -H "X-API-Key: your-api-key" "http://localhost:8000/api/sentiment/aggregated/AAPL"
```

When authentication is enabled:
- **Without API key**: Request rejected with 401 Unauthorized
- **With invalid API key**: Request rejected with 403 Forbidden
- **With valid API key**: Higher rate limits (1000/hour vs 100/minute for IP)

When authentication is disabled (default):
- All endpoints are publicly accessible
- Rate limiting is IP-based only

## Rate Limiting

Rate limiting is automatically applied to all endpoints:

### Without API Key (IP-based)
- **Default**: 100 requests per minute per IP address
- Configurable via `API_RATE_LIMIT_PER_IP` (format: `N/minute` or `N/hour`)

### With API Key (Key-based)
- **Default**: 1000 requests per hour per API key
- Configurable via `API_RATE_LIMIT_PER_KEY` (format: `N/hour` or `N/day`)

### Rate Limit Headers

All responses include rate limit information in headers:
- `X-RateLimit-Limit`: Maximum requests allowed in the window
- `X-RateLimit-Remaining`: Remaining requests in current window
- `X-RateLimit-Reset`: Unix timestamp when the limit resets

**Example Response Headers:**
```
X-RateLimit-Limit: 1000
X-RateLimit-Remaining: 995
X-RateLimit-Reset: 1703078400
```

**Rate Limit Exceeded Response:**
- **Status Code**: 429 Too Many Requests
- **Response**: `{"detail": "Rate limit exceeded"}`
- **Headers**: Include rate limit info with `Remaining: 0`

## Endpoints

### Trading Operations

#### `GET /api/trading/positions`
Get current positions.

**Response:**
```json
{
  "positions": [
    {
      "symbol": "AAPL",
      "quantity": 100,
      "average_price": 150.50,
      "current_price": 155.00,
      "unrealized_pnl": 450.00
    }
  ]
}
```

#### `POST /api/trading/orders`
Place a new order.

**Request:**
```json
{
  "symbol": "AAPL",
  "quantity": 10,
  "order_type": "market",
  "side": "buy"
}
```

### Sentiment Analysis

#### `GET /api/sentiment/twitter/{symbol}`
Get Twitter/X sentiment for a symbol.

**Parameters:**
- `symbol` (path): Stock symbol (e.g., AAPL, SPY)
- `hours` (query, optional): Hours of data to analyze (1-168, default: 24)

**Response:**
```json
{
  "symbol": "AAPL",
  "timestamp": "2024-12-19T12:00:00Z",
  "mention_count": 1250,
  "average_sentiment": 0.65,
  "weighted_sentiment": 0.72,
  "sentiment_level": "bullish",
  "confidence": 0.85,
  "volume_trend": "up"
}
```

#### `GET /api/sentiment/reddit/{symbol}`
Get Reddit sentiment for a symbol.

**Parameters:**
- `symbol` (path): Stock symbol
- `hours` (query, optional): Hours of data (1-168, default: 24)

#### `GET /api/sentiment/news/{symbol}`
Get financial news sentiment for a symbol.

**Parameters:**
- `symbol` (path): Stock symbol
- `hours` (query, optional): Hours of data (1-168, default: 24)

#### `GET /api/sentiment/aggregated/{symbol}`
Get aggregated sentiment across all sources.

**Parameters:**
- `symbol` (path): Stock symbol
- `hours` (query, optional): Hours of data (1-168, default: 24)

**Response:**
```json
{
  "symbol": "AAPL",
  "timestamp": "2024-12-19T12:00:00Z",
  "unified_sentiment": 0.68,
  "sentiment_level": "bullish",
  "confidence": 0.82,
  "provider_count": 3,
  "providers_used": ["twitter", "reddit", "options"],
  "twitter_sentiment": 0.72,
  "reddit_sentiment": 0.65,
  "options_sentiment": 0.70,
  "divergence_detected": false,
  "divergence_score": 0.15
}
```

#### `GET /api/sentiment/aggregated/{symbol}/detailed`
Get detailed aggregated sentiment with provider breakdown.

**Response:**
Includes the same data as aggregated endpoint plus:
```json
{
  "provider_breakdown": [
    {
      "provider": "twitter",
      "sentiment_score": 0.72,
      "weighted_sentiment": 0.36,
      "confidence": 0.85,
      "mention_count": 1250,
      "weight": 0.5,
      "included": true
    }
  ]
}
```

### Options Flow

#### `GET /api/options-flow/{symbol}`
Get options flow data with pattern detection.

**Parameters:**
- `symbol` (path): Stock symbol
- `hours` (query, optional): Hours of data (1-168, default: 24)
- `include_patterns` (query, optional): Include pattern detection (default: true)

**Response:**
```json
[
  {
    "symbol": "SPY",
    "strike": 450.0,
    "expiry": "2024-12-27T00:00:00Z",
    "option_type": "call",
    "volume": 5000,
    "premium": 250000.00,
    "direction": "buy",
    "unusual": true,
    "is_sweep": true,
    "is_block": false,
    "pattern_type": "sweep",
    "sweep_strength": 0.85,
    "timestamp": "2024-12-19T12:00:00Z"
  }
]
```

#### `GET /api/options-flow/{symbol}/sweeps`
Get detected sweep patterns.

#### `GET /api/options-flow/{symbol}/blocks`
Get detected block trades.

#### `GET /api/options-flow/{symbol}/pc-ratio`
Get put/call ratios.

**Response:**
```json
{
  "volume_ratio": 0.75,
  "premium_ratio": 0.82,
  "oi_ratio": 0.78,
  "timestamp": "2024-12-19T12:00:00Z"
}
```

#### `GET /api/options-flow/{symbol}/metrics`
Get comprehensive flow metrics.

**Response:**
```json
{
  "total_volume": 500000,
  "total_premium": 25000000.00,
  "call_volume": 300000,
  "put_volume": 200000,
  "bullish_flow": 0.65,
  "bearish_flow": 0.35,
  "unusual_count": 45,
  "sweep_count": 12,
  "block_count": 8
}
```

#### `GET /api/options-flow/{symbol}/chain`
Get options chain analysis.

**Response:**
```json
{
  "max_pain": 450.0,
  "gamma_exposure": 12500000,
  "call_dominance": 0.60,
  "put_dominance": 0.40,
  "strike_concentration": {
    "450": 0.25,
    "455": 0.20
  },
  "high_volume_strikes": [
    {"strike": 450.0, "volume": 50000}
  ]
}
```

#### `GET /api/options-flow/{symbol}/sentiment`
Get options flow-based sentiment.

### Confluence

#### `GET /api/confluence/{symbol}`
Get confluence score for a symbol.

**Parameters:**
- `symbol` (path): Stock symbol
- `sentiment_hours` (query, optional): Hours of sentiment data (default: 24)
- `use_sentiment` (query, optional): Include sentiment (default: true)
- `use_options_flow` (query, optional): Include options flow (default: true)

**Response:**
```json
{
  "symbol": "AAPL",
  "timestamp": "2024-12-19T12:00:00Z",
  "confluence_score": 0.78,
  "directional_bias": 0.65,
  "confluence_level": "high",
  "confidence": 0.82,
  "meets_minimum_threshold": true,
  "meets_high_threshold": false,
  "breakdown": {
    "technical_score": {
      "overall_score": 0.70,
      "rsi_score": 0.65,
      "sma_trend_score": 0.75,
      "volume_score": 0.60,
      "bollinger_score": 0.70
    },
    "sentiment_score": {
      "score": 0.68,
      "confidence": 0.85,
      "source_count": 3
    },
    "options_flow_score": {
      "score": 0.72,
      "confidence": 0.80
    },
    "technical_contribution": 0.35,
    "sentiment_contribution": 0.20,
    "options_flow_contribution": 0.13
  }
}
```

#### `GET /api/confluence/status`
Get confluence calculator status.

### Market Data

#### `GET /api/market-data/quote/{symbol}`
Get real-time quote.

#### `GET /api/market-data/historical/{symbol}`
Get historical price data.

**Parameters:**
- `symbol` (path): Stock symbol
- `days` (query): Number of days (1-365, default: 30)
- `interval` (query): Data interval (1d, 1h, 5m, default: 1d)

### Strategies

#### `GET /api/strategies`
List available strategies.

#### `POST /api/strategies`
Add a new strategy.

#### `POST /api/strategies/evaluate`
Evaluate strategies for symbols.

**Request:**
```json
{
  "symbols": ["AAPL", "MSFT"],
  "strategy_names": ["sma_crossover"],
  "fetch_data": true
}
```

### Monitoring

#### `GET /health`
System health check.

**Response:**
```json
{
  "status": "healthy",
  "version": "2.0.0",
  "environment": "development",
  "timestamp": "2024-12-19T12:00:00Z"
}
```

#### `GET /metrics`
Exposes application metrics in Prometheus exposition format.

**Response:**
- **Content-Type**: `text/plain; version=0.0.4; charset=utf-8`
- **Format**: Prometheus metrics text format

**Example Response:**
```
# HELP http_requests_total Total HTTP requests
# TYPE http_requests_total counter
http_requests_total{method="GET",endpoint="/api/health",status_code="200"} 1523

# HELP system_cpu_usage_percent CPU usage percentage
# TYPE system_cpu_usage_percent gauge
system_cpu_usage_percent 45.2
```

**Configuration:**
- Enable/disable via `METRICS_ENABLED` environment variable (default: `true`)
- When disabled, returns empty response

**Usage:**
- Intended for Prometheus scraping
- Accessible without authentication
- See `docs/METRICS_REFERENCE.md` for complete metrics catalog

## Error Responses

All errors follow this format:

```json
{
  "error": {
    "code": 404,
    "message": "Symbol not found",
    "timestamp": "2024-12-19T12:00:00Z"
  }
}
```

## Status Codes

- `200`: Success
- `400`: Bad Request (invalid parameters)
- `404`: Not Found (resource doesn't exist)
- `429`: Too Many Requests (rate limit exceeded)
- `500`: Internal Server Error
- `503`: Service Unavailable (provider not available)

## Examples

### Python Example

```python
import requests

BASE_URL = "http://localhost:8000"

# Get aggregated sentiment
response = requests.get(f"{BASE_URL}/api/sentiment/aggregated/AAPL")
sentiment = response.json()

# Get options flow
response = requests.get(f"{BASE_URL}/api/options-flow/SPY", params={"hours": 48})
flows = response.json()

# Get confluence score
response = requests.get(f"{BASE_URL}/api/confluence/AAPL")
confluence = response.json()
```

### cURL Examples

```bash
# Get Twitter sentiment
curl "http://localhost:8000/api/sentiment/twitter/AAPL?hours=24"

# Get options flow sweeps
curl "http://localhost:8000/api/options-flow/SPY/sweeps?hours=24"

# Get confluence score
curl "http://localhost:8000/api/confluence/AAPL"
```

## Interactive Documentation

When running in debug mode, interactive API documentation is available at:
- **Swagger UI**: `/docs`
- **ReDoc**: `/redoc`

## Support

For issues or questions, please refer to the main project documentation or open an issue in the repository.

