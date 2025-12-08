# Beads Viewer Reference (bv)

Comprehensive reference for [bv](https://github.com/Dicklesworthstone/beads_viewer), the AI graph sidecar for Beads projects.

## Overview

bv is a fast terminal UI for Beads projects that precomputes dependency metrics:
- **PageRank** - Measures "blocking power" of tasks
- **Betweenness** - Identifies bottlenecks connecting graph clusters
- **Critical Path** - Finds tasks on longest dependency chains
- **HITS Algorithm** - Identifies hubs (aggregators) and authorities (prerequisites)
- **Cycle Detection** - Flags circular dependencies

## Why bv vs. Raw Beads?

Using `bd` directly gives an agent **data**. Using `bv --robot-*` gives an agent **intelligence**.

| Capability | Raw Beads (JSONL) | bv Robot Mode |
|------------|-------------------|---------------|
| Query | "List all issues." | "List the top 5 bottlenecks blocking the release." |
| Context Cost | High (Linear with issue count) | Low (Fixed summary struct) |
| Graph Logic | Agent must infer/compute | Pre-computed (PageRank/Brandes) |
| Safety | Agent might miss a cycle | Cycles explicitly flagged |

## Installation

```bash
# Install via script
curl -fsSL "https://raw.githubusercontent.com/Dicklesworthstone/beads_viewer/main/install.sh" | bash

# Verify
bv --version
```

## Critical Warning for AI Agents

**⚠️ IMPORTANT: As an agent, you MUST ONLY use `bv` with the `--robot-*` flags!**

The default `bv` command launches an interactive TUI that will hang agents. Always use:
- `bv --robot-help`
- `bv --robot-insights`
- `bv --robot-plan`
- `bv --robot-priority`
- `bv --robot-recipes`
- `bv --robot-diff`

## Robot Commands

### --robot-help

Shows all AI-facing commands with explanations.

```bash
bv --robot-help
```

### --robot-insights

Get deep graph analysis with pre-computed metrics.

```bash
bv --robot-insights
```

**Output Schema:**

```json
{
  "bottlenecks": [{ "id": "CORE-123", "value": 0.45 }],
  "keystones": [{ "id": "API-001", "value": 12.0 }],
  "influencers": [{ "id": "AUTH-007", "value": 0.82 }],
  "hubs": [{ "id": "EPIC-100", "value": 0.67 }],
  "authorities": [{ "id": "UTIL-050", "value": 0.91 }],
  "cycles": [["TASK-A", "TASK-B", "TASK-A"]],
  "clusterDensity": 0.045,
  "stats": {
    "pageRank": { "CORE-123": 0.15 },
    "betweenness": { "CORE-123": 0.45 },
    "eigenvector": { "AUTH-007": 0.82 },
    "hubs": { "EPIC-100": 0.67 },
    "authorities": { "UTIL-050": 0.91 },
    "inDegree": { "CORE-123": 5 },
    "outDegree": { "CORE-123": 2 },
    "criticalPathScore": { "API-001": 12.0 },
    "density": 0.045,
    "topologicalOrder": ["CORE-123", "API-001"]
  }
}
```

**Field Reference:**

| Field | Metric | What It Contains |
|-------|--------|------------------|
| `bottlenecks` | Betweenness | Top nodes bridging graph clusters |
| `keystones` | Critical Path | Top nodes on longest dependency chains |
| `influencers` | Eigenvector | Top nodes connected to important neighbors |
| `hubs` | HITS Hub | Top dependency aggregators (Epics) |
| `authorities` | HITS Authority | Top prerequisite providers (Utilities) |
| `cycles` | Cycle Detection | All circular dependency paths (fix these first!) |
| `clusterDensity` | Density | Overall graph interconnectedness |
| `stats` | All Metrics | Full raw data for custom analysis |

### --robot-plan

Get a dependency-respecting execution plan.

```bash
bv --robot-plan
```

**Output includes:**
- `tracks` - Independent work streams that can be parallelized
- `items` - Actionable issues sorted by priority within each track
- `unblocks` - Issues that become actionable when each item is done
- `summary` - Highlights highest-impact item to work on first

**Example queries:**

```bash
# Get all tracks
bv --robot-plan | jq '.tracks'

# Get first track items
bv --robot-plan | jq '.tracks[0].items'

# See what a task unblocks
bv --robot-plan | jq '.items[] | select(.id == "home-server-xxx") | .unblocks'

# Get summary recommendation
bv --robot-plan | jq '.summary'
```

### --robot-priority

Get priority recommendations with reasoning.

```bash
bv --robot-priority
```

**Output includes:**
- `recommendations` - Sorted by confidence, then impact score
- `confidence` - 0-1 score indicating strength of recommendation
- `reasoning` - Human-readable explanations
- `direction` - 'increase' or 'decrease' priority

**Example queries:**

```bash
# Get top recommendation
bv --robot-priority | jq '.recommendations[0]'

# Get all "increase priority" recommendations
bv --robot-priority | jq '.recommendations[] | select(.direction == "increase")'

# Get high-confidence recommendations
bv --robot-priority | jq '.recommendations[] | select(.confidence > 0.8)'
```

### --robot-recipes

List available recipes (pre-defined filters).

```bash
bv --robot-recipes
```

**Common recipes:**
- `default` - Standard view
- `actionable` - Ready-to-work items
- `blocked` - Items with unresolved dependencies

**Apply a recipe:**

```bash
bv --recipe actionable --robot-plan
```

### --robot-diff

Show changes since a historical point.

```bash
bv --robot-diff --diff-since <commit|date>

# Examples
bv --robot-diff --diff-since HEAD~5
bv --robot-diff --diff-since main
bv --robot-diff --diff-since 2024-01-15
bv --robot-diff --diff-since abc123f
```

**Output includes:**
- New issues created
- Issues closed
- Status changes
- Priority changes
- Cycles introduced/resolved

## Agent Usage Patterns

### Phase 1: Triage & Orientation

Before starting a session, run `bv --robot-insights`:

```bash
# Check for cycles first (must fix before anything)
bv --robot-insights | jq '.cycles'

# If cycles exist, stop and fix them!

# Otherwise, check bottlenecks
bv --robot-insights | jq '.bottlenecks'
```

**Decision logic:**
- Cycles present → Fix cycles immediately
- High-value bottleneck → Work on it to unblock others
- No bottlenecks → Use `bv --robot-plan` for execution order

### Phase 2: Impact Analysis

When asked to work on a specific task, check its impact:

```bash
# Check if task is a bottleneck
bv --robot-insights | jq '.bottlenecks[] | select(.id == "home-server-xxx")'

# Check if task is on critical path
bv --robot-insights | jq '.keystones[] | select(.id == "home-server-xxx")'

# Check PageRank (blocking power)
bv --robot-insights | jq '.stats.pageRank["home-server-xxx"]'
```

**Decision logic:**
- High PageRank → Many downstream dependents, test thoroughly
- High betweenness → Bottleneck, prioritize
- On critical path → Blocking a long chain, don't delay

### Phase 3: Execution Planning

Get optimal work order:

```bash
# Get execution plan
bv --robot-plan | jq '.tracks'

# Find what can be parallelized
bv --robot-plan | jq '.tracks | length'  # Number of parallel tracks

# Get highest-impact first task
bv --robot-plan | jq '.summary.recommended_first'
```

## Delegation Decision Framework

| Scenario | Command | Why |
|----------|---------|-----|
| "What should I work on next?" | `bv --robot-plan` | Shows optimal execution order |
| "Which task has most impact?" | `bv --robot-insights` → bottlenecks | High betweenness = unblocks many |
| "Are there structural issues?" | `bv --robot-insights` → cycles | Fix cycles before new work |
| "Should I reprioritize?" | `bv --robot-priority` | Data-driven recommendations |
| "What can run in parallel?" | `bv --robot-plan` → tracks | Independent work streams |
| "What changed recently?" | `bv --robot-diff --diff-since HEAD~10` | Track project evolution |

## Graph Metrics Explained

### PageRank

Measures "blocking power" - how many tasks transitively depend on this one.

- **High PageRank** → Fundamental dependency, many downstream tasks
- **Use case** → Prioritize high PageRank tasks to unblock the most work

### Betweenness Centrality

Measures "bottleneck status" - how often this task appears on shortest paths between other tasks.

- **High Betweenness** → Connects disparate clusters, critical path
- **Use case** → Identify tasks that bridge different workstreams

### Critical Path Score

Heuristic for depth - how deep in the dependency chain this task sits.

- **High Score** → Blocking a long chain of subsequent work
- **Use case** → Don't delay tasks with high critical path scores

### HITS (Hubs and Authorities)

Two complementary scores:
- **Hubs** → Tasks that depend on many others (Epic aggregators)
- **Authorities** → Tasks that many others depend on (Utility prerequisites)

### Eigenvector Centrality

Measures connection to "important" neighbors - not just quantity but quality of connections.

- **High Eigenvector** → Connected to other high-value tasks
- **Use case** → Identify influencer tasks in the network

## Hooks Configuration

Configure hooks in `.bv/hooks.yaml`:

```yaml
pre-export:
  - command: "validate-tasks.sh"
    timeout: 30s
post-export:
  - command: "notify-slack.sh"
    timeout: 60s
```

**Environment variables available:**
- `BV_EXPORT_PATH` - Export file path
- `BV_EXPORT_FORMAT` - Export format
- `BV_ISSUE_COUNT` - Number of issues
- `BV_TIMESTAMP` - Export timestamp

**Skip hooks:**

```bash
bv --no-hooks --export-md report.md
```

## Export to Markdown

Generate readable status reports with Mermaid.js visualizations:

```bash
bv --export-md status-report.md
```

## Quick Reference

| Action | Command |
|--------|---------|
| Help | `bv --robot-help` |
| Graph insights | `bv --robot-insights` |
| Execution plan | `bv --robot-plan` |
| Priority recs | `bv --robot-priority` |
| Available recipes | `bv --robot-recipes` |
| Apply recipe | `bv --recipe <name> --robot-plan` |
| Diff since | `bv --robot-diff --diff-since <ref>` |
| Export markdown | `bv --export-md <file>` |
| Skip hooks | `bv --no-hooks ...` |

## Common jq Queries

```bash
# Get cycles (fix these first!)
bv --robot-insights | jq '.cycles'

# Get top 3 bottlenecks
bv --robot-insights | jq '.bottlenecks[:3]'

# Get tasks on critical path
bv --robot-insights | jq '.keystones'

# Get parallel track count
bv --robot-plan | jq '.tracks | length'

# Get first recommended task
bv --robot-priority | jq '.recommendations[0]'

# Check specific task's PageRank
bv --robot-insights | jq '.stats.pageRank["home-server-xxx"]'

# Get topological order (dependency-respecting sequence)
bv --robot-insights | jq '.stats.topologicalOrder'
```

## See Also

- [beads.md](beads.md) - Beads CLI reference (bd)
- [beads-task-management tool](../tools/beads-task-management/SKILL.md) - Workflow guide
- [task-manager-agent](../personas/task-manager-agent.md) - Task coordination persona
- [Beads Viewer GitHub](https://github.com/Dicklesworthstone/beads_viewer) - Official repository
