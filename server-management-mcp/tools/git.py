"""Git operations and deployment workflow tools."""
import re
from typing import Dict, Any, Optional, List
from mcp.server import Server
from clients.remote_exec import RemoteExecutor


executor = RemoteExecutor()


async def _detect_affected_services(changed_files: List[str]) -> Dict[str, List[str]]:
    """
    Detect which services are affected by git changes.
    
    Args:
        changed_files: List of changed file paths
        
    Returns:
        Dictionary mapping app paths to list of services
    """
    affected = {}
    
    for file_path in changed_files:
        # Look for docker-compose.yml changes
        if 'docker-compose.yml' in file_path:
            # Extract app path (e.g., "apps/media-download" from "apps/media-download/docker-compose.yml")
            match = re.search(r'apps/([^/]+)', file_path)
            if match:
                app_name = match.group(1)
                app_path = f"apps/{app_name}"
                if app_path not in affected:
                    affected[app_path] = []
        
        # Look for changes in app directories
        match = re.search(r'apps/([^/]+)/', file_path)
        if match:
            app_name = match.group(1)
            app_path = f"apps/{app_name}"
            if app_path not in affected:
                affected[app_path] = []
    
    return affected


def register_git_tools(server: Server):
    """Register Git operations and deployment workflow tools with MCP server."""
    
    @server.tool()
    async def git_status(
        path: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Check git repository status.
        
        Args:
            path: Repository path, default: ~/server (or /server if in container)
            
        Returns:
            Branch, uncommitted changes, untracked files, ahead/behind status
        """
        try:
            if not path:
                path = "/server" if executor.in_container else "~/server"
            
            # Get current branch
            branch_cmd = f"cd {path} && git rev-parse --abbrev-ref HEAD"
            branch_stdout, branch_stderr, branch_rc = await executor.execute(branch_cmd)
            
            if branch_rc != 0:
                return {
                    "status": "error",
                    "error_type": "GitError",
                    "message": f"Failed to get branch: {branch_stderr}"
                }
            
            current_branch = branch_stdout.strip()
            
            # Get status
            status_cmd = f"cd {path} && git status --porcelain"
            status_stdout, status_stderr, status_rc = await executor.execute(status_cmd)
            
            if status_rc != 0:
                return {
                    "status": "error",
                    "error_type": "GitError",
                    "message": f"Failed to get status: {status_stderr}"
                }
            
            # Parse status
            modified = []
            untracked = []
            staged = []
            
            for line in status_stdout.strip().split('\n'):
                if not line.strip():
                    continue
                status_code = line[:2]
                file_path = line[3:]
                
                if status_code.startswith('??'):
                    untracked.append(file_path)
                elif status_code.startswith(' '):
                    # Modified but not staged
                    modified.append(file_path)
                else:
                    # Staged changes
                    staged.append(file_path)
            
            # Check ahead/behind
            ahead_behind_cmd = f"cd {path} && git rev-list --left-right --count origin/{current_branch}...HEAD 2>/dev/null || echo '0 0'"
            ahead_behind_stdout, _, _ = await executor.execute(ahead_behind_cmd)
            parts = ahead_behind_stdout.strip().split()
            behind = int(parts[0]) if len(parts) > 0 else 0
            ahead = int(parts[1]) if len(parts) > 1 else 0
            
            return {
                "status": "success",
                "branch": current_branch,
                "modified": modified,
                "staged": staged,
                "untracked": untracked,
                "ahead": ahead,
                "behind": behind,
                "has_changes": len(modified) > 0 or len(staged) > 0 or len(untracked) > 0
            }
            
        except Exception as e:
            return {
                "status": "error",
                "error_type": type(e).__name__,
                "message": str(e)
            }
    
    @server.tool()
    async def git_deploy(
        commit_message: str,
        files: Optional[str] = "all",
        path: Optional[str] = None,
        branch: Optional[str] = "main",
        skip_pull: bool = False
    ) -> Dict[str, Any]:
        """
        Complete deployment workflow: add → commit → push → pull on server.
        
        Args:
            commit_message: Commit message
            files: Specific files to add or "all" for all changes
            path: Repository path, default: ~/server (or /server if in container)
            branch: Branch name, default: main
            skip_pull: Skip pulling on server (for testing)
            
        Returns:
            Status of each step, commit hash, push status, pull status, conflicts if any
        """
        try:
            if not path:
                path = "/server" if executor.in_container else "~/server"
            
            results = {
                "status": "success",
                "steps": {},
                "commit_hash": None,
                "conflicts": []
            }
            
            # Step 1: Add files
            if files == "all":
                add_cmd = f"cd {path} && git add -A"
            else:
                # Add specific files
                file_list = files.split(',')
                file_args = ' '.join([f'"{f.strip()}"' for f in file_list])
                add_cmd = f"cd {path} && git add {file_args}"
            
            add_stdout, add_stderr, add_rc = await executor.execute(add_cmd)
            results["steps"]["add"] = {
                "success": add_rc == 0,
                "output": add_stdout,
                "error": add_stderr if add_rc != 0 else None
            }
            
            if add_rc != 0:
                results["status"] = "error"
                results["error"] = f"Git add failed: {add_stderr}"
                return results
            
            # Step 2: Commit
            commit_cmd = f"cd {path} && git commit -m '{commit_message}'"
            commit_stdout, commit_stderr, commit_rc = await executor.execute(commit_cmd)
            results["steps"]["commit"] = {
                "success": commit_rc == 0,
                "output": commit_stdout,
                "error": commit_stderr if commit_rc != 0 else None
            }
            
            if commit_rc != 0:
                # Check if there's nothing to commit
                if "nothing to commit" in commit_stderr.lower():
                    results["steps"]["commit"]["nothing_to_commit"] = True
                    results["status"] = "success"
                    results["message"] = "No changes to commit"
                    return results
                else:
                    results["status"] = "error"
                    results["error"] = f"Git commit failed: {commit_stderr}"
                    return results
            
            # Get commit hash
            hash_cmd = f"cd {path} && git rev-parse HEAD"
            hash_stdout, _, _ = await executor.execute(hash_cmd)
            results["commit_hash"] = hash_stdout.strip()
            
            # Step 3: Push
            push_cmd = f"cd {path} && git push origin {branch}"
            push_stdout, push_stderr, push_rc = await executor.execute(push_cmd)
            results["steps"]["push"] = {
                "success": push_rc == 0,
                "output": push_stdout,
                "error": push_stderr if push_rc != 0 else None
            }
            
            if push_rc != 0:
                results["status"] = "error"
                results["error"] = f"Git push failed: {push_stderr}"
                return results
            
            # Step 4: Pull on server (if not in container, we're already on server)
            if not skip_pull:
                if executor.in_container:
                    # We're already on the server, just pull
                    pull_cmd = f"cd {path} && git pull origin {branch}"
                else:
                    # We're local, need to SSH to server and pull
                    pull_cmd = f"cd ~/server && git pull origin {branch}"
                
                pull_stdout, pull_stderr, pull_rc = await executor.execute(pull_cmd)
                results["steps"]["pull"] = {
                    "success": pull_rc == 0,
                    "output": pull_stdout,
                    "error": pull_stderr if pull_rc != 0 else None
                }
                
                if pull_rc != 0:
                    # Check for conflicts
                    if "conflict" in pull_stderr.lower() or "CONFLICT" in pull_stdout:
                        results["conflicts"].append("Merge conflicts detected")
                        results["status"] = "warning"
                    else:
                        results["status"] = "error"
                        results["error"] = f"Git pull failed: {pull_stderr}"
                        return results
                
                # Check for updated files
                if "Already up to date" not in pull_stdout:
                    # Extract updated files from pull output
                    updated_files = []
                    for line in pull_stdout.split('\n'):
                        if line.strip().startswith(('create', 'update', 'delete')):
                            updated_files.append(line.strip())
                    results["updated_files"] = updated_files
            
            results["message"] = "Deployment completed successfully"
            return results
            
        except Exception as e:
            return {
                "status": "error",
                "error_type": type(e).__name__,
                "message": str(e)
            }
    
    @server.tool()
    async def restart_affected_services(
        app_path: Optional[str] = None,
        service: Optional[str] = None,
        check_changes: bool = True
    ) -> Dict[str, Any]:
        """
        Restart services based on git changes or explicit app path.
        
        Args:
            app_path: Explicit app path (e.g., "apps/media-download"). Auto-detected from git changes if not provided.
            service: Specific service name or None for all services in app
            check_changes: Analyze git changes to determine affected services
            
        Returns:
            Services restarted, restart results, detected changes summary
        """
        try:
            path = "/server" if executor.in_container else "~/server"
            affected_apps = {}
            
            if check_changes and not app_path:
                # Get recent git changes
                diff_cmd = f"cd {path} && git diff --name-only HEAD~1 HEAD 2>/dev/null || git diff --name-only"
                diff_stdout, _, _ = await executor.execute(diff_cmd)
                
                changed_files = [f.strip() for f in diff_stdout.split('\n') if f.strip()]
                affected_apps = await _detect_affected_services(changed_files)
            elif app_path:
                affected_apps[app_path] = []
            
            if not affected_apps:
                return {
                    "status": "success",
                    "message": "No affected services detected",
                    "services_restarted": [],
                    "affected_apps": []
                }
            
            services_restarted = []
            restart_results = {}
            
            for app, services in affected_apps.items():
                # Restart services in this app
                if service:
                    # Restart specific service
                    restart_cmd = f"cd {path}/{app} && docker-compose restart {service}"
                    stdout, stderr, rc = await executor.execute(restart_cmd)
                    services_restarted.append(f"{app}/{service}")
                    restart_results[f"{app}/{service}"] = {
                        "success": rc == 0,
                        "output": stdout,
                        "error": stderr if rc != 0 else None
                    }
                else:
                    # Restart all services in app
                    restart_cmd = f"cd {path}/{app} && docker-compose restart"
                    stdout, stderr, rc = await executor.execute(restart_cmd)
                    services_restarted.append(f"{app}/*")
                    restart_results[app] = {
                        "success": rc == 0,
                        "output": stdout,
                        "error": stderr if rc != 0 else None
                    }
            
            return {
                "status": "success",
                "services_restarted": services_restarted,
                "restart_results": restart_results,
                "affected_apps": list(affected_apps.keys()),
                "message": f"Restarted {len(services_restarted)} service(s)"
            }
            
        except Exception as e:
            return {
                "status": "error",
                "error_type": type(e).__name__,
                "message": str(e)
            }
    
    @server.tool()
    async def deploy_and_restart(
        commit_message: str,
        app_path: Optional[str] = None,
        service: Optional[str] = None,
        files: Optional[str] = "all",
        branch: Optional[str] = "main"
    ) -> Dict[str, Any]:
        """
        Complete deployment and restart workflow: deploy changes → restart affected services.
        
        Args:
            commit_message: Commit message
            app_path: Explicit app path. Auto-detected from changes if not provided.
            service: Specific service name or None for all services in app
            files: Files to commit ("all" or comma-separated list)
            branch: Branch name, default: main
            
        Returns:
            Deployment status, services restarted, restart results, any errors
        """
        try:
            # Step 1: Deploy (git add → commit → push → pull)
            deploy_result = await git_deploy(
                commit_message=commit_message,
                files=files,
                branch=branch,
                skip_pull=False
            )
            
            if deploy_result["status"] == "error":
                return {
                    "status": "error",
                    "deployment": deploy_result,
                    "message": "Deployment failed, services not restarted"
                }
            
            # Step 2: Restart affected services
            restart_result = await restart_affected_services(
                app_path=app_path,
                service=service,
                check_changes=True
            )
            
            return {
                "status": "success" if restart_result["status"] == "success" else "partial",
                "deployment": deploy_result,
                "restart": restart_result,
                "services_restarted": restart_result.get("services_restarted", []),
                "commit_hash": deploy_result.get("commit_hash"),
                "message": f"Deployed and restarted {len(restart_result.get('services_restarted', []))} service(s)"
            }
            
        except Exception as e:
            return {
                "status": "error",
                "error_type": type(e).__name__,
                "message": str(e)
            }

