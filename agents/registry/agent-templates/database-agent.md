# Agent Template: Database Specialist

Template for creating database specialized agents.

## Specialization

Database management, optimization, and administration (PostgreSQL, MySQL, SQLite).

## Capabilities

### Skills
- Database-specific workflows (to be created)

### MCP Tools
- Database operations tools (planned)
- System monitoring tools (for database resources)

### Domain Knowledge
- PostgreSQL administration
- Database optimization
- Query performance tuning
- Database backup and restore
- Migration management
- Connection pooling
- Index management

## Typical Tasks

- Database optimization
- Query performance tuning
- Backup and restore operations
- Migration management
- Connection troubleshooting
- Index optimization

## Prompt

**Use**: `agents/prompts/base.md` (general agent prompt)

The base prompt provides:
- Discovery workflow
- Universal systems (memory, monitoring, communication, task coordination)
- How to work (principles, best practices)

**Note**: If a database-specific prompt is created in the future (`agents/prompts/database.md`), use that instead.

## Usage

Copy this template when creating a database specialized agent.

When creating the agent definition, reference:
- **Template**: `database-agent.md` (this file)
- **Prompt**: `agents/prompts/base.md`

---

**Template Version**: 1.1
**Last Updated**: 2025-01-13

