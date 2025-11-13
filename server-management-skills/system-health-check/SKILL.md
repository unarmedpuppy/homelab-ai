---
name: system-health-check
description: Comprehensive system verification: disk space → resources → services → summary
category: maintenance
mcp_tools_required:
  - check_disk_space
  - check_system_resources
  - docker_list_containers
  - service_health_check
  - get_recent_errors
prerequisites:
  - MCP tools available
---

# System Health Check

## When to Use This Skill

Use this skill when:
- Regular maintenance checks
- After system changes
- Troubleshooting multiple issues
- Pre-deployment verification
- Post-incident verification
- User requests system status

## Overview

This skill performs a comprehensive system health check:
1. Check disk space
2. Check system resources (CPU, memory, load)
3. Check all container statuses
4. Check service health
5. Check for recent errors
6. Generate health report

## Workflow Steps

### Step 1: Check Disk Space

Verify disk space availability:

```python
# Check disk space
disk = await check_disk_space()

# Analyze
disk_status = "ok"
if disk["usage_percent"] > 90:
    disk_status = "critical"
elif disk["usage_percent"] > 80:
    disk_status = "warning"

issues = []
if disk_status != "ok":
    issues.append({
        "type": "disk_space",
        "severity": disk_status,
        "usage_percent": disk["usage_percent"],
        "free_space": disk["free_space"],
        "action": "Clean up old resources or increase disk space"
    })
```

**What to check:**
- Root filesystem usage
- Critical paths (if specified)
- Status: ok, warning (>80%), critical (>90%)

### Step 2: Check System Resources

Verify CPU, memory, and load:

```python
# Check system resources
resources = await check_system_resources()

# Analyze
resource_issues = []
if resources["memory"]["usage_percent"] > 90:
    resource_issues.append({
        "type": "memory",
        "severity": "critical",
        "usage_percent": resources["memory"]["usage_percent"],
        "action": "Free memory or increase limits"
    })

if resources["cpu"]["usage_percent"] > 90:
    resource_issues.append({
        "type": "cpu",
        "severity": "warning",
        "usage_percent": resources["cpu"]["usage_percent"],
        "action": "Investigate high CPU processes"
    })

if resources["load_average"]["1min"] > resources["cpu"]["cores"] * 2:
    resource_issues.append({
        "type": "load",
        "severity": "warning",
        "load_1min": resources["load_average"]["1min"],
        "action": "System under heavy load"
    })
```

**What to check:**
- Memory usage (critical if >90%)
- CPU usage (warning if >90%)
- Load average (warning if >2x CPU cores)

### Step 3: Check All Containers

Get status of all containers:

```python
# List all containers
containers = await docker_list_containers()

# Analyze container health
container_issues = []
for container in containers["containers"]:
    if container["status"] == "stopped":
        container_issues.append({
            "container": container["name"],
            "issue": "Container stopped",
            "severity": "warning"
        })
    elif container["health"] == "unhealthy":
        container_issues.append({
            "container": container["name"],
            "issue": "Container unhealthy",
            "severity": "critical"
        })
```

**What to check:**
- All containers running
- Health status (healthy, unhealthy, unknown)
- Stopped containers
- Recent restarts

### Step 4: Check Critical Services

Verify critical services are healthy:

```python
# Critical services to check
critical_services = [
    "traefik",      # Reverse proxy
    "sonarr",       # Media automation
    "radarr",       # Media automation
    "trading-bot",  # Trading bot
    "jellyfin",     # Media server
]

service_health = {}
for service in critical_services:
    health = await service_health_check(service)
    service_health[service] = health
    
    if health["status"] != "healthy":
        issues.append({
            "type": "service_health",
            "service": service,
            "severity": "critical" if service in ["traefik"] else "warning",
            "status": health["status"],
            "issues": health.get("issues", [])
        })
```

**What to check:**
- Critical services responding
- Health endpoints accessible
- Service-specific health checks

### Step 5: Check Recent Errors

Look for recent errors across services:

```python
# Get recent errors
errors = await get_recent_errors(lines=50)

# Analyze error patterns
error_summary = {}
for error in errors.get("errors", []):
    service = error.get("service", "unknown")
    if service not in error_summary:
        error_summary[service] = []
    error_summary[service].append(error)

# Report services with errors
if error_summary:
    issues.append({
        "type": "recent_errors",
        "services_with_errors": list(error_summary.keys()),
        "total_errors": sum(len(e) for e in error_summary.values()),
        "action": "Review error logs for details"
    })
```

**What to check:**
- Recent error logs
- Error patterns
- Services with frequent errors

### Step 6: Generate Health Report

Compile all findings into a health report:

```python
# Generate report
report = {
    "timestamp": datetime.now().isoformat(),
    "overall_status": "healthy",
    "summary": {
        "disk_space": disk_status,
        "resources": "ok" if not resource_issues else "warning",
        "containers": {
            "total": len(containers["containers"]),
            "running": len([c for c in containers["containers"] if c["status"] == "running"]),
            "stopped": len([c for c in containers["containers"] if c["status"] == "stopped"]),
            "unhealthy": len([c for c in containers["containers"] if c["health"] == "unhealthy"])
        },
        "critical_services": {
            service: health["status"] 
            for service, health in service_health.items()
        }
    },
    "issues": issues,
    "recommendations": generate_recommendations(issues)
}

# Determine overall status
if any(i["severity"] == "critical" for i in issues):
    report["overall_status"] = "critical"
elif any(i["severity"] == "warning" for i in issues):
    report["overall_status"] = "warning"
```

## MCP Tools Used

This skill uses the following MCP tools:

1. **`check_disk_space`** - Check disk usage and availability
2. **`check_system_resources`** - Check CPU, memory, load average
3. **`docker_list_containers`** - List all containers and their status
4. **`service_health_check`** - Check health of specific services
5. **`get_recent_errors`** - Get recent error logs across services

## Examples

### Example 1: Regular Health Check

**User Request**: "Check system health"

**Workflow**:
```python
# Run comprehensive health check
report = await system_health_check()

# Report findings
if report["overall_status"] == "healthy":
    return "System is healthy. All services running, resources normal."
elif report["overall_status"] == "warning":
    return f"System has {len(report['issues'])} warning(s). Review report."
else:
    return f"System has critical issues. {len([i for i in report['issues'] if i['severity'] == 'critical'])} critical issue(s) found."
```

### Example 2: Post-Deployment Verification

**User Request**: "Verify system after deployment"

**Workflow**:
```python
# Run health check
report = await system_health_check()

# Focus on recently changed services
# Check for new errors
# Verify all services still healthy

if report["overall_status"] != "healthy":
    # Deployment may have caused issues
    return {
        "status": "deployment_verification_failed",
        "issues": report["issues"],
        "action": "Review issues and consider rollback"
    }
```

### Example 3: Troubleshooting Multiple Issues

**User Request**: "System seems slow, check everything"

**Workflow**:
```python
# Comprehensive check
report = await system_health_check()

# Identify resource issues
resource_issues = [i for i in report["issues"] if i["type"] in ["memory", "cpu", "load", "disk_space"]]

if resource_issues:
    return {
        "root_cause": "Resource exhaustion",
        "issues": resource_issues,
        "recommendations": [
            "Free up memory/disk",
            "Check for resource-intensive processes",
            "Consider increasing limits"
        ]
    }
```

## Health Report Format

```json
{
  "timestamp": "2025-01-10T12:00:00Z",
  "overall_status": "healthy|warning|critical",
  "summary": {
    "disk_space": "ok|warning|critical",
    "resources": "ok|warning",
    "containers": {
      "total": 50,
      "running": 48,
      "stopped": 2,
      "unhealthy": 1
    },
    "critical_services": {
      "traefik": "healthy",
      "sonarr": "healthy",
      "radarr": "unhealthy"
    }
  },
  "issues": [
    {
      "type": "container_health",
      "container": "radarr",
      "severity": "critical",
      "issue": "Container unhealthy",
      "action": "Use troubleshoot-container-failure skill"
    }
  ],
  "recommendations": [
    "Review radarr container health",
    "Check disk space (85% used)"
  ]
}
```

## Error Handling

### Tool Failures

If an MCP tool fails:
- Log the failure
- Continue with other checks
- Report tool failure in issues

### Partial Results

If some checks fail:
- Report partial results
- Indicate which checks failed
- Suggest manual verification

## Recommendations by Issue Type

| Issue Type | Recommendation |
|------------|----------------|
| Disk space >90% | Clean up old Docker images/volumes, remove old logs |
| Disk space >80% | Monitor closely, plan cleanup |
| Memory >90% | Check for memory leaks, increase limits, restart services |
| CPU >90% | Identify CPU-intensive processes, check for infinite loops |
| High load | Check for resource contention, verify all services needed |
| Container stopped | Use troubleshoot-container-failure skill |
| Container unhealthy | Use troubleshoot-container-failure skill |
| Service errors | Review error logs, check service configuration |

## Related Skills

- **`troubleshoot-container-failure`** - If containers are unhealthy
- **`cleanup-old-resources`** - If disk space is low
- **`standard-deployment`** - For pre/post deployment checks

## Notes

- Run this skill regularly (daily/weekly) for proactive monitoring
- Use after deployments to verify system health
- Use when troubleshooting to get comprehensive system view
- Health report can be saved for historical tracking

