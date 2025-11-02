# Testing Sentiment Aggregator

## Quick Test (Local - Syntax Only)

```bash
python scripts/test_aggregator_syntax.py
```

This checks syntax without requiring dependencies.

## Full Test (Docker - Requires Dependencies)

The full test requires Python dependencies and API credentials. Run it in Docker:

```bash
# Start the services
docker-compose up -d bot

# Run the test
docker-compose exec bot python scripts/test_sentiment_aggregator.py

# Or run directly if container is running
docker exec -it trading-bot python scripts/test_sentiment_aggregator.py
```

## What the Test Does

1. **Initialization Test**: Verifies aggregator can be created
2. **Provider Availability**: Checks which providers (Twitter/Reddit) are available
3. **Individual Provider Tests**: Tests each provider separately
4. **Aggregation Test**: Tests combining sentiment from multiple sources
5. **Time Decay Test**: Verifies time-based weighting
6. **Divergence Detection**: Tests sentiment divergence calculation

## Expected Output

If providers are configured:
- ✅ Aggregator initialized with available sources
- ✅ Individual provider sentiment scores
- ✅ Aggregated sentiment with unified score
- ✅ Source breakdown showing contributions
- ✅ Divergence score

If providers are NOT configured:
- ⚠️ Providers show as "Not Available"
- ✅ Aggregator still initializes correctly
- ✅ Core logic (time decay, divergence) still works

## API Testing

Once the aggregator is working, test the API endpoints:

```bash
# Check aggregator status
curl http://localhost:8000/api/sentiment/aggregated/status

# Get aggregated sentiment for a symbol
curl http://localhost:8000/api/sentiment/aggregated/SPY

# With specific sources
curl "http://localhost:8000/api/sentiment/aggregated/AAPL?sources=twitter,reddit"
```

## Troubleshooting

**Import Errors**: Install dependencies or use Docker
```bash
pip install -r requirements/base.txt
```

**No Providers Available**: Configure API credentials in `.env`:
- Twitter: `TWITTER_BEARER_TOKEN`
- Reddit: `REDDIT_CLIENT_ID`, `REDDIT_CLIENT_SECRET`, `REDDIT_USER_AGENT`

**Database Errors**: Ensure database is accessible (check `DATABASE_URL` in `.env`)

