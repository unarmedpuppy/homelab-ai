---
name: troubleshoot-container-failure
description: Diagnose container issues: check status → view logs → check dependencies → identify root cause
category: troubleshooting
mcp_tools_required:
  - docker_container_status
  - docker_view_logs
  - check_service_dependencies
  - check_system_resources
  - check_disk_space
  - find_service_by_port
prerequisites:
  - Container name or service name
  - MCP tools available
---

# Troubleshoot Container Failure

## When to Use This Skill

Use this skill when:
- Container won't start
- Container crashes or exits unexpectedly
- Container is unhealthy (health check failing)
- Container is running but not responding
- Service is unavailable after restart

## Overview

This skill provides a systematic approach to diagnosing container issues:
1. Check container status and recent state
2. View logs for errors
3. Check dependencies and resources
4. Identify root cause
5. Provide recommended fixes

## Workflow Steps

### Step 1: Check Container Status

Get detailed container status:

```python
# Check container status
status = await docker_container_status(container_name)

# Analyze status
if status["status"] == "error":
    # Container not found
    return {"issue": "Container not found", "action": "Verify container name"}

if not status["running"]:
    # Container not running
    issue = "Container stopped"
    if status["state"] == "exited":
        issue = f"Container exited (status: {status['state']})"
    
if status["health"] == "unhealthy":
    # Container running but unhealthy
    issue = "Container unhealthy"
```

**What to check:**
- Container exists
- Current state (running, stopped, exited)
- Health status (healthy, unhealthy, unknown)
- Recent logs in status response

### Step 2: View Detailed Logs

Get recent logs to identify errors:

```python
# Get recent logs (last 100 lines)
logs = await docker_view_logs(container_name, lines=100)

# Analyze logs for common issues
error_patterns = [
    "error", "exception", "fatal", "panic",
    "connection refused", "permission denied",
    "port already in use", "out of memory"
]

errors_found = []
for line in logs.split('\n'):
    for pattern in error_patterns:
        if pattern.lower() in line.lower():
            errors_found.append(line)
```

**What to look for:**
- Error messages
- Exception stack traces
- Connection failures
- Permission errors
- Port conflicts
- Resource exhaustion (OOM)

### Step 3: Check Dependencies

Verify service dependencies are running:

```python
# Check dependencies
deps = await check_service_dependencies(container_name)

if deps["status"] == "error":
    # Dependencies not met
    missing = deps.get("missing_services", [])
    return {
        "issue": "Missing dependencies",
        "missing": missing,
        "action": f"Start dependencies: {', '.join(missing)}"
    }
```

**What to check:**
- Database services running
- Required network services available
- External dependencies accessible

### Step 4: Check System Resources

Verify system has sufficient resources:

```python
# Check system resources
resources = await check_system_resources()

# Check disk space
disk = await check_disk_space()

# Analyze resource issues
issues = []
if resources["memory"]["usage_percent"] > 90:
    issues.append("High memory usage")
if resources["cpu"]["usage_percent"] > 90:
    issues.append("High CPU usage")
if disk["usage_percent"] > 90:
    issues.append("Low disk space")
```

**What to check:**
- Memory usage (OOM kills)
- CPU usage (throttling)
- Disk space (write failures)
- Load average

### Step 5: Check Port Conflicts

Verify ports are available:

```python
# Get container port from docker-compose or status
# Check if port is in use
port_status = await check_port_status(port)

if not port_status["available"]:
    # Port conflict
    conflicting_service = port_status.get("service")
    return {
        "issue": "Port conflict",
        "port": port,
        "conflicting_service": conflicting_service,
        "action": f"Change port or stop {conflicting_service}"
    }
```

### Step 6: Identify Root Cause

Based on collected information, identify the root cause:

**Common Issues:**

1. **Container Not Found**
   - Issue: Container doesn't exist
   - Action: Verify container name, check if it was removed

2. **Container Exited**
   - Check logs for exit reason
   - Common: OOM kill, crash, configuration error

3. **Health Check Failing**
   - Check health check endpoint
   - Verify service is responding internally
   - Check dependencies

4. **Port Conflict**
   - Another service using the port
   - Action: Change port or stop conflicting service

5. **Missing Dependencies**
   - Required services not running
   - Action: Start dependencies first

6. **Resource Exhaustion**
   - Out of memory
   - Disk full
   - Action: Free resources or increase limits

7. **Configuration Error**
   - Invalid docker-compose.yml
   - Missing environment variables
   - Action: Validate configuration

8. **Network Issues**
   - Can't connect to dependencies
   - DNS resolution failures
   - Action: Check network configuration

## MCP Tools Used

This skill uses the following MCP tools:

1. **`docker_container_status`** - Get container status and recent logs
2. **`docker_view_logs`** - View detailed container logs
3. **`check_service_dependencies`** - Verify dependencies are running
4. **`check_system_resources`** - Check CPU, memory, load
5. **`check_disk_space`** - Check disk space availability
6. **`find_service_by_port`** - Check for port conflicts

## Examples

### Example 1: Container Won't Start

**Symptom**: Container exits immediately after start

**Workflow**:
```python
# Step 1: Check status
status = await docker_container_status("my-service")
# Returns: {"running": false, "state": "exited"}

# Step 2: View logs
logs = await docker_view_logs("my-service", lines=50)
# Find: "Error: database connection refused"

# Step 3: Check dependencies
deps = await check_service_dependencies("my-service")
# Returns: {"missing_services": ["postgres"]}

# Root cause: Missing database dependency
# Action: Start postgres first, then my-service
```

### Example 2: Container Unhealthy

**Symptom**: Container running but health check failing

**Workflow**:
```python
# Step 1: Check status
status = await docker_container_status("my-service")
# Returns: {"running": true, "health": "unhealthy"}

# Step 2: View logs
logs = await docker_view_logs("my-service", lines=100)
# Find: "Health check endpoint returning 500"

# Step 3: Check resources
resources = await check_system_resources()
# Returns: {"memory": {"usage_percent": 95}}

# Root cause: High memory usage causing health check failures
# Action: Increase memory limit or reduce memory usage
```

### Example 3: Port Conflict

**Symptom**: Container fails to start with "port already in use"

**Workflow**:
```python
# Step 1: Check status
status = await docker_container_status("my-service")
# Returns: {"running": false, "state": "exited"}

# Step 2: View logs
logs = await docker_view_logs("my-service", lines=20)
# Find: "Error: bind: address already in use :8099"

# Step 3: Check port
port_status = await check_port_status(8099)
# Returns: {"available": false, "service": "other-service"}

# Root cause: Port 8099 already in use by other-service
# Action: Change port in docker-compose.yml or stop other-service
```

## Error Handling

### Container Not Found

**Action**: Verify container name, check if it was removed or renamed

### Logs Unavailable

**Action**: Container may have exited too quickly, check docker events or system logs

### Dependencies Unclear

**Action**: Check docker-compose.yml for `depends_on` and `healthcheck` configurations

### Resource Issues

**Action**: 
- Memory: Increase container memory limit or reduce usage
- Disk: Clean up old images/volumes or increase disk space
- CPU: Check for resource limits or throttling

## Recommended Fixes by Issue

| Issue | Recommended Fix |
|-------|----------------|
| Missing dependencies | Start dependencies first, then service |
| Port conflict | Change port or stop conflicting service |
| Out of memory | Increase memory limit or reduce usage |
| Disk full | Clean up old resources or increase disk |
| Configuration error | Validate docker-compose.yml and .env files |
| Network issue | Check network configuration and DNS |
| Health check failing | Verify health check endpoint and dependencies |

## Related Skills

- **`troubleshoot-service-startup`** - If service fails to start
- **`system-health-check`** - For comprehensive system verification
- **`standard-deployment`** - If issue occurred after deployment

## Notes

- Always check logs first - they contain the most diagnostic information
- Check dependencies before assuming the service itself is broken
- Resource issues can cause subtle failures - always verify resources
- Port conflicts are common - always check ports when services won't start

