"""Docker tools for container management.

Tools:
- docker_ps: List running containers
- docker_logs: Get container logs
- docker_restart: Restart a container
- docker_compose_up: Start services with docker-compose
- docker_inspect: Get detailed container info
"""

import subprocess
import json
from typing import Optional

from .registry import register_tool

# =============================================================================
# Helpers
# =============================================================================

def _run_docker_command(
    command: list[str],
    timeout: int = 30
) -> tuple[bool, str]:
    """
    Run a docker command.
    
    Returns:
        (success, output_or_error)
    """
    try:
        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            timeout=timeout
        )
        
        output = result.stdout
        if result.stderr:
            if result.returncode != 0:
                output += f"\n[stderr]: {result.stderr}"
        
        if result.returncode != 0:
            return False, output or result.stderr or f"Exit code: {result.returncode}"
        
        return True, output if output.strip() else "(no output)"
        
    except subprocess.TimeoutExpired:
        return False, f"Error: Docker command timed out after {timeout} seconds"
    except FileNotFoundError:
        return False, "Error: Docker not found"
    except Exception as e:
        return False, f"Error: {e}"


# =============================================================================
# Docker PS Tool
# =============================================================================

def _docker_ps(arguments: dict, working_dir: str) -> str:
    """List Docker containers."""
    all_containers = arguments.get("all", False)
    filter_name = arguments.get("filter_name", "")
    format_str = arguments.get("format", "table {{.Names}}\t{{.Status}}\t{{.Image}}\t{{.Ports}}")
    
    cmd = ["docker", "ps"]
    
    if all_containers:
        cmd.append("-a")
    
    if filter_name:
        cmd.extend(["--filter", f"name={filter_name}"])
    
    cmd.extend(["--format", format_str])
    
    success, output = _run_docker_command(cmd)
    return output


register_tool(
    name="docker_ps",
    description="List Docker containers. Shows running containers by default, use all=true to show all.",
    parameters={
        "type": "object",
        "properties": {
            "all": {
                "type": "boolean",
                "description": "Show all containers, not just running (default: false)"
            },
            "filter_name": {
                "type": "string",
                "description": "Filter containers by name pattern"
            },
            "format": {
                "type": "string",
                "description": "Output format (Go template)"
            }
        },
        "required": []
    },
    handler=_docker_ps
)


# =============================================================================
# Docker Logs Tool
# =============================================================================

def _docker_logs(arguments: dict, working_dir: str) -> str:
    """Get container logs."""
    container = arguments.get("container", "")
    tail = arguments.get("tail", 100)
    since = arguments.get("since", "")
    
    if not container:
        return "Error: container name is required"
    
    cmd = ["docker", "logs", "--tail", str(tail)]
    
    if since:
        cmd.extend(["--since", since])
    
    cmd.append(container)
    
    success, output = _run_docker_command(cmd, timeout=30)
    
    # Truncate if too long
    if len(output) > 10000:
        output = output[-10000:]
        output = "... (truncated, showing last 10000 chars)\n" + output
    
    return output


register_tool(
    name="docker_logs",
    description="Get logs from a Docker container.",
    parameters={
        "type": "object",
        "properties": {
            "container": {
                "type": "string",
                "description": "Container name or ID"
            },
            "tail": {
                "type": "integer",
                "description": "Number of lines to show from end (default: 100)"
            },
            "since": {
                "type": "string",
                "description": "Show logs since timestamp (e.g., '10m', '1h', '2024-01-01T00:00:00')"
            }
        },
        "required": ["container"]
    },
    handler=_docker_logs
)


# =============================================================================
# Docker Restart Tool
# =============================================================================

def _docker_restart(arguments: dict, working_dir: str) -> str:
    """Restart a container."""
    container = arguments.get("container", "")
    timeout = arguments.get("timeout", 10)
    
    if not container:
        return "Error: container name is required"
    
    cmd = ["docker", "restart", "-t", str(timeout), container]
    
    success, output = _run_docker_command(cmd, timeout=timeout + 30)
    
    if success:
        # Get new status
        _, status = _run_docker_command([
            "docker", "ps", "--filter", f"name={container}",
            "--format", "{{.Names}}: {{.Status}}"
        ])
        return f"Restarted {container}\nStatus: {status}"
    
    return output


register_tool(
    name="docker_restart",
    description="Restart a Docker container.",
    parameters={
        "type": "object",
        "properties": {
            "container": {
                "type": "string",
                "description": "Container name or ID"
            },
            "timeout": {
                "type": "integer",
                "description": "Seconds to wait for stop before killing (default: 10)"
            }
        },
        "required": ["container"]
    },
    handler=_docker_restart
)


# =============================================================================
# Docker Compose Up Tool
# =============================================================================

def _docker_compose_up(arguments: dict, working_dir: str) -> str:
    """Start services with docker-compose."""
    compose_file = arguments.get("compose_file", "")
    services = arguments.get("services", [])
    build = arguments.get("build", False)
    detach = arguments.get("detach", True)
    
    if not compose_file:
        return "Error: compose_file path is required"
    
    # Use docker compose (v2) or docker-compose (v1)
    cmd = ["docker", "compose", "-f", compose_file, "up"]
    
    if detach:
        cmd.append("-d")
    
    if build:
        cmd.append("--build")
    
    if services:
        if isinstance(services, str):
            services = [services]
        cmd.extend(services)
    
    success, output = _run_docker_command(cmd, timeout=180)
    
    return output


register_tool(
    name="docker_compose_up",
    description="Start services defined in a docker-compose file.",
    parameters={
        "type": "object",
        "properties": {
            "compose_file": {
                "type": "string",
                "description": "Path to docker-compose.yml file"
            },
            "services": {
                "type": "array",
                "items": {"type": "string"},
                "description": "Specific services to start (optional, starts all if empty)"
            },
            "build": {
                "type": "boolean",
                "description": "Build images before starting (default: false)"
            },
            "detach": {
                "type": "boolean",
                "description": "Run in background (default: true)"
            }
        },
        "required": ["compose_file"]
    },
    handler=_docker_compose_up
)


# =============================================================================
# Docker Inspect Tool
# =============================================================================

def _docker_inspect(arguments: dict, working_dir: str) -> str:
    """Get detailed container information."""
    container = arguments.get("container", "")
    format_str = arguments.get("format", "")
    
    if not container:
        return "Error: container name is required"
    
    cmd = ["docker", "inspect"]
    
    if format_str:
        cmd.extend(["--format", format_str])
    
    cmd.append(container)
    
    success, output = _run_docker_command(cmd)
    
    if success and not format_str:
        # Parse and summarize JSON
        try:
            data = json.loads(output)
            if data and len(data) > 0:
                info = data[0]
                summary = {
                    "Name": info.get("Name", "").lstrip("/"),
                    "Id": info.get("Id", "")[:12],
                    "Image": info.get("Config", {}).get("Image", ""),
                    "State": info.get("State", {}).get("Status", ""),
                    "Running": info.get("State", {}).get("Running", False),
                    "StartedAt": info.get("State", {}).get("StartedAt", ""),
                    "RestartCount": info.get("RestartCount", 0),
                    "Ports": list(info.get("NetworkSettings", {}).get("Ports", {}).keys()),
                    "Mounts": len(info.get("Mounts", [])),
                    "Networks": list(info.get("NetworkSettings", {}).get("Networks", {}).keys()),
                }
                return json.dumps(summary, indent=2)
        except json.JSONDecodeError:
            pass
    
    return output


register_tool(
    name="docker_inspect",
    description="Get detailed information about a Docker container.",
    parameters={
        "type": "object",
        "properties": {
            "container": {
                "type": "string",
                "description": "Container name or ID"
            },
            "format": {
                "type": "string",
                "description": "Go template format string (optional, returns summary by default)"
            }
        },
        "required": ["container"]
    },
    handler=_docker_inspect
)


# =============================================================================
# Docker Stats Tool
# =============================================================================

def _docker_stats(arguments: dict, working_dir: str) -> str:
    """Get container resource usage statistics."""
    container = arguments.get("container", "")
    
    cmd = ["docker", "stats", "--no-stream", "--format",
           "table {{.Name}}\t{{.CPUPerc}}\t{{.MemUsage}}\t{{.NetIO}}\t{{.BlockIO}}"]
    
    if container:
        cmd.append(container)
    
    success, output = _run_docker_command(cmd, timeout=15)
    
    return output


register_tool(
    name="docker_stats",
    description="Get container resource usage (CPU, memory, network, disk I/O).",
    parameters={
        "type": "object",
        "properties": {
            "container": {
                "type": "string",
                "description": "Container name or ID (optional, shows all if empty)"
            }
        },
        "required": []
    },
    handler=_docker_stats
)
