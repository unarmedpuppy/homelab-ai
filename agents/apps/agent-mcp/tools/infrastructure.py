"""
Agent Infrastructure Management Tools

Tools for managing agent infrastructure (monitoring, etc.) locally.
"""

import sys
import subprocess
import asyncio
from pathlib import Path
from typing import Dict, Any, Optional
from mcp.server import Server
from tools.logging_decorator import with_automatic_logging

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))


def register_infrastructure_tools(server: Server):
    """Register infrastructure management tools with MCP server."""

    @server.tool()
    @with_automatic_logging()
    async def start_agent_infrastructure(check_only: bool = False) -> Dict[str, Any]:
        """
        Start agent infrastructure services (monitoring backend, frontend, etc.).
        
        This ensures all agent infrastructure is running before starting work.
        Services run locally on localhost.
        
        **Note**: On macOS, Docker Desktop must be running first. If Docker is not running,
        the script will provide instructions to start it.
        
        Args:
            check_only: If True, only check if services are running (don't start them)
        
        Returns:
            Status of infrastructure services and URLs
        """
        try:
            # First check if Docker is running
            try:
                import subprocess
                result = subprocess.run(
                    ["docker", "info"],
                    capture_output=True,
                    timeout=5
                )
                if result.returncode != 0:
                    # Try to start Docker Desktop on macOS
                    import platform
                    if platform.system() == "Darwin":
                        try:
                            subprocess.run(
                                ["open", "-a", "Docker"],
                                timeout=5,
                                check=False
                            )
                            return {
                                "status": "info",
                                "message": "Docker Desktop launch command sent",
                                "instructions": "Waiting for Docker Desktop to start (30-60 seconds). Run this tool again once Docker is running.",
                                "note": "Docker Desktop must be authorized/started manually on first launch"
                            }
                        except Exception:
                            pass
                    
                    return {
                        "status": "error",
                        "message": "Docker daemon is not running",
                        "instructions": {
                            "macos": "Open Docker Desktop application, or run: open -a Docker",
                            "linux": "Start Docker service: sudo systemctl start docker"
                        },
                        "suggestion": "Start Docker Desktop first, then run this tool again"
                    }
            except Exception as e:
                return {
                    "status": "error",
                    "message": f"Could not check Docker status: {str(e)}",
                    "suggestion": "Ensure Docker Desktop is installed and running"
                }
            
            script_path = project_root / "agents" / "scripts" / "start-agent-infrastructure.sh"
            
            if not script_path.exists():
                return {
                    "status": "error",
                    "message": f"Startup script not found at {script_path}",
                    "suggestion": "Create the script or start services manually"
                }
            
            # Make script executable
            script_path.chmod(0o755)
            
            # Build command
            cmd = [str(script_path)]
            if check_only:
                cmd.append("--check-only")
            
            # Execute script
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=str(project_root)
            )
            
            stdout, stderr = await process.communicate()
            output = stdout.decode('utf-8', errors='replace')
            error_output = stderr.decode('utf-8', errors='replace')
            
            if process.returncode == 0:
                return {
                    "status": "success",
                    "message": "Agent infrastructure is running",
                    "output": output,
                    "services": {
                        "backend": "http://localhost:3001",
                        "frontend": "http://localhost:3012",
                        "grafana": "http://localhost:3011"
                    }
                }
            else:
                return {
                    "status": "error",
                    "message": "Failed to start infrastructure",
                    "output": output,
                    "error": error_output,
                    "exit_code": process.returncode
                }
                
        except Exception as e:
            return {
                "status": "error",
                "error_type": type(e).__name__,
                "message": str(e)
            }

    @server.tool()
    @with_automatic_logging()
    async def check_agent_infrastructure() -> Dict[str, Any]:
        """
        Check if agent infrastructure services are running.
        
        Returns:
            Status of each service (backend, frontend, grafana)
        """
        try:
            import requests
            
            services = {
                "backend": {
                    "url": "http://localhost:3001/health",
                    "running": False
                },
                "frontend": {
                    "url": "http://localhost:3012",
                    "running": False
                },
                "grafana": {
                    "url": "http://localhost:3011/api/health",
                    "running": False
                }
            }
            
            # Check backend
            try:
                response = requests.get(services["backend"]["url"], timeout=2)
                services["backend"]["running"] = response.status_code == 200
                services["backend"]["status_code"] = response.status_code
            except Exception as e:
                services["backend"]["error"] = str(e)
            
            # Check frontend
            try:
                response = requests.get(services["frontend"]["url"], timeout=2)
                services["frontend"]["running"] = response.status_code == 200
                services["frontend"]["status_code"] = response.status_code
            except Exception as e:
                services["frontend"]["error"] = str(e)
            
            # Check grafana
            try:
                response = requests.get(services["grafana"]["url"], timeout=2)
                services["grafana"]["running"] = response.status_code == 200
                services["grafana"]["status_code"] = response.status_code
            except Exception as e:
                services["grafana"]["error"] = str(e)
            
            all_running = all(s["running"] for s in services.values())
            
            return {
                "status": "success" if all_running else "partial",
                "all_running": all_running,
                "services": services,
                "message": "All services running" if all_running else "Some services are not running"
            }
            
        except ImportError:
            return {
                "status": "error",
                "message": "requests library not available. Install with: pip install requests"
            }
        except Exception as e:
            return {
                "status": "error",
                "error_type": type(e).__name__,
                "message": str(e)
            }

    @server.tool()
    @with_automatic_logging()
    async def stop_agent_infrastructure() -> Dict[str, Any]:
        """
        Stop agent infrastructure services.
        
        Returns:
            Status of stop operation
        """
        try:
            monitoring_dir = project_root / "agents" / "apps" / "agent-monitoring"
            
            if not monitoring_dir.exists():
                return {
                    "status": "error",
                    "message": f"Monitoring directory not found: {monitoring_dir}"
                }
            
            # Use docker compose (v2) if available, otherwise docker-compose (v1)
            try:
                result = subprocess.run(
                    ["docker", "compose", "version"],
                    capture_output=True,
                    timeout=5
                )
                if result.returncode == 0:
                    docker_compose = ["docker", "compose"]
                else:
                    docker_compose = ["docker-compose"]
            except Exception:
                docker_compose = ["docker-compose"]
            
            # Stop services
            process = await asyncio.create_subprocess_exec(
                *docker_compose,
                "down",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=str(monitoring_dir)
            )
            
            stdout, stderr = await process.communicate()
            output = stdout.decode('utf-8', errors='replace')
            error_output = stderr.decode('utf-8', errors='replace')
            
            if process.returncode == 0:
                return {
                    "status": "success",
                    "message": "Agent infrastructure stopped",
                    "output": output
                }
            else:
                return {
                    "status": "error",
                    "message": "Failed to stop infrastructure",
                    "output": output,
                    "error": error_output
                }
                
        except Exception as e:
            return {
                "status": "error",
                "error_type": type(e).__name__,
                "message": str(e)
            }

