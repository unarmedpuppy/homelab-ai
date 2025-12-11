---
name: plan-creator
description: Create consistent, comprehensive implementation plans for AI agents. Use when starting new features, complex changes, or multi-phase work. Follows Plan → Act → Test workflow with templates for features, bugs, and refactoring.
---

# Plan Creator

Create consistent implementation plans that guide AI agents through complex work.

## Overview

This skill provides tools to create well-structured plans following the Plan → Act → Test workflow documented in `agents/reference/plan_act.md`.

**Core capabilities**:
1. **create** - Generate new plan from template
2. **validate** - Check plan completeness
3. **export** - Convert plan to task list

All plans support progressive disclosure and multi-session collaboration.

## Commands

### Create a New Plan

Generate a plan with interactive prompts:

```bash
cd agents/skills/plan-creator
npm run create
```

**Prompts**:
- Plan type (feature, bug-fix, refactor, custom)
- Plan name (validates hyphen-case)
- Storage location (plans/ or plans-local/)
- Feature-specific details

**Output**: Creates plan file with YAML frontmatter and structured sections.

### Validate a Plan

Check plan completeness and structure:

```bash
cd agents/skills/plan-creator
npm run validate path/to/plan.md
```

**Validation checks**:
- YAML frontmatter present and valid
- Required fields: title, created, status
- Status is valid (draft, in-progress, completed, blocked)
- Sections present based on plan type
- Checklist items properly formatted
- No orphaned todos
- File follows markdown standards

**Exit codes**:
- 0 = Valid and complete
- 1 = Errors found
- 2 = Warnings (missing optional sections)

### Export to Task List

Convert plan phases to actionable task list:

```bash
cd agents/skills/plan-creator
npm run export path/to/plan.md
```

**Process**:
1. Extract all checklist items from plan
2. Group by phase/section
3. Add metadata (file, dependencies)
4. Output in task list format

**Output**: Markdown task list compatible with `agents/plans/tasks.md`

## Plan Types

### Feature Plan

**When to use**: Implementing new functionality, adding capabilities

**Template sections**:
- Objective: Clear goal statement
- Requirements: What must be implemented
- Out of Scope: Explicit boundaries
- Current State: Existing code exploration
- Implementation Plan: Phased checklist
- Test Strategy: How to verify correctness
- Documentation: What docs need updating

**Example**:

```markdown
---
title: Add User Authentication
created: 2025-12-10
status: draft
author: @copilot
type: feature
---

# Plan: Add User Authentication

## Objective

Implement JWT-based authentication for API endpoints.

## Requirements

- Users login with email/password
- JWT tokens expire after 1 hour
- Logout invalidates tokens

## Out of Scope

- OAuth social login
- Two-factor authentication
- Password reset

## Current State

### Existing Code
- User model: `src/models/User.ts`
- API routes: `src/routes/api.ts`
- No auth middleware exists

### Dependencies
- bcrypt (already installed)
- jsonwebtoken (need to install)

## Implementation Plan

### Phase 1: User Model
- [ ] Add password hashing to User model
- [ ] Add password verification method
- [ ] Write unit tests for User model

### Phase 2: Auth Logic
- [ ] Create JWT utility functions
- [ ] Create auth middleware
- [ ] Write tests for JWT utilities

### Phase 3: API Integration
- [ ] Add login endpoint
- [ ] Add logout endpoint
- [ ] Protect existing endpoints
- [ ] Write integration tests

### Phase 4: Documentation
- [ ] Update API docs
- [ ] Add usage examples

## Test Strategy

### Unit Tests
- Password hashing and verification
- JWT generation and validation

### Integration Tests
- Login flow (success/failure)
- Protected endpoint access
- Token refresh

### Edge Cases
- Expired tokens
- Invalid tokens
- Malformed requests

## Documentation Updates

- [ ] Update `docs/api.md` with auth endpoints
- [ ] Add authentication guide to README
- [ ] Document environment variables
```

### Bug Fix Plan

**When to use**: Fixing defects, resolving issues

**Template sections**:
- Bug Description: What's broken
- Steps to Reproduce: How to see the bug
- Expected vs Actual: What should happen vs what does
- Root Cause Analysis: Why it's broken
- Fix Plan: How to fix it
- Testing Plan: How to verify fix

**Example**:

```markdown
---
title: Fix Login Rate Limiting
created: 2025-12-10
status: draft
author: @copilot
type: bug-fix
issue: #123
---

# Plan: Fix Login Rate Limiting

## Bug Description

Rate limiting on login endpoint not working. Users can make unlimited login attempts.

## Steps to Reproduce

1. Send 100 POST requests to `/api/login`
2. All requests return 200 or 401
3. Expected: After 5 requests, should return 429 Too Many Requests

## Expected vs Actual

**Expected**: Rate limit of 5 login attempts per minute per IP
**Actual**: No rate limiting applied

## Root Cause Analysis

### Investigation
- Checked `src/middleware/rate-limit.ts`
- Rate limiter configured but not applied to login route
- Login route added after rate limiter in middleware chain

### Cause
Route registration order incorrect in `src/routes/auth.ts`

## Fix Plan

- [ ] Move rate limiter registration before route handlers
- [ ] Verify middleware order in app initialization
- [ ] Add route-specific rate limit for login (5 req/min)

## Testing Plan

- [ ] Manual test: Verify rate limiting triggers
- [ ] Add integration test for rate limiting
- [ ] Check no regression on other endpoints

## Files to Modify

- `src/routes/auth.ts` - Fix middleware order
- `tests/integration/auth.test.ts` - Add rate limit test
```

### Refactoring Plan

**When to use**: Code restructuring, improving design, tech debt

**Template sections**:
- Motivation: Why refactor
- Current Problems: What's wrong now
- Proposed Changes: What will change
- Migration Strategy: How to avoid breaking things
- Testing Strategy: Verify no behavior changes
- Rollback Plan: How to revert if needed

**Example**:

```markdown
---
title: Refactor Database Connection Pool
created: 2025-12-10
status: draft
author: @copilot
type: refactor
---

# Plan: Refactor Database Connection Pool

## Motivation

Current database connection management is scattered across multiple files, making it hard to:
- Configure connection limits
- Debug connection leaks
- Add connection retry logic

## Current Problems

- Connection creation in 5+ different files
- Inconsistent error handling
- No connection pooling (performance issue)
- Difficult to test

## Proposed Changes

### New Structure
```
src/database/
├── connection.ts       # Single connection pool
├── config.ts          # Configuration
└── middleware.ts      # Request-scoped connections
```

### Changes
- Create centralized connection pool
- Migrate all connection usage
- Add connection lifecycle hooks
- Implement retry logic

## Migration Strategy

### Phase 1: Create New System
- [ ] Create `src/database/connection.ts`
- [ ] Create `src/database/config.ts`
- [ ] Create `src/database/middleware.ts`
- [ ] Add tests for new system

### Phase 2: Migrate Usage
- [ ] Migrate `src/models/*.ts` (10 files)
- [ ] Migrate `src/routes/*.ts` (8 files)
- [ ] Migrate `src/services/*.ts` (5 files)
- [ ] Update all imports

### Phase 3: Cleanup
- [ ] Remove old connection code
- [ ] Update documentation
- [ ] Deploy to staging

## Testing Strategy

- [ ] All existing tests pass unchanged
- [ ] No behavior changes in API
- [ ] Performance not degraded
- [ ] Connection pool limits enforced
- [ ] Retry logic works correctly

## Rollback Plan

- Keep old code until Phase 3
- Feature flag for new connection system
- Can revert by environment variable
- Database schema unchanged (safe)

## Files to Modify

### Create
- `src/database/connection.ts`
- `src/database/config.ts`
- `src/database/middleware.ts`
- `tests/database/connection.test.ts`

### Modify (23 files)
- `src/models/*.ts` (10 files)
- `src/routes/*.ts` (8 files)
- `src/services/*.ts` (5 files)

### Delete
- `src/utils/db-helper.ts`
```

## Plan Organization

### Simple Plans (Single File)

Store in `agents/plans/` or `agents/plans/local/`:

```
agents/plans/add-user-search.md
agents/plans/fix-auth-bug.md
agents/plans/local/explore-graphql.md  # Local scratch
```

**Use when**:
- Single feature or bug fix
- Self-contained change
- One session of work

### Complex Plans (Subdirectory)

Store in subdirectory for multi-file features:

```
agents/plans/user-authentication/
├── overview.md          # High-level plan
├── phase-1-backend.md   # Backend implementation
├── phase-2-frontend.md  # Frontend implementation
├── api-design.md        # API specifications
└── testing-strategy.md  # Testing approach
```

**Use when**:
- Multi-phase implementation
- Separate specifications needed
- Team collaboration
- Long-running project

## Plan Lifecycle

### Status Values

**draft** - Initial planning, not yet started
```yaml
status: draft
```

**in-progress** - Active implementation
```yaml
status: in-progress
started: 2025-12-10
```

**blocked** - Waiting on dependencies
```yaml
status: blocked
blocker: "Waiting for API key from ops team"
```

**completed** - Fully implemented and tested
```yaml
status: completed
completed: 2025-12-10
pr: https://github.com/org/repo/pull/123
```

### Updating Status

Update YAML frontmatter as work progresses:

```markdown
---
title: Add User Authentication
created: 2025-12-10
status: in-progress
started: 2025-12-10
author: @copilot
progress: 6/14 tasks complete
---
```

## Best Practices

### Planning

- **Be specific**: Vague plans lead to confusion
- **Break into phases**: Large features need structure
- **Document decisions**: Record why choices were made
- **Define success**: Clear test strategy and acceptance criteria
- **Update as you go**: Plans evolve during implementation

### Storage

- **Use `plans/`**: For committed, collaborative plans
- **Use `plans-local/`**: For scratch work, exploration (gitignored)
- **Single file**: For simple features
- **Subdirectory**: For complex multi-phase work

### Collaboration

- **Include author**: Add `author: @your-id` to frontmatter
- **Link to issues**: Reference GitHub issues/PRs
- **Mark blockers**: Be explicit about dependencies
- **Commit progress**: Update plan as tasks complete

## Requirements

- Node.js 14 or higher
- npm or yarn

## Related Documentation

- `agents/reference/plan_act.md` - Complete Plan → Act → Test workflow
- `agents/reference/documentation-style.md` - Markdown formatting
- `agents/plans/tasks.md` - Task tracking and claiming
- `agents/plans/templates/task-template.md` - Task format
