# Beads UI

Web interface for the Beads issue tracker (`bd` CLI tool).

## Access

- **URL**: https://beads.server.unarmedpuppy.com
- **Port**: 3015 (direct access)
- **Status**: Active

## Overview

Beads UI provides:
- Issues view with filtering and search
- Epics view with progress tracking
- Board view with workflow columns
- Keyboard-driven navigation
- Live database synchronization

## Configuration

The service mounts the home-server `.beads/` directory to display tasks from the home-server project.

### Volume Mount

The container mounts `/home/unarmedpuppy/server/.beads` to `/app/.beads`.

## References

- [Beads UI GitHub](https://github.com/mantoni/beads-ui)
- [Beads CLI GitHub](https://github.com/steveyegge/beads)
- [Beads CLI Reference](../../agents/reference/beads.md)
