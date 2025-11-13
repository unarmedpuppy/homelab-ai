# Server Management Skills

A library of reusable workflows for managing the home server infrastructure. Skills orchestrate MCP tools into complete, tested workflows.

## Overview

**Skills** are reusable workflows that combine MCP tools into complete operations. They complement the [MCP Server tools](../server-management-mcp/README.md) by providing step-by-step guidance for common tasks.

### Skills vs MCP Tools

- **MCP Tools** = Capabilities (what agents CAN do)
  - `docker_restart_container` - Can restart a container
  - `git_deploy` - Can deploy code
  - `check_disk_space` - Can check disk usage

- **Skills** = Workflows (how and when to use tools)
  - `standard-deployment` - Complete deployment workflow
  - `troubleshoot-container-failure` - Diagnostic workflow
  - `system-health-check` - Comprehensive system check

**Skills orchestrate MCP tools** into complete, tested workflows.

## Using Skills

### In Claude.ai / Claude Code

1. Skills are automatically discovered when placed in the skills directory
2. Claude activates relevant skills based on your task
3. Skills provide step-by-step guidance using MCP tools

### In Agent Prompts

Reference skills in your agent prompts:

```markdown
## Available Skills

For common workflows, use these skills instead of manual steps:

- **`standard-deployment`** - Deploy code changes (replaces 14-step checklist)
- **`troubleshoot-container-failure`** - Diagnose container issues
- **`system-health-check`** - Comprehensive system verification

See `server-management-skills/README.md` for complete catalog.
```

## Skills Catalog

### Deployment Skills

#### `standard-deployment` ✅
**Complete deployment workflow**: verify → deploy → restart → verify

- **When to use**: Deploying code changes, updating configurations
- **MCP Tools**: `git_status`, `git_deploy`, `docker_compose_restart`, `docker_container_status`
- **Replaces**: 14-step deployment checklist from agent prompts

#### `deploy-new-service` ✅
**Complete new service setup**: create config → validate → deploy → verify

- **When to use**: Setting up a new application/service
- **MCP Tools**: `read_file`, `write_file`, `validate_docker_compose`, `check_port_status`, `git_deploy`, `docker_compose_up`
- **Includes**: Configuration patterns, templates, and best practices

#### `rollback-deployment` ⏳
**Revert to previous version**: identify commit → checkout → restart

- **When to use**: Deployment causes issues, need to revert
- **MCP Tools**: `git_log`, `git_checkout`, `docker_compose_restart`

### Troubleshooting Skills

#### `troubleshoot-container-failure` ⏳
**Diagnose container issues**: check status → view logs → check dependencies → identify root cause

- **When to use**: Container won't start, crashes, or unhealthy
- **MCP Tools**: `docker_container_status`, `docker_view_logs`, `check_service_dependencies`, `check_system_resources`
- **Output**: Root cause analysis and recommended fixes

#### `troubleshoot-stuck-downloads` ✅
**Diagnose Sonarr/Radarr queue issues**: check queue → verify clients → clear stuck items

- **When to use**: Downloads stuck in queue, not processing
- **MCP Tools**: `sonarr_queue_status`, `sonarr_check_download_clients`, `radarr_queue_status`, `troubleshoot_failed_downloads`, `diagnose_download_client_unavailable`, `remove_stuck_downloads`
- **Output**: Issue identification and resolution steps

#### `troubleshoot-service-startup` ⏳
**Diagnose service startup failures**: check logs → verify config → check dependencies → identify issues

- **When to use**: Service fails to start after deployment
- **MCP Tools**: `docker_view_logs`, `validate_docker_compose`, `check_service_dependencies`, `check_port_status`

#### `diagnose-network-issue` ⏳
**Diagnose connectivity problems**: test connectivity → check DNS → verify routing → identify issues

- **When to use**: Services can't connect, network issues
- **MCP Tools**: `test_connectivity`, `resolve_dns`, `check_network_route`, `check_port_status`

### Configuration Skills

#### `add-subdomain` ✅
**Add subdomain configuration**: Homepage labels → Traefik routing → optional Cloudflare DDNS (with explicit approval)

- **When to use**: Adding a subdomain to an existing service, configuring Traefik routing, setting up HTTPS access
- **MCP Tools**: `read_file`, `write_file`, `get_available_port`, `check_port_status`, `git_deploy`
- **Security**: By default, services are NOT exposed to internet. Cloudflare DDNS updates require explicit human approval.
- **Includes**: Complete Traefik label patterns, Homepage label templates, Cloudflare DDNS update workflow

### Maintenance Skills

#### `system-health-check` ⏳
**Comprehensive system verification**: disk space → resources → services → summary

- **When to use**: Regular maintenance, after changes, troubleshooting
- **MCP Tools**: `check_disk_space`, `check_system_resources`, `docker_list_containers`, `service_health_check`
- **Output**: System health report with issues and recommendations

#### `backup-and-restore` ⏳
**Backup workflow**: create backup → verify → store → restore if needed

- **When to use**: Before major changes, regular backups
- **MCP Tools**: `database_backup`, `backup_env_files`, `verify_backup`, `restore_backup`

#### `cleanup-disk-space` ✅
**Clean up disk space**: remove archive files → prune Docker resources → verify

- **When to use**: Disk space above 80%, critical disk space, downloads failing
- **MCP Tools**: `check_disk_space`, `cleanup_archive_files`, `docker_prune_images`, `docker_prune_volumes`
- **Output**: Space freed, usage improvement

#### `cleanup-old-resources` ⏳
**Remove unused resources**: find unused images/volumes → verify → remove

- **When to use**: Disk space issues, cleanup maintenance
- **MCP Tools**: `docker_list_images`, `docker_prune_images`, `docker_list_volumes`, `docker_prune_volumes`

#### `update-service` ⏳
**Update service to new version**: check current → pull new image → restart → verify

- **When to use**: Updating service to new version
- **MCP Tools**: `docker_list_images`, `docker_update_image`, `docker_compose_restart`, `docker_container_status`

### Configuration Skills

#### `add-root-folder` ✅
**Add root folder to Sonarr/Radarr**: check existing → verify path → add → verify

- **When to use**: Missing root folder errors, organizing media into categories
- **MCP Tools**: `radarr_list_root_folders`, `radarr_add_root_folder`, `check_disk_space`
- **Output**: Root folder ID, accessibility status, unmapped folders

#### `add-new-application` ⏳
**Set up new application**: create structure → configure → deploy → verify

- **When to use**: Adding a new service to the server
- **MCP Tools**: `read_file`, `write_file`, `validate_docker_compose`, `check_port_status`, `git_deploy`
- **Includes**: Templates and best practices

#### `configure-reverse-proxy` ⏳
**Set up Traefik routing**: create labels → update DDNS → verify routing

- **When to use**: Adding HTTPS routing for a service
- **MCP Tools**: `read_file`, `write_file`, `docker_compose_restart`, `test_connectivity`

## Skill Structure

Each skill follows this structure:

```
skill-name/
├── SKILL.md          # Skill definition with YAML frontmatter
├── templates/        # Optional: File templates
└── resources/        # Optional: Reference files
```

### SKILL.md Format

```markdown
---
name: skill-name
description: Clear description of what this skill does
category: deployment|troubleshooting|maintenance|configuration
mcp_tools_required:
  - tool1
  - tool2
prerequisites:
  - Prerequisite 1
  - Prerequisite 2
---

# Skill Name

## When to Use This Skill

[Clear use cases]

## Workflow Steps

[Step-by-step instructions using MCP tools]

## MCP Tools Used

[List of tools and how they're used]

## Examples

[Real-world examples]

## Error Handling

[How to handle common errors]

## Related Skills

[Links to related skills]
```

## Creating New Skills

### Step 1: Identify the Workflow

Ask: "Is this a common, repeatable workflow that agents do frequently?"

If yes → Create a skill
If no → Use MCP tools directly

### Step 2: Create Skill Structure

```bash
mkdir -p server-management-skills/my-skill-name
touch server-management-skills/my-skill-name/SKILL.md
```

### Step 3: Write Skill Definition

Follow the SKILL.md format above. Include:
- Clear use cases
- Step-by-step workflow using MCP tools
- Examples
- Error handling
- Related skills

### Step 4: Update Catalog

Add your skill to this README.md in the appropriate category.

### Step 5: Test the Skill

- Test in Claude.ai or Claude Code
- Verify MCP tools are called correctly
- Test error scenarios
- Update documentation if needed

## Best Practices

1. **Use MCP Tools**: Skills should orchestrate MCP tools, not duplicate their functionality
2. **Be Specific**: Clear use cases and when to use the skill
3. **Include Examples**: Real-world examples help agents understand usage
4. **Handle Errors**: Document common errors and how to handle them
5. **Link Related Skills**: Help agents discover related workflows
6. **Keep Focused**: One skill = one workflow, not multiple workflows

## Integration with MCP Tools

Skills **must** use MCP tools. They don't replace tools, they orchestrate them:

```python
# Skill: "Deploy New Service"
# Uses MCP tools:
1. read_file("apps/new-service/docker-compose.yml")  # MCP tool
2. validate_docker_compose("apps/new-service/docker-compose.yml")  # MCP tool
3. check_port_status(8099)  # MCP tool
4. git_deploy("Add new service")  # MCP tool
5. docker_compose_up("apps/new-service")  # MCP tool
6. docker_container_status("new-service")  # MCP tool
```

## Status

- ✅ **7 skills implemented**:
  - `standard-deployment` - Complete deployment workflow
  - `troubleshoot-container-failure` - Container diagnostics
  - `system-health-check` - Comprehensive system verification
  - `troubleshoot-stuck-downloads` - Download queue issues
  - `cleanup-disk-space` - Clean up disk space systematically
  - `add-root-folder` - Add root folders to Sonarr/Radarr
- ⏳ **6 skills planned**: See catalog above

**Total**: 7 implemented, 6 planned = 13 skills

## Contributing

When creating new skills:

1. Follow the skill structure template
2. Use MCP tools (don't duplicate functionality)
3. Include clear examples
4. Document error handling
5. Update this README.md
6. Test the skill before committing

## References

- **MCP Tools**: [server-management-mcp/README.md](../server-management-mcp/README.md)
- **Skills Proposal**: [apps/docs/SKILLS_PROPOSAL.md](../apps/docs/SKILLS_PROPOSAL.md)
- **Claude Skills Pattern**: [awesome-claude-skills](https://github.com/unarmedpuppy/awesome-claude-skills)

---

**Last Updated**: 2025-01-10
**Status**: Active Development

