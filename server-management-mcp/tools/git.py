"""Git operations and deployment workflow tools."""
import re
from typing import Dict, Any, Optional, List
from mcp.server import Server
from clients.remote_exec import RemoteExecutor
from tools.logging_decorator import with_automatic_logging


executor = RemoteExecutor()


def register_git_tools(server: Server):
    """Register Git operation tools with MCP server."""
    
    @server.tool()
    @with_automatic_logging()
    async def git_status(app_path: Optional[str] = None) -> Dict[str, Any]:
        """
        Check Git repository status.
        
        Args:
            app_path: Optional app directory path (default: server root)
            
        Returns:
            Repository status, changes, and branch information
        """
        try:
            if app_path:
                base_path = f"/server/{app_path}" if executor.in_container else f"~/server/{app_path}"
                command = f"cd {base_path} && git status"
            else:
                base_path = "/server" if executor.in_container else "~/server"
                command = f"cd {base_path} && git status"
            
            stdout, stderr, returncode = await executor.execute(command)
            
            if returncode != 0:
                return {
                    "status": "error",
                    "error_type": "ExecutionError",
                    "message": f"Git status failed: {stderr}"
                }
            
            # Parse git status output
            lines = stdout.split('\n')
            branch = "unknown"
            changes = []
            untracked = []
            
            for line in lines:
                if line.startswith("On branch"):
                    branch = line.replace("On branch", "").strip()
                elif line.startswith("Changes to be committed"):
                    # Next lines are staged changes
                    continue
                elif line.startswith("Changes not staged"):
                    # Next lines are unstaged changes
                    continue
                elif line.startswith("Untracked files"):
                    # Next lines are untracked files
                    continue
                elif line.strip() and not line.startswith("#"):
                    if line.startswith("\t"):
                        file_path = line.strip()
                        if file_path.startswith("new file:") or file_path.startswith("modified:") or file_path.startswith("deleted:"):
                            changes.append(file_path)
                        elif "Untracked" in stdout or "untracked" in stdout.lower():
                            untracked.append(file_path)
            
            is_clean = "nothing to commit" in stdout.lower() or "working tree clean" in stdout.lower()
            
            return {
                "status": "success",
                "branch": branch,
                "is_clean": is_clean,
                "changes": changes,
                "untracked_files": untracked,
                "has_changes": len(changes) > 0 or len(untracked) > 0
            }
            
        except Exception as e:
            return {
                "status": "error",
                "error_type": type(e).__name__,
                "message": str(e)
            }
    
    @server.tool()
    @with_automatic_logging()
    async def git_pull(app_path: Optional[str] = None) -> Dict[str, Any]:
        """
        Pull latest changes from Git repository.
        
        Args:
            app_path: Optional app directory path (default: server root)
            
        Returns:
            Pull status and changes
        """
        try:
            if app_path:
                base_path = f"/server/{app_path}" if executor.in_container else f"~/server/{app_path}"
            else:
                base_path = "/server" if executor.in_container else "~/server"
            
            command = f"cd {base_path} && git pull origin main"
            stdout, stderr, returncode = await executor.execute(command)
            
            if returncode != 0:
                return {
                    "status": "error",
                    "error_type": "ExecutionError",
                    "message": f"Git pull failed: {stderr}",
                    "output": stdout
                }
            
            # Check if there were updates
            updated = "Already up to date" not in stdout
            
            return {
                "status": "success",
                "updated": updated,
                "message": "Already up to date" if not updated else "Pulled latest changes",
                "output": stdout
            }
            
        except Exception as e:
            return {
                "status": "error",
                "error_type": type(e).__name__,
                "message": str(e)
            }
    
    @server.tool()
    @with_automatic_logging()
    async def git_deploy(
        commit_message: str,
        files: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Complete deployment workflow: add → commit → push → pull on server.
        
        Args:
            commit_message: Commit message
            files: Optional list of specific files to commit (default: all changes)
            
        Returns:
            Deployment status for each step
        """
        try:
            # This tool should be run from local repository
            # It will add, commit, push locally, then pull on server
            
            # Step 1: Add files
            if files:
                file_list = " ".join(files)
                add_cmd = f"git add {file_list}"
            else:
                add_cmd = "git add ."
            
            stdout, stderr, returncode = await executor.execute(add_cmd)
            if returncode != 0:
                return {
                    "status": "error",
                    "error_type": "GitError",
                    "message": f"Git add failed: {stderr}",
                    "step": "add"
                }
            
            # Step 2: Commit
            commit_cmd = f"git commit -m '{commit_message}'"
            stdout, stderr, returncode = await executor.execute(commit_cmd)
            if returncode != 0:
                if "nothing to commit" in stderr.lower():
                    return {
                        "status": "success",
                        "message": "Nothing to commit",
                        "step": "commit"
                    }
                return {
                    "status": "error",
                    "error_type": "GitError",
                    "message": f"Git commit failed: {stderr}",
                    "step": "commit"
                }
            
            # Step 3: Push
            push_cmd = "git push origin main"
            stdout, stderr, returncode = await executor.execute(push_cmd)
            if returncode != 0:
                return {
                    "status": "error",
                    "error_type": "GitError",
                    "message": f"Git push failed: {stderr}",
                    "step": "push"
                }
            
            # Step 4: Pull on server
            pull_result = await git_pull()
            
            return {
                "status": "success",
                "steps": {
                    "add": "success",
                    "commit": "success",
                    "push": "success",
                    "pull_on_server": pull_result
                },
                "message": "Deployment workflow completed"
            }
            
        except Exception as e:
            return {
                "status": "error",
                "error_type": type(e).__name__,
                "message": str(e)
            }
    
    @server.tool()
    @with_automatic_logging()
    async def deploy_and_restart(
        commit_message: str,
        app_path: str,
        service: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Complete workflow: deploy changes → restart affected services.
        
        Args:
            commit_message: Commit message
            app_path: App directory path (e.g., "apps/media-download")
            service: Optional specific service name, or None for all services
            
        Returns:
            Deployment and restart status
        """
        try:
            # Step 1: Deploy
            deploy_result = await git_deploy(commit_message)
            
            if deploy_result.get("status") != "success":
                return {
                    "status": "error",
                    "error_type": "DeploymentError",
                    "message": "Deployment failed",
                    "deploy_result": deploy_result
                }
            
            # Step 2: Restart services using docker-compose via RemoteExecutor
            restart_result = await executor.docker_compose(app_path, "restart", service)
            
            # Format result
            restart_result = {
                "status": "success",
                "message": f"Restarted {service or 'all services'} in {app_path}"
            }
            
            return {
                "status": "success",
                "deployment": deploy_result,
                "restart": restart_result,
                "message": f"Deployed and restarted {service or 'all services'} in {app_path}"
            }
            
        except Exception as e:
            return {
                "status": "error",
                "error_type": type(e).__name__,
                "message": str(e)
            }
