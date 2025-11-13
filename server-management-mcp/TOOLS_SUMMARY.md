# MCP Server Tools Summary

## Implemented Tools (37 total)

### Docker Management (8 tools)
1. `docker_list_containers` - List all containers with filters
2. `docker_container_status` - Get detailed container status
3. `docker_restart_container` - Restart a container
4. `docker_stop_container` - Stop a container
5. `docker_start_container` - Start a container
6. `docker_view_logs` - View container logs
7. `docker_compose_ps` - List docker-compose services
8. `docker_compose_restart` - Restart docker-compose services

### Media Download (11 tools)
9. `sonarr_clear_queue` - Clear all items from Sonarr queue
10. `sonarr_queue_status` - Get Sonarr queue summary
11. `sonarr_trigger_import_scan` - Trigger manual import scan
12. `sonarr_check_download_clients` - Check download client configuration
13. `radarr_clear_queue` - Clear all items from Radarr queue
14. `radarr_queue_status` - Get Radarr queue summary
15. `radarr_trigger_import_scan` - Trigger manual import scan
16. `radarr_list_root_folders` - List all root folders
17. `radarr_add_root_folder` - Add a root folder
18. `radarr_check_download_clients` - Check download client configuration
19. `remove_stuck_downloads` - Remove stuck items from queue

### System Monitoring (5 tools)
20. `check_disk_space` - Check disk usage with recommendations
21. `check_system_resources` - Check CPU, memory, load average
22. `service_health_check` - Comprehensive health check
23. `get_recent_errors` - Get recent errors from logs
24. `find_service_by_port` - Find service using a port

### Troubleshooting (3 tools)
25. `troubleshoot_failed_downloads` - Comprehensive diagnostic
26. `diagnose_download_client_unavailable` - Download client diagnostics
27. `check_service_dependencies` - Dependency verification

### Git Operations (4 tools)
28. `git_status` - Check repository status
29. `git_pull` - Pull latest changes
30. `git_deploy` - Complete deployment workflow
31. `deploy_and_restart` - Full workflow (deploy + restart)

### Networking (3 tools)
32. `check_port_status` - Check if port is listening
33. `vpn_status` - Check VPN services (Gluetun, Tailscale)
34. `check_dns_status` - Check DNS service (AdGuard)

### System Utilities (3 tools)
35. `cleanup_archive_files` - Remove unpacked archive files
36. `check_unmapped_folders` - Find folders not mapped to series/movies
37. `list_completed_downloads` - List completed downloads

## Tool Categories by Module

- `tools/docker.py` - 8 tools
- `tools/media_download.py` - 11 tools
- `tools/monitoring.py` - 5 tools
- `tools/troubleshooting.py` - 3 tools
- `tools/git.py` - 4 tools
- `tools/networking.py` - 3 tools
- `tools/system.py` - 3 tools

## High-Priority Planned Tools

### File Operations
- `read_file` - Read file contents
- `write_file` - Write file contents
- `read_docker_compose` - Parse docker-compose.yml
- `validate_docker_compose` - Validate configuration

### Advanced Docker
- `docker_list_images` - List Docker images
- `docker_prune_images` - Remove unused images
- `docker_container_stats` - Get container resource stats
- `docker_compose_up` - Start services
- `docker_compose_down` - Stop services

### Networking
- `check_port_status` - Check if port is listening
- `vpn_status` - Check VPN services
- `check_dns_status` - Check DNS service

### System Utilities
- `cleanup_archive_files` - Remove unpacked archives
- `list_completed_downloads` - List completed downloads

## Usage Examples

### Common Workflows

**Deploy and Restart Service:**
```python
await deploy_and_restart(
    commit_message="Update configuration",
    app_path="apps/media-download",
    service="sonarr"
)
```

**Troubleshoot Stuck Queue:**
```python
# 1. Diagnose
diagnosis = await diagnose_download_client_unavailable("sonarr")

# 2. Fix issues (if auto-fixable)
# ... apply fixes ...

# 3. Clear stuck items
await remove_stuck_downloads("sonarr", ["downloadClientUnavailable"])
```

**Check System Health:**
```python
# Check disk space
disk = await check_disk_space()

# Check service health
health = await service_health_check("media-download-sonarr")

# Get recent errors
errors = await get_recent_errors("sonarr")
```

---

**Last Updated**: 2025-11-13
**Total Implemented**: 37 tools
**Status**: Core functionality complete, expanding tool set

