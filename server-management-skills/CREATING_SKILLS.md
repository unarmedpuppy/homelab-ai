# Creating New Skills - Agent Guide

## Overview

This guide explains how agents can create new skills when they identify reusable workflow patterns.

## When to Create a Skill

Create a skill when:
- ✅ **Workflow is reusable** - You'll do this multiple times
- ✅ **Workflow is common** - Other agents will need this
- ✅ **Workflow has clear steps** - Can be documented step-by-step
- ✅ **Uses MCP tools** - Orchestrates existing MCP tools

**Don't create a skill if:**
- ❌ One-off task (won't repeat)
- ❌ Too specific to your current task
- ❌ Better as a single MCP tool

## Skill Creation Workflow

### Step 1: Check Existing Skills

Before creating, check if a similar skill exists:

```python
# Review skills catalog
# Read: server-management-skills/README.md
# Check if your workflow matches an existing skill
```

**If similar skill exists**: Use it or enhance it
**If no similar skill**: Proceed to create

### Step 2: Create Skill Proposal

Use the `propose_skill()` MCP tool to create a skill proposal:

```python
propose_skill(
    name="my-skill-name",
    description="Clear description of what this skill does",
    category="deployment|troubleshooting|maintenance|configuration",
    use_cases="When to use this skill",
    workflow_steps="Step-by-step workflow using MCP tools",
    mcp_tools_required="tool1, tool2, tool3",
    examples="Real-world examples",
    prerequisites="What's needed before using this skill"
)
```

This creates:
- Skill proposal in `server-management-skills/proposals/my-skill-name.md`
- Proposal includes all details for review

### Step 3: Test the Skill

Before submitting, test the skill:

1. Follow the workflow manually
2. Verify MCP tools work correctly
3. Test error scenarios
4. Document any issues

### Step 4: Submit for Review

Once tested, the proposal is ready for review. A human or review agent will:
- Review the proposal
- Test the workflow
- Approve or request changes

### Step 5: Skill Approved

Once approved:
- Skill directory created: `server-management-skills/my-skill-name/`
- `SKILL.md` file created with full definition
- Skills catalog (`README.md`) updated automatically
- Skill is now available to all agents

## Skill Proposal Template

When using `propose_skill()`, provide:

```markdown
---
name: skill-name
description: Clear description
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

[Clear use cases - when would an agent use this?]

## Workflow Steps

[Step-by-step instructions using MCP tools]

## MCP Tools Used

[List of tools and how they're used in the workflow]

## Examples

[Real-world examples showing the skill in action]

## Error Handling

[How to handle common errors]

## Related Skills

[Links to related skills]
```

## Best Practices

1. **Use MCP Tools**: Skills should orchestrate MCP tools, not duplicate functionality
2. **Be Specific**: Clear use cases and when to use the skill
3. **Include Examples**: Real-world examples help agents understand
4. **Handle Errors**: Document common errors and solutions
5. **Link Related Skills**: Help agents discover related workflows
6. **Keep Focused**: One skill = one workflow, not multiple workflows

## Example: Creating a Skill

### Scenario: Agent needs "Rollback Deployment" skill

**Step 1: Check Existing Skills**
- Review `server-management-skills/README.md`
- No rollback skill exists
- Proceed to create

**Step 2: Create Proposal**
```python
propose_skill(
    name="rollback-deployment",
    description="Revert to previous version: identify commit → checkout → restart",
    category="deployment",
    use_cases="Deployment causes issues, need to revert to previous working version",
    workflow_steps="""
1. Identify previous working commit using git_log()
2. Checkout previous commit using git_checkout()
3. Restart affected services using docker_compose_restart()
4. Verify services are running using docker_container_status()
""",
    mcp_tools_required="git_log, git_checkout, docker_compose_restart, docker_container_status",
    examples="Rollback after failed deployment of trading-journal app",
    prerequisites="Git repository with commit history, services running"
)
```

**Step 3: Test**
- Test rollback workflow manually
- Verify it works correctly

**Step 4: Submit**
- Proposal created in `server-management-skills/proposals/rollback-deployment.md`
- Ready for review

**Step 5: Approved**
- Skill created in `server-management-skills/rollback-deployment/SKILL.md`
- Added to catalog in README.md
- Available to all agents

## Integration with Memory

When creating skills, consider:

1. **Check Memory**: Query for similar patterns
   ```python
   memory_query_patterns(search_text="rollback deployment")
   ```

2. **Record Decision**: Document why you're creating this skill
   ```python
   memory_record_decision(
       content="Create rollback-deployment skill",
       rationale="Need systematic way to revert failed deployments",
       importance=0.8,
       tags="deployment,skills"
   )
   ```

3. **Record Pattern**: If this addresses a recurring issue
   ```python
   memory_record_pattern(
       name="Failed Deployment Recovery",
       description="Deployments sometimes fail and need rollback",
       solution="Use rollback-deployment skill",
       severity="medium"
   )
   ```

## Skill Structure

Once approved, skills follow this structure:

```
skill-name/
├── SKILL.md          # Skill definition with YAML frontmatter
├── templates/        # Optional: File templates
└── resources/        # Optional: Reference files
```

## Review Process

Skills go through review:
1. **Proposal Created** - Agent creates proposal
2. **Review** - Human/reviewer checks proposal
3. **Testing** - Reviewer tests the workflow
4. **Approval** - Skill approved and created
5. **Catalog Update** - README.md updated automatically

## Questions?

- **When should I create a skill?** - If workflow is reusable and common
- **What if skill is rejected?** - Review feedback, improve, resubmit
- **Can I update existing skills?** - Yes, propose changes via skill proposal
- **How do I test a skill?** - Follow the workflow manually before submitting

---

**See Also**:
- `server-management-skills/README.md` - Skills catalog
- `apps/docs/agents/AGENT_PROMPT.md` - Agent prompt with skill discovery
- `server-management-mcp/README.md` - MCP tools reference

---

**Last Updated**: 2025-01-10
**Status**: Active

