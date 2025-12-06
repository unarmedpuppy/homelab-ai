---
name: git-server-sync
description: Synchronize git repository between local and server
when_to_use: Syncing changes between local and server, ensuring both repos are in sync, after manual server changes
script: scripts/git-server-sync.sh
---

# Git Server Sync

Synchronizes git repository between local and server.

## When to Use

- Syncing changes between local and server
- Ensuring both repos are in sync
- After manual server changes
- Resolving sync conflicts

## Usage

```bash
bash scripts/git-server-sync.sh
```

## What It Does

1. **Local sync** - Runs `git-sync.sh` locally (pull, add, commit, push)
2. **Server sync** - Runs `git-sync.sh` on server (pull, add, commit, push)

This ensures both local and server repositories are synchronized.

## Process

1. **Local**: Pull latest changes
2. **Local**: Stage all changes (`git add .`)
3. **Local**: Commit changes
4. **Local**: Push to remote
5. **Server**: Pull latest changes
6. **Server**: Stage all changes
7. **Server**: Commit changes
8. **Server**: Push to remote

## Notes

- This script is used by file watchers for automatic sync
- Both local and server must have git configured
- Conflicts may require manual resolution

## Related Tools

- `standard-deployment` - Deploy code changes
- `connect-server` - Execute commands on server

