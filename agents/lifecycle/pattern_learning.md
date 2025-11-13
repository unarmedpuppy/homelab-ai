# Pattern Learning and Auto-Skill Creation

## Overview

The Pattern Learning system analyzes patterns stored in memory to identify common workflows and automatically propose skills. This creates a self-improving system where frequently occurring patterns become reusable skills.

## How It Works

### 1. Pattern Analysis

The system queries memory for patterns that meet skill creation criteria:
- **High Frequency**: Pattern occurs frequently (threshold: 3+ occurrences)
- **High Severity**: Pattern indicates important workflow (severity: medium or high)
- **Has Solution**: Pattern includes a documented solution
- **Reusable**: Solution can be generalized into a workflow

### 2. Skill Proposal Generation

When a pattern meets criteria, the system:
1. Analyzes the pattern's solution
2. Identifies MCP tools used in the solution
3. Extracts workflow steps
4. Generates a skill proposal
5. Links the pattern to the proposed skill

### 3. Skill Creation Criteria

A pattern should become a skill if:
- ✅ Occurs 3+ times (frequency >= 3)
- ✅ Has documented solution
- ✅ Solution involves multiple steps
- ✅ Uses MCP tools (not just manual steps)
- ✅ Can be generalized (not too specific)

## Pattern to Skill Mapping

### Example: Port Conflict Pattern

**Pattern**:
- Name: "Port Conflict Resolution"
- Frequency: 5
- Severity: high
- Solution: "Check running containers → Check docker-compose files → Check system ports → Choose available port → Update configuration"

**Generated Skill**:
- Name: `resolve-port-conflict`
- Category: configuration
- Workflow: Uses `get_available_port()`, `check_port_status()`, `read_file()`, `write_file()`
- Based on: Pattern "Port Conflict Resolution"

## Auto-Skill Creation Process

### Step 1: Identify Candidate Patterns

```python
# Query patterns that meet criteria
candidates = await memory_query_patterns(
    severity="high",
    min_frequency=3
)

# Filter for patterns with solutions
candidates_with_solutions = [
    p for p in candidates 
    if p.get("solution") and len(p["solution"]) > 50
]
```

### Step 2: Analyze Pattern Solution

Extract from pattern solution:
- MCP tools mentioned
- Workflow steps
- Prerequisites
- Use cases

### Step 3: Generate Skill Proposal

Create skill proposal with:
- Name (derived from pattern name)
- Description (from pattern description)
- Workflow steps (from pattern solution)
- MCP tools (extracted from solution)
- Examples (from pattern examples)

### Step 4: Link Pattern to Skill

Update pattern to reference proposed skill:
- Add `proposed_skill` field
- Add `skill_proposal_date`

## MCP Tools

### `analyze_patterns_for_skills()`

Analyze patterns in memory and identify candidates for skill creation.

**Parameters**:
- `min_frequency`: Minimum frequency threshold (default: 3)
- `severity`: Filter by severity (optional)
- `limit`: Maximum patterns to analyze (default: 10)

**Returns**:
- List of pattern candidates with skill proposal suggestions

### `auto_propose_skill_from_pattern()`

Automatically create a skill proposal from a pattern.

**Parameters**:
- `pattern_name`: Name of pattern to convert
- `category`: Skill category (optional, auto-detected)
- `review_required`: Require human review (default: True)

**Returns**:
- Skill proposal details and file path

## Integration with Memory System

### Pattern Fields for Skill Creation

Patterns should include:
- `name`: Pattern name (becomes skill name)
- `description`: Pattern description (becomes skill description)
- `solution`: Step-by-step solution (becomes workflow steps)
- `frequency`: How often it occurs (determines if skill-worthy)
- `severity`: Importance level (determines priority)
- `examples`: Real-world examples (becomes skill examples)
- `tags`: Categorization (helps determine skill category)

### Skill Proposal Fields

Generated skill proposals include:
- `source_pattern`: Original pattern name
- `pattern_frequency`: Frequency from pattern
- `auto_generated`: true (indicates auto-creation)
- `review_status`: pending (requires human review)

## Best Practices

### When Patterns Become Skills

1. **Frequency Threshold**: Pattern occurs 3+ times
2. **Solution Quality**: Solution is well-documented and reusable
3. **Tool Usage**: Solution uses MCP tools (not just manual steps)
4. **Generalization**: Solution can be applied to similar situations

### When Patterns Should NOT Become Skills

1. **Too Specific**: Solution only applies to one specific case
2. **No Solution**: Pattern describes problem but no clear solution
3. **Low Frequency**: Pattern occurs rarely (1-2 times)
4. **Temporary Issue**: Pattern is for temporary/one-time fixes

## Review Process

### Auto-Generated Skills

All auto-generated skill proposals:
- Marked with `auto_generated: true`
- Status: `proposal` (requires review)
- Include source pattern reference
- Should be reviewed before approval

### Human Review

Before approving auto-generated skill:
1. Review workflow steps
2. Verify MCP tools are correct
3. Check for generalization issues
4. Test workflow manually
5. Update if needed

## Examples

### Example 1: Port Conflict Pattern → Skill

**Pattern**:
```yaml
name: Port Conflict Resolution
frequency: 5
severity: high
solution: |
  1. Use get_available_port() to find available port
  2. Check port status with check_port_status()
  3. Update docker-compose.yml with read_file() and write_file()
  4. Restart service with docker_compose_restart()
```

**Generated Skill Proposal**:
```yaml
name: resolve-port-conflict
category: configuration
source_pattern: Port Conflict Resolution
auto_generated: true
mcp_tools_required:
  - get_available_port
  - check_port_status
  - read_file
  - write_file
  - docker_compose_restart
```

### Example 2: Deployment Failure Pattern → Skill

**Pattern**:
```yaml
name: Deployment Failure Recovery
frequency: 4
severity: high
solution: |
  1. Check git status with git_status()
  2. View container logs with docker_view_logs()
  3. Check service dependencies with check_service_dependencies()
  4. Rollback if needed with git_checkout()
```

**Generated Skill Proposal**:
```yaml
name: recover-deployment-failure
category: deployment
source_pattern: Deployment Failure Recovery
auto_generated: true
mcp_tools_required:
  - git_status
  - docker_view_logs
  - check_service_dependencies
  - git_checkout
```

## Future Enhancements

### Machine Learning Integration

- Analyze workflow patterns across multiple agents
- Identify common sequences of MCP tool calls
- Suggest optimizations to workflows

### Automatic Skill Updates

- Monitor skill usage
- Update skills based on new patterns
- Deprecate unused skills

### Pattern Clustering

- Group similar patterns
- Identify pattern families
- Create skill hierarchies

---

**Last Updated**: 2025-01-13
**Status**: Active
**Version**: 1.0

