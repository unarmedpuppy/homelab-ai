"""Docker API client for direct Docker operations."""
import docker
from typing import Dict, Any, List, Optional
import asyncio
from functools import partial


class DockerClient:
    """Direct Docker API client (for use inside container)."""
    
    def __init__(self):
        try:
            self.client = docker.from_env()
        except Exception as e:
            raise Exception(f"Failed to connect to Docker: {e}")
    
    async def list_containers(self, all: bool = True, filters: Optional[Dict] = None) -> List[Dict[str, Any]]:
        """List containers using Docker API."""
        loop = asyncio.get_event_loop()
        containers = await loop.run_in_executor(
            None,
            partial(self.client.containers.list, all=all, filters=filters or {})
        )
        
        result = []
        for container in containers:
            result.append({
                "name": container.name,
                "id": container.id[:12],
                "status": container.status,
                "image": container.image.tags[0] if container.image.tags else container.image.id[:12],
                "ports": self._format_ports(container.ports),
                "health": self._get_health_status(container)
            })
        
        return result
    
    def _format_ports(self, ports: Dict) -> str:
        """Format port mapping."""
        if not ports:
            return ""
        
        formatted = []
        for container_port, host_ports in ports.items():
            if host_ports:
                for host_port in host_ports:
                    formatted.append(f"{host_port['HostIp']}:{host_port['HostPort']}->{container_port}")
            else:
                formatted.append(container_port)
        
        return ", ".join(formatted)
    
    def _get_health_status(self, container) -> str:
        """Get container health status."""
        try:
            inspect = container.attrs
            health = inspect.get("State", {}).get("Health", {})
            if health:
                return health.get("Status", "unknown")
            return "no-healthcheck"
        except:
            return "unknown"
    
    async def get_container(self, name: str):
        """Get container by name."""
        loop = asyncio.get_event_loop()
        try:
            container = await loop.run_in_executor(
                None,
                self.client.containers.get,
                name
            )
            return container
        except docker.errors.NotFound:
            return None
    
    async def restart_container(self, name: str) -> bool:
        """Restart a container."""
        container = await self.get_container(name)
        if not container:
            return False
        
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, container.restart)
        return True
    
    async def stop_container(self, name: str) -> bool:
        """Stop a container."""
        container = await self.get_container(name)
        if not container:
            return False
        
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, container.stop)
        return True
    
    async def start_container(self, name: str) -> bool:
        """Start a container."""
        container = await self.get_container(name)
        if not container:
            return False
        
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, container.start)
        return True
    
    async def get_logs(self, name: str, tail: int = 50) -> List[str]:
        """Get container logs."""
        container = await self.get_container(name)
        if not container:
            return []
        
        loop = asyncio.get_event_loop()
        logs = await loop.run_in_executor(
            None,
            partial(container.logs, tail=tail, timestamps=False)
        )
        
        return logs.decode('utf-8', errors='replace').split('\n')
    
    async def inspect_container(self, name: str) -> Optional[Dict[str, Any]]:
        """Inspect a container."""
        container = await self.get_container(name)
        if not container:
            return None
        
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, container.attrs)

