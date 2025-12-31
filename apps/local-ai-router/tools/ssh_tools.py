"""SSH tools for remote server execution.

Tools:
- ssh_command: Execute a command on a remote server via SSH
- ssh_file_exists: Check if a file exists on remote server
"""

import os
import subprocess
from typing import Optional

from .security import validate_ssh_host, validate_command, SHELL_TIMEOUT
from .registry import register_tool

# =============================================================================
# Configuration
# =============================================================================

# Default SSH options for non-interactive use
SSH_OPTIONS = [
    "-o", "BatchMode=yes",
    "-o", "StrictHostKeyChecking=accept-new",
    "-o", "ConnectTimeout=10",
]

# Default SSH user and port (can be overridden per-call)
DEFAULT_SSH_USER = os.getenv("AGENT_SSH_USER", "unarmedpuppy")
DEFAULT_SSH_PORT = os.getenv("AGENT_SSH_PORT", "4242")
DEFAULT_SSH_KEY = os.getenv("AGENT_SSH_KEY", "")  # Path to SSH key if needed


# =============================================================================
# SSH Command Tool
# =============================================================================

def _ssh_command(arguments: dict, working_dir: str) -> str:
    """Execute a command on a remote server via SSH."""
    host = arguments.get("host", "")
    command = arguments.get("command", "")
    user = arguments.get("user", DEFAULT_SSH_USER)
    port = arguments.get("port", DEFAULT_SSH_PORT)
    timeout = arguments.get("timeout", SHELL_TIMEOUT)
    
    if not host:
        return "Error: host is required"
    if not command:
        return "Error: command is required"
    
    # Validate host against allowlist
    valid, error = validate_ssh_host(host)
    if not valid:
        return f"Error: {error}"
    
    # Validate command against blocklist
    valid, error = validate_command(command)
    if not valid:
        return f"Error: {error}"
    
    # Build SSH command
    ssh_cmd = ["ssh"] + SSH_OPTIONS
    ssh_cmd.extend(["-p", str(port)])
    
    if DEFAULT_SSH_KEY:
        ssh_cmd.extend(["-i", DEFAULT_SSH_KEY])
    
    ssh_cmd.append(f"{user}@{host}")
    ssh_cmd.append(command)
    
    try:
        result = subprocess.run(
            ssh_cmd,
            capture_output=True,
            text=True,
            timeout=timeout
        )
        
        output = result.stdout
        if result.stderr:
            if result.returncode != 0:
                output += f"\n[stderr]: {result.stderr}"
        
        if result.returncode != 0:
            return f"Error (exit {result.returncode}): {output or result.stderr}"
        
        return output if output.strip() else "(no output)"
        
    except subprocess.TimeoutExpired:
        return f"Error: SSH command timed out after {timeout} seconds"
    except FileNotFoundError:
        return "Error: SSH client not found"
    except Exception as e:
        return f"Error: {e}"


register_tool(
    name="ssh_command",
    description="Execute a command on a remote server via SSH. The host must be in the allowed hosts list.",
    parameters={
        "type": "object",
        "properties": {
            "host": {
                "type": "string",
                "description": "The hostname or IP address to connect to (must be in allowlist)"
            },
            "command": {
                "type": "string",
                "description": "The command to execute on the remote server"
            },
            "user": {
                "type": "string",
                "description": f"SSH username (default: {DEFAULT_SSH_USER})"
            },
            "port": {
                "type": "string",
                "description": f"SSH port (default: {DEFAULT_SSH_PORT})"
            },
            "timeout": {
                "type": "integer",
                "description": f"Command timeout in seconds (default: {SHELL_TIMEOUT})"
            }
        },
        "required": ["host", "command"]
    },
    handler=_ssh_command
)


# =============================================================================
# SSH File Exists Tool
# =============================================================================

def _ssh_file_exists(arguments: dict, working_dir: str) -> str:
    """Check if a file or directory exists on a remote server."""
    host = arguments.get("host", "")
    path = arguments.get("path", "")
    user = arguments.get("user", DEFAULT_SSH_USER)
    port = arguments.get("port", DEFAULT_SSH_PORT)
    
    if not host:
        return "Error: host is required"
    if not path:
        return "Error: path is required"
    
    # Validate host
    valid, error = validate_ssh_host(host)
    if not valid:
        return f"Error: {error}"
    
    # Build SSH command to check file existence
    ssh_cmd = ["ssh"] + SSH_OPTIONS
    ssh_cmd.extend(["-p", str(port)])
    
    if DEFAULT_SSH_KEY:
        ssh_cmd.extend(["-i", DEFAULT_SSH_KEY])
    
    ssh_cmd.append(f"{user}@{host}")
    ssh_cmd.append(f"test -e {path} && echo 'exists' || echo 'not found'")
    
    try:
        result = subprocess.run(
            ssh_cmd,
            capture_output=True,
            text=True,
            timeout=15
        )
        
        output = result.stdout.strip()
        
        if "exists" in output:
            # Get more info
            stat_cmd = ["ssh"] + SSH_OPTIONS + ["-p", str(port)]
            if DEFAULT_SSH_KEY:
                stat_cmd.extend(["-i", DEFAULT_SSH_KEY])
            stat_cmd.append(f"{user}@{host}")
            stat_cmd.append(f"ls -la {path} 2>/dev/null | head -5")
            
            stat_result = subprocess.run(stat_cmd, capture_output=True, text=True, timeout=15)
            return f"Exists:\n{stat_result.stdout.strip()}"
        
        return f"Path '{path}' not found on {host}"
        
    except subprocess.TimeoutExpired:
        return "Error: SSH command timed out"
    except Exception as e:
        return f"Error: {e}"


register_tool(
    name="ssh_file_exists",
    description="Check if a file or directory exists on a remote server.",
    parameters={
        "type": "object",
        "properties": {
            "host": {
                "type": "string",
                "description": "The hostname or IP address"
            },
            "path": {
                "type": "string",
                "description": "The file or directory path to check"
            },
            "user": {
                "type": "string",
                "description": f"SSH username (default: {DEFAULT_SSH_USER})"
            },
            "port": {
                "type": "string",
                "description": f"SSH port (default: {DEFAULT_SSH_PORT})"
            }
        },
        "required": ["host", "path"]
    },
    handler=_ssh_file_exists
)
