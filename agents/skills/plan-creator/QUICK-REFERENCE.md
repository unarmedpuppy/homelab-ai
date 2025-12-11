# Plan Creator - Quick Reference

Quick guide for using the plan-creator skill to create consistent implementation plans.

## Installation

```bash
cd agents/skills/plan-creator
npm install
```

## Create a New Plan

### Interactive Mode (Recommended)

```bash
npm run create
```

Follow the prompts:
1. Choose plan type (feature, bug-fix, refactor, custom)
2. Enter plan name in hyphen-case (e.g., `add-user-authentication`)
3. Choose storage location (`plans/` or `plans-local/`)
4. Enter plan title
5. Enter author (e.g., `@copilot`)
6. Fill in type-specific details

**Output**: Creates a complete plan with:
- YAML frontmatter
- All required sections
- Checklist placeholders
- Template guidance

### Plan Types

#### Feature Plan
- **Use for**: New functionality, capabilities, enhancements
- **Sections**: Objective, Requirements, Out of Scope, Implementation Plan, Test Strategy
- **Example**: Adding authentication, building new API endpoint

#### Bug Fix Plan
- **Use for**: Fixing defects, resolving issues
- **Sections**: Bug Description, Root Cause Analysis, Fix Plan, Testing
- **Example**: Fixing rate limiting, resolving memory leak

#### Refactor Plan
- **Use for**: Code restructuring, tech debt, performance improvements
- **Sections**: Motivation, Current Problems, Migration Strategy, Rollback Plan
- **Example**: Refactoring database layer, improving architecture

#### Custom Plan
- **Use for**: Non-standard work, exploration, research
- **Sections**: Minimal template with overview and goals
- **Example**: Spike for new technology, research task

## Validate a Plan

Check plan structure and completeness:

```bash
npm run validate ../../plans/my-plan.md
```

**Checks**:
- ✅ YAML frontmatter present and valid
- ✅ Required fields (title, created, status)
- ✅ Valid status value
- ✅ Proper checklist formatting
- ✅ Recommended sections present
- ✅ No placeholder text left

**Exit codes**:
- `0` - Valid and complete
- `1` - Errors found (must fix)
- `2` - Warnings only (optional fixes)

## Export to Task List

Convert plan checklists to task format:

```bash
npm run export ../../plans/my-plan.md
```

**Output**: Creates `my-plan-tasks.md` with:
- Task list format compatible with `agents/plans/tasks.md`
- All checklist items extracted
- Organized by section/phase
- Progress summary

## Plan Storage

### `agents/plans/` (Committed)
Use for:
- Collaborative work
- Multi-session features
- Team plans
- Documented decisions

### `agents/plans/local/` (Gitignored)
Use for:
- Scratch work
- Exploration
- Session notes
- Personal experiments

## Plan Lifecycle

### 1. Create Plan

```bash
npm run create
```

Status: `draft`

### 2. Start Work

Update frontmatter:
```yaml
status: in-progress
started: 2025-12-10
```

### 3. Track Progress

Check off tasks as completed:
```markdown
- [x] Completed task
- [ ] In progress task
- [ ] Future task
```

### 4. Complete Plan

Update frontmatter:
```yaml
status: completed
completed: 2025-12-10
pr: https://github.com/org/repo/pull/123
```

## Best Practices

### Planning
- ✅ Be specific with task descriptions
- ✅ Break large features into phases
- ✅ Document decisions in "Open Questions"
- ✅ Define clear success criteria
- ✅ Update plan as work progresses

### Storage
- ✅ Use `plans/` for committed, collaborative work
- ✅ Use `plans-local/` for scratch work
- ✅ Single file for simple features
- ✅ Subdirectory for complex multi-phase work

### Validation
- ✅ Validate before sharing plan
- ✅ Fix all errors (exit code 1)
- ✅ Address warnings when possible
- ✅ Keep placeholders only during draft

## Examples

### Example 1: Feature Plan

```bash
cd agents/skills/plan-creator
npm run create

# Prompts:
# Type: Feature - New functionality
# Name: add-user-authentication
# Storage: agents/plans/ (committed)
# Title: Add User Authentication
# Author: @copilot
# Objective: Implement JWT-based authentication for API endpoints
# Requirements: (opens editor)
#   - Users can login with email/password
#   - JWT tokens expire after 1 hour
#   - Support logout functionality

# Output: agents/plans/add-user-authentication.md
```

### Example 2: Bug Fix Plan

```bash
npm run create

# Prompts:
# Type: Bug Fix - Fix a defect
# Name: fix-rate-limiting
# Storage: agents/plans/local/ (scratch)
# Title: Fix Login Rate Limiting
# Author: @copilot
# Issue: #123
# Description: Rate limiting not working on login endpoint
# Expected: 5 attempts per minute limit
# Actual: Unlimited attempts allowed

# Output: agents/plans/local/fix-rate-limiting.md
```

### Example 3: Validate and Export

```bash
# Create plan
npm run create
# ... fill in details ...

# Validate plan
npm run validate ../../plans/add-user-authentication.md
# ✅ Plan is valid and complete!

# Export to tasks
npm run export ../../plans/add-user-authentication.md
# ✅ Task list exported successfully!
# Output: agents/plans/add-user-authentication-tasks.md
```

## Troubleshooting

### "Missing YAML frontmatter"
- Ensure plan starts with `---` and has closing `---`
- Check YAML syntax is valid

### "Invalid status"
- Use only: `draft`, `in-progress`, `blocked`, `completed`

### "Malformed checklist items"
- Use `- [ ]` for unchecked
- Use `- [x]` for checked
- Don't use other characters in brackets

### "No checklist items found"
- Plans need actionable tasks
- Add `- [ ] Task description` items

## Related Documentation

- [SKILL.md](./SKILL.md) - Complete skill documentation
- [agents/reference/plan_act.md](../../reference/plan_act.md) - Plan → Act → Test workflow
- [templates/](./templates/) - Plan templates and examples

## Quick Command Reference

| Command | Description | Example |
|---------|-------------|---------|
| `npm run create` | Interactive plan creation | Creates new plan |
| `npm run validate <path>` | Validate plan structure | Check plan is complete |
| `npm run export <path>` | Export to task list | Convert to tasks |
