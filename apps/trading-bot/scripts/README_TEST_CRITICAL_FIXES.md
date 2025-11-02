# Test Script for Critical and High-Priority Fixes

## Overview

This test script verifies all the critical and high-priority fixes implemented during the architectural review:

1. **Thread Safety** - Provider initialization is thread-safe (no race conditions)
2. **Database Session Management** - Context managers properly handle sessions
3. **Transaction Atomicity** - Batch operations are atomic
4. **Cache Serialization** - AggregatedSentiment can be cached (datetime serialization works)
5. **Error Handling** - Structured logging with proper context
6. **Volume Trend Calculation** - Real trend detection based on historical data
7. **Cache Standardization** - All providers use CacheManager (Redis-backed)
8. **Input Validation** - Comprehensive validation for API inputs

## Usage

### Prerequisites

1. Install dependencies:
   ```bash
   cd apps/trading-bot
   pip install -r requirements/base.txt
   ```

2. Set up environment variables (optional, for full functionality):
   ```bash
   # Copy and configure
   cp env.template .env
   ```

3. Ensure database is accessible (if testing database features):
   ```bash
   # SQLite will be created automatically if configured
   # PostgreSQL requires connection string in .env
   ```

### Run Tests

```bash
# From project root
cd apps/trading-bot
python scripts/test_critical_fixes.py

# Or make executable and run directly
chmod +x scripts/test_critical_fixes.py
./scripts/test_critical_fixes.py
```

### Expected Output

The script will run all tests and provide:
- ✅ **Passed tests** - Green checkmarks
- ❌ **Failed tests** - Red X marks with error messages
- ⚠️  **Warnings** - Yellow warnings (e.g., providers not configured)

Example output:
```
======================================================================
CRITICAL AND HIGH-PRIORITY FIXES - TEST SUITE
======================================================================
Test started at: 2024-12-19 10:00:00

======================================================================
TEST 1: Thread Safety - Provider Initialization
======================================================================
✅ PASSED: Thread Safety
   All 10 threads got same instance (ID: 123456789)

...

======================================================================
TEST SUMMARY
======================================================================
✅ Passed: 8
❌ Failed: 0
⚠️  Warnings: 2

✅ ALL TESTS PASSED
```

## Test Details

### Test 1: Thread Safety
- Launches 10 threads simultaneously
- Each thread requests a provider instance
- Verifies all threads get the same singleton instance
- **Expected**: Single instance created (no race conditions)

### Test 2: Database Session Management
- Tests context manager for database sessions
- Verifies sessions are properly closed
- Tests that transactions work correctly
- **Expected**: Sessions created/closed properly, no leaks

### Test 3: Transaction Atomicity
- Tests batch save operations
- Verifies atomicity of multiple operations
- **Expected**: Batch operations succeed or fail atomically

### Test 4: Cache Serialization
- Creates AggregatedSentiment with datetime objects
- Tests caching (serialization to JSON)
- Tests retrieval (deserialization)
- **Expected**: Can cache and retrieve complex objects with datetimes

### Test 5: Error Handling
- Tests error handling with structured logging
- Verifies error messages contain context
- **Expected**: Errors logged with proper context (symbol, operation, etc.)

### Test 6: Volume Trend Calculation
- Tests volume trend utility function
- Verifies it returns valid trend values
- **Expected**: Returns "up", "down", or "stable"

### Test 7: Cache Standardization
- Checks that all providers use CacheManager
- Verifies no in-memory dict caches remain
- **Expected**: All providers use Redis-backed CacheManager

### Test 8: Input Validation
- Tests symbol validation (format, reserved keywords)
- Tests hours/days/limit validation
- Tests invalid inputs are rejected
- **Expected**: Invalid inputs rejected with clear error messages

## Troubleshooting

### Database Connection Errors
If tests fail due to database connection:
- Check `DATABASE_URL` in environment variables
- SQLite: File will be created automatically
- PostgreSQL: Ensure connection string is correct

### Provider Not Available Warnings
Some providers may show warnings if:
- API credentials not configured
- Optional dependencies not installed
- This is expected - tests will skip unavailable providers

### Import Errors
If you get import errors:
- Ensure you're running from the correct directory
- Check that `sys.path.insert(0, str(project_root))` is working
- Try: `export PYTHONPATH=/path/to/trading-bot:$PYTHONPATH`

## Exit Codes

- `0` - All tests passed
- `1` - Some tests failed

Useful for CI/CD integration:
```bash
python scripts/test_critical_fixes.py && echo "Deploy approved" || echo "Deploy blocked"
```

## Notes

- Tests are designed to be **non-destructive** - they clean up test data
- Some tests may show warnings if providers aren't fully configured (expected)
- Database tests require a valid database connection
- Cache tests require Redis (or will fall back to in-memory cache)

