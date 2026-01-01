import os
import subprocess
import logging
import json

from .registry import register_tool

logger = logging.getLogger(__name__)

SSH_HOST = os.getenv("SERVER_SSH_HOST", "192.168.86.47")
SSH_PORT = os.getenv("SERVER_SSH_PORT", "4242")
SSH_USER = os.getenv("SERVER_SSH_USER", "unarmedpuppy")
SSH_KEY = os.getenv("SERVER_SSH_KEY", "/root/.ssh/id_rsa")
SSH_TIMEOUT = int(os.getenv("SERVER_SSH_TIMEOUT", "60"))

ALLOWED_DOCKER_COMMANDS = [
    "docker ps",
    "docker logs",
    "docker restart",
    "docker stop",
    "docker start",
    "docker inspect",
    "docker compose",
    "docker stats",
    "docker top",
]

# Maximum output size for tool results (to avoid LLM context overflow)
MAX_OUTPUT_SIZE = 4000


def _smart_truncate(output: str, command: str) -> str:
    """
    Smart truncation of command output to avoid LLM context overflow.
    
    - JSON output (docker inspect without --format): extract key fields only
    - Long text output: keep first and last portions
    - Already small output: return as-is
    """
    if len(output) <= MAX_OUTPUT_SIZE:
        return output
    
    # Check if this looks like docker inspect JSON output
    stripped = output.strip()
    if stripped.startswith('[') or stripped.startswith('{'):
        try:
            data = json.loads(stripped)
            
            # Docker inspect returns a list with one item
            if isinstance(data, list) and len(data) > 0:
                item = data[0]
                
                # Extract only the most useful fields for troubleshooting
                summary = {
                    "Name": item.get("Name", ""),
                    "State": item.get("State", {}),
                    "RestartCount": item.get("RestartCount", 0),
                    "Created": item.get("Created", ""),
                    "Image": item.get("Config", {}).get("Image", ""),
                    "Cmd": item.get("Config", {}).get("Cmd", []),
                    "Env": [e for e in item.get("Config", {}).get("Env", []) 
                           if not any(s in e.upper() for s in ["KEY", "SECRET", "PASSWORD", "TOKEN"])],
                    "Mounts": [{"Source": m.get("Source"), "Destination": m.get("Destination")} 
                              for m in item.get("Mounts", [])[:5]],
                    "NetworkMode": item.get("HostConfig", {}).get("NetworkMode", ""),
                    "PortBindings": item.get("HostConfig", {}).get("PortBindings", {}),
                }
                
                result_str = json.dumps(summary, indent=2)
                if len(result_str) <= MAX_OUTPUT_SIZE:
                    return f"[Summarized docker inspect - full output was {len(output)} chars]\n{result_str}"
        except (json.JSONDecodeError, KeyError, TypeError):
            pass
    
    # For non-JSON or failed JSON parsing, do head/tail truncation
    half = MAX_OUTPUT_SIZE // 2
    return (
        output[:half] + 
        f"\n\n... [truncated {len(output) - MAX_OUTPUT_SIZE} chars] ...\n\n" + 
        output[-half:]
    )


def _validate_server_command(command: str) -> tuple[bool, str]:
    dangerous_patterns = [
        "rm -rf /",
        "> /dev/sd",
        "mkfs",
        "dd if=",
        ":(){:|:&};:",
        "chmod -R 777 /",
        "curl | sh",
        "wget | sh",
    ]
    
    for pattern in dangerous_patterns:
        if pattern in command:
            return False, f"Blocked dangerous pattern: {pattern}"
    
    return True, ""


def _run_on_server(arguments: dict, working_dir: str) -> str:
    command = arguments["command"]
    
    allowed, error = _validate_server_command(command)
    if not allowed:
        return f"Error: {error}"
    
    ssh_opts = [
        "-o", "StrictHostKeyChecking=accept-new",
        "-o", "BatchMode=yes",
        "-o", f"ConnectTimeout={min(SSH_TIMEOUT, 10)}",
    ]
    
    if os.path.exists(SSH_KEY):
        ssh_opts.extend(["-i", SSH_KEY])
    
    ssh_cmd = [
        "ssh",
        *ssh_opts,
        "-p", SSH_PORT,
        f"{SSH_USER}@{SSH_HOST}",
        command
    ]
    
    try:
        logger.info(f"Executing on server: {command[:100]}...")
        result = subprocess.run(
            ssh_cmd,
            capture_output=True,
            text=True,
            timeout=SSH_TIMEOUT
        )
        
        output = result.stdout
        if result.stderr:
            output += f"\n[stderr]: {result.stderr}"
        if result.returncode != 0:
            output += f"\n[exit code: {result.returncode}]"
        
        # Smart truncation: JSON output (docker inspect) gets summarized
        output = _smart_truncate(output, command)
        
        return output if output.strip() else "(no output)"
        
    except subprocess.TimeoutExpired:
        return f"Error: SSH command timed out after {SSH_TIMEOUT} seconds"
    except FileNotFoundError:
        return "Error: SSH client not available in this container"
    except Exception as e:
        return f"Error executing SSH command: {e}"


register_tool(
    name="run_on_server",
    description="Execute a command on the home server via SSH. Use this to run docker commands, check logs, restart services, etc.",
    parameters={
        "type": "object",
        "properties": {
            "command": {
                "type": "string",
                "description": "Shell command to execute on the server"
            }
        },
        "required": ["command"]
    },
    handler=_run_on_server
)


def _docker_ps(arguments: dict, working_dir: str) -> str:
    format_str = arguments.get("format", "table {{.Names}}\t{{.Status}}\t{{.Image}}")
    filter_str = arguments.get("filter", "")
    
    cmd = f"docker ps -a --format '{format_str}'"
    if filter_str:
        cmd = f"docker ps -a --filter '{filter_str}' --format '{format_str}'"
    
    return _run_on_server({"command": cmd}, working_dir)


register_tool(
    name="docker_ps",
    description="List Docker containers on the home server. Shows all containers by default.",
    parameters={
        "type": "object",
        "properties": {
            "filter": {
                "type": "string",
                "description": "Filter containers (e.g., 'status=exited', 'name=homepage')"
            },
            "format": {
                "type": "string",
                "description": "Output format (default: table with name, status, image)"
            }
        },
        "required": []
    },
    handler=_docker_ps
)


def _docker_logs(arguments: dict, working_dir: str) -> str:
    container = arguments["container"]
    tail = arguments.get("tail", 100)
    
    if not container.replace("-", "").replace("_", "").isalnum():
        return "Error: Invalid container name"
    
    cmd = f"docker logs {container} --tail {tail} 2>&1"
    return _run_on_server({"command": cmd}, working_dir)


register_tool(
    name="docker_logs",
    description="Get logs from a Docker container on the home server.",
    parameters={
        "type": "object",
        "properties": {
            "container": {
                "type": "string",
                "description": "Container name or ID"
            },
            "tail": {
                "type": "integer",
                "description": "Number of lines to show (default: 100)"
            }
        },
        "required": ["container"]
    },
    handler=_docker_logs
)


def _docker_restart(arguments: dict, working_dir: str) -> str:
    container = arguments["container"]
    
    if not container.replace("-", "").replace("_", "").isalnum():
        return "Error: Invalid container name"
    
    cmd = f"docker restart {container}"
    return _run_on_server({"command": cmd}, working_dir)


register_tool(
    name="docker_restart",
    description="Restart a Docker container on the home server.",
    parameters={
        "type": "object",
        "properties": {
            "container": {
                "type": "string",
                "description": "Container name or ID to restart"
            }
        },
        "required": ["container"]
    },
    handler=_docker_restart
)


def _docker_inspect(arguments: dict, working_dir: str) -> str:
    container = arguments["container"]
    
    if not container.replace("-", "").replace("_", "").isalnum():
        return "Error: Invalid container name"
    
    format_str = arguments.get("format", "{{.State.Status}} {{.State.Health.Status}} {{.RestartCount}}")
    cmd = f"docker inspect {container} --format '{format_str}'"
    return _run_on_server({"command": cmd}, working_dir)


register_tool(
    name="docker_inspect",
    description="Inspect a Docker container to get status, health, restart count, etc.",
    parameters={
        "type": "object",
        "properties": {
            "container": {
                "type": "string",
                "description": "Container name or ID"
            },
            "format": {
                "type": "string",
                "description": "Go template format string (default: status, health, restart count)"
            }
        },
        "required": ["container"]
    },
    handler=_docker_inspect
)
