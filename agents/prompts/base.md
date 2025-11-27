# Agent Prompt

## User Information

**User Name**: shua

---

## Home Server Context

This is a home server codebase with Docker-based services. Key paths:
- `apps/` - Docker applications (trading-bot, media-download, etc.)
- `agents/tasks/registry.md` - **Task list across sessions**
- `agents/memory/` - SQLite memory for decisions and patterns
- `agents/skills/` - Reusable workflow guides

## Memory System

Use the SQLite memory at `agents/memory/memory.db` to:
- **Query past decisions** before making new ones
- **Record important decisions** with rationale
- **Track patterns** (common issues and solutions)

Direct queries:
```bash
sqlite3 agents/memory/memory.db "SELECT * FROM decisions WHERE project='trading-bot' ORDER BY created_at DESC LIMIT 5;"
sqlite3 agents/memory/memory.db "SELECT * FROM patterns WHERE severity='high';"
```

Record a decision:
```bash
sqlite3 agents/memory/memory.db "INSERT INTO decisions (content, rationale, project, importance) VALUES ('decision text', 'why', 'project-name', 0.8);"
```

## Skills

Check `agents/skills/` for documented workflows:
- **standard-deployment** - Deploy code changes
- **troubleshoot-container-failure** - Debug container issues
- **cleanup-disk-space** - Free disk space

Skills are markdown guides - read them and follow the steps.

## Common Commands

### Docker
```bash
docker ps                                    # List containers
docker logs <container> --tail 100           # View logs
docker compose -f apps/X/docker-compose.yml restart  # Restart service
```

### Git Deploy (to server)
```bash
git add . && git commit -m "message" && git push
ssh server "cd /path && git pull && docker compose restart"
```

### Check Resources
```bash
df -h                    # Disk space
free -h                  # Memory (Linux)
docker system df         # Docker disk usage
```

## Task Registry

Check `agents/tasks/registry.md` at session start for pending tasks:
```bash
cat agents/tasks/registry.md
```

Update task status as you work. Add notes for the next session.

## Workflow

1. **Session start**: Check task registry for pending/in-progress tasks
2. **Before work**: Check memory for related decisions
3. **During work**: Use skills when applicable, update task status
4. **Session end**: Update task registry, record important decisions

---

**Keep it simple. Run commands directly. Use tasks + memory for continuity.**
