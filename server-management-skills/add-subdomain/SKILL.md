---
name: add-subdomain
description: Add subdomain configuration to a service: Homepage labels, Traefik routing, and optionally Cloudflare DDNS (with explicit approval)
category: configuration
mcp_tools_required:
  - read_file
  - write_file
  - get_available_port
  - check_port_status
  - git_deploy
prerequisites:
  - Service docker-compose.yml exists
  - Service is running or ready to deploy
  - Subdomain name chosen (e.g., "myapp.server.unarmedpuppy.com")
  - Service port known
  - Explicit approval required for internet exposure (Cloudflare DDNS)
---

# Add Subdomain Configuration

## When to Use This Skill

Use this skill when:
- Adding a subdomain to an existing service
- Configuring Traefik routing for a new service
- Adding Homepage labels for service discovery
- Setting up HTTPS access via Traefik
- **IMPORTANT**: Only update Cloudflare DDNS if explicitly approved by human user for internet exposure

## Overview

This skill adds complete subdomain configuration to a service:
1. Add Homepage labels (for service discovery)
2. Add Traefik labels (HTTPS routing with automatic SSL)
3. Optionally update Cloudflare DDNS (only with explicit approval)
4. Verify configuration
5. Deploy changes

**⚠️ SECURITY**: By default, services are NOT exposed to the internet. Cloudflare DDNS updates require explicit human approval.

## Workflow Steps

### Step 1: Verify Prerequisites

Before adding subdomain configuration, verify:

```python
# Check service exists and has docker-compose.yml
compose_file = f"apps/{app_name}/docker-compose.yml"
compose_content = await read_file(compose_file)

if not compose_content:
    return {
        "status": "error",
        "issue": "docker-compose.yml not found",
        "action": f"Create docker-compose.yml for {app_name} first"
    }

# Verify service port is known
# Check if port is already configured in docker-compose.yml
# Or use get_available_port if port needs to be assigned
```

**What to verify:**
- Service docker-compose.yml exists
- Service port is known or can be determined
- Subdomain name is valid (format: `name.server.unarmedpuppy.com`)
- Service is on `my-network` (required for Traefik)

### Step 2: Check Port Configuration

Verify port is available and configured:

```python
# If port not specified, find available port
if not port:
    available = await get_available_port(preferred_range="3000-3100", count=1)
    if not available["available_ports"]:
        return {
            "status": "error",
            "issue": "No available ports in range",
            "action": "Specify a port or use different range"
        }
    port = available["recommendation"]

# Verify port is not in use
port_status = await check_port_status(port)
if port_status.get("in_use"):
    return {
        "status": "error",
        "issue": "Port already in use",
        "port": port,
        "conflicting_service": port_status.get("containers", []),
        "action": "Use different port or stop conflicting service"
    }
```

### Step 3: Add Homepage Labels

Add Homepage labels for service discovery:

```python
# Homepage labels template
homepage_labels = f"""
      - "homepage.group={group}"
      - "homepage.name={display_name}"
      - "homepage.icon={icon}"
      - "homepage.href=https://{subdomain}"
      - "homepage.description={description}"
"""

# Insert into docker-compose.yml under service labels section
```

**Homepage Label Format:**
```yaml
labels:
  - "homepage.group=Category"  # e.g., "Media", "Automation", "Infrastructure"
  - "homepage.name=Service Name"
  - "homepage.icon=si-iconname"  # Simple Icons name (e.g., si-plex, si-sonarr)
  - "homepage.href=https://subdomain.server.unarmedpuppy.com"
  - "homepage.description=Service description"
```

**Common Homepage Groups:**
- `Infrastructure` - Core services (Traefik, Grafana, etc.)
- `Media` - Media services (Plex, Jellyfin, etc.)
- `Automation` - Automation tools (n8n, Home Assistant, etc.)
- `Finance & Trading` - Financial tools
- `Apps` - General applications
- `Services` - Utility services

### Step 4: Add Traefik Labels

Add Traefik labels for HTTPS routing:

```python
# Traefik labels template
traefik_labels = f"""
      - "traefik.enable=true"
      - "traefik.http.routers.{service_name}-redirect.rule=Host(`{subdomain}`)"
      - "traefik.http.routers.{service_name}-redirect.entrypoints=web"
      - "traefik.http.middlewares.{service_name}-redirect.redirectscheme.scheme=https"
      - "traefik.http.routers.{service_name}-redirect.middlewares={service_name}-redirect"
      - "traefik.http.routers.{service_name}.rule=Host(`{subdomain}`)"
      - "traefik.http.routers.{service_name}.entrypoints=websecure"
      - "traefik.http.routers.{service_name}.tls.certresolver=myresolver"
      - "traefik.http.routers.{service_name}.service={service_name}"
      - "traefik.http.services.{service_name}.loadbalancer.server.port={internal_port}"
      - "traefik.docker.network=my-network"
"""

# Insert into docker-compose.yml under service labels section
```

**Traefik Label Format:**
```yaml
labels:
  # Enable Traefik
  - "traefik.enable=true"
  
  # HTTP to HTTPS redirect
  - "traefik.http.routers.{service}-redirect.rule=Host(`subdomain.server.unarmedpuppy.com`)"
  - "traefik.http.routers.{service}-redirect.entrypoints=web"
  - "traefik.http.middlewares.{service}-redirect.redirectscheme.scheme=https"
  - "traefik.http.routers.{service}-redirect.middlewares={service}-redirect"
  
  # Main HTTPS router
  - "traefik.http.routers.{service}.rule=Host(`subdomain.server.unarmedpuppy.com`)"
  - "traefik.http.routers.{service}.entrypoints=websecure"
  - "traefik.http.routers.{service}.tls.certresolver=myresolver"
  - "traefik.http.routers.{service}.service={service}"
  - "traefik.http.services.{service}.loadbalancer.server.port={internal_port}"
  - "traefik.docker.network=my-network"
```

**Important Notes:**
- `{service}` should match the docker-compose service name
- `{internal_port}` is the port the service listens on inside the container (usually 80, 3000, 8080, etc.)
- `my-network` is the external Docker network Traefik uses
- `myresolver` is the Let's Encrypt certificate resolver configured in Traefik

### Step 5: Verify Network Configuration

Ensure service is on `my-network`:

```python
# Check if service has network configuration
if "my-network" not in compose_content:
    # Add network configuration
    network_config = """
networks:
  my-network:
    external: true
"""
    # Add to docker-compose.yml
    
# Verify service uses my-network
if f"  {service_name}:" in compose_content:
    # Check if networks section exists under service
    # If not, add it
```

**Network Configuration:**
```yaml
services:
  service-name:
    # ... other config ...
    networks:
      - my-network

networks:
  my-network:
    external: true
```

### Step 6: Update Cloudflare DDNS (ONLY WITH EXPLICIT APPROVAL)

**⚠️ CRITICAL**: Only update Cloudflare DDNS if:
1. Human user has explicitly approved internet exposure
2. Service is intended to be publicly accessible
3. Security considerations have been reviewed

**Default Behavior**: Do NOT update Cloudflare DDNS unless explicitly approved.

```python
# Check if internet exposure is approved
if not internet_exposure_approved:
    return {
        "status": "success",
        "message": "Subdomain configuration added (local access only)",
        "note": "Cloudflare DDNS not updated - service not exposed to internet",
        "action": "If internet exposure needed, get explicit approval and run again with internet_exposure_approved=true"
    }

# If approved, update Cloudflare DDNS
if internet_exposure_approved:
    # Read cloudflare-ddns docker-compose.yml
    ddns_file = "apps/cloudflare-ddns/docker-compose.yml"
    ddns_content = await read_file(ddns_file)
    
    # Extract current DOMAINS list
    # Add new subdomain to list
    # Update DOMAINS environment variable
    
    # Write updated file
    await write_file(ddns_file, updated_ddns_content)
    
    return {
        "status": "success",
        "message": "Subdomain added and Cloudflare DDNS updated",
        "note": "Service will be accessible from internet after DDNS container restarts"
    }
```

**Cloudflare DDNS Update Format:**
```yaml
environment:
  - DOMAINS=existing1.server.unarmedpuppy.com, existing2.server.unarmedpuppy.com, new-subdomain.server.unarmedpuppy.com
```

**Important:**
- Add subdomain to comma-separated list
- Do not remove existing domains
- Restart cloudflare-ddns container after update (or it will auto-update)

### Step 7: Update Docker Compose File

Update the docker-compose.yml with all labels:

```python
# Read current docker-compose.yml
compose_content = await read_file(f"apps/{app_name}/docker-compose.yml")

# Parse YAML structure
# Find service section
# Add labels section (or append to existing)

# Combine all labels
all_labels = homepage_labels + traefik_labels

# Insert into service labels section
updated_compose = insert_labels_into_service(compose_content, service_name, all_labels)

# Write updated file
await write_file(f"apps/{app_name}/docker-compose.yml", updated_compose)
```

**Label Insertion Pattern:**
```yaml
services:
  service-name:
    image: image:tag
    container_name: service-name
    # ... other config ...
    networks:
      - my-network
    labels:
      # Homepage labels
      - "homepage.group=Category"
      - "homepage.name=Service Name"
      - "homepage.icon=si-icon"
      - "homepage.href=https://subdomain.server.unarmedpuppy.com"
      - "homepage.description=Description"
      # Traefik labels
      - "traefik.enable=true"
      - "traefik.http.routers.service-redirect.rule=Host(`subdomain.server.unarmedpuppy.com`)"
      # ... rest of Traefik labels ...
```

### Step 8: Deploy Changes

Deploy updated configuration:

```python
# Deploy docker-compose.yml changes
deploy_result = await git_deploy(
    commit_message=f"Add subdomain configuration for {app_name}: {subdomain}",
    files=[f"apps/{app_name}/docker-compose.yml"]
)

# If Cloudflare DDNS was updated, deploy that too
if internet_exposure_approved:
    deploy_result = await git_deploy(
        commit_message=f"Add {subdomain} to Cloudflare DDNS",
        files=["apps/cloudflare-ddns/docker-compose.yml"]
    )
```

### Step 9: Restart Services

Restart affected services:

```python
# Restart service to apply new labels
restart_result = await docker_compose_restart(
    app_path=f"apps/{app_name}",
    services=[service_name]
)

# If Cloudflare DDNS was updated, restart it
if internet_exposure_approved:
    restart_result = await docker_compose_restart(
        app_path="apps/cloudflare-ddns",
        services=["cloudflare-ddns"]
    )
```

### Step 10: Verify Configuration

Verify subdomain is working:

```python
# Wait a moment for Traefik to pick up changes
await asyncio.sleep(5)

# Check if Traefik has the route
# (This would require a Traefik API check - may not be available)

# Verify service is accessible
# Test HTTPS endpoint
```

## MCP Tools Used

This skill uses the following MCP tools:

1. **`read_file`** - Read docker-compose.yml and Cloudflare DDNS config
2. **`write_file`** - Update docker-compose.yml and Cloudflare DDNS config
3. **`get_available_port`** - Find available port if not specified
4. **`check_port_status`** - Verify port is not in use
5. **`git_deploy`** - Deploy configuration changes

## Examples

### Example 1: Add Subdomain to Existing Service (Local Only)

**Service**: `myapp` on port 8080
**Subdomain**: `myapp.server.unarmedpuppy.com`
**Internet Exposure**: NOT approved (default)

**Workflow:**
```python
# Step 1: Read docker-compose.yml
compose = await read_file("apps/myapp/docker-compose.yml")

# Step 2: Add Homepage labels
homepage_labels = """
      - "homepage.group=Apps"
      - "homepage.name=My App"
      - "homepage.icon=si-app"
      - "homepage.href=https://myapp.server.unarmedpuppy.com"
      - "homepage.description=My application"
"""

# Step 3: Add Traefik labels
traefik_labels = """
      - "traefik.enable=true"
      - "traefik.http.routers.myapp-redirect.rule=Host(`myapp.server.unarmedpuppy.com`)"
      - "traefik.http.routers.myapp-redirect.entrypoints=web"
      - "traefik.http.middlewares.myapp-redirect.redirectscheme.scheme=https"
      - "traefik.http.routers.myapp-redirect.middlewares=myapp-redirect"
      - "traefik.http.routers.myapp.rule=Host(`myapp.server.unarmedpuppy.com`)"
      - "traefik.http.routers.myapp.entrypoints=websecure"
      - "traefik.http.routers.myapp.tls.certresolver=myresolver"
      - "traefik.http.routers.myapp.service=myapp"
      - "traefik.http.services.myapp.loadbalancer.server.port=80"
      - "traefik.docker.network=my-network"
"""

# Step 4: Update docker-compose.yml
updated_compose = insert_labels(compose, "myapp", homepage_labels + traefik_labels)
await write_file("apps/myapp/docker-compose.yml", updated_compose)

# Step 5: Deploy (Cloudflare DDNS NOT updated - local only)
await git_deploy("Add subdomain for myapp (local access only)")

# Step 6: Restart service
await docker_compose_restart("apps/myapp", ["myapp"])

# Result: Service accessible at https://myapp.server.unarmedpuppy.com (local network only)
# Cloudflare DDNS NOT updated - not exposed to internet
```

### Example 2: Add Subdomain with Internet Exposure (Explicit Approval)

**Service**: `publicapp` on port 3000
**Subdomain**: `publicapp.server.unarmedpuppy.com`
**Internet Exposure**: ✅ Explicitly approved by human user

**Workflow:**
```python
# Steps 1-4: Same as Example 1

# Step 5: Update Cloudflare DDNS (with approval)
if internet_exposure_approved:
    ddns_content = await read_file("apps/cloudflare-ddns/docker-compose.yml")
    
    # Extract current DOMAINS
    # Add "publicapp.server.unarmedpuppy.com" to list
    updated_domains = existing_domains + ", publicapp.server.unarmedpuppy.com"
    
    # Update DOMAINS environment variable
    updated_ddns = update_domains_in_ddns(ddns_content, updated_domains)
    await write_file("apps/cloudflare-ddns/docker-compose.yml", updated_ddns)

# Step 6: Deploy both files
await git_deploy("Add subdomain for publicapp with internet exposure", 
                 files=["apps/publicapp/docker-compose.yml", "apps/cloudflare-ddns/docker-compose.yml"])

# Step 7: Restart both services
await docker_compose_restart("apps/publicapp", ["publicapp"])
await docker_compose_restart("apps/cloudflare-ddns", ["cloudflare-ddns"])

# Result: Service accessible from internet at https://publicapp.server.unarmedpuppy.com
```

## Configuration Patterns

### Standard Traefik Configuration

```yaml
labels:
  # Enable Traefik
  - "traefik.enable=true"
  
  # HTTP to HTTPS redirect
  - "traefik.http.routers.{service}-redirect.rule=Host(`{subdomain}`)"
  - "traefik.http.routers.{service}-redirect.entrypoints=web"
  - "traefik.http.middlewares.{service}-redirect.redirectscheme.scheme=https"
  - "traefik.http.routers.{service}-redirect.middlewares={service}-redirect"
  
  # Main HTTPS router
  - "traefik.http.routers.{service}.rule=Host(`{subdomain}`)"
  - "traefik.http.routers.{service}.entrypoints=websecure"
  - "traefik.http.routers.{service}.tls.certresolver=myresolver"
  - "traefik.http.routers.{service}.service={service}"
  - "traefik.http.services.{service}.loadbalancer.server.port={internal_port}"
  - "traefik.docker.network=my-network"
```

### Standard Homepage Configuration

```yaml
labels:
  - "homepage.group={category}"
  - "homepage.name={display_name}"
  - "homepage.icon={icon_name}"
  - "homepage.href=https://{subdomain}"
  - "homepage.description={description}"
```

### Cloudflare DDNS Update

```yaml
environment:
  - DOMAINS=domain1.server.unarmedpuppy.com, domain2.server.unarmedpuppy.com, newdomain.server.unarmedpuppy.com
```

## Error Handling

### Service Not Found

**Error**: docker-compose.yml not found

**Action**:
- Verify app_name is correct
- Check if service exists in `apps/` directory
- Use `deploy-new-service` skill first if service doesn't exist

### Port Already in Use

**Error**: Port conflict detected

**Action**:
- Use `get_available_port` to find alternative port
- Check `apps/docs/APPS_DOCUMENTATION.md` for port usage
- Stop conflicting service if not needed

### Network Not Configured

**Error**: Service not on `my-network`

**Action**:
- Add network configuration to docker-compose.yml
- Ensure `my-network` is external network
- Restart service after adding network

### Invalid Subdomain Format

**Error**: Subdomain doesn't match expected format

**Action**:
- Verify format: `name.server.unarmedpuppy.com`
- Check for typos
- Ensure subdomain is unique

### Cloudflare DDNS Update Failed

**Error**: Failed to update Cloudflare DDNS

**Action**:
- Verify internet_exposure_approved is true
- Check Cloudflare DDNS docker-compose.yml exists
- Verify DOMAINS format is correct (comma-separated)
- Restart cloudflare-ddns container manually

## Security Considerations

### Default: No Internet Exposure

**By default, services are NOT exposed to the internet:**
- Traefik labels added (local HTTPS access)
- Homepage labels added (service discovery)
- Cloudflare DDNS NOT updated (no internet access)

### Internet Exposure Requires Approval

**Only update Cloudflare DDNS if:**
1. ✅ Human user explicitly approves
2. ✅ Service is intended for public access
3. ✅ Security review completed
4. ✅ Authentication/authorization configured (if needed)

### Best Practices

1. **Start Local**: Always add subdomain for local access first
2. **Test Locally**: Verify service works on local network
3. **Security Review**: Review security before internet exposure
4. **Explicit Approval**: Never expose to internet without approval
5. **Document Changes**: Record why service is exposed (if applicable)

## Related Skills

- **`deploy-new-service`** - For setting up new services (includes subdomain setup)
- **`standard-deployment`** - For deploying configuration changes
- **`troubleshoot-container-failure`** - If service fails after subdomain addition

## Notes

- **Default Behavior**: Services are NOT exposed to internet (Cloudflare DDNS not updated)
- **Explicit Approval Required**: Internet exposure requires human approval
- **Network Requirement**: Service must be on `my-network` for Traefik routing
- **SSL Automatic**: Traefik automatically provisions SSL certificates via Let's Encrypt
- **Homepage Auto-Discovery**: Homepage automatically discovers services via labels
- **Port Configuration**: Internal port (container port) may differ from exposed port
- **Service Restart**: Services must be restarted for Traefik to pick up new labels

---

**Last Updated**: 2025-01-13
**Status**: Active
**Security**: Default no internet exposure, explicit approval required

