# Agents Archive

This directory contains archived state files and historical data.

## Structure

```
archive/
├── state/              # Runtime state files (databases, exports, cache)
│   ├── memory/        # Memory system state
│   └── monitoring/    # Monitoring system state
└── README.md          # This file
```

## What's Archived Here

### State Files
- **Database files** - SQLite databases (memory.db, agent_activity.db)
- **Exported data** - Exported decisions/patterns from memory system
- **Index files** - Runtime index files

These files are runtime state and should not be committed to git. They're archived here for reference but will be regenerated when systems run.

## Why Archive Instead of Delete?

State files are archived (not deleted) to:
- Preserve historical data if needed
- Allow recovery of test data
- Maintain reference for debugging

However, these files are excluded from git via `.gitignore`.

## Restoring State

If you need to restore state files:
1. Copy from `archive/state/` to their original locations
2. Ensure proper permissions
3. Systems will use the restored state

**Note**: State files are runtime-generated. Systems will create new state files if they don't exist.

