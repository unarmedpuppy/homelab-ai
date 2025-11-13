---
name: standard-deployment
description: Complete deployment workflow: verify → deploy → restart → verify. Replaces the 14-step agent checklist.
category: deployment
mcp_tools_required:
  - git_status
  - git_deploy
  - docker_compose_restart
  - docker_container_status
  - docker_view_logs
prerequisites:
  - Changes made locally (or use git_deploy to commit)
  - MCP tools available
---

# Standard Deployment Workflow

## When to Use This Skill

Use this skill when:
- Deploying code changes to the server
- Updating service configurations
- After making local changes that need to be deployed
- Restarting services after configuration changes

**This skill replaces the 14-step deployment checklist** that was previously embedded in agent prompts.

## Overview

This skill orchestrates the complete deployment workflow:
1. Verify current state
2. Deploy changes (git add → commit → push → pull on server)
3. Restart affected services
4. Verify deployment success
5. Handle errors if any

## Workflow Steps

### Step 1: Verify Current State

Before deploying, verify the current state:

```python
# Check git status
git_status_result = await git_status()
# Returns: branch, changes, untracked files, ahead/behind

# Check affected services are running
if app_path:
    container_status = await docker_container_status(f"{app_path}-{service}")
    # Verify service is currently running
```

**What to check:**
- Repository is clean or has expected changes
- Services are currently running (if restarting)
- No uncommitted critical changes

### Step 2: Deploy Changes

Deploy using the `git_deploy` MCP tool:

```python
# Deploy changes
deploy_result = await git_deploy(
    commit_message="Description of changes",
    files=None  # None = all changes, or list specific files
)

# Check result
if deploy_result["status"] != "success":
    # Handle deployment error
    return {
        "status": "error",
        "step": "deployment",
        "error": deploy_result.get("error")
    }
```

**What happens:**
- `git add` - Stages changes
- `git commit` - Commits with message
- `git push` - Pushes to remote
- `git pull` - Pulls on server

### Step 3: Restart Affected Services

Restart services using MCP tools:

**Option A: Auto-detect affected services**
```python
# Use deploy_and_restart for automatic detection
result = await deploy_and_restart(
    commit_message="Update configuration",
    app_path="apps/media-download"  # Optional, auto-detected if not provided
)
```

**Option B: Explicit restart**
```python
# Restart specific service
restart_result = await docker_compose_restart(
    app_path="apps/media-download",
    service="sonarr"  # Optional, None = all services
)
```

### Step 4: Verify Deployment

Verify services are healthy after restart:

```python
# Check container status
status = await docker_container_status("media-download-sonarr")

if status["health"] != "healthy":
    # Check logs
    logs = await docker_view_logs("media-download-sonarr", lines=50)
    # Investigate issues
```

**What to verify:**
- Container is running
- Health check is passing (if configured)
- No error logs
- HTTP endpoint responds (if applicable)

### Step 5: Handle Errors

If any step fails:

**Deployment Errors:**
- Git conflicts: Report conflicts, suggest resolution
- Push failures: Check network, verify permissions
- Pull failures: Check server connectivity

**Restart Errors:**
- Service won't start: Check logs, verify dependencies
- Health check fails: Investigate logs, check configuration
- Port conflicts: Use `check_port_status` to find conflicts

**Error Recovery:**
- If deployment fails: Changes not pushed, safe to retry
- If restart fails: Code is deployed, but service needs manual intervention
- If service unhealthy: Use `troubleshoot-container-failure` skill

## MCP Tools Used

This skill uses the following MCP tools:

1. **`git_status`** - Check repository state before deployment
2. **`git_deploy`** - Complete deployment workflow (add → commit → push → pull)
3. **`docker_compose_restart`** - Restart services
4. **`docker_container_status`** - Verify service health
5. **`docker_view_logs`** - Check logs if issues occur

## Examples

### Example 1: Deploy Configuration Change

**User Request**: "Deploy the updated n8n configuration"

**Agent Action**:
```python
# Activate standard-deployment skill

# Step 1: Verify
git_status()  # Check current state

# Step 2: Deploy
git_deploy(
    commit_message="Update n8n configuration",
    files=["apps/n8n/docker-compose.yml"]
)

# Step 3: Restart
docker_compose_restart("apps/n8n")

# Step 4: Verify
docker_container_status("n8n")
```

### Example 2: Deploy with Specific Service Restart

**User Request**: "Deploy and restart just the sonarr service"

**Agent Action**:
```python
# Use deploy_and_restart MCP tool (combines deploy + restart)
deploy_and_restart(
    commit_message="Update media-download config",
    app_path="apps/media-download",
    service="sonarr"
)
```

### Example 3: Deploy Multiple Services

**User Request**: "Deploy changes and restart all media-download services"

**Agent Action**:
```python
# Deploy
git_deploy("Update media stack configuration")

# Restart all services in app
docker_compose_restart("apps/media-download", service=None)

# Verify each service
for service in ["sonarr", "radarr", "nzbget"]:
    docker_container_status(f"media-download-{service}")
```

## Error Scenarios

### Scenario 1: Git Conflicts

**Symptom**: `git_deploy` returns conflicts

**Action**:
1. Report conflicts to user
2. Suggest resolution: `git pull` and merge, or `git reset` to discard
3. Do not proceed with restart until conflicts resolved

### Scenario 2: Service Won't Start

**Symptom**: `docker_compose_restart` succeeds but container exits

**Action**:
1. Check logs: `docker_view_logs(container_name, lines=100)`
2. Check dependencies: `check_service_dependencies(service_name)`
3. Activate `troubleshoot-service-startup` skill if needed

### Scenario 3: Service Unhealthy

**Symptom**: Container running but health check failing

**Action**:
1. Check logs for errors
2. Verify configuration changes didn't break service
3. Check resource limits: `check_system_resources()`
4. Activate `troubleshoot-container-failure` skill if needed

## Best Practices

1. **Always verify before deploying**: Check git status and service state
2. **Use descriptive commit messages**: Help track what changed
3. **Restart only affected services**: Don't restart everything unnecessarily
4. **Verify after restart**: Don't assume restart succeeded
5. **Check logs on failure**: Logs contain diagnostic information
6. **Handle errors gracefully**: Report issues clearly to user

## Related Skills

- **`troubleshoot-container-failure`** - If deployment causes container issues
- **`system-health-check`** - For comprehensive post-deployment verification
- **`rollback-deployment`** - If deployment needs to be reverted

## Notes

- This skill replaces the 14-step checklist from `SERVER_AGENT_PROMPT.md`
- All steps use MCP tools for consistency and error handling
- Skills can be used in Claude.ai, Claude Code, or via API
- Skills are portable and can be shared between agents

