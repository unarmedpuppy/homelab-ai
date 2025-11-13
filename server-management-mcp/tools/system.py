"""System-level operations and utilities."""
from typing import Dict, Any, Optional
from mcp.server import Server
from clients.remote_exec import RemoteExecutor


executor = RemoteExecutor()


def register_system_tools(server: Server):
    """Register system-level tools with MCP server."""
    
    @server.tool()
    async def cleanup_archive_files(
        dry_run: bool = False,
        category: str = "all"
    ) -> Dict[str, Any]:
        """
        Remove unpacked archive files (.rar, .par2, .nzb) from completed downloads.
        
        Args:
            dry_run: Show what would be deleted without deleting
            category: Specific category to clean ("tv", "movies", "music", "all")
            
        Returns:
            Files removed count, space freed, list of removed files
        """
        try:
            base_path = "/server/apps/media-download/downloads/completed"
            
            if category == "all":
                paths = [
                    f"{base_path}/tv",
                    f"{base_path}/movies",
                    f"{base_path}/music",
                    f"{base_path}/books"
                ]
            else:
                paths = [f"{base_path}/{category}"]
            
            all_removed = []
            total_size = 0
            
            for path in paths:
                # Find archive files
                find_cmd = f"find {path} -type f \\( -name '*.rar' -o -name '*.par2' -o -name '*.nzb' \\)"
                stdout, stderr, returncode = await executor.execute(find_cmd)
                
                if returncode != 0 and returncode != 1:  # 1 = no matches found
                    continue
                
                files = [f.strip() for f in stdout.split('\n') if f.strip()]
                
                if dry_run:
                    all_removed.extend(files)
                else:
                    # Delete files
                    for file_path in files:
                        rm_cmd = f"rm -f '{file_path}'"
                        await executor.execute(rm_cmd)
                        all_removed.append(file_path)
            
            # Calculate space (rough estimate)
            if all_removed:
                # Get total size of removed files
                size_cmd = f"du -ch {' '.join([f'\"{f}\"' for f in all_removed[:100]])} 2>/dev/null | tail -1 | awk '{{print $1}}'"
                size_stdout, _, _ = await executor.execute(size_cmd)
                space_freed = size_stdout.strip() if size_stdout else "unknown"
            else:
                space_freed = "0"
            
            return {
                "status": "success",
                "dry_run": dry_run,
                "category": category,
                "files_removed": len(all_removed),
                "space_freed": space_freed,
                "files_removed_list": all_removed[:50] if not dry_run else all_removed,  # Limit in real run
                "message": f"{'Would remove' if dry_run else 'Removed'} {len(all_removed)} archive files"
            }
            
        except Exception as e:
            return {
                "status": "error",
                "error_type": type(e).__name__,
                "message": str(e)
            }
    
    @server.tool()
    async def check_unmapped_folders(
        service: str,
        root_folder_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Find folders in root directories that aren't mapped to series/movies.
        
        Args:
            service: "sonarr" or "radarr"
            root_folder_id: Optional specific root folder ID to check
            
        Returns:
            Unmapped folders that could be imported
        """
        try:
            if service == "sonarr":
                from clients.sonarr import SonarrClient
                client = SonarrClient()
                root_folders = await client.get_root_folders()
            elif service == "radarr":
                from clients.radarr import RadarrClient
                client = RadarrClient()
                root_folders = await client.get_root_folders()
            else:
                return {
                    "status": "error",
                    "error_type": "ValueError",
                    "message": f"Unknown service: {service}"
                }
            
            unmapped_all = []
            
            for folder in root_folders:
                if root_folder_id and folder.get("id") != root_folder_id:
                    continue
                
                unmapped = folder.get("unmappedFolders", [])
                for item in unmapped:
                    unmapped_all.append({
                        "root_folder_id": folder.get("id"),
                        "root_folder_path": folder.get("path"),
                        "name": item.get("name"),
                        "path": item.get("path"),
                        "relative_path": item.get("relativePath")
                    })
            
            return {
                "status": "success",
                "service": service,
                "unmapped_folders": unmapped_all,
                "total": len(unmapped_all)
            }
            
        except Exception as e:
            return {
                "status": "error",
                "error_type": type(e).__name__,
                "message": str(e)
            }
    
    @server.tool()
    async def list_completed_downloads(
        category: str = "all",
        limit: int = 50
    ) -> Dict[str, Any]:
        """
        List completed downloads in download directories.
        
        Args:
            category: "tv", "movies", "music", "books", or "all"
            limit: Maximum number of items to return per category
            
        Returns:
            List of completed download directories
        """
        try:
            base_path = "/server/apps/media-download/downloads/completed"
            
            if category == "all":
                categories = ["tv", "movies", "music", "books"]
            else:
                categories = [category]
            
            results = {}
            
            for cat in categories:
                path = f"{base_path}/{cat}"
                command = f"ls -d {path}/*/ 2>/dev/null | head -{limit}"
                stdout, _, _ = await executor.execute(command)
                
                if stdout:
                    dirs = [d.strip().rstrip('/') for d in stdout.split('\n') if d.strip()]
                    # Extract just the directory name
                    dir_names = [d.split('/')[-1] for d in dirs]
                    results[cat] = dir_names
                else:
                    results[cat] = []
            
            total = sum(len(v) for v in results.values())
            
            return {
                "status": "success",
                "category": category,
                "downloads": results,
                "total": total
            }
            
        except Exception as e:
            return {
                "status": "error",
                "error_type": type(e).__name__,
                "message": str(e)
            }

