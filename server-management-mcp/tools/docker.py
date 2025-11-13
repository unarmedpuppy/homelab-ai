"""Docker and container management tools."""
import json
from typing import List, Dict, Any, Optional
from mcp.server import Server
from mcp.types import Tool
from clients.remote_exec import RemoteExecutor


executor = RemoteExecutor()


async def _get_container_status_internal(container_name: str) -> Dict[str, Any]:
    """Internal helper to get container status (not a tool)."""
    try:
        check_cmd = f"docker inspect {container_name} --format '{{{{.State.Status}}}}\t{{{{.State.Health.Status}}}}\t{{{{.State.Running}}}}'"
        stdout, stderr, returncode = await executor.execute(check_cmd)
        
        if returncode != 0:
            return {
                "status": "error",
                "error_type": "NotFoundError",
                "message": f"Container {container_name} not found"
            }
        
        parts = stdout.strip().split('\t')
        container_status = parts[0] if len(parts) > 0 else "unknown"
        health_status = parts[1] if len(parts) > 1 else "unknown"
        is_running = parts[2] == "true" if len(parts) > 2 else False
        
        logs_cmd = f"docker logs {container_name} --tail 20 2>&1"
        logs_stdout, _, _ = await executor.execute(logs_cmd)
        
        return {
            "status": "success",
            "container": container_name,
            "state": container_status,
            "health": health_status if health_status != "" else "unknown",
            "running": is_running,
            "recent_logs": logs_stdout.split('\n')[-20:] if logs_stdout else []
        }
    except Exception as e:
        return {
            "status": "error",
            "error_type": type(e).__name__,
            "message": str(e)
        }


def register_docker_tools(server: Server):
    """Register Docker management tools with MCP server."""
    
    @server.tool()
    async def docker_list_containers(
        filter_status: Optional[str] = None,
        filter_app: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        List all Docker containers with their status.
        
        Args:
            filter_status: Filter by status (running, stopped, etc.)
            filter_app: Filter by app name (e.g., "media-download")
            
        Returns:
            List of containers with name, status, ports, and health
        """
        try:
            # Get docker ps output
            command = "docker ps -a --format '{{.Names}}\t{{.Status}}\t{{.Ports}}\t{{.Image}}'"
            stdout, stderr, returncode = await executor.execute(command)
            
            if returncode != 0:
                return {
                    "status": "error",
                    "error_type": "ExecutionError",
                    "message": f"Failed to list containers: {stderr}"
                }
            
            containers = []
            for line in stdout.strip().split('\n'):
                if not line.strip():
                    continue
                
                parts = line.split('\t')
                if len(parts) < 4:
                    continue
                
                name, status, ports, image = parts
                
                # Parse status
                is_running = "Up" in status
                health = "healthy" if "healthy" in status.lower() else ("unhealthy" if "unhealthy" in status.lower() else "unknown")
                
                # Apply filters
                if filter_status:
                    if filter_status == "running" and not is_running:
                        continue
                    if filter_status == "stopped" and is_running:
                        continue
                
                if filter_app and filter_app not in name:
                    continue
                
                containers.append({
                    "name": name,
                    "status": "running" if is_running else "stopped",
                    "health": health,
                    "ports": ports,
                    "image": image,
                    "status_detail": status
                })
            
            return {
                "status": "success",
                "containers": containers,
                "total": len(containers)
            }
            
        except Exception as e:
            return {
                "status": "error",
                "error_type": type(e).__name__,
                "message": str(e)
            }
    
    @server.tool()
    async def docker_container_status(container_name: str) -> Dict[str, Any]:
        """
        Get detailed status of a Docker container.
        
        Args:
            container_name: Name of the container
            
        Returns:
            Container status, logs, and resource usage
        """
        return await _get_container_status_internal(container_name)
    
    @server.tool()
    async def docker_restart_container(
        container_name: str,
        wait_healthy: bool = False,
        timeout: int = 60
    ) -> Dict[str, Any]:
        """
        Restart a Docker container.
        
        Args:
            container_name: Name of the container
            wait_healthy: Wait for container to be healthy after restart
            timeout: Timeout in seconds for health check
            
        Returns:
            Restart status and new container status
        """
        try:
            # Restart container
            command = f"docker restart {container_name}"
            stdout, stderr, returncode = await executor.execute(command)
            
            if returncode != 0:
                return {
                    "status": "error",
                    "error_type": "ExecutionError",
                    "message": f"Failed to restart container: {stderr}"
                }
            
            # Wait a moment for restart
            import asyncio
            await asyncio.sleep(2)
            
            # Get new status
            status = await _get_container_status_internal(container_name)
            
            if wait_healthy and status.get("health") != "healthy":
                # Wait for healthy status
                import asyncio
                elapsed = 0
                while elapsed < timeout:
                    await asyncio.sleep(2)
                    elapsed += 2
                    status = await _get_container_status_internal(container_name)
                    if status.get("health") == "healthy":
                        break
            
            return {
                "status": "success",
                "container": container_name,
                "message": f"Container {container_name} restarted",
                "current_status": status
            }
            
        except Exception as e:
            return {
                "status": "error",
                "error_type": type(e).__name__,
                "message": str(e)
            }
    
    @server.tool()
    async def docker_stop_container(container_name: str) -> Dict[str, Any]:
        """
        Stop a Docker container.
        
        Args:
            container_name: Name of the container
            
        Returns:
            Stop status
        """
        try:
            command = f"docker stop {container_name}"
            stdout, stderr, returncode = await executor.execute(command)
            
            if returncode != 0:
                return {
                    "status": "error",
                    "error_type": "ExecutionError",
                    "message": f"Failed to stop container: {stderr}"
                }
            
            return {
                "status": "success",
                "container": container_name,
                "message": f"Container {container_name} stopped"
            }
            
        except Exception as e:
            return {
                "status": "error",
                "error_type": type(e).__name__,
                "message": str(e)
            }
    
    @server.tool()
    async def docker_start_container(container_name: str) -> Dict[str, Any]:
        """
        Start a Docker container.
        
        Args:
            container_name: Name of the container
            
        Returns:
            Start status
        """
        try:
            command = f"docker start {container_name}"
            stdout, stderr, returncode = await executor.execute(command)
            
            if returncode != 0:
                return {
                    "status": "error",
                    "error_type": "ExecutionError",
                    "message": f"Failed to start container: {stderr}"
                }
            
            # Get status after start
            status = await _get_container_status_internal(container_name)
            
            return {
                "status": "success",
                "container": container_name,
                "message": f"Container {container_name} started",
                "current_status": status
            }
            
        except Exception as e:
            return {
                "status": "error",
                "error_type": type(e).__name__,
                "message": str(e)
            }
    
    @server.tool()
    async def docker_view_logs(
        container_name: str,
        lines: int = 50,
        follow: bool = False
    ) -> Dict[str, Any]:
        """
        View container logs.
        
        Args:
            container_name: Name of the container
            lines: Number of lines to retrieve
            follow: Whether to follow logs (not supported in async, returns last N lines)
            
        Returns:
            Log lines
        """
        try:
            command = f"docker logs {container_name} --tail {lines} 2>&1"
            stdout, stderr, returncode = await executor.execute(command)
            
            if returncode != 0:
                return {
                    "status": "error",
                    "error_type": "ExecutionError",
                    "message": f"Failed to get logs: {stderr}"
                }
            
            return {
                "status": "success",
                "container": container_name,
                "lines": stdout.split('\n') if stdout else [],
                "total_lines": len(stdout.split('\n')) if stdout else 0
            }
            
        except Exception as e:
            return {
                "status": "error",
                "error_type": type(e).__name__,
                "message": str(e)
            }
    
    @server.tool()
    async def docker_compose_ps(app_path: str) -> Dict[str, Any]:
        """
        List containers from docker-compose.
        
        Args:
            app_path: Path to app directory (e.g., "apps/media-download")
            
        Returns:
            List of services and their status
        """
        try:
            command = f"cd ~/server/{app_path} && docker-compose ps --format json"
            stdout, stderr, returncode = await executor.execute(command)
            
            if returncode != 0:
                return {
                    "status": "error",
                    "error_type": "ExecutionError",
                    "message": f"Failed to get docker-compose status: {stderr}"
                }
            
            # Parse JSON output (one JSON object per line)
            services = []
            for line in stdout.strip().split('\n'):
                if not line.strip():
                    continue
                try:
                    service = json.loads(line)
                    services.append(service)
                except json.JSONDecodeError:
                    continue
            
            return {
                "status": "success",
                "app_path": app_path,
                "services": services,
                "total": len(services)
            }
            
        except Exception as e:
            return {
                "status": "error",
                "error_type": type(e).__name__,
                "message": str(e)
            }
    
    @server.tool()
    async def docker_compose_restart(
        app_path: str,
        service: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Restart services via docker-compose.
        
        Args:
            app_path: Path to app directory (e.g., "apps/media-download")
            service: Optional specific service name, or None for all services
            
        Returns:
            Restart results
        """
        try:
            if service:
                command = f"cd ~/server/{app_path} && docker-compose restart {service}"
            else:
                command = f"cd ~/server/{app_path} && docker-compose restart"
            
            stdout, stderr, returncode = await executor.execute(command)
            
            if returncode != 0:
                return {
                    "status": "error",
                    "error_type": "ExecutionError",
                    "message": f"Failed to restart: {stderr}"
                }
            
            return {
                "status": "success",
                "app_path": app_path,
                "service": service or "all",
                "message": f"Restarted {service or 'all services'} in {app_path}"
            }
            
        except Exception as e:
            return {
                "status": "error",
                "error_type": type(e).__name__,
                "message": str(e)
            }

