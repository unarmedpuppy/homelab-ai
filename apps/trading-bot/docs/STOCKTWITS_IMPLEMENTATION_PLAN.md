# StockTwits Sentiment Integration - Implementation Plan

## Overview

Integrate StockTwits API for sentiment analysis. StockTwits is a social network for traders and investors, providing real-time stock discussions with built-in sentiment indicators (bullish/bearish).

## API Research

**StockTwits API**: RESTful API v2
- **Base URL**: `https://api.stocktwits.com/api/2`
- **Authentication**: Token-based (optional for public data, required for user-specific data)
- **Rate Limits**: ~200 requests/hour for unauthenticated, higher for authenticated
- **Documentation**: https://stocktwits.com/developers/docs

**Key Endpoints**:
- `GET /streams/symbol/{symbol}.json` - Get messages for a symbol
- `GET /streams/trending.json` - Get trending symbols
- `GET /streams/user/{user_id}.json` - Get user messages
- `GET /symbols/search.json?q={query}` - Search symbols
- `GET /messages/show/{id}.json` - Get specific message

**Built-in Sentiment**:
- StockTwits messages include built-in sentiment: `bullish`, `bearish`, or `null`
- Users can mark messages as bullish/bearish
- No need for external sentiment analysis (though we can enhance with VADER)

## Implementation Phases

### Phase 1: Foundation (2-3 hours)
**Goal**: Create basic StockTwits provider infrastructure

**Steps**:
1. ✅ Add dependencies (use `requests` library, no special package needed)
2. ✅ Create `StockTwitsSettings` in `src/config/settings.py`
3. ✅ Create `src/data/providers/sentiment/stocktwits.py`
   - `StockTwitsClient` class for API interaction
   - `StockTwitsSentimentProvider` class
   - Basic message fetching
4. ✅ Add configuration to `env.template` and `docker-compose.yml`

**Deliverables**:
- StockTwits client can fetch messages for symbols
- Can parse built-in sentiment indicators
- Basic provider working

---

### Phase 2: Database Integration (1-2 hours)
**Goal**: Store StockTwits messages and sentiment in database

**Steps**:
1. ✅ Reuse existing `Tweet`/`TweetSentiment` models (prefix with `stocktwits_`)
2. ✅ Update repository if needed for StockTwits-specific queries
3. ✅ Integrate persistence in `StockTwitsSentimentProvider`

**Deliverables**:
- Messages stored in database
- Sentiment persisted
- Historical queries working

---

### Phase 3: API Integration (1-2 hours)
**Goal**: Expose StockTwits sentiment via API

**Steps**:
1. ✅ Add endpoints to `src/api/routes/sentiment.py`
   - `GET /api/sentiment/stocktwits/{symbol}` - Get sentiment
   - `GET /api/sentiment/stocktwits/{symbol}/mentions` - Get recent messages
   - `GET /api/sentiment/stocktwits/{symbol}/trend` - Get sentiment trend
   - `GET /api/sentiment/stocktwits/trending` - Get trending symbols
   - `GET /api/sentiment/stocktwits/status` - Provider status

2. ✅ Integrate with aggregator
   - Update `SentimentAggregator` to include StockTwits provider

**Deliverables**:
- All API endpoints working
- StockTwits integrated into sentiment aggregator
- API documentation updated

---

### Phase 4: Testing & Integration (1-2 hours)
**Goal**: Comprehensive testing and validation

**Steps**:
1. ✅ Create `scripts/test_stocktwits_sentiment.py`
   - Test message fetching
   - Test sentiment parsing
   - Test database persistence
   - Test API endpoints

2. ✅ Integration testing
   - Test with aggregator
   - Test error handling
   - Test rate limiting

3. ✅ Update documentation
   - Update checklist
   - Update TODOS

**Deliverables**:
- Comprehensive test script
- All tests passing
- Documentation complete

---

## Technical Details

### API Authentication

StockTwits API uses token-based authentication:
- Get token from: https://stocktwits.com/developers/apps
- Token passed via `Authorization: Bearer {token}` header
- Optional for public data, but provides higher rate limits

### Message Structure

```python
{
    "id": 123456,
    "body": "AAPL looking strong!",
    "created_at": "2024-12-19T10:30:00Z",
    "user": {
        "id": 789,
        "username": "trader123"
    },
    "symbol": {
        "symbol": "AAPL",
        "id": 123
    },
    "sentiment": {
        "basic": "Bullish"  # or "Bearish" or None
    }
}
```

### Sentiment Scoring

1. **Built-in Sentiment** (Primary):
   - `Bullish` = +1.0
   - `Bearish` = -1.0
   - `null` = 0.0 (neutral)

2. **Enhanced Sentiment** (Optional):
   - Use VADER to analyze message body for additional context
   - Combine built-in + VADER for more nuanced scores

3. **Engagement Weighting**:
   - Likes (respects) count
   - Followers of user
   - Verification status

### Rate Limiting

- Public API: ~200 requests/hour
- Authenticated: ~1000 requests/hour
- Implement rate limiting with exponential backoff
- Cache results (5-minute TTL recommended)

---

## Configuration

### Environment Variables

```bash
# StockTwits API Configuration
STOCKTWITS_API_TOKEN=  # Optional, for authenticated requests
STOCKTWITS_RATE_LIMIT_ENABLED=true
STOCKTWITS_CACHE_TTL=300
STOCKTWITS_MAX_RESULTS=30  # Max messages per request (API limit: 30)
STOCKTWITS_ENABLE_VADER=false  # Optional: enhance with VADER sentiment
```

### Settings Class

```python
class StockTwitsSettings(BaseSettings):
    api_token: Optional[str] = None
    rate_limit_enabled: bool = True
    cache_ttl: int = 300
    max_results: int = 30
    enable_vader: bool = False  # Optional VADER enhancement
```

---

## Implementation Order

1. **Phase 1** (Foundation)
   - Dependencies (requests already available)
   - Settings
   - Basic StockTwitsClient
   - StockTwitsSentimentProvider skeleton
   - Basic message fetching

2. **Phase 2** (Database)
   - Persistence integration
   - Store messages and sentiment

3. **Phase 3** (API)
   - API endpoints
   - Aggregator integration

4. **Phase 4** (Testing)
   - Test script
   - Integration tests
   - Documentation

---

## Success Criteria

- ✅ Can fetch messages from StockTwits API
- ✅ Can parse built-in sentiment indicators
- ✅ Can calculate sentiment scores per symbol
- ✅ Stores messages and sentiment in database
- ✅ Exposes sentiment via API
- ✅ Integrates with sentiment aggregator
- ✅ Test script passes
- ✅ All code follows existing patterns

---

## Estimated Time

- Phase 1: 2-3 hours
- Phase 2: 1-2 hours
- Phase 3: 1-2 hours
- Phase 4: 1-2 hours
- **Total: 5-9 hours**

---

## Dependencies & Considerations

**Dependencies**:
- `requests` (already in requirements)
- Internet connectivity for API calls
- Optional: StockTwits API token for higher rate limits

**Considerations**:
- StockTwits has rate limits (200 req/hour public, 1000 req/hour authenticated)
- Messages have built-in sentiment (no need for external analysis, but VADER optional)
- API returns max 30 messages per request
- Need to handle pagination for historical data
- Some messages may not have sentiment assigned

---

**Status**: Planning Complete ✅  
**Started**: 2024-12-19  
**Next**: Begin Phase 1 implementation

