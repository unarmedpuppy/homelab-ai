# Unit Tests for Sentiment Providers

This directory contains comprehensive unit tests for all sentiment data providers and related components.

## Test Structure

Tests are organized by component:
- `test_analyst_ratings.py` - Analyst Ratings provider tests
- `test_stocktwits_provider.py` - StockTwits provider tests
- `test_google_trends_provider.py` - Google Trends provider tests
- `test_mention_volume_provider.py` - Mention Volume provider tests
- `test_news_provider.py` - News provider tests
- `test_sentiment_aggregator.py` - Sentiment Aggregator tests
- `test_sentiment_repository.py` - Repository layer tests (existing)
- `test_sentiment_analyzer.py` - Sentiment analyzer tests (existing)
- `test_twitter_client.py` - Twitter client tests (existing)
- `test_reddit_client.py` - Reddit client tests (existing)
- `test_reddit_provider.py` - Reddit provider tests (existing)

## Running Tests

```bash
# Run all unit tests
pytest tests/unit/

# Run specific test file
pytest tests/unit/test_analyst_ratings.py

# Run with coverage
pytest tests/unit/ --cov=src.data.providers.sentiment --cov-report=html

# Run with verbose output
pytest tests/unit/ -v

# Run specific test class
pytest tests/unit/test_analyst_ratings.py::TestAnalystRatingsClient

# Run specific test method
pytest tests/unit/test_analyst_ratings.py::TestAnalystRatingsClient::test_client_initialization
```

## Test Coverage Goals

- **Unit Tests**: Test individual components in isolation with mocks
- **Coverage Target**: >80% code coverage for sentiment providers
- **Focus Areas**:
  - Client initialization and configuration
  - Data fetching and parsing
  - Sentiment calculation logic
  - Error handling and edge cases
  - Rate limiting and caching
  - Batch operations

## Mocking Strategy

All external dependencies are mocked:
- API clients (yfinance, httpx, tweepy, etc.)
- Database connections
- Cache managers
- Rate limiters
- Usage monitors

This ensures tests are:
- Fast (no network calls)
- Reliable (no flakiness from external services)
- Isolated (test one component at a time)
- Deterministic (consistent results)

## Fixtures

Shared fixtures are defined in `tests/conftest.py`:
- `mock_db_session` - Mock database session
- `mock_cache_manager` - Mock cache manager
- `mock_rate_limiter` - Mock rate limiter
- `mock_usage_monitor` - Mock usage monitor
- `mock_yfinance` - Mock yfinance module
- `sample_symbol_sentiment` - Sample sentiment data
- `sample_tweet` - Sample tweet data

## Test Categories

1. **Initialization Tests**: Verify components initialize correctly
2. **Success Path Tests**: Test happy path scenarios
3. **Error Handling Tests**: Test failure scenarios and edge cases
4. **Validation Tests**: Test input validation
5. **Integration Tests**: Test component interactions (minimal, prefer unit tests)

## Adding New Tests

When adding tests for a new provider:

1. Create test file: `test_{provider_name}.py`
2. Follow existing test structure
3. Mock all external dependencies
4. Test both success and failure cases
5. Include edge case tests
6. Add fixtures to `conftest.py` if reusable

Example:
```python
class TestNewProvider:
    @pytest.fixture
    def provider(self):
        # Setup mocked provider
        pass
    
    def test_success_case(self, provider):
        # Test success scenario
        pass
    
    def test_error_case(self, provider):
        # Test error scenario
        pass
```

