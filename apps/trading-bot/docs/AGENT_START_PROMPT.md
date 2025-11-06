# 🚀 Agent Start Prompt - Complete Guide

**Purpose**: Comprehensive guide for agents working on the trading bot project. This document consolidates all agent guidance and includes critical review processes.

---

## 📋 How to Use This Guide

When assigned a task, you will be provided with:
- **Task/Feature Context**: What you're working on (e.g., "Sentiment Integration", "Backtesting Engine", "Real-time Data Feeds")
- **Target Documentation**: Which documentation to reference (e.g., `docs/SENTIMENT_FEATURES_COMPLETE.md`, `IMPLEMENTATION_ROADMAP.md`)
- **Task List/Tracking Doc**: Where to track your progress (if applicable)

**Replace placeholders like `[FEATURE]` and `[TARGET_DOC]` with your specific context.**

---

## 📋 Current Project Status

### Overview

Refer to `IMPLEMENTATION_ROADMAP.md` for overall project status and priorities. Key areas include:
- ✅ Sentiment Integration System (Complete - see `docs/SENTIMENT_FEATURES_COMPLETE.md`)
- 🔄 Real-time data feeds (in progress)
- ⏳ Backtesting engine
- ⏳ Advanced strategies
- ⏳ Risk management enhancements

**Note**: When you receive your task assignment, you'll be told which specific documentation to review for context.

---

## 🎯 For New Agents: Getting Started

### ⭐ STEP 1: Understand What's Already Built (REQUIRED)

**Read First**: `[TARGET_DOC]` (provided in your task assignment)

Your target documentation will contain:
- Feature/component overview
- System architecture and design
- API documentation (if applicable)
- Configuration guide
- Database schema (if applicable)
- Code structure and patterns
- How to extend or integrate with the system

**DO NOT skip this step!** Understanding what exists prevents duplication and ensures proper integration.

**Common Documentation References**:
- `docs/SENTIMENT_FEATURES_COMPLETE.md` - Sentiment integration features
- `IMPLEMENTATION_ROADMAP.md` - Overall project status and priorities
- `docs/DATABASE_SCHEMA.md` - Database schema documentation
- `docs/API_DOCUMENTATION.md` - API endpoint reference
- Feature-specific docs in `docs/` directory

### ⭐ STEP 2: Review Project Structure

**Key Documentation Files**:
- `[TARGET_DOC]` - Your main feature documentation (provided in task)
- `IMPLEMENTATION_ROADMAP.md` - Overall project status
- `docs/DATABASE_SCHEMA.md` - Database schema details
- `docs/API_DOCUMENTATION.md` - API endpoint reference
- `docs/archive/` - Historical implementation documents

**Code Reference**:
- Check `[TARGET_DOC]` for specific reference implementations
- `src/config/settings.py` - Configuration management
- Feature-specific models/routes (see your target doc for locations)

### ⭐ STEP 3: If Adding New Features

**Review your target documentation** for extension guidelines:

1. **Follow Established Patterns**:
   - Study reference implementations mentioned in your target doc
   - Look for existing similar features/components
   - Follow the same architectural patterns
   - Use the same libraries/frameworks where appropriate

2. **Integration Points**:
   - Configuration management (`src/config/settings.py`)
   - Database models (if applicable)
   - API endpoints (if applicable)
   - Testing patterns
   - Documentation structure

3. **Best Practices** (apply as relevant):
   - Thread-safe initialization (if using singletons)
   - Caching strategies (if performance-critical)
   - Database persistence (if data storage needed)
   - Input validation
   - Structured error logging with context
   - Configuration-driven (no hardcoded values)

### ⭐ STEP 4: Code Implementation Requirements

**All code must follow these standards**:

1. **Code Patterns**:
   - Follow patterns from reference implementations (see `[TARGET_DOC]`)
   - Use type hints throughout
   - Include comprehensive docstrings
   - Use structured logging with context

2. **Error Handling**:
   - Specific exception handling (don't catch generic `Exception`)
   - Structured logging with `extra` parameter for context
   - Graceful degradation (don't fail entire operation on single error)

3. **Thread Safety**:
   - Use locks for singleton initialization
   - Use context managers for database sessions
   - Avoid global mutable state

4. **Configuration**:
   - No hardcoded values
   - Use Pydantic `BaseSettings`
   - Environment variable driven
   - Docker-compatible

5. **Testing**:
   - Create test script in `scripts/`
   - Test happy path and error scenarios
   - Verify database persistence
   - Test thread safety (if applicable)

---

## 🔍 Critical Review Process (MANDATORY)

### After Completing Any Work

**You MUST perform a critical architectural review** of what you've built before marking work complete. Act as if you are a **high-level principal architect** reviewing the codebase.

### Review Checklist

Use this checklist to systematically review your work:

#### 🔴 CRITICAL - Must Fix Immediately

- [ ] **Thread Safety**: Are all global instances/singletons thread-safe?
- [ ] **Resource Leaks**: Are database connections, file handles, network connections properly closed?
- [ ] **Transaction Atomicity**: Are multi-step database operations atomic (all succeed or all fail)?
- [ ] **Error Handling**: Is error handling specific (not generic `except Exception`)?
- [ ] **Data Integrity**: Can partial failures leave data in inconsistent state?

#### 🟡 HIGH PRIORITY - Should Fix Soon

- [ ] **Caching Consistency**: Are all providers using the same caching mechanism?
- [ ] **Input Validation**: Are all user inputs validated before processing?
- [ ] **Rate Limiting**: Is rate limiting implemented and enforced?
- [ ] **Logging Quality**: Do error logs include sufficient context for debugging?
- [ ] **Performance**: Are database queries optimized (indexes, no N+1 queries)?

#### 🟢 MEDIUM PRIORITY - Good to Fix

- [ ] **Code Duplication**: Can repeated code be extracted into utilities?
- [ ] **Documentation**: Are complex functions/algorithms documented?
- [ ] **Test Coverage**: Are edge cases and error scenarios tested?
- [ ] **Configuration**: Are magic numbers/strings extracted to configuration?

#### 🔵 LOW PRIORITY - Nice to Have

- [ ] **Code Style**: Does code follow PEP 8 and project conventions?
- [ ] **Type Hints**: Are all function signatures fully type-hinted?
- [ ] **Async/Await**: Could blocking operations be made async?
- [ ] **Monitoring**: Are metrics/monitoring hooks in place?

### Review Process Steps

1. **Run Tests**: Execute all relevant test scripts
2. **Static Analysis**: Review code for patterns from checklist above
3. **Trace Data Flow**: Trace how data flows through your code (API → Provider → DB → Response)
4. **Concurrency Check**: Consider what happens with concurrent requests
5. **Error Scenarios**: Think through failure modes (API down, DB timeout, network error)
6. **Security Review**: Check for SQL injection, XSS, auth bypass risks

### Creating an Issue Checklist

**When you find issues during review:**

1. **Create a Checklist Document**: `docs/[FEATURE]_REVIEW_CHECKLIST.md`

2. **Structure the Checklist**:
   ```markdown
   # [Feature Name] - Architectural Review Checklist
   
   **Review Date**: [Date]
   **Reviewer**: [Agent Name]
   **Status**: Issues Identified / All Resolved
   
   ## 🔴 CRITICAL ISSUES
   
   ### 1. [Issue Title]
   **Location**: `file.py:line`
   **Problem**: [Description]
   **Impact**: [What could go wrong]
   **Fix**: [ ] Implemented / [ ] Pending
   
   ## 🟡 HIGH PRIORITY
   [Same format]
   
   ## 🟢 MEDIUM PRIORITY
   [Same format]
   ```

3. **Prioritize**: Sort issues by severity (Critical → High → Medium → Low)

4. **Estimate**: Note time/complexity estimates for each fix

### Resolving Issues

**Systematic Resolution Process**:

1. **Start with Critical**: Fix all critical issues first, test, then move to high priority
2. **One at a Time**: Fix one issue, test, commit, then move to next
3. **Update Checklist**: Mark each item as `[x] Implemented` when complete
4. **Re-test**: After fixing each category, re-run tests and review again
5. **Document Fixes**: Create a summary document when all issues resolved

**Example Fix Summary Document**:
```markdown
# [Feature Name] - Fixes Applied Summary

**Date**: [Date]
**Status**: ✅ All Critical/High Priority Issues Fixed

## ✅ Fixed Issues

### 1. Thread Safety (CRITICAL #1)
**Problem**: [Description]
**Solution**: [What was changed]
**Files Changed**: [List files]
**Impact**: [Result]

[Continue for each fixed issue]
```

### Continuous Improvement

**After resolving all issues from your review**:

1. ✅ **Document What Was Fixed**: Create summary document (e.g., `docs/[FEATURE]_FIXES_SUMMARY.md`)
2. ✅ **Update Main Docs**: Update feature documentation if architecture changed
3. ✅ **Share Learnings**: Note patterns to avoid in future (add to workflow guide if recurring)
4. ✅ **Re-review**: After fixes, do a quick review to ensure no regressions

### Documentation Cleanup After Fixes

**Once all fixes are complete**:
- Archive fix summary to `docs/archive/` (after consolidating key learnings into core docs)
- Update core documentation with any architectural changes or important patterns
- Remove any temporary docs created during the review/fix process

---

## 📝 Workflow for New Tasks

### If Assigned a New Task

**Your task assignment will specify**:
- Feature/component name: `[FEATURE]`
- Target documentation: `[TARGET_DOC]`
- Task tracking doc (if applicable): `[TASK_DOC]`

1. **Read Required Docs**:
   - `[TARGET_DOC]` - Main feature/component documentation
   - `IMPLEMENTATION_ROADMAP.md` - Overall project context
   - Related documentation referenced in target doc
   - Reference implementations mentioned

2. **Study Existing Patterns**:
   - **Search the codebase** for similar implementations
   - Review reference code mentioned in `[TARGET_DOC]`
   - Examine how similar features were built
   - Note shared patterns, utilities, and practices

3. **Plan Your Approach**:
   - Break task into sub-tasks
   - Identify dependencies
   - Estimate time
   - Note potential challenges
   - **Base approach on existing patterns** - don't reinvent
   - **Create initial documentation** (e.g., `docs/[FEATURE]_IMPLEMENTATION_PLAN.md`) to track approach
   - **Document any deviations** from existing patterns and why
   - **Update task tracking doc** (if provided) - mark status as "🔄 In Progress"

4. **Document As You Work**:
   - **Create progress documents**: `docs/[FEATURE]_PROGRESS.md` or update your plan doc
   - **Note decisions**: Why you chose certain approaches, alternatives considered
   - **Document challenges**: Issues encountered and how you resolved them
   - **Track changes**: List files created/modified as you go
   - **Screenshot/Examples**: Capture test outputs, API responses if helpful

4. **Implement Following Patterns**:
   - **Follow existing patterns** from reference implementations and codebase search
   - Use shared utilities, helpers, and existing code when possible
   - Integrate with existing systems (config, logging, database patterns)
   - Follow code quality standards
   - Add comprehensive error handling (matching existing patterns)
   - Include logging (using existing logging patterns)
   - **If you need to deviate**: Document why in progress doc, but prefer following existing patterns
   - **Update progress doc** as you complete each component
   - **Ask questions if genuinely stuck**, but continue with reasonable decisions

5. **Test Thoroughly**:
   - Happy path scenarios
   - Error scenarios
   - Edge cases
   - Concurrent access (if applicable)
   - **Document test results** in progress doc

6. **Critical Review** (MANDATORY):
   - Perform architectural review checklist
   - Create issue checklist if problems found (e.g., `docs/[FEATURE]_REVIEW_CHECKLIST.md`)
   - Fix issues systematically
   - Document fixes in review checklist or create fix summary

7. **Complete Task & Clean Up Documentation** (MANDATORY):
   - ✅ **Deploy Changes** (MANDATORY):
     - Follow the deployment workflow (see "🚀 Deployment Workflow" section)
     - Commit and push changes to git
     - Pull changes on server
     - Rebuild Docker image with --no-cache
     - Restart container
     - Verify deployment works correctly
   
   - ✅ **Consolidate Documentation**:
     - Review all docs created during implementation
     - Extract key information into core documentation:
       - Update `[TARGET_DOC]` with final implementation details
       - Update `docs/API_DOCUMENTATION.md` (if API changes)
       - Update `docs/DATABASE_SCHEMA.md` (if schema changes)
       - Update `IMPLEMENTATION_ROADMAP.md` (if feature status changes)
       - Update any other relevant core docs
     - Ensure core docs reflect final implementation (not just plan)
     - **Update task tracking doc** (if provided) - mark as "✅ Complete"
   
   - ✅ **Archive Work-in-Progress Docs**:
     - Move implementation plans to `docs/archive/`
     - Move progress tracking docs to `docs/archive/`
     - Move review checklists to `docs/archive/` (after fixes applied)
     - Keep only final fix summaries if they contain important patterns/lessons
   
   - ✅ **Update Archive README**:
     - Update `docs/archive/README.md` to list new archived docs
     - Add brief description of what was archived and why
   
   - ✅ **Verify Core Documentation**:
     - Ensure core docs are complete and accurate
     - Remove outdated information
     - Add any important learnings/patterns to relevant sections
     - Cross-reference archived docs where appropriate
   
   - ✅ **Final Checklist**:
     - Verify all tests pass
     - Check code quality
     - Ensure Docker compatibility
     - **Deployment completed and verified**
     - Core documentation updated and accurate
     - Work-in-progress docs archived
     - Archive README updated

---

## 📁 Quick Reference

### Essential Files (Use Your Task Context)

- **Target Documentation**: `[TARGET_DOC]` - Your main reference (provided in task)
- **Roadmap**: `IMPLEMENTATION_ROADMAP.md` - Overall project status
- **Database Schema**: `docs/DATABASE_SCHEMA.md` - Database structure
- **API Docs**: `docs/API_DOCUMENTATION.md` - API endpoints
- **Settings**: `src/config/settings.py` - Configuration management
- **Reference Code**: Check your `[TARGET_DOC]` for specific reference implementations

### Key Directories

- `src/` - Source code (structure depends on feature)
- `src/api/routes/` - API endpoint definitions
- `src/data/` - Data providers and database
- `src/core/` - Core business logic
- `scripts/` - Test scripts and utilities
- `docs/` - Documentation
- `docs/archive/` - Historical documentation

### Common Patterns (Apply as Relevant)

**Thread-Safe Singleton** (if needed):
```python
_instance: Optional[Class] = None
_lock = threading.Lock()

def get_instance():
    global _instance
    if _instance is None:
        with _lock:
            if _instance is None:
                _instance = Class()
    return _instance
```

**Database Operations (Context Manager)**:
```python
with repository._get_session() as session:
    # Auto-commit on success, rollback on error
    # Auto-close session
```

**Input Validation**:
```python
from ...validators import validate_symbol, validate_hours
symbol = validate_symbol(symbol)
hours = validate_hours(hours, min_hours=1, max_hours=168)
```

**Check your `[TARGET_DOC]` for feature-specific patterns and examples.**

---

## 🆘 Getting Help & Decision Making

### When You're Uncertain: Ask Clarifying Questions (But Keep Moving Forward)

**Priority: Agency First**

1. **Make a Reasonable Decision**: If you encounter ambiguity, make the most reasonable decision based on:
   - Existing patterns in the codebase
   - Similar implementations you've reviewed
   - Best practices from the target documentation
   - Common sense and consistency

2. **Continue With Agency**: Don't stop progress waiting for clarification. Choose an approach and proceed.

3. **Ask Questions Alongside Progress**: 
   - Document your decision and reasoning in your progress doc
   - Note what you're uncertain about
   - Ask clarifying questions, but continue working
   - Example: "I chose approach X because it matches pattern Y in [file]. Please confirm if this aligns with expectations."

4. **When to Pause vs. Continue**:
   - **Continue**: Minor implementation details, naming conventions, optional features
   - **Ask & Continue**: Architectural decisions where you have a reasonable guess
   - **Ask & Wait**: Major architectural changes that contradict existing patterns

### Follow Existing Patterns - Don't Reinvent the Wheel

**Critical Principle**: Reference and follow existing patterns in the codebase.

1. **Search for Similar Code**:
   - Look for similar features/components already implemented
   - Search the codebase for patterns you're trying to implement
   - Check how similar problems were solved before

2. **Use Shared Patterns**:
   - Follow established architectural patterns (don't create new ones without good reason)
   - Use existing utilities, helpers, and shared code
   - Leverage existing configuration patterns
   - Reuse database patterns and repository structures

3. **Avoid Unnecessary Innovation**:
   - ❌ **Don't**: Create a new pattern just because you prefer it
   - ✅ **Do**: Follow existing patterns even if slightly different from what you'd choose
   - ❌ **Don't**: Introduce new libraries/frameworks without checking if similar solutions exist
   - ✅ **Do**: Use existing dependencies and patterns when possible

4. **When Deviation is OK**:
   - Clear improvement with minimal disruption
   - Existing pattern has known issues you're fixing
   - New requirement genuinely doesn't fit existing patterns (rare)
   - Document why you deviated in your progress notes

5. **Integration Over Isolation**:
   - Integrate with existing systems, not alongside them
   - Use shared configuration, logging, error handling
   - Follow naming conventions and structure
   - Make it feel like part of the existing codebase

### If You're Stuck

1. **Review Existing Code First**:
   - Search codebase for similar implementations
   - Study reference implementations from `[TARGET_DOC]`
   - Look at how other features handle similar challenges
   - Examine test scripts for usage patterns

2. **Check Documentation**:
   - Re-read relevant docs, especially `[TARGET_DOC]`
   - Review `IMPLEMENTATION_ROADMAP.md` for context
   - Check `docs/archive/` for past implementation examples

3. **Review Fix Summaries**: 
   - Check `docs/archive/` for past issue resolutions
   - Learn from previous architectural decisions

### Common Issues

- **Import Errors**: Check `sys.path` setup, ensure running from project root or Docker
- **Database Errors**: Verify `DATABASE_URL`, check migrations applied
- **Cache Issues**: Verify Redis running (if using Redis), check TTL settings
- **Rate Limits**: Check rate limit configuration, verify API keys valid
- **Pattern Mismatch**: Search codebase for how similar features were implemented

---

## ✅ Success Checklist

Before marking any work complete, verify:

### Code Quality
- [ ] Code implements all requirements
- [ ] Follows existing patterns and conventions
- [ ] Includes comprehensive error handling
- [ ] Has logging with sufficient context
- [ ] Thread-safe (if applicable)
- [ ] Database operations use context managers
- [ ] Input validation implemented
- [ ] Test script passes
- [ ] Docker-compatible
- [ ] Configuration-driven (no hardcoded values)

### Review & Fixes
- [ ] **Critical review completed**
- [ ] **Review checklist created** (if issues found)
- [ ] **All critical/high priority issues fixed**
- [ ] **Fixes documented** (fix summary created)

### Deployment (MANDATORY)
- [ ] **Changes committed to git**
- [ ] **Changes pushed to remote repository**
- [ ] **Changes pulled on server**
- [ ] **Docker image rebuilt with --no-cache**
- [ ] **Container restarted**
- [ ] **Deployment verified** (tested in browser/API)

### Documentation & Cleanup
- [ ] **Progress documented** (implementation plan, progress notes, decisions)
- [ ] **Core documentation updated**:
  - [ ] Target documentation updated (`[TARGET_DOC]`)
  - [ ] Task tracking doc updated (if provided)
  - [ ] API documentation updated (if API changes)
  - [ ] Database schema docs updated (if schema changes)
  - [ ] Roadmap updated (if feature status changed)
- [ ] **Work-in-progress docs archived**:
  - [ ] Implementation plans moved to `docs/archive/`
  - [ ] Progress tracking docs moved to `docs/archive/`
  - [ ] Review checklists moved to `docs/archive/` (after fixes applied)
- [ ] **Archive README updated** (new archived docs listed)
- [ ] **Temporary docs removed** (test docs, scratch files, etc.)

---

## 📚 Documentation Practices

### During Development

**Create and maintain these documents as you work**:

1. **Implementation Plan** (`docs/[FEATURE]_IMPLEMENTATION_PLAN.md`):
   - Initial approach and design decisions
   - Task breakdown
   - Dependencies and challenges
   - Can be created at start or evolved as you work

2. **Progress Tracking** (`docs/[FEATURE]_PROGRESS.md`):
   - Update regularly as you complete components
   - Track decisions made and why
   - Note issues encountered and resolutions
   - List files created/modified

3. **Review Checklist** (`docs/[FEATURE]_REVIEW_CHECKLIST.md`):
   - Created during critical review phase
   - Documents all issues found (critical → low priority)
   - Track fix status for each item

4. **Fix Summary** (`docs/[FEATURE]_FIXES_SUMMARY.md`):
   - Created after all fixes applied
   - Documents what was fixed and how
   - Includes impact and lessons learned

### After Completion

**Documentation cleanup is MANDATORY**:

1. **Consolidate into Core Docs**:
   - Extract final implementation details into feature documentation
   - Update API docs with new endpoints
   - Update database schema docs if schema changed
   - Add important patterns/learnings to relevant sections
   - Update roadmap to reflect completion

2. **Archive Work-in-Progress Docs**:
   - Move to `docs/archive/`:
     - Implementation plans
     - Progress tracking docs
     - Review checklists (after fixes applied)
     - Fix summaries (keep if valuable patterns, archive after extracting learnings)
   - These provide historical context but shouldn't clutter main docs

3. **Update Archive README**:
   - Add entries for new archived docs
   - Brief description of what each contains
   - Date archived

4. **Verify Core Docs**:
   - Core docs should reflect final state (not plans)
   - Remove outdated information
   - Ensure cross-references are correct
   - Add links to archived docs where historical context is helpful

### Documentation Template Examples

**Implementation Plan Template**:
```markdown
# [Feature Name] - Implementation Plan

**Status**: Planning / In Progress / Complete
**Started**: [Date]
**Completed**: [Date]

## Overview
[Brief description]

## Approach
[Design decisions, approach chosen]

## Tasks
- [ ] Task 1
- [ ] Task 2

## Decisions Made
- Decision 1: Why this approach
- Decision 2: Alternatives considered

## Challenges & Solutions
- Challenge 1: How resolved

## Files Created/Modified
- `path/to/file.py` - Description
```

**Progress Tracking Template**:
```markdown
# [Feature Name] - Progress Tracking

**Last Updated**: [Date]

## Completed
- ✅ Component 1 (Date)
- ✅ Component 2 (Date)

## In Progress
- 🔄 Component 3

## Decisions
- [Date]: Decision made - reason

## Issues
- [Date]: Issue encountered - resolution

## Next Steps
- [ ] Next task
```

---

## 🚀 Deployment Workflow (MANDATORY)

**After completing any code changes that affect the running application, you MUST deploy to the server using this workflow.**

### Deployment Steps

1. **Stage and Commit Changes**:
   ```bash
   cd /Users/joshuajenquist/repos/personal/home-server
   git add apps/trading-bot/[modified_files]
   git commit -m "Descriptive commit message"
   ```

2. **Push to Remote Repository**:
   ```bash
   git push origin main
   ```

3. **Pull Changes on Server**:
   ```bash
   bash scripts/connect-server.sh "cd ~/server && git pull origin main"
   ```

4. **Rebuild Docker Image** (with --no-cache to ensure fresh build):
   ```bash
   bash scripts/connect-server.sh "cd ~/server/apps/trading-bot && docker-compose build --no-cache bot"
   ```

5. **Restart Container**:
   ```bash
   bash scripts/connect-server.sh "cd ~/server/apps/trading-bot && docker-compose up -d bot"
   ```

### Important Notes

- **Always use `--no-cache`** when rebuilding to ensure changes are included
- **Verify deployment** by checking the application after restart
- **This workflow applies to ALL code changes** that affect the running application
- **UI changes, API changes, configuration changes** all require deployment
- **Test in incognito mode** after deployment to verify changes are live

### Quick Deployment Command Sequence

For convenience, you can run these commands in sequence:
```bash
cd /Users/joshuajenquist/repos/personal/home-server
git add apps/trading-bot/[files]
git commit -m "Your message"
git push origin main
bash scripts/connect-server.sh "cd ~/server && git pull origin main"
bash scripts/connect-server.sh "cd ~/server/apps/trading-bot && docker-compose build --no-cache bot && docker-compose up -d bot"
```

### When to Deploy

- ✅ After completing code changes
- ✅ After fixing bugs
- ✅ After updating configuration
- ✅ After UI changes
- ✅ After API endpoint changes
- ✅ Before marking work as "complete"

**Deployment is part of the completion checklist - do not mark work complete until deployed and verified.**

---

## 🎯 Remember

1. **Always understand existing code first** - Read documentation before coding
2. **Follow established patterns** - Consistency is critical; search codebase for similar implementations
3. **Use existing code and patterns** - Don't reinvent; integrate with shared utilities and practices
4. **Agency over perfection** - Make reasonable decisions, ask questions alongside progress, don't stop
5. **Test thoroughly** - Including error scenarios
6. **Review critically** - Act as a principal architect
7. **Fix systematically** - Address issues in priority order
8. **Document as you work** - Don't wait until the end
9. **Clean up documentation** - Archive work-in-progress, consolidate into core docs
10. **Keep core docs current** - They should reflect final state, not plans
11. **Integration over innovation** - Make your code feel like part of the existing codebase, not a separate system
12. **Deploy after changes** - Always follow the deployment workflow before marking work complete

---

---

## 📌 Task Assignment Template

**When assigning tasks to agents, provide this information**:

```
Task: [Feature/Component Name]
Target Documentation: [Path to main doc, e.g., docs/SENTIMENT_FEATURES_COMPLETE.md]
Task Tracking: [Optional - path to task list/checklist if applicable]
Reference Implementation: [Optional - specific file to use as pattern]
Priority: [High/Medium/Low]
```

**Example**:
```
Task: Add new sentiment data source - Discord
Target Documentation: docs/SENTIMENT_FEATURES_COMPLETE.md
Task Tracking: docs/archive/SENTIMENT_INTEGRATION_CHECKLIST.md (for historical reference)
Reference Implementation: src/data/providers/sentiment/twitter.py
Priority: Medium
```

---

**Ready to start?** Review your task assignment, read the target documentation, and follow the workflow above.

**Good luck!** 🚀
