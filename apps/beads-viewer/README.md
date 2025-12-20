# Beads Viewer

Web interface for visualizing and managing Beads projects (dependency-aware issue tracker).

## Access

- **URL**: https://beads.server.unarmedpuppy.com
- **Port**: 3015 (direct access)
- **Status**: Active

## Overview

Beads Viewer provides:
- Kanban board view of tasks
- Dependency graph visualization
- Smart filtering and search
- Real-time updates via WebSocket

## Configuration

The service mounts the home-server `.beads/` directory in read-only mode to display tasks from the home-server project.

### Volume Mount

The container mounts `/home/unarmedpuppy/server/.beads` to `/app/.beads` which allows the viewer to read the beads data.

### Building

The Docker image is built locally since there's no official image:

```bash
cd apps/beads-viewer
docker compose build
```

## Requirements

- Beads CLI (`bd`) is installed in the container
- Bun runtime for the server
- Access to `.beads/issues.jsonl` file

## References

- [Beads Viewer GitHub](https://github.com/mgalpert/beads-viewer)
- [Beads CLI GitHub](https://github.com/steveyegge/beads)
- [Beads CLI Reference](../../agents/reference/beads.md)
- [Beads Viewer (bv) Reference](../../agents/reference/beads-viewer.md)
