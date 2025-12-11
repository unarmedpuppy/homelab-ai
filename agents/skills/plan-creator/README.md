# Plan Creator Skill

Create consistent, comprehensive implementation plans for AI agents.

## Quick Start

```bash
cd agents/skills/plan-creator
npm install
npm run create
```

## Commands

| Command | Description |
|---------|-------------|
| `npm run create` | Interactive plan creation wizard |
| `npm run validate <path>` | Validate plan structure |
| `npm run export <path>` | Export plan to task list |

## Documentation

See [SKILL.md](./SKILL.md) for complete documentation.

## Examples

### Create a Feature Plan

```bash
npm run create
# Choose: Feature - New functionality
# Enter plan name: add-user-authentication
# Fill in prompts...
```

### Validate a Plan

```bash
npm run validate ../../plans/add-user-auth.md
```

### Export to Tasks

```bash
npm run export ../../plans/add-user-auth.md
# Creates: ../../plans/add-user-auth-tasks.md
```

## Directory Structure

```
plan-creator/
├── SKILL.md              # Complete skill documentation
├── package.json          # Dependencies and scripts
├── README.md             # This file
├── scripts/              # Implementation scripts
│   ├── create-plan.js    # Interactive plan creation
│   ├── validate-plan.js  # Plan validation
│   └── export-to-tasks.js # Export to task list
└── templates/            # Plan templates
    ├── README.md
    ├── feature-template.md
    ├── bug-fix-template.md
    └── refactor-template.md
```

## Requirements

- Node.js 14 or higher
- npm or yarn
