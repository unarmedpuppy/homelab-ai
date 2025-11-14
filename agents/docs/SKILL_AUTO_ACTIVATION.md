# Skill Auto-Activation Guide

**Critical**: Skills won't be used unless you explicitly check them!

---

## The Problem

Even with comprehensive skills in the library, agents often don't use them unless explicitly reminded. Skills sit unused, and agents reinvent workflows that already exist.

## The Solution

**Always use skill activation tools before starting work.**

---

## Quick Start

### Before Starting ANY Work

```python
# Get skill suggestions based on your context
suggest_relevant_skills(
    prompt_text="What you're asking or working on",
    file_paths="files you're editing (comma-separated)",
    task_description="Description of your current task"
)
```

**Example:**
```python
suggest_relevant_skills(
    prompt_text="How do I deploy code changes?",
    file_paths="apps/trading-bot/docker-compose.yml",
    task_description="Deploy latest changes to trading-bot service"
)
```

**Returns:**
- List of relevant skills with match reasons
- Formatted activation reminder
- Paths to skill files

### Then Load and Review Skills

1. Review the suggested skills
2. Read the skill files (e.g., `agents/skills/standard-deployment/SKILL.md`)
3. Follow the skill workflow instead of reinventing

---

## When to Use

### Always Use Before:
- Starting implementation
- Working on deployment
- Troubleshooting issues
- Configuring services
- Any workflow task

### Use When Unsure:
- Not sure which skill applies
- Working on something new
- Need to find the right workflow

---

## Available Tools

### `suggest_relevant_skills()`

**Purpose**: Analyze context and suggest relevant skills

**Parameters**:
- `prompt_text` (optional): Your current prompt or question
- `file_paths` (optional): Comma-separated file paths you're working with
- `task_description` (optional): Description of your current task

**Returns**:
- List of relevant skills with match scores
- Formatted activation reminder
- Match reasons for each skill

**Example**:
```python
result = suggest_relevant_skills(
    prompt_text="Deploy code changes",
    file_paths="apps/my-app/docker-compose.yml",
    task_description="Deploy latest changes"
)

# Result includes:
# - skills: List of relevant skills
# - activation_reminder: Formatted reminder to check skills
# - suggestion: Which skills to check
```

### `get_skill_activation_reminder()`

**Purpose**: Get a quick reminder of which skills to check

**Parameters**:
- `context_summary`: Brief summary of what you're about to work on

**Returns**:
- Formatted reminder with top 5 relevant skills
- Skill descriptions and when to use them
- Paths to skill files

**Example**:
```python
reminder = get_skill_activation_reminder(
    context_summary="Deploying code changes to trading-bot service"
)

# Returns formatted reminder you can display
```

---

## Workflow Integration

### Discovery Workflow (Updated)

```
0. Start Monitoring
0.5. Check Messages
1. Check Active Dev Docs
2. Query Memory
3. Check Specialized Agents
4. ⭐ USE suggest_relevant_skills() - Find relevant skills
5. Load and review suggested skills
6. Check MCP Tools
7. Start work following skill workflows
```

---

## Example Workflows

### Example 1: Deployment

```python
# 1. Get skill suggestions
suggest_relevant_skills(
    prompt_text="Deploy code changes",
    task_description="Deploy latest changes to production"
)

# Returns: standard-deployment skill (high match)

# 2. Load the skill
# Read: agents/skills/standard-deployment/SKILL.md

# 3. Follow the skill workflow
# Skill provides step-by-step deployment workflow
```

### Example 2: Troubleshooting

```python
# 1. Get skill suggestions
suggest_relevant_skills(
    prompt_text="Container is failing",
    file_paths="apps/my-app/docker-compose.yml"
)

# Returns: troubleshoot-container-failure skill

# 2. Load the skill
# Read: agents/skills/troubleshoot-container-failure/SKILL.md

# 3. Follow the diagnostic workflow
```

### Example 3: Configuration

```python
# 1. Get skill suggestions
suggest_relevant_skills(
    prompt_text="Add subdomain for new service",
    task_description="Configure subdomain routing"
)

# Returns: add-subdomain skill

# 2. Load the skill
# Read: agents/skills/add-subdomain/SKILL.md

# 3. Follow the configuration workflow
```

---

## Why This Matters

### Before Skill Activation
- ❌ Skills sit unused
- ❌ Agents reinvent workflows
- ❌ Inconsistent implementations
- ❌ More mistakes and rework

### After Skill Activation
- ✅ Skills are actually used
- ✅ Consistent workflows
- ✅ Tested patterns followed
- ✅ Fewer mistakes

---

## Best Practices

1. **Always Check First** - Use `suggest_relevant_skills()` before starting work
2. **Load Suggested Skills** - Don't just see the list, actually read the skill files
3. **Follow Skill Workflows** - Skills provide tested workflows, use them
4. **Update Skills** - If a skill is missing something, propose improvements
5. **Create New Skills** - If no skill exists for your workflow, create one

---

## Integration with Other Systems

### Dev Docs
- Skills are referenced in dev docs
- Dev docs preserve which skills were used
- Skills provide the "how", dev docs provide the "what"

### Memory System
- Skills can be learned from patterns
- Pattern learning can suggest new skills
- Skills become part of institutional knowledge

### Task Coordination
- Tasks can reference skills
- Skills provide workflows for tasks
- Task completion follows skill workflows

---

## Troubleshooting

### "No relevant skills found"

**Solution**: 
- Review `agents/skills/README.md` for all available skills
- Your task might be too specific (use MCP tools directly)
- Consider creating a new skill if workflow is reusable

### "Skills don't match my context"

**Solution**:
- Provide more context in `prompt_text` and `task_description`
- Include relevant file paths
- Skills match on keywords, be more specific

### "I still don't use skills"

**Solution**:
- Make it a habit: Always call `suggest_relevant_skills()` first
- Read the skill files, don't just see the list
- Follow the skill workflows step-by-step

---

**Last Updated**: 2025-01-13  
**Status**: Active  
**See Also**:
- `agents/skills/README.md` - Skills catalog
- `agents/prompts/base.md` - Main agent prompt
- `agents/docs/AGENT_SYSTEM_ENHANCEMENT_PLAN.md` - Enhancement plan

