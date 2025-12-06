# Plans

Shared implementation plans for multi-session features, architectural decisions, and team collaboration.

## When to Use

- Multi-session features requiring planning
- Architectural decisions that need documentation
- Implementation specs for complex changes
- Team collaboration on features

## Plan File Format

Use consistent frontmatter for agent discovery:

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

## Workflow

1. **Starting a feature**: Create plan in `agents/plans-local/` for exploration
2. **Plan solidifies**: Move refined plan to `agents/plans/` and commit
3. **During implementation**: Update plan status, add session notes
4. **Completion**: Mark plan as `complete`, reference in PR

