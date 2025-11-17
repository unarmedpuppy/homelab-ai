# Archive Directory

**Historical documentation and proposals that have been superseded or completed.**

## Purpose

This directory contains archived documentation that is kept for historical reference. These documents may reference deprecated systems or patterns that have been replaced.

## Deprecated Systems

The following systems have been **removed** and replaced:

### ❌ Per-Agent Files (REMOVED)

- **`TASKS.md`** → **Replaced by**: Task Coordination System (`agents/tasks/registry.md`)
  - Use `register_task()`, `query_tasks()`, `claim_task()`, `update_task_status()` MCP tools
  - Central registry for all tasks across all agents
  - Dependency tracking and validation

- **`STATUS.md`** → **Replaced by**: Monitoring System (dashboard at `localhost:3012`)
  - Use `start_agent_session()`, `update_agent_status()`, `get_agent_status()` MCP tools
  - Real-time visibility in monitoring dashboard
  - Automatic logging of all agent activity

- **`COMMUNICATION.md`** → **Replaced by**: Communication Protocol (`agents/communication/`)
  - Use `send_agent_message()`, `get_agent_messages()`, `acknowledge_message()` MCP tools
  - Structured messaging between agents
  - Message queue with status tracking

**See**: `agents/docs/SYSTEM_ARCHITECTURE.md` for current system architecture.

## Archive Contents

### Recently Archived (2025-01-13)

**One-Time Summaries**:
- `A2A_TESTING_COMPLETE.md` - A2A protocol testing completion summary
- `A2A_TEST_RESULTS.md` - A2A protocol test results
- `AUTO_SESSION_SUMMARY.md` - Auto agent session summary
- `AUTO_AGENT_PRESERVATION.md` - Agent preservation and template
- `REVIEW_AND_CLEANUP_ANALYSIS.md` - Documentation review analysis (superseded by CLEANUP_SUMMARY.md)

**Analysis/Audit Documents**:
- `AGENT_ARCHITECTURE_AUDIT.md` - Agent architecture audit (recommendations implemented, see SYSTEM_ARCHITECTURE.md)
- `A2A_MIGRATION_AUDIT.md` - A2A migration audit (migration complete, see communication/ for current implementation)
- `AG_UI_INTEGRATION_ANALYSIS.md` - AG-UI integration analysis (future work if needed)
- `AGENTIC_PROTOCOLS_LANDSCAPE_ANALYSIS.md` - Agentic protocols landscape analysis (future work if needed)

### Previously Archived

See individual files for details on what replaced them.

## Archive Purpose

Documents in this directory are kept for:
- Historical reference
- Understanding evolution of the system
- Learning from past decisions

**Note**: These documents may contain outdated information. Always refer to current documentation in `agents/docs/` for active systems.

---

**Last Updated**: 2025-01-13
