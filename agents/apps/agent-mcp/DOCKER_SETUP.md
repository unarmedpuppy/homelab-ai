# Docker Setup for MCP Server

## Overview

The MCP server is designed to run in a Docker container on your server. This provides:
- Isolation from host system
- Easy deployment and updates
- Consistent environment
- Access to Docker socket for container management

## Architecture

The containerized MCP server:
- **Runs on the server** (not locally)
- **Accesses Docker socket** directly (no SSH needed for docker commands)
- **Mounts server directory** for docker-compose access
- **Connects to docker network** to access other containers
- **Uses stdio transport** for MCP (or HTTP/SSE if configured)

## Setup

### 1. Build and Start

```bash
cd agents/apps/agent-mcp
docker-compose up -d --build
```

### 2. Verify It's Running

```bash
docker ps | grep agent-mcp
docker logs agent-mcp
```

### 3. Test the Server

```bash
# Execute a test inside the container
docker exec agent-mcp python test_setup.py
```

## Configuration

### Environment Variables

Set in `docker-compose.yml` or `.env` file:

```bash
SONARR_API_KEY=your-key
RADARR_API_KEY=your-key
NZBGET_USERNAME=nzbget
NZBGET_PASSWORD=nzbget
QBITTORRENT_USERNAME=admin
QBITTORRENT_PASSWORD=adminadmin
```

### Config File (Optional)

Create `config.json` in the `agents/apps/agent-mcp` directory:

```json
{
  "sonarr": {
    "api_key": "your-key"
  },
  "radarr": {
    "api_key": "your-key"
  }
}
```

This will be mounted into the container.

## Connecting from Claude Desktop

Since the MCP server runs in a container on the server, you have two options:

### Option 1: SSH Tunnel (Recommended)

Use SSH to forward the MCP connection:

```json
{
  "mcpServers": {
    "home-server": {
      "command": "ssh",
      "args": [
        "-p", "4242",
        "unarmedpuppy@192.168.86.47",
        "docker exec -i agent-mcp python /app/server.py"
      ]
    }
  }
}
```

### Option 2: HTTP/SSE Transport (Future)

If we implement HTTP/SSE transport, expose port 8000 and connect via HTTP:

```json
{
  "mcpServers": {
    "home-server": {
      "url": "http://192.168.86.47:8000/sse"
    }
  }
}
```

## Security Considerations

### Docker Socket Access

The container has read-only access to `/var/run/docker.sock`. This allows it to:
- List containers
- Inspect containers
- Execute commands in containers
- **NOT** create/delete containers (read-only mount)

### User Permissions

Currently runs as `root` to access Docker socket. For better security:
1. Create docker group on host: `sudo groupadd docker`
2. Add user to group: `sudo usermod -aG docker mcpuser`
3. Update docker-compose.yml to use that user

### Network Access

The container is on `my-network` (external network) so it can:
- Access other containers by name
- Make API calls to services
- Connect to databases if needed

## Troubleshooting

### Container Can't Access Docker Socket

```bash
# Check socket permissions
ls -la /var/run/docker.sock

# Check if container can access
docker exec agent-mcp ls -la /var/run/docker.sock
```

### Container Can't Access Server Directory

```bash
# Check mount
docker exec agent-mcp ls -la /server

# Verify path in docker-compose.yml matches your server structure
```

### MCP Connection Issues

```bash
# Check logs
docker logs agent-mcp

# Test server manually
docker exec -it agent-mcp python server.py
```

## Updating

```bash
cd agents/apps/agent-mcp
docker-compose pull  # If using image
docker-compose build  # If building locally
docker-compose up -d
```

## Development

For development, you can mount the code directory:

```yaml
volumes:
  - .:/app
  - /var/run/docker.sock:/var/run/docker.sock:ro
```

Then changes will be reflected immediately (if using a development server with auto-reload).

## Production Considerations

1. **Use docker group instead of root** (more secure)
2. **Add health checks** to docker-compose.yml
3. **Set resource limits** (memory, CPU)
4. **Use secrets management** for API keys
5. **Enable logging** to external service
6. **Set up monitoring** for the MCP server itself

