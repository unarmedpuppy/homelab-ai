# AI Agent Workflow - Best Practices

## Overview

This document outlines a proven workflow for managing AI agents working on software projects. This approach ensures quality, consistency, and effective collaboration between multiple AI agents.

## ⚠️ CRITICAL: Skills and MCP Tools First

**Before starting any task, your PRIMARY method for gaining context and capabilities is to discover Skills and MCP Tools.**

### Discovery Workflow (Do This First)

1. **Check Memory** - Query previous decisions and patterns
   - **If MCP tools available**: Use `memory_query_decisions()`, `memory_query_patterns()`, `memory_search()`
   - **If MCP tools NOT available**: Use fallback methods (direct SQLite queries or Python helpers - see Memory System section)
   - **This is how you gain context from past work** - don't repeat decisions

2. **Check Skills** - Review `server-management-skills/README.md` for workflows
   - Skills provide complete workflows for common tasks
   - Skills orchestrate MCP tools into tested workflows
   - Skills include error handling and best practices
   - **This is how you gain context** - don't start from scratch

3. **Check MCP Tools** - Review `server-management-mcp/README.md` for available tools
   - MCP tools provide individual operations (check status, restart, view logs)
   - **Memory tools** (9 tools) for querying and recording decisions/patterns/context
   - Tools are type-safe, tested, and documented
   - **This is how you gain capabilities** - don't write custom commands

4. **Use What Exists** - Memory, Skills, and Tools are your primary knowledge base
   - Memory = past decisions and patterns (what was decided before)
   - Skills = workflows (how to do complete tasks)
   - MCP Tools = capabilities (what you can do)
   - All provide context, examples, and best practices

5. **Create New Only If Needed** - Only create new tools/skills if:
   - No existing skill/tool exists for your operation
   - The operation is reusable and should be shared
   - You've tested your approach first

## Decision Framework: When to Store, Create, or Add

**CRITICAL**: After completing any work, follow this framework:

### Store in Memory (Always)
- ✅ **Important decisions** - Technology choices, architecture decisions, configuration choices
- ✅ **Patterns discovered** - Common issues and their solutions  
- ✅ **Context updates** - Current work status, progress, blockers
- ✅ **Rationale** - Why decisions were made (for future reference)

**When**: After making any important decision or discovering a pattern
**How**: Use `memory_record_decision()` or `memory_record_pattern()`

### Create a Skill (Reusable Workflows)
- ✅ **Multi-step workflows** - Complete processes that combine multiple operations
- ✅ **Tested procedures** - Workflows that have been validated and work reliably
- ✅ **Common tasks** - Operations that will be needed again in the future
- ✅ **Error handling** - Workflows that include troubleshooting steps

**When**: After completing a workflow that you anticipate needing again
**How**: Create a skill in `server-management-skills/` following the skill template

**Examples**:
- Deployment workflows → `standard-deployment` skill
- Troubleshooting procedures → `troubleshoot-container-failure` skill
- Setup procedures → `deploy-new-service` skill

### Add MCP Tool (Reusable Operations)
- ✅ **Single operations** - Individual actions that can be reused
- ✅ **Type-safe operations** - Operations that benefit from validation
- ✅ **Server operations** - Any operation that needs to run on the server
- ✅ **Frequently needed** - Operations you'll use multiple times

**When**: After identifying an operation that should be standardized and reusable
**How**: Add tool to `server-management-mcp/tools/` and update `server-management-mcp/README.md`

**Examples**:
- Container management → `docker_restart_container`, `docker_container_status`
- System checks → `check_disk_space`, `check_port_status`
- Git operations → `git_deploy`, `git_status`

### Decision Tree

```
After completing work:
│
├─→ Important decision made?
│   └─→ YES: Store in memory (memory_record_decision)
│
├─→ Discovered a pattern/issue?
│   └─→ YES: Store in memory (memory_record_pattern)
│
├─→ Created a reusable workflow?
│   └─→ YES: Create skill (server-management-skills/)
│
└─→ Identified a reusable operation?
    └─→ YES: Add MCP tool (server-management-mcp/tools/)
```

**Remember**: 
- **Memory** = Knowledge (what was decided, what patterns exist)
- **Skills** = Workflows (how to do complete tasks)
- **MCP Tools** = Operations (what you can do)

**Discovery Priority**:
1. **Memory** (past context) → Use `memory_query_*` and `memory_search` MCP tools (or fallback: direct SQLite queries)
2. **Skills** (workflows) → `server-management-skills/README.md`
3. **MCP Tools** (operations) → `server-management-mcp/README.md`
4. **Check for Specialized Agents** → Query agent registry if task requires specialization
5. **Create Specialized Agent** → Use `create_agent_definition` if no existing agent
6. Create new MCP tool (if operation is reusable)
7. Create new skill (if workflow is reusable)
8. Existing scripts (fallback)
9. SSH commands (last resort)

**See**: 
- `server-management-skills/README.md` - Skills catalog
- `server-management-mcp/README.md` - MCP tools reference
- `agents/docs/MCP_TOOL_DISCOVERY.md` - Tool discovery guide

## Core Workflow Components

### 1. Implementation Plan (`IMPLEMENTATION_PLAN.md`)

**Purpose**: Complete specification of what to build

**Contents**:
- Feature requirements and specifications
- Architecture and technology stack
- Database schemas
- API endpoint specifications
- UI/UX requirements
- Security considerations
- Performance requirements
- Testing strategy

**Key Principles**:
- Be comprehensive - include all details
- Be specific - avoid ambiguity
- Include examples - show expected behavior
- Document decisions - explain why, not just what
- Reference external resources - link to docs, APIs, etc.

**When to Create**: Before any implementation begins

### 2. Startup Guide (`STARTUP_GUIDE.md`)

**Purpose**: Essential information agents need to start working immediately

**Contents**:
- Calculation formulas (if applicable)
- API key setup instructions
- Environment variables template
- Configuration details
- Design preferences (UI/UX)
- Common gotchas and pitfalls
- Testing procedures
- Quick start checklist

**Key Principles**:
- Focus on actionable information
- Include formulas, constants, and algorithms
- Provide setup instructions
- Document gotchas to avoid
- Make it the first stop for agents

**When to Create**: Alongside or immediately after implementation plan

### 3. Agent Prompt (`[PROJECT]_AGENTS_PROMPT.md`)

**Purpose**: Guidelines and standards for agents implementing features

**Contents**:
- **Getting Started Section** (critical):
  - Reading order (STARTUP_GUIDE first!)
  - Quick start workflow
  - Task claiming process
- Agent role and responsibilities
- Technology stack and patterns
- Coding standards (backend and frontend)
- Code review process expectations
- Pre-submission checklist
- Common issues to avoid
- Task details (if included)
- Testing checklist

**Key Principles**:
- Self-contained - agent should know what to do
- Clear expectations - what reviewers will check
- Actionable checklists - pre-submission, testing
- Reference other docs - but summarize key points
- Include examples - show patterns to follow

**When to Create**: After implementation plan and startup guide

### 4. Agent Reviewer Prompt (`[PROJECT]_AGENT_REVIEWER_PROMPT.md`)

**Purpose**: Standards and process for reviewing agent code

**Contents**:
- Reviewer role and responsibilities
- Review process (step-by-step)
- Detailed checklists:
  - Backend code review
  - Frontend code review
  - API review
  - Integration review
  - Documentation review
  - Testing review
- Review decision criteria (APPROVED/NEEDS REVISION/REJECTED)
- Review report template
- Common issues reference
- Quality standards

**Key Principles**:
- Be thorough - cover all aspects
- Be specific - exact things to check
- Be fair - constructive feedback
- Be consistent - same standards for all
- Provide templates - standardized reports

**When to Create**: Alongside agent prompt

### 5. Task Tracking (`TASKS.md`)

**Purpose**: Manageable, claimable tasks with status tracking

**Contents**:
- Task list with unique IDs
- Status tracking (PENDING/CLAIMED/IN PROGRESS/REVIEW/COMPLETED/BLOCKED)
- Dependencies between tasks
- Priority levels
- Task descriptions
- Files to create/modify
- Completion criteria

**Key Principles**:
- Break down into small, manageable tasks
- Clear dependencies
- Specific deliverables
- Status updates required
- Claimable by agents

**When to Create**: After implementation plan (can be refined as needed)

## Workflow Process

### Phase 1: Planning

1. **Create Implementation Plan**
   - Define all features
   - Specify architecture
   - Document requirements
   - Include API specs, schemas, etc.

2. **Create Startup Guide**
   - Extract essential formulas/algorithms
   - Document setup requirements
   - List API keys needed
   - Document design preferences

3. **Create Agent Prompt**
   - Define agent role
   - Set coding standards
   - Include review expectations
   - Add task details (or reference TASKS.md)

4. **Create Reviewer Prompt**
   - Define review process
   - Create checklists
   - Set quality standards
   - Provide report templates

5. **Create Task List**
   - Break down into tasks
   - Define dependencies
   - Set priorities
   - Make tasks claimable

### Phase 2: Implementation

1. **Agent Claims Task**
   - Updates TASKS.md: `[CLAIMED]` or `[IN PROGRESS]`
   - Adds identifier/name

2. **Agent Discovers Memory, Skills, Tools, and Agents** (PRIMARY STEP)
   - **Check Memory first**: Query previous decisions and patterns using memory MCP tools
     - `memory_query_decisions()` - Find related decisions
     - `memory_query_patterns()` - Find common patterns
     - `memory_search()` - Full-text search across memories
     - `memory_get_recent_context()` - Check recent work
   - **Check for Specialized Agents**: If task requires specialization, query agent registry
     - `query_agent_registry(specialization="...")` - Find existing specialized agents
     - If found: Assign task to existing agent
     - If not found: Consider creating specialized agent
   - **Check Skills**: Review `server-management-skills/README.md` for workflows
   - **Check MCP Tools**: Review `server-management-mcp/README.md` for available tools
   - **Memory provides past context**: Learn from previous decisions and patterns
   - **Specialized Agents provide expertise**: Delegate to domain experts when needed
   - **Skills provide workflows**: Use existing skills for common tasks
   - **MCP Tools provide capabilities**: Use tools for individual operations
   - **This is how you gain context and capabilities** - don't start from scratch

3. **Agent Reads Documentation**
   - STARTUP_GUIDE.md (essential)
   - IMPLEMENTATION_PLAN.md (relevant sections)
   - Agent prompt (guidelines)
   - Skills and tools documentation (capabilities)
   - Task details

4. **Agent Implements**
   - **Uses Memory to avoid repeating decisions** (query before deciding)
   - **Records important decisions** using `memory_record_decision()`
   - **Records patterns discovered** using `memory_record_pattern()`
   - **Updates context** using `memory_save_context()` during work
   - **Creates specialized agents when needed** using `create_agent_definition()`
     - If task requires domain expertise not in current agent
     - If task would benefit from specialized knowledge
     - If similar tasks will recur (reusable specialization)
   - **Uses Skills for workflows** (don't reinvent common workflows)
   - **Uses MCP Tools for operations** (don't write custom commands)
   - Follows coding standards
   - Uses patterns from examples
   - Documents as they go
   - Tests functionality

5. **Agent Self-Reviews**
   - Completes Pre-Submission Checklist
   - Runs self-review questions
   - Fixes obvious issues

6. **Agent Submits for Review**
   - **Saves final context** using `memory_save_context(status="completed")`
   - Updates TASKS.md: `[REVIEW]`
   - Adds completion summary
   - Commits and pushes code

### Phase 3: Review

1. **Reviewer Picks Up Task**
   - Sees `[REVIEW]` status in TASKS.md
   - Reads reviewer prompt
   - Gathers task context

2. **Reviewer Conducts Review**
   - Follows review process step-by-step
   - Uses detailed checklists
   - Tests functionality
   - Checks documentation

3. **Reviewer Creates Report**
   - Uses standardized template
   - Categorizes issues (Critical/Medium/Minor)
   - Provides recommendations
   - Makes decision (APPROVED/NEEDS REVISION/REJECTED)

4. **Reviewer Updates Status**
   - Updates TASKS.md with review status
   - Adds review report reference
   - Communicates decision

### Phase 4: Iteration

1. **If APPROVED**
   - Task marked `[COMPLETED]`
   - Agent can claim next task
   - Documentation updated if needed

2. **If NEEDS REVISION**
   - Agent addresses issues
   - Resubmits for review
   - Reviewer re-checks fixes

3. **If REJECTED**
   - Agent reviews feedback
   - May need to restart task
   - Significant rework required

## Optimization Strategies

### 1. Documentation Structure

**Current Approach**:
```
[PROJECT]/
├── IMPLEMENTATION_PLAN.md      # Complete spec
├── STARTUP_GUIDE.md            # Essential details
├── [PROJECT]_AGENTS_PROMPT.md  # Agent guidelines
├── [PROJECT]_AGENT_REVIEWER_PROMPT.md  # Review standards
├── TASKS.md                    # Task tracking
└── README.md                   # Overview
```

**Optimization**: Create a `docs/` subdirectory for larger projects:
```
[PROJECT]/
├── README.md                   # Quick overview
├── TASKS.md                    # Task tracking
└── docs/
    ├── IMPLEMENTATION_PLAN.md
    ├── STARTUP_GUIDE.md
    ├── AGENTS_PROMPT.md
    └── REVIEWER_PROMPT.md
```

### 2. Task Granularity

**Best Practices**:
- Tasks should be completable in 1-4 hours
- Each task should have clear deliverables
- Dependencies should be explicit
- Tasks should be independently testable

**Anti-Patterns to Avoid**:
- Tasks too large (days of work)
- Tasks too small (minutes of work)
- Vague deliverables
- Hidden dependencies

### 3. Review Efficiency

**Optimizations**:
- **Automated Checks First**: Run linters, type checkers, tests before review
- **Checklist Automation**: Create scripts to verify common issues
- **Template Responses**: Pre-written feedback for common issues
- **Batch Reviews**: Review related tasks together

**Review Focus Areas** (priority order):
1. **Critical**: Security, correctness, breaking changes
2. **High**: Requirements met, calculations accurate
3. **Medium**: Code quality, consistency
4. **Low**: Style, minor optimizations

### 4. Communication Patterns

**Current**: Status updates in TASKS.md

**Enhancements**:
- **Review Comments**: Add inline comments in code (if supported)
- **Issue Tracking**: Link to GitHub issues for complex problems
- **Progress Updates**: Regular status updates for long tasks
- **Blockers**: Clear communication when blocked

### 5. Feedback Loops

**Short Loop** (Immediate):
- Agent self-review before submission
- Automated checks (linting, tests)
- Quick validation

**Medium Loop** (Review Cycle):
- Reviewer feedback
- Agent fixes
- Re-review

**Long Loop** (Project Level):
- Retrospectives on completed phases
- Process improvements
- Documentation updates

### 6. Quality Gates

**Before Submission**:
- [ ] Pre-Submission Checklist complete
- [ ] Self-review complete
- [ ] Code compiles/runs
- [ ] Tests pass (if applicable)
- [ ] Documentation updated

**Before Approval**:
- [ ] All requirements met
- [ ] Code quality acceptable
- [ ] Documentation complete
- [ ] Integration works
- [ ] No critical issues

### 7. Knowledge Sharing

**Patterns**:
- Document common solutions in STARTUP_GUIDE
- Add examples to agent prompt
- Share learnings in implementation plan
- Update gotchas as discovered

**Anti-Patterns**:
- Repeating same mistakes
- Not documenting solutions
- Inconsistent patterns
- Knowledge silos

## Memory System Integration

### Why Memory Matters

**Current Limitation**: Each agent session starts from scratch, losing context and decisions from previous sessions.

**Solution**: Use **File-Based Memory System** - since agents run in Cursor/Claude Desktop, we use markdown files that agents can read/write directly.

**See**: 
- `agents/memory/README_FILE_BASED.md` for complete guide

### Quick Integration (SQLite-Based via MCP Tools)

**Agents use MCP tools to interact with memory throughout the workflow:**

**Before Starting Work:**
```python
# Example: Starting a deployment task
# Query previous decisions (learn from past)
memory_query_decisions(project="home-server", search_text="deployment", limit=5)

# Check for common patterns
memory_query_patterns(severity="high", tags="deployment,docker", limit=5)

# Search for related work
memory_search("docker-compose setup")

# Check recent context from other agents
memory_get_recent_context(limit=5)
```

**During Work:**
```python
# Example: Recording decisions as you make them
memory_record_decision(
    content="Use PostgreSQL for trading-journal database",
    rationale="Need ACID compliance, concurrent writes, and complex queries. SQLite doesn't support concurrent writes well.",
    project="trading-journal",
    task="T1.3",
    importance=0.9,
    tags="database,architecture,postgresql"
)

# Example: Recording patterns when discovered
memory_record_pattern(
    name="Port Conflict Resolution",
    description="Services failing to start due to port conflicts. Common when adding new services without checking existing port usage.",
    solution="Always check port availability first using check_port_status MCP tool. Reference apps/docs/APPS_DOCUMENTATION.md for port list.",
    severity="medium",
    tags="docker,networking,ports,troubleshooting"
)

# Example: Updating context regularly
memory_save_context(
    agent_id="agent-001",
    task="T1.3",
    current_work="PostgreSQL setup in progress. Created docker-compose.yml, configured environment variables. Next: Run migrations.",
    status="in_progress",
    notes="Database password generated with openssl rand -hex 32"
)
```

**After Work:**
```python
# Example: Completing a task
memory_save_context(
    agent_id="agent-001",
    task="T1.3",
    current_work="PostgreSQL setup complete. Database running, migrations applied, connection tested.",
    status="completed",
    notes="Used port 5432 internally, exposed via docker network"
)
```

**See**: `agents/memory/MEMORY_USAGE_EXAMPLES.md` for complete examples and best practices.

**9 Memory MCP Tools Available:**
- **Query** (5 tools): `memory_query_decisions`, `memory_query_patterns`, `memory_search`, `memory_get_recent_context`, `memory_get_context_by_task`
- **Record** (3 tools): `memory_record_decision`, `memory_record_pattern`, `memory_save_context`
- **Export** (1 tool): `memory_export_to_markdown`

**See**: 
- `agents/memory/MCP_TOOLS_GUIDE.md` - Complete reference with examples
- `agents/memory/MEMORY_USAGE_EXAMPLES.md` - Real-world usage examples and best practices
- `server-management-mcp/README.md` - Memory tools in MCP catalog

### ⚠️ Fallback: When MCP Tools Aren't Available

**If MCP tools are not available** (e.g., MCP server not connected), use these fallback methods:

#### Option 1: Use Helper Script (Recommended)

Use the `query_memory.sh` helper script for easy command-line access:

```bash
cd apps/agent_memory

# Query decisions
./query_memory.sh decisions --project home-server --limit 5
./query_memory.sh decisions --search "deployment" --limit 10

# Query patterns
./query_memory.sh patterns --severity high --limit 10
./query_memory.sh patterns --search "container" --limit 5

# Full-text search
./query_memory.sh search "your search query"

# Get recent context
./query_memory.sh recent --limit 5
```

**See**: `agents/memory/QUERY_MEMORY_README.md` for complete usage guide.

#### Option 1b: Direct SQLite Database Queries

If helper script unavailable, query the SQLite database directly:

```bash
# Query recent decisions
cd apps/agent_memory
sqlite3 memory.db "SELECT * FROM decisions ORDER BY created_at DESC LIMIT 5;"

# Query by project
sqlite3 memory.db "SELECT * FROM decisions WHERE project='home-server' LIMIT 10;"

# Query patterns by severity
sqlite3 memory.db "SELECT * FROM patterns WHERE severity='high' LIMIT 10;"

# Full-text search (if FTS enabled)
sqlite3 memory.db "SELECT * FROM decisions_fts WHERE decisions_fts MATCH 'search_term' LIMIT 10;"

# Search in content
sqlite3 memory.db "SELECT * FROM decisions WHERE content LIKE '%search_term%' LIMIT 10;"
```

#### Option 2: Python Memory Helper Functions

Use the Python memory module directly:

```python
from agents.memory import get_memory

memory = get_memory()

# Query decisions
decisions = memory.query_decisions(project="home-server", limit=5)

# Query patterns
patterns = memory.query_patterns(severity="high", limit=5)

# Full-text search
results = memory.search("search query", limit=20)
```

#### Option 3: Read Exported Markdown Files

If markdown exports exist, read them directly:

```bash
# Check for exported memory files
ls agents/memory/memory/export/

# Read exported decisions
cat agents/memory/memory/export/decisions/*.md
```

**Important**: Always try MCP tools first. Use fallback methods only when MCP is unavailable.

### Benefits

- ✅ **Fast queries**: 10-100x faster than file-based (indexed SQLite)
- ✅ **Full-text search**: SQLite FTS5 for fast searching
- ✅ **Relationships**: Link decisions to patterns via tags
- ✅ **Structured**: Proper indexing and foreign keys
- ✅ **Human readable**: Optional markdown export
- ✅ **No setup**: Database auto-created on first use

## Advanced Workflows

### Parallel Development

**When Multiple Agents Work Simultaneously**:
- Clear task boundaries
- Explicit interfaces (API contracts)
- Regular integration checks
- Communication of changes
- **Memory system**: Share context via memory graph

**Coordination**:
- Claim tasks in TASKS.md immediately
- Update status frequently
- Communicate blockers
- Share progress
- **Memory system**: Use message queue for coordination

### Iterative Refinement

**Process**:
1. Implement MVP feature
2. Review and approve
3. Enhance based on feedback
4. Refine documentation
5. Repeat

**Benefits**:
- Faster initial delivery
- Continuous improvement
- Learning from usage
- Reduced risk

### Quality Assurance Layers

**Layer 1: Agent Self-Check**
- Pre-submission checklist
- Self-review questions
- Manual testing

**Layer 2: Automated Checks**
- Linters
- Type checkers
- Unit tests
- Integration tests

**Layer 3: Peer Review**
- Reviewer agent
- Detailed checklists
- Manual testing
- Integration verification

**Layer 4: Integration Testing**
- End-to-end tests
- Performance tests
- Security scans

## Metrics and Improvement

### Track These Metrics

1. **Task Completion Rate**
   - Tasks completed vs. claimed
   - Time to completion
   - Revision rate

2. **Review Efficiency**
   - Time to review
   - Approval rate
   - Common issues

3. **Code Quality**
   - Issues found in review
   - Critical vs. minor issues
   - Patterns of problems

4. **Documentation Quality**
   - Completeness
   - Accuracy
   - Usefulness

### Continuous Improvement

**Regular Reviews**:
- What's working well?
- What's causing problems?
- What can be improved?
- What should be documented?

**Process Refinement**:
- Update prompts based on learnings
- Refine checklists
- Improve templates
- Share best practices

## Best Practices Summary

### For Project Managers

1. **Start with Planning**
   - Comprehensive implementation plan
   - Clear requirements
   - Well-defined tasks

2. **Provide Context**
   - Startup guide with essentials
   - Clear agent guidelines
   - Review standards

3. **Enable Self-Service**
   - Agents can claim tasks
   - Clear documentation
   - Examples and patterns

4. **Ensure Quality**
   - Review process
   - Quality gates
   - Feedback loops

### For Agents

1. **Discover Memory, Skills and Tools First** (PRIMARY METHOD)
   - **Check Memory**: Query previous decisions and patterns using memory MCP tools
     - `memory_query_decisions()` - Find related decisions
     - `memory_query_patterns()` - Find common patterns
     - `memory_search()` - Full-text search
     - Learn from past work - don't repeat decisions
   - **Check Skills**: Review `server-management-skills/README.md` for workflows matching your task
   - **Check MCP Tools**: Review `server-management-mcp/README.md` for available tools
   - **Memory provides past context**: Learn from previous decisions and patterns
   - **Skills provide workflows**: Complete step-by-step guidance for common tasks
   - **MCP Tools provide capabilities**: Individual operations you can use
   - **Skills use MCP Tools**: Skills orchestrate tools into workflows
   - **This is your primary way to gain context and capabilities** - don't start from scratch

2. **Read Documentation**
   - STARTUP_GUIDE.md (essential)
   - IMPLEMENTATION_PLAN.md (context)
   - Agent prompt (guidelines)
   - Skills and tools documentation (capabilities)

3. **Follow Standards**
   - Query memory before making decisions (don't repeat past mistakes)
   - Record important decisions using `memory_record_decision()`
   - Record patterns using `memory_record_pattern()`
   - Update context using `memory_save_context()` during work
   - Use Skills for workflows (don't reinvent)
   - Use MCP Tools for operations (don't write custom commands)
   - Follow coding standards
   - Follow patterns and examples

4. **Self-Review**
   - Complete checklists
   - Test thoroughly
   - Fix obvious issues

5. **Communicate**
   - Update task status
   - Record decisions in memory (not just in code comments)
   - Save context regularly
   - Document decisions
   - Ask questions early

### For Reviewers

1. **Be Thorough**
   - Follow checklists
   - Test functionality
   - Check all aspects

2. **Be Fair**
   - Constructive feedback
   - Specific issues
   - Actionable recommendations

3. **Be Consistent**
   - Same standards for all
   - Use templates
   - Document decisions

4. **Be Efficient**
   - Focus on critical issues
   - Batch similar reviews
   - Provide clear feedback

## Tools and Automation

### ⚠️ CRITICAL: Skills and MCP Tools First

**For all server operations, your PRIMARY discovery method is Skills and MCP Tools.**

**Discovery Priority**:
1. **Skills** (preferred for workflows) - Check `server-management-skills/README.md` first
2. **MCP Tools** (preferred for operations) - Check `server-management-mcp/README.md` second
3. Create new MCP tool (if operation is reusable)
4. Create new skill (if workflow is reusable)
5. Existing scripts (fallback)
6. SSH commands (last resort)

### Server Management Skills

**Location**: `server-management-skills/` in repository root

**What Skills Provide**:
- Complete workflows for common tasks
- Step-by-step guidance using MCP tools
- Error handling and best practices
- Examples and use cases

**Available Skills**:
- `standard-deployment` - Complete deployment workflow
- `troubleshoot-container-failure` - Container diagnostics
- `system-health-check` - Comprehensive system verification
- `troubleshoot-stuck-downloads` - Download queue issues
- `deploy-new-service` - New service setup
- And more...

**Usage**:
- Review `server-management-skills/README.md` for complete catalog
- Skills work in Claude.ai, Claude Code, and API
- Skills automatically use MCP tools correctly

**See**: `server-management-skills/README.md` for complete skills catalog.

### Server Management MCP Server

**Location**: `server-management-mcp/` in repository root

**What MCP Tools Provide**:
- Individual operations (check status, restart service, view logs)
- Type-safe, tested capabilities
- Consistent error handling
- Standardized return formats

**Available Tools** (58 tools):
- **Memory management** (9 tools) - Query and record decisions, patterns, context
- **Task coordination** (6 tools) - Register, claim, update, and query tasks
- **Agent management** (3 tools) - Create specialized agents, query registry, assign tasks
- Docker container management (8 tools)
- Media download operations (13 tools)
- System monitoring (5 tools)
- Git operations (4 tools)
- Troubleshooting (3 tools)
- Networking (3 tools)
- System utilities (3 tools)

**Usage**:
- If you have MCP access (Claude Desktop, GPT-4 with MCP): Use tools directly
- If no MCP access: Reference `server-management-mcp/README.md` for tool documentation
- **Memory tools**: Use `memory_query_*` and `memory_record_*` throughout workflow
- Skills orchestrate MCP tools into workflows

**See**: 
- `server-management-mcp/README.md` for tool reference
- `apps/docs/MCP_SERVER_PLAN.md` for complete architecture and tool catalog
- `agents/docs/MCP_TOOL_DISCOVERY.md` for tool discovery guide

### Recommended Tools

1. **Server Management**: 
   - **Skills** (preferred for workflows) - `server-management-skills/README.md`
   - **MCP Tools** (preferred for operations) - `server-management-mcp/README.md`
   - SSH commands (last resort fallback)
2. **Task Tracking**: 
   - **Central Task Registry** (preferred) - `agents/tasks/registry.md` with 6 MCP tools
   - Individual TASKS.md files (for agent-specific context)
   - GitHub Issues (for external tracking)
3. **Code Review**: GitHub PRs or inline comments
4. **Automated Checks**: GitHub Actions, pre-commit hooks
5. **Documentation**: Markdown files, auto-generated API docs

### Automation Opportunities

1. **Pre-Submission Checks**
   - Linting
   - Type checking
   - Test running
   - Documentation generation

2. **Review Assistance**
   - Automated code analysis
   - Security scanning
   - Dependency checking
   - Performance profiling

3. **Status Updates**
   - Auto-update task status
   - Generate progress reports
   - Track metrics

## Example Workflow Timeline

**Day 1: Planning**
- Create implementation plan
- Create startup guide
- Create agent prompt
- Create reviewer prompt
- Create task list

**Day 2-3: First Tasks**
- Agent claims T1.1
- Agent implements
- Agent submits for review
- Reviewer reviews
- Iterate if needed

**Week 1: Foundation**
- Complete Phase 1 tasks
- Establish patterns
- Refine process
- Document learnings

**Week 2+: Features**
- Implement features
- Review and iterate
- Continuous improvement
- Documentation updates

## Additional Resources

### Primary Discovery Resources (Check First)

1. **Agent Prompt**: `agents/docs/AGENT_PROMPT.md` ⭐ **START HERE**
   - Complete, efficient prompt with everything you need
   - Discovery workflow, memory, skills, MCP tools, agent spawning
   - Quick reference and common operations
   - **Read this first** - it has everything

2. **Memory Tools Guide**: `agents/memory/MCP_TOOLS_GUIDE.md`
   - Complete reference for 9 memory MCP tools
   - Query and record examples
   - Workflow integration patterns

3. **Skills Catalog**: `server-management-skills/README.md`
   - Complete workflows for common tasks
   - Step-by-step guidance using MCP tools
   - Examples and error handling

3. **Task Coordination Guide**: `agents/tasks/README.md` ⭐
   - Complete task coordination system guide
   - 6 MCP tools for task management
   - Dependency tracking and validation
   - Workflow examples

4. **MCP Tools Reference**: `server-management-mcp/README.md`
   - All available tools with parameters (58 tools total)
   - Memory tools (9 tools) documented
   - Task coordination tools (6 tools) documented
   - Agent management tools (3 tools) documented
   - Usage examples
   - Tool categories

5. **Tool Discovery Guide**: `agents/docs/MCP_TOOL_DISCOVERY.md`
   - How to discover and use tools
   - Memory operations section
   - Task coordination operations section
   - When to create new tools
   - Tool creation workflow

6. **MCP Server Plan**: `apps/docs/MCP_SERVER_PLAN.md`
   - Complete tool catalog (implemented and planned)
   - Architecture and design
   - Implementation status

### Other Resources

- **Memory System**: See `agents/memory/README.md` for current SQLite-based memory system
- **Server Setup**: See `SERVER_AGENT_PROMPT.md` for server-specific context
- **Skills Proposal**: See `apps/docs/SKILLS_PROPOSAL.md` for skills architecture

## Conclusion

This workflow provides:
- **Structure**: Clear process and documentation
- **Quality**: Multiple review layers
- **Efficiency**: Self-service and automation
- **Consistency**: Standards and patterns
- **Improvement**: Feedback loops and metrics
- **Memory**: Persistent context and knowledge sharing (with mem-layer)

**Key Success Factors**:
1. Comprehensive planning
2. Clear documentation
3. Defined standards
4. Effective review process
5. Continuous improvement
6. **Memory system** (optional but recommended)

---

**Last Updated**: Based on Trading Journal project experience
**Maintained By**: Project maintainers
**Version**: 1.1 (added memory system integration)

