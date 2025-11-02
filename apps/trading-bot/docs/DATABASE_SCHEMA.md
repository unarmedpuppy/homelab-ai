# Database Schema Documentation

## Overview

This document provides comprehensive documentation for the sentiment and confluence database schema used in the trading bot.

**Last Updated**: 2024-12-19  
**Database**: SQLite (default) / PostgreSQL / MySQL supported  
**ORM**: SQLAlchemy  
**Migrations**: Alembic

## Table of Contents

1. [Schema Overview](#schema-overview)
2. [Sentiment Data Models](#sentiment-data-models)
3. [Confluence Models](#confluence-models)
4. [Indexes and Performance](#indexes-and-performance)
5. [Data Retention](#data-retention)
6. [Query Patterns](#query-patterns)
7. [Migration Guide](#migration-guide)

---

## Schema Overview

### Sentiment Data Flow

```
┌─────────────┐
│   Sources   │
│             │
│ - Twitter   │
│ - Reddit    │
│ - News      │
│ - Options   │
└──────┬──────┘
       │
       ▼
┌──────────────────┐
│  Raw Data        │
│  (Tweets/Posts)  │
└──────┬───────────┘
       │
       ▼
┌──────────────────┐
│  Sentiment       │
│  Analysis        │
│  (Per Source)    │
└──────┬───────────┘
       │
       ▼
┌──────────────────┐
│  Aggregated      │
│  Sentiment       │
└──────┬───────────┘
       │
       ▼
┌──────────────────┐
│  Confluence      │
│  Score           │
└──────────────────┘
```

---

## Sentiment Data Models

### 1. Tweet

Stores raw Twitter/X post data.

**Table**: `tweets`

| Column | Type | Description |
|--------|------|-------------|
| id | Integer | Primary key |
| tweet_id | String(50) | Twitter tweet ID (unique, indexed) |
| text | Text | Tweet content |
| author_id | String(50) | Twitter user ID (indexed) |
| author_username | String(100) | Twitter username |
| created_at | DateTime | Tweet creation time (indexed) |
| like_count | Integer | Number of likes |
| retweet_count | Integer | Number of retweets |
| reply_count | Integer | Number of replies |
| quote_count | Integer | Number of quotes |
| is_retweet | Boolean | Is this a retweet? |
| is_quote | Boolean | Is this a quote tweet? |
| is_reply | Boolean | Is this a reply? |
| language | String(10) | Language code |
| symbols_mentioned | Text | JSON array of stock symbols |
| raw_data | Text | JSON raw API response |
| stored_at | DateTime | When record was created |

**Indexes**:
- `ix_tweets_tweet_id` (unique)
- `ix_tweets_author_id`
- `ix_tweets_created_at`

**Relationships**:
- One-to-Many: `TweetSentiment`

---

### 2. TweetSentiment

Stores sentiment analysis results for individual tweets.

**Table**: `tweet_sentiments`

| Column | Type | Description |
|--------|------|-------------|
| id | Integer | Primary key |
| tweet_id | Integer | Foreign key to tweets.id (indexed) |
| symbol | String(20) | Stock symbol (indexed) |
| sentiment_score | Float | Sentiment score (-1.0 to 1.0) |
| confidence | Float | Confidence (0.0 to 1.0) |
| sentiment_level | String(20) | Categorical level |
| vader_compound | Float | VADER compound score |
| vader_pos | Float | VADER positive score |
| vader_neu | Float | VADER neutral score |
| vader_neg | Float | VADER negative score |
| engagement_score | Float | Engagement score |
| influencer_weight | Float | Influencer weight multiplier |
| weighted_score | Float | Final weighted sentiment score |
| analyzed_at | DateTime | When analyzed (indexed) |

**Indexes**:
- `ix_tweet_sentiments_tweet_id`
- `ix_tweet_sentiments_symbol`
- `ix_tweet_sentiments_analyzed_at`

**Relationships**:
- Many-to-One: `Tweet`

---

### 3. SymbolSentiment

Aggregated sentiment for a symbol from a single source.

**Table**: `symbol_sentiments`

| Column | Type | Description |
|--------|------|-------------|
| id | Integer | Primary key |
| symbol | String(20) | Stock symbol (indexed) |
| timestamp | DateTime | When sentiment calculated (indexed) |
| mention_count | Integer | Number of mentions |
| average_sentiment | Float | Average sentiment (-1.0 to 1.0) |
| weighted_sentiment | Float | Weighted sentiment (-1.0 to 1.0) |
| influencer_sentiment | Float | Influencer-only sentiment |
| engagement_score | Float | Average engagement |
| sentiment_level | String(20) | Categorical level |
| confidence | Float | Overall confidence |
| volume_trend | String(20) | Volume trend (up/down/stable) |
| tweet_ids | Text | JSON array of tweet IDs used |
| aggregated_at | DateTime | When record created |

**Indexes**:
- `ix_symbol_sentiments_symbol`
- `ix_symbol_sentiments_timestamp`

---

### 4. RedditPost

Stores raw Reddit post/comment data.

**Table**: `reddit_posts`

| Column | Type | Description |
|--------|------|-------------|
| id | Integer | Primary key |
| post_id | String(50) | Reddit post/comment ID (unique, indexed) |
| text | Text | Post/comment content |
| author | String(100) | Reddit username (indexed) |
| created_at | DateTime | Creation time (indexed) |
| score | Integer | Upvote score |
| upvote_ratio | Float | Upvote ratio |
| num_comments | Integer | Comment count |
| subreddit | String(100) | Subreddit name (indexed) |
| is_post | Boolean | True for post, False for comment |
| parent_id | String(50) | Parent post/comment ID |
| symbols_mentioned | Text | JSON array of symbols |
| raw_data | Text | JSON raw API response |
| stored_at | DateTime | When stored |

**Indexes**:
- `ix_reddit_posts_post_id` (unique)
- `ix_reddit_posts_author`
- `ix_reddit_posts_created_at`
- `ix_reddit_posts_subreddit`

**Relationships**:
- One-to-Many: `RedditSentiment`

---

### 5. RedditSentiment

Sentiment analysis results for Reddit posts/comments.

**Table**: `reddit_sentiments`

Similar structure to `TweetSentiment`, but references `RedditPost`.

---

### 6. Influencer

Twitter influencer/trader accounts.

**Table**: `influencers`

| Column | Type | Description |
|--------|------|-------------|
| id | Integer | Primary key |
| user_id | String(50) | Twitter user ID (unique, indexed) |
| username | String(100) | Twitter username (unique, indexed) |
| display_name | String(200) | Display name |
| follower_count | Integer | Number of followers |
| following_count | Integer | Number following |
| tweet_count | Integer | Total tweets |
| is_verified | Boolean | Verified account? |
| is_protected | Boolean | Protected account? |
| category | String(50) | Category (trader, analyst, etc.) |
| weight_multiplier | Float | Sentiment weight multiplier |
| is_active | Boolean | Active tracking (indexed) |
| added_at | DateTime | When added |
| updated_at | DateTime | Last update |

---

## Confluence Models

### 7. AggregatedSentiment

Cross-source aggregated sentiment (combines Twitter, Reddit, News, Options).

**Table**: `aggregated_sentiments`

| Column | Type | Description |
|--------|------|-------------|
| id | Integer | Primary key |
| symbol | String(20) | Stock symbol (indexed) |
| timestamp | DateTime | Calculation time (indexed) |
| unified_sentiment | Float | Unified score (-1.0 to 1.0) |
| confidence | Float | Overall confidence (0.0 to 1.0) |
| sentiment_level | String(20) | Categorical level |
| source_count | Integer | Number of sources used |
| provider_count | Integer | Number of providers used |
| total_mention_count | Integer | Total mentions across sources |
| divergence_detected | Boolean | Sources disagree? |
| divergence_score | Float | Divergence magnitude (0.0 to 1.0) |
| volume_trend | String(20) | Volume trend |
| twitter_sentiment | Float | Twitter-specific score |
| reddit_sentiment | Float | Reddit-specific score |
| news_sentiment | Float | News-specific score |
| options_flow_sentiment | Float | Options flow-specific score |
| source_breakdown | Text | JSON: source contribution percentages |
| providers_used | Text | JSON array: provider names |
| aggregated_at | DateTime | Record creation time |

**Indexes**:
- `ix_aggregated_sentiments_symbol`
- `ix_aggregated_sentiments_timestamp`
- `idx_aggregated_sentiment_symbol_timestamp` (composite: symbol, timestamp)

**Example Query**:
```sql
-- Get latest aggregated sentiment for a symbol
SELECT * FROM aggregated_sentiments
WHERE symbol = 'SPY'
ORDER BY timestamp DESC
LIMIT 1;
```

---

### 8. ConfluenceScore

Unified confluence score combining technical indicators, sentiment, and options flow.

**Table**: `confluence_scores`

| Column | Type | Description |
|--------|------|-------------|
| id | Integer | Primary key |
| symbol | String(20) | Stock symbol (indexed) |
| timestamp | DateTime | Calculation time (indexed) |
| confluence_score | Float | Confluence strength (0.0 to 1.0) |
| directional_bias | Float | Bullish/bearish bias (-1.0 to 1.0) |
| confluence_level | String(20) | Level (very_low to very_high) |
| confidence | Float | Confidence (0.0 to 1.0) |
| technical_score | Float | Technical component (-1.0 to 1.0) |
| sentiment_score | Float | Sentiment component (-1.0 to 1.0) |
| options_flow_score | Float | Options flow component (-1.0 to 1.0) |
| technical_contribution | Float | Technical contribution (0.0 to 1.0) |
| sentiment_contribution | Float | Sentiment contribution (0.0 to 1.0) |
| options_flow_contribution | Float | Options flow contribution (0.0 to 1.0) |
| technical_breakdown | Text | JSON: technical indicator details |
| components_used | Text | JSON array: components included |
| meets_minimum_threshold | Boolean | Meets minimum for trade (indexed) |
| meets_high_threshold | Boolean | Meets high confidence (indexed) |
| volume_trend | String(20) | Volume trend |
| calculated_at | DateTime | Record creation time |

**Indexes**:
- `ix_confluence_scores_symbol`
- `ix_confluence_scores_timestamp`
- `ix_confluence_scores_meets_minimum_threshold`
- `ix_confluence_scores_meets_high_threshold`
- `idx_confluence_symbol_timestamp` (composite: symbol, timestamp)
- `idx_confluence_meets_thresholds` (composite: meets_minimum_threshold, meets_high_threshold)

**Example Query**:
```sql
-- Find symbols with high confluence
SELECT symbol, confluence_score, directional_bias, timestamp
FROM confluence_scores
WHERE meets_high_threshold = 1
  AND timestamp >= datetime('now', '-24 hours')
ORDER BY confluence_score DESC;
```

---

## Indexes and Performance

### Index Strategy

1. **Primary Keys**: All tables have integer primary keys
2. **Unique Indexes**: On natural unique identifiers (tweet_id, post_id, user_id)
3. **Single Column Indexes**: On frequently queried fields (symbol, timestamp, author_id)
4. **Composite Indexes**: For common query patterns (symbol + timestamp)

### Performance Considerations

- Use composite indexes for time-series queries on symbols
- Consider partitioning large tables by date range (future enhancement)
- Monitor query performance and add indexes as needed
- Use `EXPLAIN QUERY PLAN` to analyze query performance

---

## Data Retention

### Retention Periods

| Data Type | Default Retention | Rationale |
|-----------|-------------------|-----------|
| Tweets | 90 days | Raw data, detailed records |
| Reddit Posts | 90 days | Raw data, detailed records |
| Symbol Sentiments | 365 days | Source-level aggregations |
| Aggregated Sentiments | 730 days | Cross-source aggregations |
| Confluence Scores | 730 days | Critical for backtesting |

### Cleanup Process

Run cleanup script daily:
```bash
python scripts/cleanup_sentiment_data.py
```

Or with custom retention periods:
```bash
python scripts/cleanup_sentiment_data.py --days 60,60,180,365,365
```

### Configuration

Set retention periods via environment variables:
```bash
RETENTION_TWEETS_DAYS=90
RETENTION_REDDIT_POSTS_DAYS=90
RETENTION_SYMBOL_SENTIMENTS_DAYS=365
RETENTION_AGGREGATED_SENTIMENTS_DAYS=730
RETENTION_CONFLUENCE_SCORES_DAYS=730
```

---

## Query Patterns

### Common Queries

#### 1. Get Latest Sentiment for Symbol
```sql
SELECT * FROM aggregated_sentiments
WHERE symbol = 'SPY'
ORDER BY timestamp DESC
LIMIT 1;
```

#### 2. Get Sentiment Trend Over Time
```sql
SELECT 
    DATE(timestamp) as date,
    AVG(unified_sentiment) as avg_sentiment,
    COUNT(*) as data_points
FROM aggregated_sentiments
WHERE symbol = 'SPY'
  AND timestamp >= datetime('now', '-30 days')
GROUP BY DATE(timestamp)
ORDER BY date DESC;
```

#### 3. Find High Confluence Opportunities
```sql
SELECT 
    symbol,
    confluence_score,
    directional_bias,
    sentiment_score,
    technical_score,
    timestamp
FROM confluence_scores
WHERE meets_high_threshold = 1
  AND timestamp >= datetime('now', '-1 hour')
ORDER BY confluence_score DESC
LIMIT 20;
```

#### 4. Get Trending Symbols by Mentions
```sql
SELECT 
    symbol,
    SUM(total_mention_count) as total_mentions,
    AVG(unified_sentiment) as avg_sentiment
FROM aggregated_sentiments
WHERE timestamp >= datetime('now', '-24 hours')
GROUP BY symbol
HAVING total_mentions >= 50
ORDER BY total_mentions DESC
LIMIT 20;
```

---

## Migration Guide

### Running Migrations

```bash
# Create new migration
alembic revision --autogenerate -m "description"

# Upgrade database
alembic upgrade head

# Downgrade one version
alembic downgrade -1

# Check current version
alembic current
```

### Migration History

- **001**: Initial Twitter sentiment tables
- **002**: Add AggregatedSentiment and ConfluenceScore tables

---

## Entity Relationship Diagram

```
┌─────────────┐         ┌──────────────────┐
│   Tweet     │────1:N──│ TweetSentiment   │
│             │         │                  │
│ tweet_id PK │         │ id PK            │
│ author_id   │         │ tweet_id FK      │
│ created_at  │         │ symbol           │
└─────────────┘         └────────┬─────────┘
                                 │
┌─────────────┐                 │
│ RedditPost  │                 │
│             │                 │
│ post_id PK  │                 │
│ created_at  │                 │
└──────┬──────┘                 │
       │                        │
       │ 1:N                    │
       ▼                        │
┌──────────────────┐            │
│ RedditSentiment  │            │
│                  │            │
│ post_id FK       │            │
│ symbol           │            │
└──────────────────┘            │
                                │
                                ▼
                    ┌──────────────────────┐
                    │  SymbolSentiment     │
                    │  (per source)        │
                    │                      │
                    │ symbol               │
                    │ timestamp            │
                    └──────────┬───────────┘
                               │
                               ▼
                    ┌──────────────────────┐
                    │ AggregatedSentiment  │
                    │  (cross-source)      │
                    │                      │
                    │ unified_sentiment    │
                    │ source_breakdown     │
                    └──────────┬───────────┘
                               │
                               ▼
                    ┌──────────────────────┐
                    │  ConfluenceScore     │
                    │                      │
                    │ confluence_score     │
                    │ directional_bias     │
                    └──────────────────────┘
```

---

## Data Dictionary

### Sentiment Levels

| Level | Score Range | Description |
|-------|-------------|-------------|
| very_bearish | -1.0 to -0.6 | Strongly negative sentiment |
| bearish | -0.6 to -0.2 | Negative sentiment |
| neutral | -0.2 to 0.2 | Neutral/no strong sentiment |
| bullish | 0.2 to 0.6 | Positive sentiment |
| very_bullish | 0.6 to 1.0 | Strongly positive sentiment |

### Confluence Levels

| Level | Score Range | Description |
|-------|-------------|-------------|
| very_low | 0.0 to 0.3 | Weak confluence |
| low | 0.3 to 0.5 | Low confluence |
| moderate | 0.5 to 0.7 | Moderate confluence |
| high | 0.7 to 0.85 | High confluence |
| very_high | 0.85 to 1.0 | Very strong confluence |

---

## Best Practices

1. **Use Indexed Columns**: Always filter by indexed columns when possible
2. **Limit Results**: Use `LIMIT` for queries that might return many rows
3. **Batch Operations**: Use bulk inserts/updates when processing many records
4. **Regular Cleanup**: Run cleanup scripts regularly to maintain performance
5. **Monitor Growth**: Track table sizes and adjust retention as needed
6. **Backup Before Cleanup**: Always backup before running large cleanup operations

---

## Troubleshooting

### Common Issues

**Issue**: Slow queries on large tables
- **Solution**: Ensure indexes are created and used
- **Check**: Use `EXPLAIN QUERY PLAN` to verify index usage

**Issue**: Database growing too large
- **Solution**: Adjust retention periods or run cleanup more frequently
- **Check**: `RETENTION_*_DAYS` settings

**Issue**: Migration fails
- **Solution**: Check for data conflicts, backup database first
- **Check**: Review migration file for syntax errors

---

**For more details, see**: [DATABASE_SCHEMA_PLAN.md](./DATABASE_SCHEMA_PLAN.md)

