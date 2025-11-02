# Financial News Sentiment Integration - Implementation Plan

## Overview

Integrate financial news aggregation and sentiment analysis from multiple sources (Bloomberg, Reuters, CNBC, Yahoo Finance, etc.) to provide news-based sentiment signals for trading decisions.

## Library Selection

**Primary Choice**: `feedparser` + `newspaper3k` (free, open-source)
- `feedparser`: Parse RSS/Atom feeds from news sources
- `newspaper3k`: Extract and parse full article content

**Alternative**: `newsapi-python` (requires API key, but provides unified API)
- Consider for future enhancement if free tier is sufficient

## Implementation Phases

### Phase 1: Foundation (3-4 hours)
**Goal**: Create basic news provider infrastructure

**Steps**:
1. ✅ Add dependencies to `requirements/base.txt`
   - `feedparser==6.0.10`
   - `newspaper3k==0.2.8`
   - `beautifulsoup4==4.12.2` (dependency for newspaper3k)
   - `lxml==4.9.3` (for faster parsing)

2. ✅ Create `NewsSettings` in `src/config/settings.py`
   - News source URLs (RSS feeds)
   - Cache TTL
   - Rate limiting settings
   - Article parsing settings
   - Filter settings (min article length, relevance threshold)

3. ✅ Create `src/data/providers/sentiment/news.py`
   - `NewsClient` class for fetching/parsing news
   - `NewsArticle` dataclass/model
   - `NewsSentimentProvider` class
   - Integration with existing `SentimentAnalyzer`

4. ✅ Add configuration to `env.template` and `docker-compose.yml`

**Deliverables**:
- News provider can fetch articles from RSS feeds
- Can parse article content
- Can extract symbol mentions
- Basic sentiment analysis working

---

### Phase 2: Database Integration (2-3 hours)
**Goal**: Store news articles and sentiment in database

**Steps**:
1. ✅ Add database models in `src/data/database/models.py`
   - `NewsArticle` model (reuse existing Tweet table structure or create new)
   - `NewsSentiment` model (similar to TweetSentiment)

2. ✅ Update repository (`src/data/providers/sentiment/repository.py`)
   - Add methods to save news articles
   - Add methods to save news sentiment
   - Add query methods for news articles by symbol

3. ✅ Integrate persistence in `NewsSentimentProvider`
   - Save articles to database
   - Save sentiment analysis results
   - Track historical news sentiment

**Deliverables**:
- News articles stored in database
- News sentiment persisted
- Historical queries working

---

### Phase 3: API Integration (2-3 hours)
**Goal**: Expose news sentiment via API

**Steps**:
1. ✅ Add endpoints to `src/api/routes/sentiment.py`
   - `GET /api/sentiment/news/{symbol}` - Get news sentiment
   - `GET /api/sentiment/news/{symbol}/articles` - Get recent articles
   - `GET /api/sentiment/news/{symbol}/trend` - Get sentiment trend
   - `GET /api/sentiment/news/breaking` - Get breaking news
   - `GET /api/sentiment/news/status` - Provider status

2. ✅ Integrate with aggregator
   - Update `SentimentAggregator` to include news provider
   - Test aggregated sentiment with news included

**Deliverables**:
- All API endpoints working
- News integrated into sentiment aggregator
- API documentation updated

---

### Phase 4: Testing & Integration (2-3 hours)
**Goal**: Comprehensive testing and validation

**Steps**:
1. ✅ Create `scripts/test_news_sentiment.py`
   - Test news fetching
   - Test article parsing
   - Test sentiment analysis
   - Test database persistence
   - Test API endpoints

2. ✅ Integration testing
   - Test with aggregator
   - Test error handling
   - Test rate limiting

3. ✅ Update documentation
   - Update checklist
   - Update TODOS
   - Add usage examples

**Deliverables**:
- Comprehensive test script
- All tests passing
- Documentation complete

---

## Technical Details

### News Sources (RSS Feeds)

**Initial Sources**:
- Yahoo Finance: `https://feeds.finance.yahoo.com/rss/2.0/headline`
- Reuters Business: `https://feeds.reuters.com/reuters/businessNews`
- MarketWatch: `https://feeds.marketwatch.com/marketwatch/marketpulse/`
- CNBC: `https://www.cnbc.com/id/100003114/device/rss/rss.html`
- Seeking Alpha: Various RSS feeds by topic

**Symbol-Specific Feeds**:
- Yahoo Finance symbol feed: `https://feeds.finance.yahoo.com/rss/2.0/headline?s={SYMBOL}`
- Custom query-based feeds where available

### Data Models

```python
@dataclass
class NewsArticle:
    """News article data model"""
    article_id: str  # URL or hash
    title: str
    content: str
    summary: Optional[str]
    url: str
    source: str  # 'yahoo', 'reuters', etc.
    published_at: datetime
    author: Optional[str]
    symbols_mentioned: List[str]
    category: Optional[str]  # 'earnings', 'ma', 'analyst', etc.
    raw_data: Optional[Dict] = None
```

### Sentiment Calculation

- Analyze headline sentiment (high weight)
- Analyze article summary sentiment (medium weight)
- Analyze full article sentiment (lower weight, but more context)
- Weight by source credibility
- Weight by recency (breaking news weighted higher)
- Consider article category (earnings news might be more significant)

### Article Relevance

- Symbol mention frequency
- Symbol mention position (headline vs. body)
- Article category relevance
- Source credibility
- Article length (too short = low quality)

---

## Configuration

### Environment Variables

```bash
# News Provider Settings
NEWS_CACHE_TTL=300  # 5 minutes
NEWS_RATE_LIMIT_REQUESTS_PER_MINUTE=60
NEWS_MIN_ARTICLE_LENGTH=100
NEWS_RELEVANCE_THRESHOLD=0.3
NEWS_SOURCES=yahoo,reuters,marketwatch,cnbc
NEWS_ENABLE_FULL_ARTICLE_PARSING=true
NEWS_MAX_ARTICLES_PER_FETCH=50
```

### Settings Class

```python
class NewsSettings(BaseSettings):
    cache_ttl: int = 300
    rate_limit_requests_per_minute: int = 60
    min_article_length: int = 100
    relevance_threshold: float = 0.3
    sources: List[str] = ["yahoo", "reuters", "marketwatch", "cnbc"]
    enable_full_article_parsing: bool = True
    max_articles_per_fetch: int = 50
    symbol_feed_base_url: str = "https://feeds.finance.yahoo.com/rss/2.0/headline"
```

---

## Implementation Order

1. **Phase 1** (Foundation)
   - Dependencies
   - Settings
   - Basic NewsClient
   - NewsSentimentProvider skeleton
   - Basic article fetching

2. **Phase 2** (Database)
   - Database models
   - Repository methods
   - Persistence integration

3. **Phase 3** (API)
   - API endpoints
   - Aggregator integration

4. **Phase 4** (Testing)
   - Test script
   - Integration tests
   - Documentation

---

## Success Criteria

- ✅ Can fetch news from multiple RSS sources
- ✅ Can parse article content and extract symbols
- ✅ Can calculate sentiment for articles
- ✅ Can aggregate news sentiment per symbol
- ✅ Stores articles and sentiment in database
- ✅ Exposes sentiment via API
- ✅ Integrates with sentiment aggregator
- ✅ Test script passes
- ✅ All code follows existing patterns

---

## Estimated Time

- Phase 1: 3-4 hours
- Phase 2: 2-3 hours
- Phase 3: 2-3 hours
- Phase 4: 2-3 hours
- **Total: 9-13 hours**

---

## Dependencies & Considerations

**Dependencies**:
- Internet connectivity for RSS feeds
- Sufficient storage for article content
- Rate limiting to avoid being blocked

**Considerations**:
- Some sources may block automated access
- Article parsing may be slow (full article parsing)
- Need to handle different RSS feed formats
- Need to deduplicate articles from multiple sources
- May need to handle paywalled content gracefully

---

**Status**: Planning Complete ✅  
**Started**: 2024-12-19  
**Next**: Begin Phase 1 implementation

