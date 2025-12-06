# Task Coordination

Task tracking with multi-agent claiming protocol.

## Files

- **tasks.md** - The task list (edit directly)

## Usage

### View Tasks
```bash
cat agents/tasks/tasks.md
```

### Add a Task
Edit `tasks.md` and add a row to the Current Tasks table:
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

## Task Claiming Protocol

For multi-agent work, use the claiming protocol:

```bash
# 1. Pull latest
git pull origin main

# 2. Claim task (edit agents/tasks/tasks.md)
# Change [AVAILABLE] → [CLAIMED by @your-id]

# 3. Commit and push within 1 minute
git add agents/tasks/tasks.md
git commit -m "claim: Task X - Description"
git push origin main

# 4. Create feature branch
git checkout -b feature/task-x-description
```

## Cross-Session Workflow

1. At session start: Check `tasks.md` for pending/in_progress tasks
2. During work: Update status as you progress
3. At session end: Update status, add notes for next session
