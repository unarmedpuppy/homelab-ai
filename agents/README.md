# Agents

Lightweight agent support for the home server.

## Structure

```
agents/
├── prompts/          # Agent prompt templates
│   └── base.md       # Base prompt with context
├── tasks/            # Task coordination
│   └── registry.md   # Persistent task list across sessions
├── memory/           # SQLite memory system
│   └── memory.db     # Decisions, patterns, context
└── skills/           # Workflow guides
    ├── standard-deployment/
    ├── troubleshoot-container-failure/
    └── ...
```

## Memory System

SQLite database for persistent memory across sessions.

**Query decisions:**
```bash
sqlite3 agents/memory/memory.db "SELECT * FROM decisions WHERE project='PROJECT' ORDER BY created_at DESC LIMIT 5;"
```

**Record a decision:**
```bash
sqlite3 agents/memory/memory.db "INSERT INTO decisions (content, rationale, project, importance) VALUES ('what', 'why', 'project', 0.8);"
```

**Tables:**
- `decisions` - Technology choices, architecture decisions
- `patterns` - Common issues and solutions
- `context` - Work-in-progress state

## Skills

Markdown workflow guides in `skills/`. See [skills/README.md](./skills/README.md).

## Task Registry

Persistent task list for work across sessions. Edit `tasks/registry.md` directly.

```bash
# View tasks
cat agents/tasks/registry.md

# Tasks are markdown table rows - edit directly
```

## Usage

1. **Session start**: Check `tasks/registry.md` for pending tasks
2. Reference `prompts/base.md` in your agent prompt
3. Query memory before making decisions
4. Use skills for common workflows
5. **Session end**: Update tasks, record important decisions
