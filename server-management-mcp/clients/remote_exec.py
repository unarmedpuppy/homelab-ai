"""Remote command execution via SSH or direct execution."""
import asyncio
import subprocess
import os
from typing import Tuple
from pathlib import Path
from config.settings import settings


class RemoteExecutor:
    """Execute commands on remote server via SSH or directly if in container."""
    
    def __init__(self):
        # Check if we're running in a container (Docker)
        self.in_container = os.path.exists('/.dockerenv') or os.path.exists('/var/run/docker.sock')
        
        if not self.in_container:
            # Running locally, use SSH
            project_root = Path(__file__).parent.parent.parent
            connect_script = project_root / "scripts" / "connect-server.sh"
            self.connect_script = str(connect_script)
        else:
            # Running in container, execute directly
            self.connect_script = None
    
    async def execute(self, command: str, timeout: int = 60) -> Tuple[str, str, int]:
        """
        Execute command on remote server or directly if in container.
        
        Args:
            command: Command to execute
            timeout: Timeout in seconds
            
        Returns:
            (stdout, stderr, returncode)
        """
        try:
            if self.in_container:
                # Running in container, execute directly via shell
                process = await asyncio.create_subprocess_exec(
                    'sh', '-c', command,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE
                )
            else:
                # Running locally, use SSH
                process = await asyncio.create_subprocess_exec(
                    self.connect_script,
                    command,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE
                )
            
            try:
                stdout, stderr = await asyncio.wait_for(
                    process.communicate(),
                    timeout=timeout
                )
            except asyncio.TimeoutError:
                process.kill()
                await process.wait()
                return "", "Command timed out", 1
            
            return (
                stdout.decode('utf-8', errors='replace'),
                stderr.decode('utf-8', errors='replace'),
                process.returncode
            )
        except Exception as e:
            return "", str(e), 1
    
    async def docker_exec(self, container: str, command: str) -> str:
        """
        Execute command inside Docker container.
        
        Args:
            container: Container name
            command: Command to execute
            
        Returns:
            Command output
        """
        if self.in_container:
            # In container, use docker exec directly
            full_command = f"docker exec {container} {command}"
        else:
            # Local, use SSH
            full_command = f"docker exec {container} {command}"
        
        stdout, stderr, returncode = await self.execute(full_command)
        
        if returncode != 0:
            raise Exception(f"Command failed: {stderr}")
        
        return stdout
    
    async def docker_compose(self, app_path: str, action: str, service: str = None) -> str:
        """
        Execute docker-compose command.
        
        Args:
            app_path: Path to app directory (e.g., "apps/media-download")
            action: docker-compose action (ps, restart, stop, start, logs)
            service: Optional service name
            
        Returns:
            Command output
        """
        if self.in_container:
            # In container, use mounted /server path
            base_path = f"/server/{app_path}"
        else:
            # Local, use ~/server path
            base_path = f"~/server/{app_path}"
        
        if service:
            command = f"cd {base_path} && docker-compose {action} {service}"
        else:
            command = f"cd {base_path} && docker-compose {action}"
        
        stdout, stderr, returncode = await self.execute(command)
        
        if returncode != 0:
            raise Exception(f"docker-compose failed: {stderr}")
        
        return stdout

