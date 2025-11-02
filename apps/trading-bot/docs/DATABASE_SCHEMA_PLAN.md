# Database Schema & Retention Policy Plan

## Overview

This document outlines the database schema plan, data retention policies, and migration strategy for the sentiment and confluence data systems.

## Database Models

### Sentiment Data Models

#### Core Models (Already Implemented)
- **Tweet**: Twitter/X post data
- **TweetSentiment**: Sentiment analysis for individual tweets
- **SymbolSentiment**: Aggregated sentiment per symbol (single source)
- **RedditPost**: Reddit post/comment data
- **RedditSentiment**: Sentiment analysis for Reddit posts/comments
- **Influencer**: Twitter influencer/trader accounts

#### New Models (Just Added)
- **AggregatedSentiment**: Cross-source aggregated sentiment (Twitter + Reddit + News + Options)
- **ConfluenceScore**: Unified confluence scores combining technical + sentiment + options flow

### Schema Details

#### AggregatedSentiment Table
```sql
- id: Primary key
- symbol: Stock symbol (indexed)
- timestamp: When sentiment was calculated (indexed)
- unified_sentiment: Overall sentiment score (-1.0 to 1.0)
- confidence: Confidence in the score (0.0 to 1.0)
- sentiment_level: Categorical level (very_bearish, bearish, neutral, bullish, very_bullish)
- source_count: Number of sources contributing
- provider_count: Number of providers used
- total_mention_count: Total mentions across all sources
- divergence_detected: Whether sources disagreed
- divergence_score: Magnitude of divergence (0.0 to 1.0)
- volume_trend: Trend indicator (up, down, stable)
- twitter_sentiment: Twitter-specific score (-1.0 to 1.0)
- reddit_sentiment: Reddit-specific score (-1.0 to 1.0)
- news_sentiment: News-specific score (-1.0 to 1.0)
- options_flow_sentiment: Options flow-specific score (-1.0 to 1.0)
- source_breakdown: JSON - Source contribution percentages
- providers_used: JSON array - List of providers
- aggregated_at: When record was created

Indexes:
- idx_aggregated_sentiment_symbol_timestamp (symbol, timestamp)
```

#### ConfluenceScore Table
```sql
- id: Primary key
- symbol: Stock symbol (indexed)
- timestamp: When confluence was calculated (indexed)
- confluence_score: Confluence strength (0.0 to 1.0)
- directional_bias: Bullish/bearish bias (-1.0 to 1.0)
- confluence_level: Categorical level (very_low, low, moderate, high, very_high)
- confidence: Confidence in the score (0.0 to 1.0)
- technical_score: Technical indicator score (-1.0 to 1.0)
- sentiment_score: Sentiment component score (-1.0 to 1.0)
- options_flow_score: Options flow component score (-1.0 to 1.0)
- technical_contribution: Weighted technical contribution (0.0 to 1.0)
- sentiment_contribution: Weighted sentiment contribution (0.0 to 1.0)
- options_flow_contribution: Weighted options flow contribution (0.0 to 1.0)
- technical_breakdown: JSON - Detailed technical indicators
- components_used: JSON array - Components included
- meets_minimum_threshold: Boolean (indexed)
- meets_high_threshold: Boolean (indexed)
- volume_trend: Trend indicator
- calculated_at: When record was created

Indexes:
- idx_confluence_symbol_timestamp (symbol, timestamp)
- idx_confluence_meets_thresholds (meets_minimum_threshold, meets_high_threshold)
```

## Data Retention Policies

### Policy Strategy

Data retention is critical for:
1. **Performance**: Removing old data keeps queries fast
2. **Storage**: Prevents unbounded database growth
3. **Compliance**: May be required for data privacy
4. **Cost**: Reduces database storage costs

### Retention Periods

| Data Type | Retention Period | Rationale |
|-----------|------------------|-----------|
| **Raw Tweets/Posts** | 90 days | Detailed data only needed for recent analysis |
| **Individual Sentiment Scores** | 180 days | Needed for trend analysis and model training |
| **Symbol Sentiment (single source)** | 1 year | Historical sentiment trends |
| **Aggregated Sentiment** | 2 years | Important for long-term pattern analysis |
| **Confluence Scores** | 2 years | Critical for backtesting and strategy development |
| **Influencers** | Indefinite | Reference data, updated but never deleted |

### Archival Strategy

Instead of deleting data, we'll use a two-tier approach:

1. **Hot Storage** (Database):
   - Recent data (within retention period)
   - Frequently accessed
   - Indexed for fast queries

2. **Cold Storage** (Optional):
   - Archived data (beyond retention period)
   - Compressed/parquet files
   - Can be loaded for backtesting if needed

### Implementation Plan

#### Phase 1: Retention Methods (Repository Layer)
```python
# Methods to add to SentimentRepository:

1. cleanup_old_tweets(days: int = 90) -> int
   - Delete tweets older than N days
   - Also delete associated TweetSentiment records
   - Returns count of deleted records

2. cleanup_old_reddit_posts(days: int = 90) -> int
   - Delete Reddit posts older than N days
   - Also delete associated RedditSentiment records

3. cleanup_old_symbol_sentiments(days: int = 365) -> int
   - Delete SymbolSentiment records older than N days

4. cleanup_old_aggregated_sentiments(days: int = 730) -> int
   - Delete AggregatedSentiment records older than N days
   
5. cleanup_old_confluence_scores(days: int = 730) -> int
   - Delete ConfluenceScore records older than N days

6. cleanup_all_old_data() -> Dict[str, int]
   - Run all cleanup methods
   - Return summary of deleted records
```

#### Phase 2: Automated Cleanup (Cron/Scheduled Task)
```python
# Script: scripts/cleanup_sentiment_data.py
- Run daily via cron or scheduled task
- Execute cleanup methods with configured retention periods
- Log cleanup results
- Optional: Archive to cold storage before deletion
```

#### Phase 3: Configuration
```python
# Add to settings.py:

class DataRetentionSettings(BaseSettings):
    """Data retention configuration"""
    retention_tweets_days: int = 90
    retention_reddit_posts_days: int = 90
    retention_symbol_sentiments_days: int = 365
    retention_aggregated_sentiments_days: int = 730
    retention_confluence_scores_days: int = 730
    enable_cleanup: bool = True
    cleanup_schedule_hours: int = 24  # Run every 24 hours
    
    class Config:
        env_prefix = "RETENTION_"
```

## Database Migrations

### Migration Strategy

Use Alembic for version-controlled database migrations.

### Migration 002: Add AggregatedSentiment and ConfluenceScore Tables

**File**: `migrations/versions/002_add_aggregated_and_confluence_tables.py`

**Operations**:
1. Create `aggregated_sentiments` table
2. Create `confluence_scores` table
3. Add composite indexes
4. Add individual indexes

**Rollback**: Drop tables and indexes

### Migration Process

1. **Create Migration**:
   ```bash
   alembic revision -m "add_aggregated_and_confluence_tables"
   ```

2. **Auto-generate or Manual**:
   - Auto-generate detects new models (if configured correctly)
   - Manually edit to ensure proper indexes and constraints

3. **Test Migration**:
   ```bash
   # Test upgrade
   alembic upgrade head
   
   # Test rollback
   alembic downgrade -1
   ```

4. **Apply to Production**:
   ```bash
   alembic upgrade head
   ```

## Schema Documentation

### Documentation Plan

#### 1. ER Diagram
- Visual representation of all tables
- Relationships between tables
- Key fields and indexes

#### 2. Table Documentation
For each table, document:
- Purpose and use case
- All columns with types and constraints
- Indexes and their purpose
- Relationships to other tables
- Example queries

#### 3. Query Patterns
- Common queries and their performance characteristics
- Recommended indexes for custom queries
- Best practices for data access

#### 4. Data Dictionary
- Field definitions
- Value ranges and constraints
- Enum values and meanings

## Implementation Checklist

### Data Retention
- [x] Define retention policies
- [ ] Implement cleanup methods in repository
- [ ] Add DataRetentionSettings to config
- [ ] Create cleanup script
- [ ] Set up scheduled cleanup (cron/scheduler)
- [ ] Test cleanup process
- [ ] Document retention policies

### Database Migrations
- [x] Verify Alembic setup
- [ ] Create migration 002 for new tables
- [ ] Test migration upgrade/downgrade
- [ ] Document migration process
- [ ] Add migration rollback procedures

### Schema Documentation
- [x] Create this plan document
- [ ] Create ER diagram
- [ ] Document all tables in detail
- [ ] Create data dictionary
- [ ] Document query patterns
- [ ] Add to main documentation

## Next Steps

1. **Immediate**: Create migration 002 for new tables
2. **Short-term**: Implement retention cleanup methods
3. **Medium-term**: Set up automated cleanup
4. **Long-term**: Create comprehensive schema documentation

---

**Last Updated**: 2024-12-19  
**Status**: Plan Complete, Implementation In Progress

