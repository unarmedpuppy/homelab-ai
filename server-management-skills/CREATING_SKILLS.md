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

## Skill Structure (Progressive Disclosure)

**CRITICAL**: Follow Anthropic's best practices - keep main SKILL.md under 500 lines and use resource files for details.

### Recommended Structure

```
skill-name/
├── SKILL.md          # Main skill file (<500 lines) - Core patterns, quick reference
├── resources/        # Optional: Detailed examples, edge cases, advanced patterns
│   ├── advanced-patterns.md
│   ├── error-handling.md
│   ├── examples.md
│   └── troubleshooting.md
└── templates/        # Optional: File templates
    └── example-template.yml
```

### SKILL.md Format

**Main file should be <500 lines** and include:
- YAML frontmatter with metadata
- When to use this skill
- Core workflow steps (using MCP tools)
- Quick reference to resources for details
- Basic examples

**Resource files** contain:
- Detailed examples
- Edge cases
- Advanced patterns
- Troubleshooting guides
- Extended documentation

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
- Resources added if needed
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
7. **Progressive Disclosure**: Main file <500 lines, use resources for details
8. **Attach Scripts**: Document utility scripts in the skill (see Scripts section)

## Progressive Disclosure Pattern

### Main SKILL.md (<500 lines)

```markdown
---
name: standard-deployment
description: Complete deployment workflow
category: deployment
---

# Standard Deployment

## When to Use

[Brief use cases]

## Quick Start

1. Check git status
2. Deploy changes
3. Restart services
4. Verify deployment

## Detailed Resources

For detailed examples and advanced patterns, see:
- `resources/examples.md` - Real-world examples
- `resources/error-handling.md` - Error handling patterns
- `resources/troubleshooting.md` - Common issues

## MCP Tools Used

- `git_status()` - Check repository status
- `git_deploy()` - Deploy changes
- `docker_compose_restart()` - Restart services
```

### Resource Files (Detailed Content)

**resources/examples.md**:
```markdown
# Deployment Examples

## Example 1: Simple Deployment
[Detailed example with full context]

## Example 2: Deployment with Rollback
[Detailed example with rollback steps]
```

**resources/error-handling.md**:
```markdown
# Error Handling Patterns

## Common Errors

### Error: Git conflicts
[How to handle]

### Error: Service won't restart
[How to handle]
```

## Scripts Attached to Skills

**Document utility scripts in your skill:**

```markdown
## Utility Scripts

### Testing Authenticated Routes

Use the provided test script:
```bash
./agents/scripts/test-auth-route.sh <endpoint>
```

This script handles:
- Authentication token retrieval
- Request signing
- Cookie header creation
```

**Benefits:**
- Agents know exactly what script to use
- Prevents script duplication
- Documents script purpose and usage

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
4. Verify services are running
""",
    mcp_tools_required="git_log, git_checkout, docker_compose_restart, docker_container_status"
)
```

**Step 3: Test**
- Follow workflow manually
- Test error scenarios
- Document issues

**Step 4: Submit**
- Proposal created in `proposals/rollback-deployment.md`
- Ready for review

**Step 5: Approved**
- Skill directory created
- `SKILL.md` created
- Resources added if needed
- Catalog updated

---

**Last Updated**: 2025-01-13  
**Status**: Active  
**See Also**:
- `server-management-skills/README.md` - Skills catalog
- `agents/docs/SKILL_AUTO_ACTIVATION.md` - How to use skills
- `agents/docs/AGENT_PROMPT.md` - Main agent prompt
