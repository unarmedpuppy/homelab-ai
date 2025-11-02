# 🚀 Agent Start Prompt - Copy/Paste Ready

Copy and paste this prompt to new agents getting started on sentiment integration tasks:

---

## 📋 Agent Assignment: Sentiment Data Integration

You are assigned to work on sentiment data source integrations for the trading bot. Follow these steps to get started:

### ⭐ STEP 1: Read the Workflow Guide (REQUIRED)

**Read this first**: `docs/AGENT_WORKFLOW_SENTIMENT.md`

This guide contains everything you need:
- Complete workflow instructions
- Code patterns and templates  
- File locations and structure
- Testing requirements
- Status update procedures
- Common pitfalls to avoid

**DO NOT skip this step!** It will save you time and ensure consistency.

### ⭐ STEP 2: Check the Master Checklist

**Review**: `docs/SENTIMENT_INTEGRATION_CHECKLIST.md`

This is the **source of truth** for task status. 

1. Find tasks marked as `⏳ Pending`
2. Check priority levels (High priority first)
3. Verify dependencies are met
4. Select a task to work on

### ⭐ STEP 3: Claim Your Task

Once you've selected a task:

1. **Update the checklist**:
   - Change status from `⏳ Pending` to `🔄 In Progress`
   - Add your agent identifier to the "Agent" column
   - Add start date

2. **Read task details**: 
   - Check `docs/SENTIMENT_INTEGRATION_TODOS.md` for detailed task breakdown
   - Review the specific section for your task number

### ⭐ STEP 4: Study the Reference Implementation

**Study**: `src/data/providers/sentiment/twitter.py`

This is the completed Twitter/X implementation. Use it as a reference for:
- Code structure and patterns
- Error handling approach
- Configuration integration
- Caching implementation
- Docker compatibility

**Also review**: `docs/TWITTER_SENTIMENT_STRATEGY.md` for strategy details

### ⭐ STEP 5: Start Implementation

Follow the workflow guide and implement your provider:

**Required Components**:
1. Provider class in `src/data/providers/sentiment/[source].py`
2. Configuration added to `src/config/settings.py`
3. Environment variables in `env.template` and `docker-compose.yml`
4. Dependencies added to `requirements/base.txt`
5. Test script in `scripts/test_[source]_sentiment.py`

**Key Requirements**:
- Follow existing code patterns (match Twitter/X style)
- Include error handling and logging
- Implement rate limiting if needed
- Add caching (5-15 min TTL)
- Docker-compatible
- Configuration-driven (no hardcoded values)

### ⭐ STEP 6: Update Progress Frequently

As you work, update the checklist:
- Mark completed subtasks: `[x]`
- Update "Last Updated" date
- Note any blockers or issues
- Document files created/modified

### ⭐ STEP 7: Complete Your Task

When finished:
1. All code implemented and tested
2. Test script passes
3. Docker configuration verified
4. Documentation updated
5. **Update checklist**: Status → `✅ Complete`
6. Add completion date
7. List files created/modified

---

## 📁 Quick File Reference

- **Workflow Guide**: `docs/AGENT_WORKFLOW_SENTIMENT.md` ⭐ READ FIRST
- **Master Checklist**: `docs/SENTIMENT_INTEGRATION_CHECKLIST.md` ⭐ SOURCE OF TRUTH
- **Task Details**: `docs/SENTIMENT_INTEGRATION_TODOS.md`
- **Reference Code**: `src/data/providers/sentiment/twitter.py`
- **Settings File**: `src/config/settings.py`
- **Models**: `src/data/providers/sentiment/models.py`

## 🎯 Success Checklist

Before marking complete, verify:
- [ ] Provider class works correctly
- [ ] Can fetch data from API
- [ ] Sentiment analysis functional
- [ ] Returns `SymbolSentiment` objects
- [ ] Configuration added and working
- [ ] Docker-compatible
- [ ] Test script passes
- [ ] Checklist updated
- [ ] Documentation current

## 🆘 Need Help?

1. Re-read the workflow guide
2. Study Twitter/X reference implementation more carefully
3. Check existing database models/API patterns
4. Update checklist with `❌ Blocked` status and document the issue

---

**Ready to start?** 
1. Read `docs/AGENT_WORKFLOW_SENTIMENT.md` now
2. Check `docs/SENTIMENT_INTEGRATION_CHECKLIST.md` for available tasks
3. Claim a task and begin!

Good luck! 🚀

