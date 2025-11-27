# Task Coordination

Simple task registry for tracking work across sessions.

## Files

- **registry.md** - The task list (edit directly)

## Usage

### View Tasks
```bash
cat agents/tasks/registry.md
```

### Add a Task
Edit `registry.md` and add a row to the Active Tasks table:
```markdown
| T2 | Implement feature X | trading-bot | pending | high | Details |
```

### Claim a Task
Change status from `pending` to `in_progress`

### Complete a Task
1. Change status to `completed`
2. Move row to Completed Tasks section
3. Add completion date

## Task Format

| Field | Description |
|-------|-------------|
| ID | Unique identifier (T1, T2, etc.) |
| Task | Brief description |
| Project | Project name (trading-bot, media-download, etc.) |
| Status | pending, in_progress, blocked, completed |
| Priority | high, medium, low |
| Notes | Additional context |

## Cross-Session Workflow

1. At session start: Check `registry.md` for pending/in_progress tasks
2. During work: Update status as you progress
3. At session end: Update status, add notes for next session
