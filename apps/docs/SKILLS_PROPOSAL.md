# Server Management Skills Proposal

## Overview

Based on the [Claude Skills pattern](https://github.com/unarmedpuppy/awesome-claude-skills), this proposal outlines how to structure **Server Management Skills** that complement the MCP tools and reduce agent context bloat.

## Current State Analysis

### What You Have Now
- ✅ **MCP Tools** (39 tools): Capabilities - what agents CAN do
- ✅ **Agent Prompts** (649 lines): Context and guidelines
- ✅ **Documentation**: Scattered across multiple files
- ❌ **Workflow Bloat**: Common workflows embedded in prompts (14-step checklist, etc.)

### The Problem
- **Growing Context**: `SERVER_AGENT_PROMPT.md` is 649 lines and growing
- **Workflow Duplication**: Same workflows repeated in different prompts
- **Hard to Discover**: Workflows buried in long prompt files
- **Not Reusable**: Can't easily share workflows between agents

## Skills vs MCP Tools

### MCP Tools = **Capabilities** (What)
- `docker_restart_container` - Can restart a container
- `git_deploy` - Can deploy code
- `check_disk_space` - Can check disk usage

### Skills = **Workflows** (How & When)
- "Deploy a New Service" - Step-by-step workflow using MCP tools
- "Troubleshoot Stuck Downloads" - Diagnostic workflow
- "Standard Deployment" - Git workflow with verification

**They're Complementary**: Skills orchestrate MCP tools into complete workflows.

## Proposed Skills Structure

```
agents/skills/
├── README.md                    # Skills catalog and usage guide
├── deploy-new-service/
│   ├── SKILL.md                 # Skill definition with YAML frontmatter
│   └── templates/
│       └── docker-compose.yml.template
├── standard-deployment/
│   └── SKILL.md
├── troubleshoot-stuck-downloads/
│   └── SKILL.md
├── troubleshoot-container-failure/
│   └── SKILL.md
├── add-new-application/
│   ├── SKILL.md
│   └── templates/
│       ├── docker-compose.yml.template
│       └── env.template
├── system-health-check/
│   └── SKILL.md
└── backup-and-restore/
    └── SKILL.md
```

## Skill Template Structure

Each skill follows the Claude Skills pattern:

```markdown
---
name: standard-deployment
description: Complete deployment workflow: verify → deploy → restart → verify
category: deployment
mcp_tools_required:
  - git_status
  - git_deploy
  - docker_compose_restart
  - docker_container_status
---

# Standard Deployment Workflow

## When to Use This Skill

Use this skill when:
- Deploying code changes to the server
- Updating service configurations
- After making local changes that need to be deployed

## Prerequisites

- Changes committed locally (or use `git_deploy` to commit)
- MCP tools available: `git_deploy`, `docker_compose_restart`, `docker_container_status`

## Workflow Steps

1. **Verify Current State**
   - Use `git_status` to check repository state
   - Use `docker_container_status` to verify services are running
   - Check for uncommitted changes

2. **Deploy Changes**
   - Use `git_deploy(commit_message, files)` to:
     - Add changes
     - Commit with message
     - Push to remote
     - Pull on server

3. **Restart Affected Services**
   - Use `restart_affected_services(app_path, service)` or
   - Use `docker_compose_restart(app_path, service)` for explicit restart

4. **Verify Deployment**
   - Use `docker_container_status(container_name)` to verify services are healthy
   - Check logs if needed: `docker_view_logs(container_name)`
   - Verify HTTP response if applicable

5. **Handle Errors**
   - If deployment fails: Check git conflicts, verify connectivity
   - If restart fails: Check logs, verify dependencies
   - If service unhealthy: Use troubleshooting skills

## MCP Tools Used

- `git_status` - Check repository state
- `git_deploy` - Deploy code changes
- `restart_affected_services` - Restart affected services
- `docker_container_status` - Verify service health
- `docker_view_logs` - Check logs if needed

## Examples

### Example 1: Deploy Configuration Change

```
User: "Deploy the updated n8n configuration"

Agent activates: standard-deployment skill
1. git_status() → Check current state
2. git_deploy("Update n8n configuration", files=["apps/n8n/docker-compose.yml"])
3. restart_affected_services(app_path="apps/n8n")
4. docker_container_status("n8n") → Verify healthy
```

### Example 2: Deploy with Specific Service Restart

```
User: "Deploy and restart just the sonarr service"

Agent activates: standard-deployment skill
1. git_deploy("Update media-download config")
2. docker_compose_restart("apps/media-download", service="sonarr")
3. docker_container_status("media-download-sonarr")
```

## Error Handling

- **Git conflicts**: Report conflicts, suggest resolution
- **Service restart failure**: Check logs, verify dependencies
- **Service unhealthy**: Activate troubleshooting skill
- **Network issues**: Verify connectivity, check VPN status

## Related Skills

- `troubleshoot-container-failure` - If deployment causes issues
- `system-health-check` - For comprehensive verification
```

## Benefits of Skills Approach

### 1. **Reduced Context Bloat**
- Move 14-step checklist from prompt → `standard-deployment` skill
- Move troubleshooting workflows → dedicated skills
- Main prompt becomes focused on principles, not procedures

### 2. **Reusability**
- Skills work across Claude.ai, Claude Code, and API
- Share skills between different agents
- Version skills independently

### 3. **Discoverability**
- Skills catalog in README.md
- Clear metadata (name, description, category)
- Easy to find relevant skills

### 4. **Maintainability**
- Update workflows in one place (skill file)
- Test skills independently
- Document edge cases per skill

### 5. **Composability**
- Skills can call other skills
- Skills can use MCP tools
- Build complex workflows from simple skills

## Integration with MCP Tools

Skills **orchestrate** MCP tools:

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

## Proposed Skills Catalog

### Deployment Skills
- `standard-deployment` - Git deploy + restart workflow
- `deploy-new-service` - Complete new service setup
- `rollback-deployment` - Revert to previous version

### Troubleshooting Skills
- `troubleshoot-container-failure` - Diagnose container issues
- `troubleshoot-stuck-downloads` - Sonarr/Radarr queue issues
- `troubleshoot-service-startup` - Service won't start
- `diagnose-network-issue` - Connectivity problems

### Maintenance Skills
- `system-health-check` - Comprehensive system check
- `backup-and-restore` - Backup workflow
- `cleanup-old-resources` - Remove unused images/volumes
- `update-service` - Update service to new version

### Configuration Skills
- `add-new-application` - Set up new app with all requirements
- `configure-reverse-proxy` - Set up Traefik routing
- `setup-homepage-entry` - Add service to homepage

## Implementation Plan

### Phase 1: Core Skills (High Priority)
1. `standard-deployment` - Most common workflow
2. `troubleshoot-container-failure` - Common issue
3. `system-health-check` - Regular maintenance

### Phase 2: Deployment Skills
4. `deploy-new-service` - New service setup
5. `rollback-deployment` - Safety net

### Phase 3: Troubleshooting Skills
6. `troubleshoot-stuck-downloads`
7. `troubleshoot-service-startup`
8. `diagnose-network-issue`

### Phase 4: Maintenance Skills
9. `backup-and-restore`
10. `cleanup-old-resources`
11. `update-service`

## Usage in Agent Prompts

### Before (Current)
```markdown
## Agent Workflow Checklist

When working on a new task:

1. ✅ **Read this prompt and relevant README files**
2. ✅ **Check MCP Server tools first**
3. ✅ **Verify current state**
4. ✅ **Plan the approach**
5. ✅ **Make changes locally**
6. ✅ **Review changes carefully**
7. ✅ **Test locally if possible**
8. ✅ **Commit and push to Git** (MANDATORY)
9. ✅ **Pull on server** (MANDATORY)
10. ✅ **Deploy/restart services**
11. ✅ **Verify deployment**
12. ✅ **Monitor for issues**
13. ✅ **Document changes**
```

### After (With Skills)
```markdown
## Available Skills

Skills are reusable workflows that orchestrate MCP tools. Use them for common tasks:

- **`standard-deployment`** - Deploy code changes (replaces 14-step checklist)
- **`troubleshoot-container-failure`** - Diagnose container issues
- **`system-health-check`** - Comprehensive system verification

See `agents/skills/README.md` for complete catalog.

## When to Use Skills vs MCP Tools

- **Use Skills**: For complete workflows (deployment, troubleshooting, setup)
- **Use MCP Tools**: For individual operations (check status, restart service, view logs)
- **Skills use MCP Tools**: Skills orchestrate multiple MCP tools into workflows
```

## Comparison: Skills vs Current Approach

| Aspect | Current (Prompts) | Skills Approach |
|--------|------------------|-----------------|
| **Context Size** | 649 lines, growing | Focused prompts + discoverable skills |
| **Reusability** | Copy-paste between prompts | One skill, many agents |
| **Discoverability** | Buried in prompts | Catalog with metadata |
| **Maintainability** | Update multiple prompts | Update one skill file |
| **Composability** | Hard to combine | Skills can call skills |
| **Testing** | Manual | Test skills independently |
| **Versioning** | Git history only | Skill versioning |

## Recommendation

**Yes, implement Skills!** Here's why:

1. **Immediate Benefit**: Reduce `SERVER_AGENT_PROMPT.md` from 649 lines to ~200 lines
2. **Long-term Benefit**: Skills become reusable knowledge base
3. **Scalability**: Add new workflows without bloating prompts
4. **Compatibility**: Works with existing MCP tools
5. **Portability**: Skills work across Claude.ai, Claude Code, API

## Next Steps

1. Create `agents/skills/` directory
2. Implement `standard-deployment` skill (most common)
3. Update `SERVER_AGENT_PROMPT.md` to reference skills
4. Create skills catalog README
5. Migrate workflows from prompts to skills incrementally

---

**Reference**: [Claude Skills Pattern](https://github.com/unarmedpuppy/awesome-claude-skills)

