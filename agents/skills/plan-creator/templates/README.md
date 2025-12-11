# Plan Templates

This directory contains example plan templates that agents can reference when creating new plans.

## Available Templates

| Template | Description | Use Case |
|----------|-------------|----------|
| `feature-template.md` | Feature implementation plan | Adding new functionality |
| `bug-fix-template.md` | Bug fix plan | Resolving defects |
| `refactor-template.md` | Refactoring plan | Code restructuring |
| `custom-template.md` | Minimal custom plan | Non-standard work |

## Usage

### With plan-creator skill

```bash
cd agents/skills/plan-creator
npm run create
```

The interactive wizard will generate plans based on these templates.

### Manual usage

1. Copy template file
2. Rename to your plan name (hyphen-case)
3. Fill in frontmatter fields
4. Replace placeholder sections
5. Add specific tasks to checklists

## Template Structure

All templates follow this pattern:

```markdown
---
title: Plan Title
created: YYYY-MM-DD
status: draft
author: @agent-id
type: feature|bug-fix|refactor|custom
---

# Plan: Title

[Sections specific to plan type]

## Implementation Plan

### Phase 1: Name
- [ ] Task 1
- [ ] Task 2

[More phases...]

## Test Strategy

[How to verify correctness]
```

## Customization

Templates are starting points. Customize based on:
- Project requirements
- Team conventions
- Complexity of work
- Collaboration needs

## Related Documentation

- `agents/reference/plan_act.md` - Plan → Act → Test workflow
- `agents/skills/plan-creator/SKILL.md` - Plan creator documentation
