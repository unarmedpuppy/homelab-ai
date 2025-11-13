"""
Service Debugging Tools for MCP Server

Provides tools for agents to access logs and debug running services in real-time.
This addresses the issue where agents can't easily access logs without manual copying.
"""

import sys
import subprocess
from pathlib import Path
from typing import Dict, List, Optional, Any

# Add project root to path for imports
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from mcp.server import Server
from tools.logging_decorator import with_automatic_logging


def _get_docker_logs(container_name: str, lines: int = 200, follow: bool = False) -> Dict[str, Any]:
    """Get logs from a Docker container."""
    try:
        cmd = ["docker", "logs", "--tail", str(lines)]
        if follow:
            cmd.append("--follow")
        cmd.append(container_name)
        
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=5 if not follow else 30
        )
        
        if result.returncode == 0:
            return {
                "status": "success",
                "logs": result.stdout,
                "container": container_name,
                "lines": lines
            }
        else:
            return {
                "status": "error",
                "message": result.stderr,
                "container": container_name
            }
    except subprocess.TimeoutExpired:
        return {
            "status": "timeout",
            "message": "Log retrieval timed out",
            "container": container_name
        }
    except Exception as e:
        return {
            "status": "error",
            "message": f"Error getting logs: {str(e)}",
            "container": container_name
        }


def _filter_logs_by_level(logs: str, level: str = "error") -> str:
    """Filter logs by level (error, warning, info, debug)."""
    if not logs:
        return ""
    
    level_keywords = {
        "error": ["error", "ERROR", "Error", "exception", "Exception", "failed", "Failed", "FAILED"],
        "warning": ["warning", "WARNING", "Warning", "warn", "WARN"],
        "info": ["info", "INFO", "Info"],
        "debug": ["debug", "DEBUG", "Debug"]
    }
    
    keywords = level_keywords.get(level.lower(), level_keywords["error"])
    
    filtered_lines = []
    for line in logs.split("\n"):
        if any(keyword in line for keyword in keywords):
            filtered_lines.append(line)
    
    return "\n".join(filtered_lines)


def _get_container_status(container_name: str) -> Dict[str, Any]:
    """Get status of a Docker container."""
    try:
        result = subprocess.run(
            ["docker", "ps", "-a", "--filter", f"name={container_name}", "--format", "{{.Names}}|{{.Status}}|{{.State}}"],
            capture_output=True,
            text=True,
            timeout=5
        )
        
        if result.returncode == 0 and result.stdout.strip():
            parts = result.stdout.strip().split("|")
            if len(parts) >= 3:
                return {
                    "status": "success",
                    "container": parts[0],
                    "status_text": parts[1],
                    "state": parts[2],
                    "is_running": parts[2] == "running"
                }
        
        return {
            "status": "not_found",
            "message": f"Container '{container_name}' not found"
        }
    except Exception as e:
        return {
            "status": "error",
            "message": f"Error checking container status: {str(e)}"
        }


def register_service_debugging_tools(server: Server):
    """Register service debugging tools with MCP server."""
    
    @server.tool()
    @with_automatic_logging()
    async def get_service_logs(
        service_name: str,
        lines: int = 200,
        level: str = "all"
    ) -> Dict[str, Any]:
        """
        Get logs from a service/container for debugging.
        
        This tool allows agents to access service logs in real-time without
        manual copying, making debugging much more efficient.
        
        Args:
            service_name: Name of the service/container
            lines: Number of lines to retrieve (default: 200)
            level: Log level to filter by ("all", "error", "warning", "info", "debug")
        
        Returns:
            Service logs with optional filtering
        
        Example:
            get_service_logs(
                service_name="trading-bot",
                lines=500,
                level="error"
            )
        """
        # Try to get logs from Docker container
        result = _get_docker_logs(service_name, lines=lines)
        
        if result["status"] == "error":
            # Try with different container name patterns
            # Check if it's a docker-compose service
            try:
                # Try with project prefix
                compose_result = _get_docker_logs(f"{service_name}_1", lines=lines)
                if compose_result["status"] == "success":
                    result = compose_result
            except Exception:
                pass
        
        if result["status"] != "success":
            return result
        
        logs = result["logs"]
        
        # Filter by level if requested
        if level != "all":
            logs = _filter_logs_by_level(logs, level)
            result["filtered_level"] = level
            result["original_lines"] = len(result["logs"].split("\n"))
            result["filtered_lines"] = len(logs.split("\n")) if logs else 0
        
        result["logs"] = logs
        
        # Format summary
        log_lines = logs.split("\n") if logs else []
        summary_lines = [
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━",
            f"📋 SERVICE LOGS: {service_name}",
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━",
            f"Lines retrieved: {len(log_lines)}",
        ]
        
        if level != "all":
            summary_lines.append(f"Filtered by level: {level}")
            summary_lines.append(f"Original lines: {result.get('original_lines', 0)}")
            summary_lines.append(f"Filtered lines: {result.get('filtered_lines', 0)}")
        
        summary_lines.append("")
        summary_lines.append("Recent logs:")
        summary_lines.append("─" * 40)
        
        # Show last 20 lines in summary
        for line in log_lines[-20:]:
            if line.strip():
                summary_lines.append(line)
        
        if len(log_lines) > 20:
            summary_lines.append(f"... ({len(log_lines) - 20} more lines)")
        
        summary_lines.append("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
        
        result["summary"] = "\n".join(summary_lines)
        
        return result
    
    @server.tool()
    @with_automatic_logging()
    async def monitor_service_status(
        service_name: str
    ) -> Dict[str, Any]:
        """
        Monitor the status of a service/container.
        
        Provides real-time status information including running state,
        uptime, and recent status changes.
        
        Args:
            service_name: Name of the service/container
        
        Returns:
            Service status information
        
        Example:
            monitor_service_status(service_name="trading-bot")
        """
        status = _get_container_status(service_name)
        
        if status["status"] != "success":
            # Try with different patterns
            try:
                compose_status = _get_container_status(f"{service_name}_1")
                if compose_status["status"] == "success":
                    status = compose_status
            except Exception:
                pass
        
        if status["status"] == "success":
            # Get additional info
            try:
                result = subprocess.run(
                    ["docker", "inspect", "--format", "{{.State.StartedAt}}|{{.State.FinishedAt}}|{{.RestartCount}}", service_name],
                    capture_output=True,
                    text=True,
                    timeout=5
                )
                
                if result.returncode == 0:
                    parts = result.stdout.strip().split("|")
                    if len(parts) >= 3:
                        status["started_at"] = parts[0] if parts[0] != "<no value>" else None
                        status["finished_at"] = parts[1] if parts[1] != "<no value>" else None
                        status["restart_count"] = int(parts[2]) if parts[2].isdigit() else 0
            except Exception:
                pass
        
        return status
    
    @server.tool()
    @with_automatic_logging()
    async def restart_service(
        service_name: str,
        method: str = "docker"
    ) -> Dict[str, Any]:
        """
        Restart a service/container.
        
        Supports Docker containers and docker-compose services.
        
        Args:
            service_name: Name of the service/container
            method: Restart method ("docker" or "compose")
        
        Returns:
            Restart result
        
        Example:
            restart_service(service_name="trading-bot", method="docker")
        """
        try:
            if method == "compose":
                # Find docker-compose.yml file
                compose_files = list(project_root.glob("**/docker-compose.yml"))
                for compose_file in compose_files:
                    try:
                        result = subprocess.run(
                            ["docker", "compose", "-f", str(compose_file), "restart", service_name],
                            cwd=str(compose_file.parent),
                            capture_output=True,
                            text=True,
                            timeout=30
                        )
                        
                        if result.returncode == 0:
                            return {
                                "status": "success",
                                "message": f"Service '{service_name}' restarted via docker-compose",
                                "method": "compose",
                                "compose_file": str(compose_file.relative_to(project_root))
                            }
                    except Exception:
                        continue
                
                return {
                    "status": "error",
                    "message": f"Could not restart '{service_name}' via docker-compose"
                }
            else:
                # Docker restart
                result = subprocess.run(
                    ["docker", "restart", service_name],
                    capture_output=True,
                    text=True,
                    timeout=30
                )
                
                if result.returncode == 0:
                    return {
                        "status": "success",
                        "message": f"Container '{service_name}' restarted",
                        "method": "docker"
                    }
                else:
                    return {
                        "status": "error",
                        "message": result.stderr or "Failed to restart container"
                    }
        except subprocess.TimeoutExpired:
            return {
                "status": "timeout",
                "message": "Restart operation timed out"
            }
        except Exception as e:
            return {
                "status": "error",
                "message": f"Error restarting service: {str(e)}"
            }
    
    @server.tool()
    @with_automatic_logging()
    async def get_service_metrics(
        service_name: str
    ) -> Dict[str, Any]:
        """
        Get resource usage metrics for a service/container.
        
        Provides CPU, memory, and network usage statistics.
        
        Args:
            service_name: Name of the service/container
        
        Returns:
            Service metrics
        
        Example:
            get_service_metrics(service_name="trading-bot")
        """
        try:
            result = subprocess.run(
                ["docker", "stats", "--no-stream", "--format", "{{.Name}}|{{.CPUPerc}}|{{.MemUsage}}|{{.NetIO}}", service_name],
                capture_output=True,
                text=True,
                timeout=5
            )
            
            if result.returncode == 0 and result.stdout.strip():
                parts = result.stdout.strip().split("|")
                if len(parts) >= 4:
                    return {
                        "status": "success",
                        "container": parts[0],
                        "cpu_percent": parts[1].strip(),
                        "memory_usage": parts[2].strip(),
                        "network_io": parts[3].strip()
                    }
            
            return {
                "status": "not_found",
                "message": f"Could not get metrics for '{service_name}'"
            }
        except Exception as e:
            return {
                "status": "error",
                "message": f"Error getting metrics: {str(e)}"
            }

