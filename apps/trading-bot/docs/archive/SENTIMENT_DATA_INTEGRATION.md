# Market Sentiment & Data Aggregation Integration Plan

## Overview

Integration plan for market sentiment and data aggregation sources to provide confluence for trading decisions. This will enhance strategy signals by incorporating social media sentiment, news sentiment, options flow, and alternative data sources.

## Integration Architecture

### Sentiment Confluence System

The sentiment system will:
1. Aggregate data from multiple sources
2. Calculate sentiment scores for each source
3. Combine into a unified confluence score
4. Integrate with strategy evaluation for signal filtering/enhancement

```
┌─────────────────┐
│  Data Sources   │
│  (12 Libraries) │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Sentiment       │
│ Aggregator      │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Confluence      │
│ Calculator      │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Strategy        │
│ Signal Filter   │
└─────────────────┘
```

## 📋 Master Checklist

**For the most up-to-date status and task tracking, see**: [SENTIMENT_INTEGRATION_CHECKLIST.md](./SENTIMENT_INTEGRATION_CHECKLIST.md)

This document provides detailed implementation information. The checklist document is the source of truth for status tracking.

## Integration TODO List

### Category 1: Social Media Sentiment

#### ✅ 1. Twitter/X API Integration
**Status**: 🔄 In Progress (Phase 1 Complete, Phase 2-4 Pending)  
**Library**: `tweepy` or `python-twitter`  
**Purpose**: Monitor Twitter/X for stock mentions, sentiment, and influential trader commentary  
**Tasks**:
- [ ] Install and configure Twitter/X API client
- [ ] Create `TwitterSentimentProvider` class
- [ ] Implement symbol mention tracking
- [ ] Implement sentiment analysis (positive/negative/neutral)
- [ ] Track influential accounts (traders, analysts)
- [ ] Implement rate limiting and error handling
- [ ] Add caching to reduce API calls
- [ ] Integrate with sentiment aggregator
- [ ] Add configuration for API keys and settings
- [ ] Create API endpoints for Twitter sentiment data

**API Endpoints**:
- `GET /api/sentiment/twitter/{symbol}` - Get Twitter sentiment for symbol
- `GET /api/sentiment/twitter/{symbol}/mentions` - Get recent mentions
- `GET /api/sentiment/twitter/influencers` - Track influential accounts

---

#### ✅ 2. Reddit Sentiment Integration
**Status**: Pending  
**Library**: `praw` (Python Reddit API Wrapper)  
**Purpose**: Monitor subreddits (r/wallstreetbets, r/stocks, r/investing) for sentiment  
**Tasks**:
- [ ] Install and configure PRAW
- [ ] Create `RedditSentimentProvider` class
- [ ] Implement subreddit monitoring (WSB, stocks, investing, etc.)
- [ ] Track post/comment mentions of symbols
- [ ] Implement upvote/downvote weighted sentiment
- [ ] Detect trending tickers
- [ ] Implement sentiment scoring based on post type and engagement
- [ ] Add filtering for spam/low-quality posts
- [ ] Integrate with sentiment aggregator
- [ ] Create API endpoints for Reddit sentiment

**API Endpoints**:
- `GET /api/sentiment/reddit/{symbol}` - Get Reddit sentiment
- `GET /api/sentiment/reddit/trending` - Get trending tickers
- `GET /api/sentiment/reddit/posts/{symbol}` - Get recent posts

---

#### ✅ 3. StockTwits Integration
**Status**: Pending  
**Library**: `stocktwits-python` or direct API  
**Purpose**: Financial social media platform focused on stock discussions  
**Tasks**:
- [ ] Install StockTwits API client
- [ ] Create `StockTwitsProvider` class
- [ ] Implement symbol stream monitoring
- [ ] Track bullish/bearish sentiment indicators
- [ ] Monitor trending symbols
- [ ] Implement sentiment scoring from messages
- [ ] Add real-time stream support
- [ ] Integrate with sentiment aggregator
- [ ] Create API endpoints

**API Endpoints**:
- `GET /api/sentiment/stocktwits/{symbol}` - Get StockTwits sentiment
- `GET /api/sentiment/stocktwits/stream` - Real-time stream

---

### Category 2: News & Financial Media

#### ✅ 4. Financial News Aggregation
**Status**: Pending  
**Library**: `feedparser` + `newspaper3k` or `newsapi-python`  
**Purpose**: Aggregate and analyze financial news from multiple sources  
**Tasks**:
- [ ] Install news aggregation libraries
- [ ] Create `NewsSentimentProvider` class
- [ ] Implement news source aggregation (Bloomberg, Reuters, CNBC, etc.)
- [ ] Implement article scraping and parsing
- [ ] Implement headline sentiment analysis
- [ ] Track news volume per symbol
- [ ] Detect breaking news events
- [ ] Implement article relevance scoring
- [ ] Add news categorization (earnings, M&A, analyst ratings, etc.)
- [ ] Integrate with sentiment aggregator
- [ ] Create API endpoints

**API Endpoints**:
- `GET /api/sentiment/news/{symbol}` - Get news sentiment
- `GET /api/sentiment/news/{symbol}/articles` - Get recent articles
- `GET /api/sentiment/news/breaking` - Get breaking news

---

#### ✅ 5. SEC Filings & Corporate Data
**Status**: Pending  
**Library**: `sec-edgar-downloader` or `python-sec-edgar`  
**Purpose**: Monitor SEC filings (10-K, 10-Q, 8-K, insider trading)  
**Tasks**:
- [ ] Install SEC EDGAR libraries
- [ ] Create `SECFilingsProvider` class
- [ ] Implement filing monitoring (10-K, 10-Q, 8-K, 13F)
- [ ] Track insider trading filings (Form 4)
- [ ] Implement filing sentiment analysis
- [ ] Detect unusual filing activity
- [ ] Parse key financial metrics from filings
- [ ] Add filing alerts system
- [ ] Integrate with sentiment aggregator
- [ ] Create API endpoints

**API Endpoints**:
- `GET /api/data/sec/{symbol}/filings` - Get recent filings
- `GET /api/data/sec/{symbol}/insiders` - Get insider trading
- `GET /api/data/sec/alerts` - Get filing alerts

---

#### ✅ 6. Earnings & Event Calendar
**Status**: Pending  
**Library**: `yfinance` or custom APIs  
**Purpose**: Track earnings announcements, economic events, Fed meetings  
**Tasks**:
- [ ] Create `EventCalendarProvider` class
- [ ] Implement earnings calendar tracking
- [ ] Track economic event calendar (CPI, Fed meetings, etc.)
- [ ] Implement event impact scoring
- [ ] Add event reminders/alerts
- [ ] Integrate historical earnings impact analysis
- [ ] Create API endpoints

**API Endpoints**:
- `GET /api/data/calendar/earnings` - Get earnings calendar
- `GET /api/data/calendar/economic` - Get economic events
- `GET /api/data/calendar/{symbol}/events` - Get events for symbol

---

### Category 3: Options & Flow Data

#### ✅ 7. Options Flow Analysis
**Status**: Partial (Unusual Whales exists)  
**Library**: Enhance existing Unusual Whales integration + `openbb-terminal` or `yfinance`  
**Purpose**: Deep options flow analysis and unusual activity detection  
**Tasks**:
- [ ] Enhance existing Unusual Whales integration
- [ ] Add additional options data sources
- [ ] Implement options flow pattern recognition
- [ ] Track unusual options activity (sweeps, blocks)
- [ ] Calculate put/call ratios
- [ ] Implement options-based sentiment scoring
- [ ] Add options chain analysis
- [ ] Integrate with sentiment aggregator

---

#### ✅ 8. Dark Pool & Institutional Flow
**Status**: Pending  
**Library**: Custom APIs or data providers (FlowAlgo, Cheddar Flow)  
**Purpose**: Track institutional and dark pool trading activity  
**Tasks**:
- [ ] Research dark pool data providers
- [ ] Create `DarkPoolProvider` class
- [ ] Implement dark pool volume tracking
- [ ] Track large block trades
- [ ] Monitor institutional flow patterns
- [ ] Implement flow-based sentiment scoring
- [ ] Integrate with sentiment aggregator
- [ ] Create API endpoints

---

### Category 4: Alternative Data Sources

#### ✅ 9. Google Trends & Search Volume
**Status**: Pending  
**Library**: `pytrends`  
**Purpose**: Track search interest and trending topics  
**Tasks**:
- [ ] Install pytrends library
- [ ] Create `GoogleTrendsProvider` class
- [ ] Implement symbol search volume tracking
- [ ] Track related search terms
- [ ] Implement trend momentum scoring
- [ ] Add regional interest data
- [ ] Integrate with sentiment aggregator
- [ ] Create API endpoints

**API Endpoints**:
- `GET /api/data/trends/{symbol}` - Get Google Trends data
- `GET /api/data/trends/related/{symbol}` - Get related searches

---

#### ✅ 10. Social Media Mentions Volume
**Status**: Pending  
**Library**: Aggregate from Twitter, Reddit, StockTwits  
**Purpose**: Track overall mention volume across platforms  
**Tasks**:
- [ ] Create `MentionVolumeProvider` class
- [ ] Aggregate mentions from all social platforms
- [ ] Implement volume trend analysis
- [ ] Detect mention spikes
- [ ] Calculate mention momentum
- [ ] Integrate with sentiment aggregator
- [ ] Create API endpoints

---

#### ✅ 11. Analyst Ratings & Price Targets
**Status**: Pending  
**Library**: `yfinance` or `finviz`  
**Purpose**: Track analyst ratings, upgrades/downgrades, price targets  
**Tasks**:
- [ ] Create `AnalystRatingsProvider` class
- [ ] Implement analyst rating tracking
- [ ] Track rating changes (upgrades/downgrades)
- [ ] Monitor price target changes
- [ ] Calculate consensus ratings
- [ ] Implement rating-based sentiment scoring
- [ ] Integrate with sentiment aggregator
- [ ] Create API endpoints

**API Endpoints**:
- `GET /api/data/analyst/{symbol}/ratings` - Get analyst ratings
- `GET /api/data/analyst/{symbol}/targets` - Get price targets
- `GET /api/data/analyst/changes` - Get recent changes

---

#### ✅ 12. Insider Trading & Institutional Holdings
**Status**: Partial (SEC integration covers some)  
**Library**: `yfinance` or custom SEC parsing  
**Purpose**: Track insider trading and 13F institutional holdings  
**Tasks**:
- [ ] Enhance SEC filings integration
- [ ] Create `InsiderTradingProvider` class
- [ ] Implement Form 4 parsing (insider trades)
- [ ] Track 13F filings (institutional holdings)
- [ ] Implement insider trading sentiment scoring
- [ ] Detect unusual insider activity
- [ ] Monitor institutional position changes
- [ ] Integrate with sentiment aggregator
- [ ] Create API endpoints

---

### Category 5: Core Integration Components

#### ✅ 13. Sentiment Aggregator System
**Status**: Pending  
**Purpose**: Unified system to aggregate all sentiment sources  
**Tasks**:
- [ ] Create `SentimentAggregator` class
- [ ] Implement weighted sentiment scoring
- [ ] Create sentiment confidence metrics
- [ ] Implement sentiment time-decay weighting
- [ ] Add sentiment divergence detection
- [ ] Create unified sentiment score (-1 to +1)
- [ ] Integrate with strategy evaluation
- [ ] Add sentiment caching system
- [ ] Create API endpoints

**Files to Create**:
- `src/data/providers/sentiment/aggregator.py`
- `src/data/providers/sentiment/models.py`
- `src/core/confluence/confluence_calculator.py`

---

#### ✅ 14. Confluence Calculator
**Status**: Pending  
**Purpose**: Calculate overall confluence score combining technical + sentiment  
**Tasks**:
- [ ] Create `ConfluenceCalculator` class
- [ ] Implement multi-factor scoring (technical + sentiment + flow)
- [ ] Define confluence weights (configurable)
- [ ] Create confluence thresholds for trade filtering
- [ ] Implement confluence trend analysis
- [ ] Add confluence alerts
- [ ] Integrate with strategy signals
- [ ] Create API endpoints

**API Endpoints**:
- `GET /api/confluence/{symbol}` - Get confluence score
- `GET /api/confluence/{symbol}/breakdown` - Get detailed breakdown
- `POST /api/confluence/calculate` - Calculate confluence for signal

---

#### ✅ 15. Strategy Integration
**Status**: Pending  
**Purpose**: Integrate sentiment/confluence into strategy evaluation  
**Tasks**:
- [ ] Enhance `BaseStrategy` to accept sentiment data
- [ ] Add sentiment filtering to signal generation
- [ ] Implement confluence-based confidence adjustment
- [ ] Add sentiment requirements to strategy configs
- [ ] Update `StrategyEvaluator` to fetch sentiment
- [ ] Add sentiment to signal metadata
- [ ] Create sentiment-based strategy variants
- [ ] Update documentation

---

### Category 6: Data Infrastructure

#### ✅ 16. Database Schema for Sentiment Data
**Status**: Pending  
**Tasks**:
- [ ] Design sentiment data tables
- [ ] Create database models for all data types
- [ ] Implement data retention policies
- [ ] Add indexing for performance
- [ ] Create data aggregation views
- [ ] Implement data archival

---

#### ✅ 17. Caching & Rate Limiting
**Status**: Pending  
**Tasks**:
- [ ] Implement Redis caching for sentiment data
- [ ] Add rate limiting per data source
- [ ] Implement data refresh strategies
- [ ] Add cache invalidation logic
- [ ] Monitor API usage and costs

---

#### ✅ 18. API Endpoints & Documentation
**Status**: Partial  
**Tasks**:
- [ ] Create unified sentiment API routes
- [ ] Add OpenAPI/Swagger documentation
- [ ] Implement API authentication
- [ ] Add rate limiting to endpoints
- [ ] Create usage examples
- [ ] Add error handling

---

## Implementation Priority

### Phase 1: Core Infrastructure (Week 1-2)
1. ✅ Sentiment Aggregator System (#13)
2. ✅ Database Schema (#16)
3. ✅ Caching & Rate Limiting (#17)

### Phase 2: High-Value Sources (Week 3-4)
4. ✅ Twitter/X Integration (#1)
5. ✅ Reddit Integration (#2)
6. ✅ Financial News (#4)
7. ✅ Options Flow Enhancement (#7)

### Phase 3: Additional Sources (Week 5-6)
8. ✅ StockTwits (#3)
9. ✅ Google Trends (#9)
10. ✅ Analyst Ratings (#11)
11. ✅ SEC Filings (#5)

### Phase 4: Advanced Features (Week 7-8)
12. ✅ Confluence Calculator (#14)
13. ✅ Strategy Integration (#15)
14. ✅ Dark Pool Data (#8)
15. ✅ Insider Trading (#12)

### Phase 5: Polish & Optimization (Week 9-10)
16. ✅ API Documentation (#18)
17. ✅ Performance Optimization
18. ✅ Monitoring & Alerts

## Configuration Example

```yaml
sentiment:
  enabled: true
  sources:
    twitter:
      enabled: true
      api_key: ${TWITTER_API_KEY}
      weight: 0.20
      rate_limit: 300  # requests per 15 min
    
    reddit:
      enabled: true
      client_id: ${REDDIT_CLIENT_ID}
      client_secret: ${REDDIT_CLIENT_SECRET}
      weight: 0.15
      subreddits: [wallstreetbets, stocks, investing]
    
    news:
      enabled: true
      api_key: ${NEWS_API_KEY}
      weight: 0.25
      sources: [bloomberg, reuters, cnbc]
    
    options:
      enabled: true
      provider: unusual_whales
      weight: 0.30
    
    google_trends:
      enabled: true
      weight: 0.10
  
  aggregation:
    time_window: 24h  # hours
    decay_factor: 0.9  # per hour
    min_confidence: 0.3
    divergence_threshold: 0.5

confluence:
  enabled: true
  weights:
    technical: 0.50
    sentiment: 0.30
    options_flow: 0.20
  
  thresholds:
    min_confluence: 0.6  # Minimum to execute trade
    high_confluence: 0.8  # High confidence trades
```

## Success Metrics

- [ ] All 12+ data sources integrated
- [ ] Sentiment scores calculated in < 2 seconds
- [ ] API rate limits respected for all sources
- [ ] Confluence scores improve trade win rate by 10%+
- [ ] System handles 100+ symbols simultaneously
- [ ] 95%+ uptime for sentiment data aggregation

---

**Note**: This plan is comprehensive and can be adapted based on the specific libraries mentioned in the referenced Twitter/X post. The structure allows for easy addition/modification of data sources as requirements evolve.

