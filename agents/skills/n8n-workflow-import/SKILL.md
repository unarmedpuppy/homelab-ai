---
name: n8n-workflow-import
description: Import or update n8n workflows via CLI
when_to_use: When you need to deploy workflow changes to n8n from the repo
---

# n8n Workflow Import

Import n8n workflow JSON files into the running n8n instance via CLI.

## Prerequisites

- Workflow JSON file must have `"active": true` field at root level
- n8n container must be running

## Required JSON Fields

Workflow JSON must include:

```json
{
  "name": "Workflow Name",
  "active": true,
  "nodes": [...],
  "connections": {...}
}
```

**IMPORTANT**: The `"active": true` field is required or import will fail with:
```
SQLITE_CONSTRAINT: NOT NULL constraint failed: workflow_entity.active
```

## Import Workflow

### Single Workflow

```bash
# Copy file to container and import
bash scripts/connect-server.sh "docker cp ~/server/apps/n8n/workflows/<workflow>.json n8n:/tmp/ && docker exec n8n n8n import:workflow --input=/tmp/<workflow>.json"
```

### All Workflows in Directory

```bash
# Import all workflows from directory
bash scripts/connect-server.sh "docker cp ~/server/apps/n8n/workflows n8n:/tmp/ && docker exec n8n n8n import:workflow --separate --input=/tmp/workflows/"
```

## List Workflows

```bash
# List all workflows
bash scripts/connect-server.sh "docker exec n8n n8n list:workflow"

# Search for specific workflow
bash scripts/connect-server.sh "docker exec n8n n8n list:workflow | grep -i 'workflow-name'"
```

## Export Workflow

```bash
# Export single workflow by ID
bash scripts/connect-server.sh "docker exec n8n n8n export:workflow --id=<workflow-id> --output=/tmp/exported.json && docker cp n8n:/tmp/exported.json ~/server/apps/n8n/workflows/"

# Export all workflows
bash scripts/connect-server.sh "docker exec n8n n8n export:workflow --all --output=/tmp/workflows/ && docker cp n8n:/tmp/workflows ~/server/apps/n8n/"
```

## Caveats

### Import Creates New Workflows

The CLI `import:workflow` command **creates new workflows** - it does not update existing ones by name. This means:

- Importing the same JSON multiple times creates duplicates
- To "update" a workflow, you must:
  1. Delete the old workflow via UI or API
  2. Import the new version

### Cleaning Up Duplicates

After import, check for duplicates:

```bash
bash scripts/connect-server.sh "docker exec n8n n8n list:workflow | grep -i '<workflow-name>'"
```

To delete via n8n API (requires API key):

```bash
curl -X DELETE "https://n8n.server.unarmedpuppy.com/api/v1/workflows/<id>" \
  -H "X-N8N-API-KEY: <your-api-key>"
```

Or delete via n8n UI manually.

## Example: Full Workflow Update Process

```bash
# 1. Make changes to workflow JSON locally
# 2. Ensure "active": true is set
# 3. Commit and push
git add apps/n8n/workflows/my-workflow.json
git commit -m "fix(n8n): update my-workflow"
git push

# 4. Pull on server
bash scripts/connect-server.sh "cd ~/server && git pull"

# 5. Import workflow
bash scripts/connect-server.sh "docker cp ~/server/apps/n8n/workflows/my-workflow.json n8n:/tmp/ && docker exec n8n n8n import:workflow --input=/tmp/my-workflow.json"

# 6. Verify import
bash scripts/connect-server.sh "docker exec n8n n8n list:workflow | grep -i 'my-workflow'"

# 7. (Optional) Clean up old duplicates via n8n UI
```

## n8n CLI Reference

```bash
# Available commands
docker exec n8n n8n --help

# Workflow commands
n8n import:workflow --input=<file>           # Import from file
n8n import:workflow --separate --input=<dir> # Import all from directory
n8n export:workflow --id=<id> --output=<file>
n8n export:workflow --all --output=<dir>
n8n list:workflow

# Credentials commands
n8n import:credentials --input=<file>
n8n export:credentials --id=<id> --output=<file>
```

## Troubleshooting

### "NOT NULL constraint failed: workflow_entity.active"

Add `"active": true` to the workflow JSON root level.

### Import Timeout

The CLI can be slow. If it times out, check if the workflow was imported:

```bash
bash scripts/connect-server.sh "docker exec n8n n8n list:workflow | grep -i '<name>'"
```

### Workflow Not Running

After import, workflows are active but may need to be manually activated in the UI if the trigger isn't firing. Check the workflow in n8n UI.
