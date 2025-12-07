# Plan → Act → Test Workflow

Embedded workflow for agent development tasks.

## Plan Phase

**When**: Starting a new feature, complex changes, unclear requirements

1. **Understand Requirements**
   - What is being asked?
   - What problem does this solve?
   - What are the acceptance criteria?

2. **Explore the Codebase**
   - Read relevant existing code
   - Understand current patterns
   - Identify files that need changes

3. **Ask Clarifying Questions**
   - Resolve ambiguities before building
   - Confirm assumptions
   - Discuss tradeoffs

4. **Create Implementation Plan**
   - Break into actionable tasks
   - Identify dependencies
   - Note files to create/modify

5. **Define Test Strategy**
   - What tests are needed?
   - What edge cases to cover?

### Planning Documentation

Store plans in `agents/plans/` (shared) or `agents/plans-local/` (local only):

- **`agents/plans/`** - Committed plans for multi-session features, architectural decisions, implementation strategies
- **`agents/plans-local/`** - Gitignored scratch work, session notes, exploratory analysis

**Reference Documentation** (not plans):
- **`agents/reference/`** - Persistent reference guides, how-to documentation, architectural references (e.g., `agents/reference/storage/`, `agents/reference/setup/`)
- **`docs/`** - Project-level documentation (security audits, implementation docs)

**⚠️ IMPORTANT**: 
- **Plans and strategies** → `agents/plans/` or `agents/plans-local/`
- **Reference guides and how-tos** → `agents/reference/`
- **Do NOT** create planning/strategy docs in `docs/` - use `agents/plans/` instead

## Act Phase

**When**: Plan approved, simple changes that don't need planning

1. Create feature branch
2. Implement incrementally
3. Commit after each logical unit
4. Run tests frequently
5. Follow code style guide

**Rules**:
- DO implement the approved plan
- DO make small, focused commits
- DON'T make unplanned changes
- DON'T skip tests
- DON'T commit broken code

## Test Phase

**When**: Implementation complete

1. Run full test suite
2. Verify type checking passes
3. Run linter
4. Check test coverage
5. Update documentation
6. Create pull request

## Plan File Template

```markdown
---
title: Feature Name
created: YYYY-MM-DD
status: draft | in_progress | approved | complete
author: @agent-id
---

# Plan: Feature Name

## Objective

[What problem does this solve? What's the goal?]

## Approach

[High-level strategy]

## Tasks

1. [ ] Task 1 - [description]
2. [ ] Task 2 - [description]
3. [ ] Task 3 - [description]

## Files to Modify

- `src/path/file.ts` - [what changes]
- `tests/path/file.test.ts` - [what tests]

## Test Strategy

- Unit tests for [components]
- Integration test for [workflow]

## Open Questions

- [ ] Question 1?
- [x] Resolved: Chose option A because...

## Session Notes

### YYYY-MM-DD
- [Progress update]
- [Decisions made]
```

## Integration with Task Management

- Create tasks in `agents/tasks/tasks.md` from plan
- Update task status as you work
- Reference plan in task notes
- Mark plan complete when all tasks done

