# Performance Optimization Guide

## Overview

This document outlines performance optimizations implemented in the Trading Bot API.

## Database Optimizations

### Indexes

Composite indexes have been added for common query patterns:

#### Sentiment Tables
- `tweets`: Composite index on `(symbol, created_at)` for time-range queries
- `tweet_sentiments`: Composite index on `(symbol, timestamp)` for sentiment history
- `symbol_sentiments`: Composite index on `(symbol, timestamp)` for aggregated sentiment
- `aggregated_sentiments`: Composite index on `(symbol, timestamp)` for unified sentiment
- `confluence_scores`: Composite index on `(symbol, timestamp)` for confluence history

#### Options Flow Tables
- `options_flow`: Composite indexes on `(symbol, timestamp)` and `(symbol, pattern_type, timestamp)`
- `options_patterns`: Composite indexes on `(symbol, pattern_type, detected_at)` and `(symbol, strength, detected_at)`

### Query Optimization

1. **Use Indexes**: All time-range queries use indexed columns
2. **Limit Results**: All queries include reasonable `limit` clauses
3. **Batch Operations**: Use bulk inserts/updates where possible
4. **Connection Pooling**: SQLAlchemy connection pooling enabled by default

### Best Practices

- Use `.filter()` with indexed columns first
- Order by indexed columns when possible
- Use composite indexes for multi-column queries
- Limit result sets to reasonable sizes (default: 100 records)

## Caching Strategy

### Provider-Level Caching

All sentiment providers use in-memory caching:
- **TTL**: Configurable per provider (default: 300 seconds)
- **Cache Key**: `{provider}_{symbol}_{hours}`
- **Invalidation**: Automatic expiration based on TTL

### Aggregator Caching

Sentiment aggregator caches:
- Aggregated sentiment results
- Source sentiment data
- TTL: 300 seconds (configurable)

### Recommendations

- For high-traffic symbols, consider increasing cache TTL
- Monitor cache hit rates
- Use Redis for distributed caching (future enhancement)

## API Performance

### Rate Limiting

Rate limits applied per endpoint type:
- Market Data: 60 requests/minute
- Sentiment: 30 requests/minute
- Options Flow: 20 requests/minute
- Trading Operations: 10 requests/minute

### Response Times

Target response times:
- Simple queries: < 100ms
- Aggregated sentiment: < 500ms
- Options flow analysis: < 1s
- Confluence calculation: < 1s

### Optimization Tips

1. Use appropriate `hours` parameter (shorter = faster)
2. Use provider-specific endpoints when possible
3. Enable caching on client side
4. Use batch endpoints for multiple symbols

## Data Retention

### Retention Policies

Default retention periods:
- Raw tweets/posts: 90 days
- Sentiments: 90-180 days (aggregated kept longer)
- Options flow: 90 days
- Aggregated/confluence: 180 days

### Cleanup

Run cleanup script regularly:
```bash
python scripts/cleanup_old_data.py
```

For dry run:
```bash
python scripts/cleanup_old_data.py --dry-run
```

## Monitoring

### Health Checks

- `/health`: Basic health check
- `/api/monitoring/health/detailed`: Comprehensive health with component status
- `/api/monitoring/metrics`: System resource metrics
- `/api/monitoring/providers/status`: Provider availability

### Performance Metrics

Monitor:
- Response times
- Database query times
- Cache hit rates
- Provider availability
- System resource usage

## Future Optimizations

### Planned Enhancements

1. **Redis Caching**: Distributed caching layer
2. **Database Read Replicas**: Separate read/write databases
3. **Query Result Pagination**: Cursor-based pagination
4. **Async Database Operations**: Full async/await support
5. **Materialized Views**: Pre-computed aggregations
6. **Connection Pooling Tuning**: Optimize pool sizes

### Database Migrations

Use migration utilities:
```bash
python scripts/verify_database_schema.py
```

This verifies:
- All required tables exist
- All indexes are in place
- Schema matches models

