"""System monitoring and health check tools."""
import re
from typing import Dict, Any, Optional
from mcp.server import Server
from clients.remote_exec import RemoteExecutor


executor = RemoteExecutor()


def register_monitoring_tools(server: Server):
    """Register monitoring tools with MCP server."""
    
    @server.tool()
    async def check_disk_space(path: Optional[str] = None) -> Dict[str, Any]:
        """
        Check disk space usage.
        
        Args:
            path: Optional specific path to check (default: root /)
            
        Returns:
            Usage percentage, free space, status, and recommendations
        """
        try:
            check_path = path or "/"
            command = f"df -h {check_path} | tail -1"
            stdout, stderr, returncode = await executor.execute(command)
            
            if returncode != 0:
                return {
                    "status": "error",
                    "error_type": "ExecutionError",
                    "message": f"Failed to check disk space: {stderr}"
                }
            
            # Parse df output: Filesystem Size Used Avail Use% Mounted
            parts = stdout.strip().split()
            if len(parts) < 5:
                return {
                    "status": "error",
                    "error_type": "ParseError",
                    "message": f"Unexpected df output format: {stdout}"
                }
            
            # Extract usage percentage (remove % sign)
            usage_str = parts[4].replace("%", "")
            try:
                usage_percent = float(usage_str)
            except ValueError:
                usage_percent = 0
            
            # Determine status
            if usage_percent >= 90:
                status = "critical"
                recommendations = ["Disk space is critical. Clean up files immediately."]
            elif usage_percent >= 75:
                status = "warning"
                recommendations = ["Disk space is getting low. Consider cleaning up old files."]
            else:
                status = "ok"
                recommendations = []
            
            # Parse sizes (e.g., "100G" -> 100)
            size_str = parts[1]
            used_str = parts[2]
            avail_str = parts[3]
            
            return {
                "status": "success",
                "data": {
                    "path": check_path,
                    "usage_percent": usage_percent,
                    "total_size": size_str,
                    "used": used_str,
                    "available": avail_str,
                    "status": status,
                    "recommendations": recommendations
                }
            }
            
        except Exception as e:
            return {
                "status": "error",
                "error_type": type(e).__name__,
                "message": str(e)
            }
    
    @server.tool()
    async def check_system_resources() -> Dict[str, Any]:
        """
        Check CPU, memory, and network usage.
        
        Returns:
            Resource metrics and status
        """
        try:
            # Get CPU and memory info
            cpu_cmd = "top -bn1 | grep 'Cpu(s)' | awk '{print $2}' | sed 's/%us,//'"
            mem_cmd = "free -m | grep Mem | awk '{printf \"%.1f\", $3/$2 * 100.0}'"
            
            cpu_stdout, _, _ = await executor.execute(cpu_cmd)
            mem_stdout, _, _ = await executor.execute(mem_cmd)
            
            try:
                cpu_usage = float(cpu_stdout.strip())
            except (ValueError, AttributeError):
                cpu_usage = 0
            
            try:
                mem_usage = float(mem_stdout.strip())
            except (ValueError, AttributeError):
                mem_usage = 0
            
            # Get load average
            load_cmd = "uptime | awk -F'load average:' '{print $2}' | awk '{print $1}' | sed 's/,//'"
            load_stdout, _, _ = await executor.execute(load_cmd)
            try:
                load_avg = float(load_stdout.strip())
            except (ValueError, AttributeError):
                load_avg = 0
            
            # Determine status
            status = "ok"
            if cpu_usage > 90 or mem_usage > 90:
                status = "critical"
            elif cpu_usage > 75 or mem_usage > 75:
                status = "warning"
            
            return {
                "status": "success",
                "data": {
                    "cpu_usage_percent": cpu_usage,
                    "memory_usage_percent": mem_usage,
                    "load_average": load_avg,
                    "overall_status": status
                }
            }
            
        except Exception as e:
            return {
                "status": "error",
                "error_type": type(e).__name__,
                "message": str(e)
            }
    
    @server.tool()
    async def service_health_check(service_name: str) -> Dict[str, Any]:
        """
        Comprehensive health check for a service.
        
        Args:
            service_name: Name of the service/container to check
            
        Returns:
            Health status, checks performed, and issues found
        """
        try:
            checks = []
            issues = []
            
            # Check if container exists and is running
            check_cmd = f"docker ps --filter name={service_name} --format '{{{{.Names}}}}\t{{{{.Status}}}}'"
            stdout, stderr, returncode = await executor.execute(check_cmd)
            
            if returncode != 0 or not stdout.strip():
                return {
                    "status": "error",
                    "error_type": "NotFoundError",
                    "message": f"Service {service_name} not found"
                }
            
            parts = stdout.strip().split('\t')
            container_status = parts[1] if len(parts) > 1 else "unknown"
            is_running = "Up" in container_status
            
            checks.append({
                "check": "container_running",
                "status": "pass" if is_running else "fail",
                "details": container_status
            })
            
            if not is_running:
                issues.append("Container is not running")
            
            # Check health status if available
            health_cmd = f"docker inspect {service_name} --format '{{{{.State.Health.Status}}}}'"
            health_stdout, _, _ = await executor.execute(health_cmd)
            health_status = health_stdout.strip()
            
            if health_status and health_status != "":
                checks.append({
                    "check": "health_status",
                    "status": "pass" if health_status == "healthy" else "fail",
                    "details": health_status
                })
                
                if health_status != "healthy":
                    issues.append(f"Health check status: {health_status}")
            
            # Check recent logs for errors
            logs_cmd = f"docker logs {service_name} --tail 50 2>&1 | grep -i error | tail -5"
            logs_stdout, _, _ = await executor.execute(logs_cmd)
            
            error_count = len([l for l in logs_stdout.split('\n') if l.strip()]) if logs_stdout else 0
            
            checks.append({
                "check": "recent_errors",
                "status": "pass" if error_count == 0 else "warning",
                "details": f"{error_count} recent errors found"
            })
            
            if error_count > 0:
                issues.append(f"Found {error_count} recent errors in logs")
            
            overall_status = "healthy" if not issues else "unhealthy"
            
            return {
                "status": "success",
                "service": service_name,
                "overall_status": overall_status,
                "checks": checks,
                "issues": issues,
                "is_running": is_running
            }
            
        except Exception as e:
            return {
                "status": "error",
                "error_type": type(e).__name__,
                "message": str(e)
            }
    
    @server.tool()
    async def get_recent_errors(
        service: Optional[str] = None,
        lines: int = 50
    ) -> Dict[str, Any]:
        """
        Get recent errors from service logs.
        
        Args:
            service: Optional service name (if not provided, searches all containers)
            lines: Number of log lines to check (default: 50)
            
        Returns:
            Error log entries
        """
        try:
            if service:
                # Check specific service
                command = f"docker logs {service} --tail {lines} 2>&1 | grep -i -E '(error|exception|failed|fatal)' | tail -20"
                stdout, stderr, returncode = await executor.execute(command)
                
                if returncode != 0 and stderr:
                    return {
                        "status": "error",
                        "error_type": "ExecutionError",
                        "message": f"Failed to get logs: {stderr}"
                    }
                
                errors = [line for line in stdout.split('\n') if line.strip()]
                
                return {
                    "status": "success",
                    "service": service,
                    "error_count": len(errors),
                    "errors": errors
                }
            else:
                # Search all containers
                command = f"docker ps --format '{{{{.Names}}}}'"
                stdout, _, _ = await executor.execute(command)
                
                containers = [c.strip() for c in stdout.split('\n') if c.strip()]
                all_errors = []
                
                for container in containers:
                    log_cmd = f"docker logs {container} --tail {lines} 2>&1 | grep -i -E '(error|exception|failed|fatal)' | tail -5"
                    log_stdout, _, _ = await executor.execute(log_cmd)
                    
                    errors = [line for line in log_stdout.split('\n') if line.strip()]
                    if errors:
                        all_errors.append({
                            "container": container,
                            "errors": errors
                        })
                
                return {
                    "status": "success",
                    "service": "all",
                    "containers_with_errors": len(all_errors),
                    "errors_by_container": all_errors
                }
            
        except Exception as e:
            return {
                "status": "error",
                "error_type": type(e).__name__,
                "message": str(e)
            }
    
    @server.tool()
    async def find_service_by_port(port: int) -> Dict[str, Any]:
        """
        Find which service is using a specific port.
        
        Args:
            port: Port number to check
            
        Returns:
            Service name, container, and process information
        """
        try:
            # Check Docker containers
            docker_cmd = f"docker ps --format '{{{{.Names}}}}\t{{{{.Ports}}}}' | grep -E ':{port}[^0-9]|:{port}$'"
            docker_stdout, _, _ = await executor.execute(docker_cmd)
            
            docker_services = []
            for line in docker_stdout.split('\n'):
                if line.strip():
                    parts = line.split('\t')
                    if len(parts) >= 2:
                        docker_services.append({
                            "container": parts[0],
                            "ports": parts[1]
                        })
            
            # Check system processes
            process_cmd = f"netstat -tuln | grep ':{port} ' || ss -tuln | grep ':{port} '"
            process_stdout, _, _ = await executor.execute(process_cmd)
            
            return {
                "status": "success",
                "port": port,
                "docker_containers": docker_services,
                "system_processes": process_stdout.strip().split('\n') if process_stdout.strip() else [],
                "in_use": len(docker_services) > 0 or bool(process_stdout.strip())
            }
            
        except Exception as e:
            return {
                "status": "error",
                "error_type": type(e).__name__,
                "message": str(e)
            }
