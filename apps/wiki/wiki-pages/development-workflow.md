# Development Workflow

### Workspace Automations

The [Run on Save](https://marketplace.visualstudio.com/items?itemName=emeraldwalk.RunOnSave) extension is enabled in this repository. Settings are in `.vscode/settings.json`.

**How it works**: When a file is saved in this workspace, the bash script `scripts/git-server-sync.sh` executes. This will:
1. Pull latest changes
2. Add all changed files to a new commit
3. Push to remote repository
4. SSH into the home server and run the same git operations

This effectively syncs any changes made locally to the server automatically.

### Repository Structure

- **Root**: `/Users/joshuajenquist/repos/personal/home-server` (local)
- **Server**: `~/server` (usually `/home/unarmedpuppy/server`)

### Git Sync Script

The `scripts/git-server-sync.sh` script handles automatic synchronization between local repository and server.

---