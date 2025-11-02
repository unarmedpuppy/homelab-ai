# Twitter/X Sentiment Integration - Strategy & Implementation Plan

## Executive Summary

Integrate Twitter/X as a sentiment data source to provide market sentiment signals for trading strategies. This will track stock mentions, analyze sentiment, monitor influential traders, and aggregate sentiment scores that can be used as confluence for trade decisions.

## Strategy Overview

### Goals
1. **Track Symbol Mentions**: Monitor Twitter/X for mentions of trading symbols (e.g., $SPY, $AAPL)
2. **Sentiment Analysis**: Determine if mentions are bullish, bearish, or neutral
3. **Influencer Tracking**: Monitor influential traders/analysts for their opinions
4. **Real-time Monitoring**: Track mentions in near real-time (within rate limits)
5. **Historical Analysis**: Store and analyze sentiment trends over time
6. **Integration**: Provide sentiment scores that integrate with trading strategies

### Twitter API Strategy

**API Version**: Twitter API v2 (modern, more reliable)

**Access Tier Options**:
1. **Free Tier**: 10,000 tweets/month, 1,500 tweets/day
   - Good for: Low-volume testing, single symbol monitoring
   - Limitations: Rate limits, restricted features

2. **Basic Tier ($100/month)**: 10,000 tweets/month, 3,000 tweets/day
   - Good for: Moderate usage, multiple symbols
   
3. **Pro Tier ($5,000/month)**: 1M tweets/month, 50,000 tweets/day
   - Good for: Production, high-volume monitoring

**Recommended**: Start with Free/Basic tier, upgrade as needed.

### Data Collection Strategy

#### 1. Symbol Mention Tracking
- **Query Method**: Search recent tweets mentioning `$SYMBOL` or `#SYMBOL`
- **Search Query**: `"$SPY" OR "#SPY" OR "SPY stock" -is:retweet lang:en`
- **Volume Tracking**: Count mentions per time window (1h, 4h, 24h)
- **Engagement Metrics**: Track likes, retweets, replies for signal strength

#### 2. Influencer Monitoring
- **Approach**: Follow specific influential accounts
- **List Management**: Maintain list of trader/analyst accounts
- **Signal Weighting**: Weight influencer tweets higher in sentiment calculation
- **Account Types**:
  - Finance influencers (verified accounts)
  - Trading education accounts
  - Stock analysts
  - Financial news accounts

#### 3. Sentiment Analysis
- **Method**: VADER Sentiment Analysis (pre-trained, fast, works well for social media)
- **Alternative**: TextBlob (simpler, less accurate) or Transformers (more accurate, slower)
- **Scoring**: Convert to -1 (bearish) to +1 (bullish) scale
- **Context Awareness**: Consider financial terms, emojis, sarcasm indicators

#### 4. Data Storage
- **Raw Tweets**: Store tweet text, metadata, engagement metrics
- **Aggregated Scores**: Store hourly/daily sentiment scores per symbol
- **Trends**: Track sentiment changes over time

### Architecture Design

```
┌──────────────────┐
│  Twitter API v2  │
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│ TwitterClient    │  ← API wrapper with rate limiting
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│ SentimentAnalyzer│  ← VADER sentiment analysis
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│ TwitterSentiment │  ← Business logic, aggregation
│ Provider         │
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│   Database       │  ← Store tweets & sentiment scores
└──────────────────┘
         │
         ▼
┌──────────────────┐
│ Sentiment        │  ← Integration with aggregator
│ Aggregator       │
└──────────────────┘
```

### Rate Limiting Strategy

**Twitter API v2 Rate Limits** (Free/Basic tier):
- **Recent Search**: 300 requests per 15 minutes (per app)
- **User Lookup**: 300 requests per 15 minutes
- **Tweet Lookup**: 300 requests per 15 minutes

**Our Strategy**:
- Implement request queuing
- Distribute requests over time windows
- Cache results aggressively (5-15 minutes)
- Prioritize symbols by trading activity
- Batch requests when possible

**Implementation**:
```python
# Rate limiter decorator
@rate_limit(max_calls=300, period=900)  # 300 per 15 min
async def search_tweets(query, ...):
    ...
```

### Sentiment Analysis Strategy

#### VADER (Valence Aware Dictionary and sEntiment Reasoner)
- **Pros**: Fast, works well with social media, handles emojis/slang
- **Cons**: Less context-aware, financial domain not specialized
- **Score Range**: -1 (most negative) to +1 (most positive)
- **Compound Score**: Weighted composite score

#### Scoring Methodology
```python
# Raw VADER scores
vader_scores = {
    'neg': 0.0,    # Negative
    'neu': 0.0,    # Neutral
    'pos': 0.0,    # Positive
    'compound': 0.0  # -1 to +1
}

# Weighted sentiment score
sentiment_score = (
    vader_scores['compound'] * 0.6 +  # Base sentiment
    engagement_weight * 0.2 +           # Likes/RTs boost
    influencer_weight * 0.2             # Influencer boost
)
```

#### Engagement Weighting
- **High Engagement** (1000+ likes/RTs): 1.5x weight
- **Medium Engagement** (100-1000): 1.0x weight
- **Low Engagement** (<100): 0.5x weight

#### Influencer Weighting
- **Verified Account**: 2.0x weight
- **High Follower Count** (>100K): 1.5x weight
- **In Trading List**: 1.8x weight
- **Regular Account**: 1.0x weight

## Implementation Plan

### Phase 1: Foundation (2-3 hours)

#### 1.1 Install Dependencies
```bash
pip install tweepy vaderSentiment python-dotenv
```

**Libraries**:
- `tweepy`: Twitter API v2 wrapper
- `vaderSentiment`: Sentiment analysis
- `python-dotenv`: Environment variable management (already installed)

#### 1.2 Create Project Structure
```
src/data/providers/sentiment/
├── __init__.py
├── twitter.py              # Main Twitter client
├── sentiment_analyzer.py   # VADER wrapper
└── models.py               # Data models
```

#### 1.3 Configuration Setup
Add to `env.template`:
```env
# Twitter/X API Configuration
TWITTER_API_KEY=your_api_key
TWITTER_API_SECRET=your_api_secret
TWITTER_BEARER_TOKEN=your_bearer_token
TWITTER_ACCESS_TOKEN=your_access_token
TWITTER_ACCESS_TOKEN_SECRET=your_access_token_secret

# Twitter Settings
TWITTER_RATE_LIMIT_ENABLED=true
TWITTER_CACHE_TTL=300  # 5 minutes
TWITTER_MAX_RESULTS=100  # Max tweets per search
TWITTER_SEARCH_LANGUAGE=en
```

### Phase 2: Core Implementation (4-5 hours)

#### 2.1 Twitter Client (`twitter.py`)

**Key Components**:
1. **TwitterClient Class**:
   - Authentication handling
   - Rate limiting
   - Request queuing
   - Error handling/retries

2. **Methods**:
   - `search_tweets(query, max_results=100)` - Search for tweets
   - `get_user_tweets(user_id, max_results=100)` - Get tweets from user
   - `get_trending_symbols()` - Detect trending stock symbols
   - `monitor_symbol(symbol, hours=24)` - Monitor symbol mentions

#### 2.2 Sentiment Analyzer (`sentiment_analyzer.py`)

**Key Components**:
1. **SentimentAnalyzer Class**:
   - VADER initialization
   - Tweet preprocessing
   - Sentiment scoring
   - Engagement weighting
   - Influencer weighting

2. **Methods**:
   - `analyze_tweet(tweet)` - Analyze single tweet
   - `analyze_batch(tweets)` - Analyze multiple tweets
   - `calculate_weighted_score(tweet, sentiment_score)` - Apply weights

#### 2.3 Twitter Sentiment Provider (`twitter.py` - Provider class)

**Key Components**:
1. **TwitterSentimentProvider Class**:
   - High-level interface
   - Symbol monitoring
   - Aggregation logic
   - Caching
   - Database integration

2. **Methods**:
   - `get_sentiment(symbol, hours=24)` - Get sentiment for symbol
   - `get_mention_count(symbol, hours=24)` - Get mention count
   - `get_influencer_sentiment(symbol, hours=24)` - Influencer-specific sentiment
   - `track_symbol(symbol)` - Start tracking symbol
   - `get_trending_symbols()` - Get trending symbols

### Phase 3: Data Models & Database (2-3 hours)

#### 3.1 Database Models (`models.py`)

**Tables to Create**:
1. **twitter_tweets**:
   - tweet_id (unique)
   - symbol (indexed)
   - text
   - author_id
   - author_username
   - created_at
   - like_count
   - retweet_count
   - reply_count
   - sentiment_score
   - is_influencer
   - raw_data (JSON)

2. **twitter_sentiment_scores**:
   - id
   - symbol (indexed)
   - timestamp (indexed)
   - mention_count
   - average_sentiment
   - weighted_sentiment
   - influencer_sentiment
   - engagement_score
   - volume_trend (up/down/stable)

3. **twitter_influencers**:
   - user_id (unique)
   - username
   - display_name
   - follower_count
   - is_verified
   - category (trader, analyst, news, etc.)
   - weight_multiplier

#### 3.2 SQLAlchemy Models
- Follow pattern from existing `models.py`
- Add relationships
- Add indexes for performance
- Add data retention policies

### Phase 4: API Integration (2-3 hours)

#### 4.1 API Endpoints

**Routes to Create** (`src/api/routes/sentiment.py`):
1. `GET /api/sentiment/twitter/{symbol}` - Get current sentiment
2. `GET /api/sentiment/twitter/{symbol}/mentions` - Get recent mentions
3. `GET /api/sentiment/twitter/{symbol}/trend` - Get sentiment trend
4. `GET /api/sentiment/twitter/influencers` - List tracked influencers
5. `POST /api/sentiment/twitter/influencers` - Add influencer
6. `GET /api/sentiment/twitter/trending` - Get trending symbols
7. `GET /api/sentiment/twitter/{symbol}/history` - Historical sentiment

### Phase 5: Testing & Validation (2-3 hours)

#### 5.1 Unit Tests
- Test Twitter client authentication
- Test rate limiting
- Test sentiment analysis accuracy
- Test aggregation logic
- Test error handling

#### 5.2 Integration Tests
- Test full flow: API → Analysis → Database
- Test caching behavior
- Test concurrent requests
- Test rate limit handling

#### 5.3 Validation Tests
- Validate sentiment scores are reasonable (-1 to +1)
- Validate mention counts are accurate
- Validate trending detection works
- Test with real symbols (SPY, AAPL, etc.)

### Phase 6: Documentation & Deployment (1-2 hours)

#### 6.1 Documentation
- API documentation
- Configuration guide
- Usage examples
- Troubleshooting guide

#### 6.2 Deployment Checklist
- Environment variables set
- API keys configured
- Database migrations run
- Rate limits configured
- Monitoring set up

## Data Flow

### Real-time Monitoring Flow
```
1. Schedule/Trigger → Search for symbol mentions
2. Fetch tweets from Twitter API
3. Analyze sentiment for each tweet
4. Weight by engagement/influencer status
5. Aggregate scores
6. Store in database
7. Update sentiment cache
8. Return aggregated sentiment score
```

### Historical Analysis Flow
```
1. Query database for historical tweets
2. Aggregate by time window (hourly/daily)
3. Calculate trends
4. Generate insights
5. Return time series data
```

## Configuration

### Default Configuration
```python
TWITTER_CONFIG = {
    'rate_limit': {
        'enabled': True,
        'requests_per_window': 300,
        'window_seconds': 900,  # 15 minutes
    },
    'cache': {
        'ttl': 300,  # 5 minutes
        'enabled': True,
    },
    'search': {
        'max_results': 100,
        'language': 'en',
        'exclude_retweets': True,
    },
    'sentiment': {
        'analyzer': 'vader',
        'engagement_weight': 0.2,
        'influencer_weight': 0.2,
        'min_engagement': 10,  # Min likes+RTs to consider
    },
    'influencers': {
        'min_followers': 10000,
        'verified_bonus': 2.0,
        'weight_multiplier': 1.5,
    }
}
```

## Error Handling Strategy

### API Errors
- **429 (Rate Limit)**: Queue request, retry after delay
- **401 (Unauthorized)**: Log error, alert admin
- **500 (Server Error)**: Exponential backoff retry
- **Network Errors**: Retry with exponential backoff

### Data Quality
- **No Results**: Return neutral sentiment (0.0)
- **Low Volume**: Flag as low confidence
- **Spam Detection**: Filter out suspected spam

## Performance Considerations

### Caching Strategy
- **Sentiment Scores**: Cache for 5 minutes
- **Trending Symbols**: Cache for 15 minutes
- **Influencer Lists**: Cache for 1 hour
- **Historical Data**: No cache (query database)

### Query Optimization
- Index database tables properly
- Batch database inserts
- Use async/await for API calls
- Implement connection pooling

## Monitoring & Alerts

### Metrics to Track
- API request rate
- Rate limit hits
- Sentiment score distribution
- Mention volume per symbol
- Error rates
- Cache hit rates

### Alerts
- Rate limit approaching
- API authentication failures
- Unusual sentiment spikes
- Database connection issues

## Success Criteria

✅ **Functional**:
- Successfully authenticate with Twitter API
- Fetch tweets mentioning symbols
- Calculate accurate sentiment scores
- Store data in database
- Provide sentiment via API endpoints

✅ **Performance**:
- Handle 100+ symbol queries/day
- Response time < 2 seconds (cached)
- < 5% error rate
- Respect rate limits

✅ **Integration**:
- Works with sentiment aggregator
- Can be used in strategy evaluation
- Provides meaningful sentiment scores

## Estimated Timeline

- **Phase 1 (Foundation)**: 2-3 hours
- **Phase 2 (Core Implementation)**: 4-5 hours
- **Phase 3 (Database)**: 2-3 hours
- **Phase 4 (API)**: 2-3 hours
- **Phase 5 (Testing)**: 2-3 hours
- **Phase 6 (Documentation)**: 1-2 hours

**Total**: 13-19 hours (2-3 days)

## Risks & Mitigations

### Risk 1: Rate Limits
- **Mitigation**: Aggressive caching, request queuing, prioritize important symbols

### Risk 2: API Costs
- **Mitigation**: Start with free tier, monitor usage, optimize queries

### Risk 3: Sentiment Accuracy
- **Mitigation**: Validate against known events, use multiple analyzers if needed

### Risk 4: Spam/Noise
- **Mitigation**: Filter low-engagement tweets, focus on verified accounts

## Next Steps After Implementation

1. Integrate with Sentiment Aggregator
2. Add to strategy confluence calculation
3. Monitor performance and accuracy
4. Expand to more symbols
5. Add more sophisticated filtering
6. Implement real-time streaming (if upgrading API tier)

---

**Ready to implement?** Let's start with Phase 1!

