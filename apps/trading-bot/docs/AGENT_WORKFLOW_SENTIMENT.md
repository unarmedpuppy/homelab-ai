# Agent Workflow Guide - Sentiment Integration

## 🎯 Purpose

This guide helps agents understand how to work on sentiment data source integrations for the trading bot. Follow this workflow to ensure consistent implementation, proper documentation, and effective collaboration with other agents.

## 📋 Getting Started

### Step 1: Review the Master Checklist

**Primary Document**: [SENTIMENT_INTEGRATION_CHECKLIST.md](./SENTIMENT_INTEGRATION_CHECKLIST.md)

This is your **source of truth** for:
- What tasks exist
- What's already completed
- What's in progress
- What's pending

**Always check this document first before starting any work.**

### Step 2: Understand Completed Work

**Note**: All sentiment integration work is **100% COMPLETE** ✅

**Read First**: [SENTIMENT_FEATURES_COMPLETE.md](./SENTIMENT_FEATURES_COMPLETE.md)

This comprehensive document contains:
- Complete feature overview
- System architecture
- All 12 data sources
- How to extend the system

### Step 3: Review Related Documentation

For understanding or extending the system:
- **Complete Documentation**: See [SENTIMENT_FEATURES_COMPLETE.md](./SENTIMENT_FEATURES_COMPLETE.md) - Everything that was built
- **Database Schema**: See [DATABASE_SCHEMA.md](./DATABASE_SCHEMA.md) for database details
- **API Documentation**: See [API_DOCUMENTATION.md](./API_DOCUMENTATION.md) for API reference
- **Reference Implementation**: Review `src/data/providers/sentiment/twitter.py` for code patterns
- **Historical Reference**: See `docs/archive/` for old implementation plans and status documents

## 🔄 Workflow Process

### 1. Before Starting Work

```markdown
1. Read this workflow guide completely
2. Check SENTIMENT_INTEGRATION_CHECKLIST.md for task status
3. Review detailed task in SENTIMENT_INTEGRATION_TODOS.md
4. Check for dependencies (database, API infrastructure, etc.)
5. Review existing similar implementations (e.g., Twitter/X)
6. Update checklist: Mark task as "🔄 In Progress" + add your agent ID
```

**Example Update**:
```markdown
### 2. Reddit Sentiment
**Status**: 🔄 In Progress  
**Agent**: Agent-B  
**Started**: 2024-12-19
```

### 2. During Implementation

#### Implementation Standards

**Follow Existing Patterns**:
- ✅ **File Structure**: Follow the pattern from `src/data/providers/sentiment/twitter.py`
- ✅ **Code Style**: Match existing code style and conventions
- ✅ **Error Handling**: Include proper error handling and logging
- ✅ **Documentation**: Add docstrings to all classes and methods
- ✅ **Type Hints**: Use type hints for all function signatures
- ✅ **Configuration**: Add settings to `src/config/settings.py`
- ✅ **Docker**: Ensure Docker-compose compatibility

**Required Components**:

1. **Provider Class** (e.g., `RedditSentimentProvider`):
   - Main business logic
   - Data fetching
   - Sentiment aggregation
   - Caching support

2. **Client Class** (if needed, e.g., `RedditClient`):
   - API wrapper
   - Authentication
   - Rate limiting
   - Error handling

3. **Data Models** (in `models.py` or separate file):
   - Data structures for the source
   - Sentiment result models
   - Follow pattern from `sentiment/models.py`

4. **Configuration**:
   - Add settings class to `src/config/settings.py`
   - Add environment variables to `env.template`
   - Add to `docker-compose.yml`

5. **Test Script**:
   - Create `scripts/test_[source]_sentiment.py`
   - Basic validation and smoke tests

#### Code Quality Checklist

- [ ] Follows existing code patterns
- [ ] Includes error handling
- [ ] Has logging statements
- [ ] Includes docstrings
- [ ] Uses type hints
- [ ] Handles rate limiting
- [ ] Implements caching
- [ ] Docker-compatible
- [ ] Configuration-driven

### 3. Updating Progress

**Update Frequently**: As you complete subtasks, update the checklist.

**Format for Updates**:
```markdown
### X. [Task Name]
**Status**: 🔄 In Progress  
**Agent**: Your-Agent-ID  
**Last Updated**: YYYY-MM-DD

**Completed**:
- [x] Task 1
- [x] Task 2

**In Progress**:
- [ ] Task 3 (currently working on...)

**Remaining**:
- [ ] Task 4
- [ ] Task 5
```

### 4. When Blocked

If you encounter issues:

1. **Update Status**: Change to `❌ Blocked` in checklist
2. **Document Issue**: Add a note explaining the blocker
3. **Check Dependencies**: Ensure required infrastructure exists
4. **Ask for Help**: Document what you need

**Example**:
```markdown
**Status**: ❌ Blocked  
**Blocker**: Waiting on database schema (#16) for data persistence
**Note**: Can proceed with API integration once schema is ready
```

### 5. Completing a Task

When finishing a task:

1. **Update Checklist**: Mark all subtasks complete
2. **Update Status**: Change to `🔍 Review` or `✅ Complete`
3. **Create Summary**: Document what was implemented
4. **Update Documentation**: Ensure docs are current
5. **Test**: Run test scripts and verify functionality

**Completion Checklist**:
- [ ] All code implemented and tested
- [ ] Documentation updated
- [ ] Checklist updated with completion status
- [ ] Test script works
- [ ] Docker configuration verified
- [ ] Environment variables documented

## 📁 File Locations Reference

### Core Files to Modify/Create

**Configuration**:
- `src/config/settings.py` - Add settings class
- `env.template` - Add environment variables
- `docker-compose.yml` - Add environment variables
- `requirements/base.txt` - Add dependencies

**Implementation**:
- `src/data/providers/sentiment/[source].py` - Main provider class
- `src/data/providers/sentiment/models.py` - Data models (or separate file)
- `src/data/providers/sentiment/__init__.py` - Export new provider

**API** (Phase 3):
- `src/api/routes/sentiment.py` - API endpoints (or create if doesn't exist)
- `src/api/main.py` - Register routes

**Database** (Phase 2):
- `src/data/database/models.py` - Database models
- `migrations/versions/` - Database migrations

**Testing**:
- `scripts/test_[source]_sentiment.py` - Test script

**Documentation**:
- `docs/SENTIMENT_INTEGRATION_CHECKLIST.md` - Update status
- `docs/SENTIMENT_INTEGRATION_TODOS.md` - Update task details

## 🔍 Reference Implementation: Twitter/X

**Study this implementation as a reference**:

- **Provider**: `src/data/providers/sentiment/twitter.py`
- **Models**: `src/data/providers/sentiment/models.py`
- **Analyzer**: `src/data/providers/sentiment/sentiment_analyzer.py`
- **Config**: See `TwitterSettings` in `src/config/settings.py`
- **Strategy Doc**: `docs/TWITTER_SENTIMENT_STRATEGY.md`

**Key Patterns to Follow**:
1. Provider class with `get_sentiment(symbol, hours)` method
2. Client class for API interaction
3. Sentiment analyzer integration
4. Caching implementation
5. Error handling and logging
6. Docker configuration

## 📝 Implementation Template

### Standard Provider Structure

```python
"""
[Source] Sentiment Provider
===========================

Integration with [Source] API for sentiment analysis.
"""

import logging
from typing import Optional, Dict, List
from datetime import datetime, timedelta

from ...config.settings import settings
from .models import SymbolSentiment, SentimentLevel
# Import analyzer if using VADER, or create custom analyzer

logger = logging.getLogger(__name__)

class [Source]Client:
    """
    [Source] API client
    """
    
    def __init__(self):
        self.config = settings.[source]
        # Initialize client
        pass
    
    def is_available(self) -> bool:
        """Check if client is available"""
        pass
    
    def fetch_data(self, symbol: str, **kwargs):
        """Fetch data from API"""
        pass

class [Source]SentimentProvider:
    """
    [Source] sentiment provider
    """
    
    def __init__(self):
        self.client = [Source]Client()
        self.cache = {}
        logger.info(f"[Source]SentimentProvider initialized")
    
    def is_available(self) -> bool:
        """Check if provider is available"""
        return self.client.is_available()
    
    def get_sentiment(self, symbol: str, hours: int = 24) -> Optional[SymbolSentiment]:
        """
        Get sentiment for a symbol
        
        Args:
            symbol: Stock symbol
            hours: Hours of data to analyze
            
        Returns:
            SymbolSentiment object or None
        """
        # 1. Check cache
        # 2. Fetch data from API
        # 3. Analyze sentiment
        # 4. Aggregate results
        # 5. Return SymbolSentiment
        pass
```

### Standard Settings Class

```python
class [Source]Settings(BaseSettings):
    """[Source] API configuration"""
    api_key: Optional[str] = Field(default=None, description="API key")
    # ... other settings
    
    class Config:
        env_prefix = "[SOURCE]_"
```

Then add to main `Settings` class:
```python
[source]: [Source]Settings = [Source]Settings()
```

## 🧪 Testing Requirements

### Test Script Template

Create `scripts/test_[source]_sentiment.py`:

```python
#!/usr/bin/env python3
"""
Test [Source] Sentiment Integration
"""

import sys
from pathlib import Path
import asyncio  # if async

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.data.providers.sentiment import [Source]SentimentProvider
from src.config.settings import settings
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_[source]_sentiment():
    """Test [Source] sentiment provider"""
    print("Testing [Source] Sentiment Provider...")
    
    # Check configuration
    provider = [Source]SentimentProvider()
    
    if not provider.is_available():
        print("❌ Provider not available - check configuration")
        return False
    
    # Test sentiment retrieval
    sentiment = provider.get_sentiment("SPY", hours=24)
    
    if sentiment:
        print(f"✅ Sentiment: {sentiment.weighted_sentiment:.3f}")
        return True
    
    return False

if __name__ == "__main__":
    success = test_[source]_sentiment()
    sys.exit(0 if success else 1)
```

## 🔗 Integration Points

### Sentiment Aggregator Integration

Once your provider is ready, it needs to integrate with the sentiment aggregator (task #13).

**Required Interface**:
- `get_sentiment(symbol: str, hours: int) -> Optional[SymbolSentiment]`
- `is_available() -> bool`

The aggregator will call your provider's `get_sentiment()` method.

### Strategy Integration

Sentiment will eventually be used in strategies (task #15):

1. Strategies receive sentiment data
2. Sentiment affects signal confidence
3. Sentiment can filter trades (e.g., no trades if sentiment too negative)

## 📊 Status Update Examples

### Starting Work
```markdown
### 2. Reddit Sentiment
**Status**: 🔄 In Progress  
**Agent**: Agent-B  
**Started**: 2024-12-19

**Progress**:
- [x] Install PRAW library
- [x] Create file structure
- [ ] Implement Reddit client
```

### Making Progress
```markdown
**Status**: 🔄 In Progress  
**Agent**: Agent-B  
**Last Updated**: 2024-12-19

**Completed**:
- [x] Install PRAW library
- [x] Create `src/data/providers/sentiment/reddit.py`
- [x] Implement Reddit API client
- [x] Add authentication

**In Progress**:
- [ ] Implement sentiment analysis

**Remaining**:
- [ ] Add database models
- [ ] Create API endpoints
- [ ] Write tests
```

### Completing Task
```markdown
**Status**: ✅ Complete  
**Agent**: Agent-B  
**Completed**: 2024-12-20

**All tasks completed**:
- [x] All implementation tasks
- [x] Database integration
- [x] API endpoints
- [x] Testing complete
- [x] Documentation updated

**Files Created**:
- `src/data/providers/sentiment/reddit.py`
- `scripts/test_reddit_sentiment.py`
- Database migrations

**Ready for**: Integration with sentiment aggregator (#13)
```

## ⚠️ Common Pitfalls

### Don't:
- ❌ Start work without checking checklist for current status
- ❌ Modify files without understanding existing patterns
- ❌ Forget to update the checklist as you progress
- ❌ Skip error handling
- ❌ Ignore rate limiting
- ❌ Hardcode configuration values
- ❌ Forget Docker compatibility

### Do:
- ✅ Check checklist before starting
- ✅ Follow existing code patterns
- ✅ Update progress frequently
- ✅ Include comprehensive error handling
- ✅ Implement rate limiting
- ✅ Use configuration files
- ✅ Test with Docker
- ✅ Document your work

## 🆘 Getting Help

If you need help:

1. **Check Documentation**:
   - This workflow guide
   - Strategy documents
   - Reference implementation (Twitter/X)

2. **Review Existing Code**:
   - Look at Twitter/X implementation
   - Check similar providers
   - Review database models

3. **Check Dependencies**:
   - Ensure required infrastructure exists
   - Verify database schema if needed
   - Check API configuration

4. **Document Issues**:
   - Update checklist with blocker status
   - Note what you need
   - Describe the issue clearly

## 📋 Quick Start Checklist

Before starting any task, verify:

- [ ] Read this workflow guide
- [ ] Checked master checklist for task status
- [ ] Reviewed detailed task in TODOS document
- [ ] Reviewed reference implementation (Twitter/X)
- [ ] Understood file structure and patterns
- [ ] Updated checklist: Status → "🔄 In Progress"
- [ ] Added your agent identifier
- [ ] Noted start date

## 🎯 Success Criteria

Your implementation is complete when:

- [ ] Provider class implemented and working
- [ ] Can fetch data from source API
- [ ] Sentiment analysis working
- [ ] Returns `SymbolSentiment` objects
- [ ] Configuration added to settings
- [ ] Docker-compatible
- [ ] Test script passes
- [ ] Documentation updated
- [ ] Checklist marked complete

## 🔄 Next Steps After Completion

Once your provider is complete:

1. **Update Checklist**: Mark as ✅ Complete
2. **Integration**: Provider ready for sentiment aggregator (#13)
3. **Review**: Code ready for review/testing
4. **Documentation**: Update relevant docs
5. **Move On**: Pick next pending task

---

**Note**: All sentiment integration work is complete. See [SENTIMENT_FEATURES_COMPLETE.md](./SENTIMENT_FEATURES_COMPLETE.md) for complete documentation. Historical task tracking documents are in `docs/archive/`.

**Good luck! 🚀**

