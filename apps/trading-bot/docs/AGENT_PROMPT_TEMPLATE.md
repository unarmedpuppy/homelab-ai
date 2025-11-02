# Agent Prompt Template - Sentiment Integration Tasks

## Quick Start Prompt for Agents

Copy and customize this prompt to assign sentiment integration tasks to agents:

---

## 🎯 Task Assignment Prompt

```
You are working on the trading bot's sentiment data integration system. Your task is to implement integration for [DATA_SOURCE_NAME] following the established patterns and architecture.

### 📋 Your Task

**Task Number**: #[TASK_NUMBER] - [DATA_SOURCE_NAME]  
**Priority**: [High/Medium/Low]  
**Estimated Time**: [X-Y hours]  
**Library to Use**: [LIBRARY_NAME]

### 📚 Required Reading (IN ORDER)

1. **FIRST**: Read [AGENT_WORKFLOW_SENTIMENT.md](./docs/AGENT_WORKFLOW_SENTIMENT.md) - This is your primary guide
2. **SECOND**: Review [SENTIMENT_INTEGRATION_CHECKLIST.md](./docs/SENTIMENT_INTEGRATION_CHECKLIST.md) - Check current status
3. **THIRD**: Read task details in [SENTIMENT_INTEGRATION_TODOS.md](./docs/SENTIMENT_INTEGRATION_TODOS.md) - Section #[TASK_NUMBER]
4. **REFERENCE**: Study Twitter/X implementation as a reference pattern:
   - `src/data/providers/sentiment/twitter.py`
   - `docs/TWITTER_SENTIMENT_STRATEGY.md`

### ✅ Before Starting

1. Check that the task is marked as "⏳ Pending" in the checklist
2. Update checklist: Status → "🔄 In Progress"
3. Add your agent identifier to the "Agent" column
4. Note the start date

### 🎯 What You Need to Implement

Following the workflow guide and reference implementation, create:

1. **Provider Class**: `src/data/providers/sentiment/[source].py`
   - API client for [DATA_SOURCE]
   - Sentiment analysis integration
   - Data fetching and aggregation
   - Caching support

2. **Configuration**: 
   - Add settings to `src/config/settings.py`
   - Add env vars to `env.template`
   - Add to `docker-compose.yml`
   - Add library to `requirements/base.txt`

3. **Data Models** (if needed):
   - Extend `src/data/providers/sentiment/models.py`
   - Or create new model file if needed

4. **Test Script**: `scripts/test_[source]_sentiment.py`

### 📝 Implementation Requirements

- Follow existing code patterns (match Twitter/X implementation style)
- Include comprehensive error handling
- Implement rate limiting (if API has limits)
- Add caching (5-15 minute TTL)
- Use configuration from settings (no hardcoded values)
- Docker-compatible
- Add logging statements
- Include docstrings
- Use type hints

### 🔄 Progress Updates

Update the checklist frequently as you complete tasks:
- Mark completed subtasks with [x]
- Update "Last Updated" date
- Note any blockers or issues

### ✅ Completion Criteria

Your task is complete when:
- [ ] Provider class implemented and tested
- [ ] Can fetch and analyze sentiment data
- [ ] Returns `SymbolSentiment` objects
- [ ] Configuration added and working
- [ ] Docker-compatible
- [ ] Test script passes
- [ ] Checklist updated to "✅ Complete"
- [ ] Documentation updated

### 🆘 If You Get Stuck

1. Review the Agent Workflow Guide troubleshooting section
2. Study the Twitter/X reference implementation more carefully
3. Check existing database models and API patterns
4. Update checklist with "❌ Blocked" status and note the issue

### 📁 Key Files Location

- Checklist: `docs/SENTIMENT_INTEGRATION_CHECKLIST.md`
- Workflow Guide: `docs/AGENT_WORKFLOW_SENTIMENT.md`
- Task Details: `docs/SENTIMENT_INTEGRATION_TODOS.md`
- Reference: `src/data/providers/sentiment/twitter.py`
- Settings: `src/config/settings.py`

Good luck! Follow the workflow guide closely and update your progress frequently.
```

---

## Example: Reddit Sentiment Task

```
You are working on the trading bot's sentiment data integration system. Your task is to implement Reddit sentiment integration following the established patterns.

### 📋 Your Task

**Task Number**: #2 - Reddit Sentiment  
**Priority**: High  
**Estimated Time**: 8-12 hours  
**Library to Use**: `praw` (Python Reddit API Wrapper)

### 📚 Required Reading (IN ORDER)

1. **FIRST**: Read docs/AGENT_WORKFLOW_SENTIMENT.md - Your primary guide
2. **SECOND**: Review docs/SENTIMENT_INTEGRATION_CHECKLIST.md - Check status
3. **THIRD**: Read task details in docs/SENTIMENT_INTEGRATION_TODOS.md - Section #2
4. **REFERENCE**: Study Twitter/X implementation (twitter.py) as reference

### ✅ Before Starting

Update checklist: Status → "🔄 In Progress", add your agent ID

### 🎯 Implementation

Create RedditSentimentProvider following Twitter/X pattern, with Reddit API integration for monitoring subreddits like r/wallstreetbets, r/stocks, r/investing for stock mentions and sentiment.

Follow all requirements in the workflow guide.

Good luck!
```

---

## Quick Reference Card

**For agents to keep handy:**

```
START HERE:
1. Read: docs/AGENT_WORKFLOW_SENTIMENT.md
2. Check: docs/SENTIMENT_INTEGRATION_CHECKLIST.md
3. Study: src/data/providers/sentiment/twitter.py (reference)

KEY FILES:
- Checklist: docs/SENTIMENT_INTEGRATION_CHECKLIST.md
- Workflow: docs/AGENT_WORKFLOW_SENTIMENT.md
- Settings: src/config/settings.py
- Models: src/data/providers/sentiment/models.py

UPDATE CHECKLIST:
- Start: Status → "🔄 In Progress" + Agent ID
- Progress: Update checkboxes + dates
- Complete: Status → "✅ Complete"
- Blocked: Status → "❌ Blocked" + reason

PATTERNS:
- Follow twitter.py structure
- Use SymbolSentiment return type
- Add caching (5-15 min TTL)
- Error handling + logging
- Docker-compatible
```

---

