---
name: deploy-new-service
description: Complete new service setup: create config → validate → deploy → verify
category: deployment
mcp_tools_required:
  - read_file
  - write_file
  - validate_docker_compose
  - check_port_status
  - git_deploy
  - docker_compose_up
  - docker_container_status
prerequisites:
  - Service name and requirements known
  - Port availability checked
  - MCP tools available
---

# Deploy New Service

## When to Use This Skill

Use this skill when:
- Setting up a new application/service on the server
- Adding a new Docker service to the infrastructure
- Deploying a new containerized application

## Overview

This skill provides a complete workflow for deploying a new service:
1. Check prerequisites (port availability, dependencies)
2. Create docker-compose.yml configuration
3. Create .env file from template
4. Validate configuration
5. Deploy and start service
6. Verify service is running
7. Add to homepage (if applicable)

## Workflow Steps

### Step 1: Check Prerequisites

Verify prerequisites before creating configuration:

```python
# Check port availability
port_status = await check_port_status(port)

if not port_status["available"]:
    return {
        "status": "error",
        "issue": "Port conflict",
        "port": port,
        "conflicting_service": port_status.get("service"),
        "action": f"Use different port or stop {port_status.get('service')}"
    }

# Check for existing service
existing_containers = await docker_list_containers(filter_app=app_name)
if existing_containers["containers"]:
    return {
        "status": "error",
        "issue": "Service already exists",
        "action": "Use different name or remove existing service"
    }
```

**What to check:**
- Port is available (no conflicts)
- Service name is unique
- Dependencies are available (if any)

### Step 2: Create Docker Compose Configuration

Create docker-compose.yml following server patterns:

```python
# Read template or create from scratch
# Follow patterns from existing apps

docker_compose_content = f"""
version: '3.8'

services:
  {service_name}:
    image: {image}
    container_name: {container_name}
    ports:
      - "{port}:{internal_port}"
    environment:
      - ENV_VAR1=${{ENV_VAR1}}
    volumes:
      - ./data:/data
    networks:
      - my-network
    labels:
      - "homepage.group={group}"
      - "homepage.name={display_name}"
      - "homepage.icon={icon}"
      - "homepage.href=http://192.168.86.47:{port}"
      - "homepage.description={description}"
    healthcheck:
      test: ["CMD", "health-check-command"]
      interval: 10s
      timeout: 5s
      retries: 5

networks:
  my-network:
    external: true
"""

# Write docker-compose.yml
write_result = await write_file(
    file_path=f"apps/{app_name}/docker-compose.yml",
    content=docker_compose_content,
    backup=False
)
```

**Key patterns to follow:**
- Use `my-network` external network
- Add homepage labels for services with UI
- Include health checks for critical services
- Use environment variables from .env file
- Follow port conventions (see APPS_DOCUMENTATION.md)

### Step 3: Create Environment File

Create .env file from template:

```python
# Create .env.template (for documentation)
env_template = f"""
# {service_name} Configuration
ENV_VAR1=value1
ENV_VAR2=value2
SECRET_KEY=generate-with-openssl-rand-hex-32
"""

# Write template
await write_file(
    file_path=f"apps/{app_name}/env.template",
    content=env_template
)

# Note: .env file should be created on server manually
# (not committed to git)
```

**Important:**
- `.env.template` goes in git (documentation)
- `.env` file stays on server only (gitignored)
- Generate secrets with `openssl rand -hex 32`

### Step 4: Validate Configuration

Validate docker-compose.yml before deploying:

```python
# Validate docker-compose.yml
validation = await validate_docker_compose(
    file_path=f"apps/{app_name}/docker-compose.yml"
)

if validation["status"] != "success":
    return {
        "status": "error",
        "issue": "Configuration validation failed",
        "errors": validation.get("errors", []),
        "action": "Fix configuration errors before deploying"
    }
```

**What to validate:**
- YAML syntax
- Required fields present
- Port conflicts
- Network configuration
- Volume paths

### Step 5: Deploy Configuration

Deploy using git workflow:

```python
# Deploy configuration
deploy_result = await git_deploy(
    commit_message=f"Add new service: {service_name}",
    files=[f"apps/{app_name}/docker-compose.yml", f"apps/{app_name}/env.template"]
)

if deploy_result["status"] != "success":
    return {
        "status": "error",
        "issue": "Deployment failed",
        "deploy_result": deploy_result
    }
```

### Step 6: Start Service

Start the service using docker-compose:

```python
# Start service
start_result = await docker_compose_up(
    app_path=f"apps/{app_name}",
    build=False  # Set to True if building from source
)

if start_result["status"] != "success":
    return {
        "status": "error",
        "issue": "Service failed to start",
        "start_result": start_result,
        "action": "Check logs and configuration"
    }
```

### Step 7: Verify Service

Verify service is running and healthy:

```python
# Check container status
status = await docker_container_status(container_name)

if not status["running"]:
    return {
        "status": "error",
        "issue": "Service not running",
        "status_detail": status,
        "action": "Check logs and configuration"
    }

if status["health"] == "unhealthy":
    return {
        "status": "warning",
        "issue": "Service running but unhealthy",
        "status_detail": status,
        "action": "Check logs and health check configuration"
    }

# Verify HTTP endpoint (if applicable)
if has_http_endpoint:
    # Test connectivity
    connectivity = await test_connectivity("192.168.86.47", port)
    if not connectivity["success"]:
        return {
            "status": "warning",
            "issue": "HTTP endpoint not responding",
            "action": "Check service logs and configuration"
        }
```

**What to verify:**
- Container is running
- Health check passing (if configured)
- HTTP endpoint responding (if applicable)
- No error logs

### Step 8: Update Documentation

Update relevant documentation:

```python
# Update APPS_DOCUMENTATION.md (if exists)
# Add service to homepage (automatic via labels)
# Update any relevant README files
```

## MCP Tools Used

This skill uses the following MCP tools:

1. **`check_port_status`** - Verify port availability
2. **`read_file`** - Read templates or existing configs
3. **`write_file`** - Create docker-compose.yml and env.template
4. **`validate_docker_compose`** - Validate configuration
5. **`git_deploy`** - Deploy configuration to server
6. **`docker_compose_up`** - Start the service
7. **`docker_container_status`** - Verify service is running
8. **`test_connectivity`** - Verify HTTP endpoint (if applicable)

## Examples

### Example 1: Deploy Simple Web Service

**Service**: New web application on port 8099

**Workflow**:
```python
# Step 1: Check port
port_status = await check_port_status(8099)
# Returns: {"available": true}

# Step 2: Create docker-compose.yml
await write_file("apps/new-app/docker-compose.yml", compose_content)

# Step 3: Create env.template
await write_file("apps/new-app/env.template", env_template)

# Step 4: Validate
validation = await validate_docker_compose("apps/new-app/docker-compose.yml")
# Returns: {"status": "success"}

# Step 5: Deploy
deploy_result = await git_deploy("Add new-app service")

# Step 6: Start
start_result = await docker_compose_up("apps/new-app")

# Step 7: Verify
status = await docker_container_status("new-app")
# Returns: {"running": true, "health": "healthy"}
```

### Example 2: Deploy Service with Database

**Service**: Application requiring PostgreSQL

**Workflow**:
```python
# Step 1: Check dependencies
# Verify PostgreSQL is available (check existing containers or create new)

# Step 2: Create docker-compose.yml with database
# Include depends_on and healthcheck for database

# Step 3: Create .env with database connection string
# Use existing PostgreSQL or create new

# Step 4-7: Same as Example 1, but verify database connection
```

## Configuration Patterns

### Standard Docker Compose Structure

```yaml
version: '3.8'

services:
  service-name:
    image: image:tag
    container_name: service-name
    ports:
      - "PORT:INTERNAL_PORT"
    environment:
      - VAR=${{VAR}}
    env_file:
      - .env
    volumes:
      - ./data:/data
    networks:
      - my-network
    labels:
      - "homepage.group=Category"
      - "homepage.name=Service Name"
      - "homepage.icon=si-icon"
      - "homepage.href=http://192.168.86.47:PORT"
      - "homepage.description=Description"
    healthcheck:
      test: ["CMD", "health-check"]
      interval: 10s
      timeout: 5s
      retries: 5
    depends_on:
      - database  # If needed
      - redis      # If needed

networks:
  my-network:
    external: true
```

### Homepage Labels

Always include for services with UI:
- `homepage.group` - Category (e.g., "Media", "Automation")
- `homepage.name` - Display name
- `homepage.icon` - Simple Icons name (e.g., "si-sonarr")
- `homepage.href` - URL (use local IP: `http://192.168.86.47:PORT`)
- `homepage.description` - Brief description

### Traefik Labels (If Using HTTPS)

For services with domain names:
```yaml
labels:
  - "traefik.enable=true"
  - "traefik.http.routers.service.rule=Host(`service.domain.com`)"
  - "traefik.http.routers.service.entrypoints=websecure"
  - "traefik.http.routers.service.tls.certresolver=myresolver"
  - "traefik.http.services.service.loadbalancer.server.port=PORT"
```

**Important**: When adding Traefik subdomains, also update Cloudflare DDNS configuration.

## Error Handling

### Port Conflict

**Action**: 
- Use different port
- Check `apps/docs/APPS_DOCUMENTATION.md` for port usage
- Stop conflicting service if not needed

### Configuration Validation Failed

**Action**:
- Fix YAML syntax errors
- Verify required fields
- Check for typos in service names, networks, etc.

### Service Won't Start

**Action**:
- Check logs: `docker_view_logs(container_name)`
- Verify .env file exists on server
- Check dependencies are running
- Use `troubleshoot-container-failure` skill

### Service Unhealthy

**Action**:
- Check health check command is correct
- Verify health check endpoint is accessible
- Check service logs for errors
- Use `troubleshoot-container-failure` skill

## Best Practices

1. **Check Port First**: Always verify port availability before creating config
2. **Follow Patterns**: Use existing apps as templates
3. **Validate Before Deploy**: Always validate docker-compose.yml
4. **Include Health Checks**: Add health checks for critical services
5. **Add Homepage Labels**: Make service discoverable in homepage
6. **Document Secrets**: Use env.template to document required variables
7. **Test Locally First**: If possible, test configuration locally
8. **Verify After Start**: Always verify service is running and healthy

## Related Skills

- **`standard-deployment`** - For updating existing services
- **`troubleshoot-container-failure`** - If service fails to start
- **`system-health-check`** - For post-deployment verification

## Notes

- `.env` files are server-only (never commit to git)
- Always use `my-network` external network
- Check `apps/docs/APPS_DOCUMENTATION.md` for port conventions
- Follow existing app patterns for consistency
- Update Cloudflare DDNS when adding Traefik subdomains

