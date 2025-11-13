# AI Agent Workflow - Best Practices

## Overview

This document outlines a proven workflow for managing AI agents working on software projects. This approach ensures quality, consistency, and effective collaboration between multiple AI agents.

## ⚠️ CRITICAL: Skills and MCP Tools First

**Before starting any task, your PRIMARY method for gaining context and capabilities is to discover Skills and MCP Tools.**

### Discovery Workflow (Do This First)

1. **Check Skills** - Review `server-management-skills/README.md` for workflows
   - Skills provide complete workflows for common tasks
   - Skills orchestrate MCP tools into tested workflows
   - Skills include error handling and best practices
   - **This is how you gain context** - don't start from scratch

2. **Check MCP Tools** - Review `server-management-mcp/README.md` for available tools
   - MCP tools provide individual operations (check status, restart, view logs)
   - Tools are type-safe, tested, and documented
   - **This is how you gain capabilities** - don't write custom commands

3. **Use What Exists** - Skills and tools are your primary knowledge base
   - Skills = workflows (how to do complete tasks)
   - MCP Tools = capabilities (what you can do)
   - Both provide context, examples, and best practices

4. **Create New Only If Needed** - Only create new tools/skills if:
   - No existing skill/tool exists for your operation
   - The operation is reusable and should be shared
   - You've tested your approach first

**Discovery Priority**:
1. **Skills** (workflows) → `server-management-skills/README.md`
2. **MCP Tools** (operations) → `server-management-mcp/README.md`
3. Create new MCP tool (if operation is reusable)
4. Create new skill (if workflow is reusable)
5. Existing scripts (fallback)
6. SSH commands (last resort)

**See**: 
- `server-management-skills/README.md` - Skills catalog
- `server-management-mcp/README.md` - MCP tools reference
- `apps/docs/MCP_TOOL_DISCOVERY.md` - Tool discovery guide

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

2. **Agent Discovers Skills and Tools** (PRIMARY STEP)
   - **Check Skills first**: Review `server-management-skills/README.md` for workflows
   - **Check MCP Tools**: Review `server-management-mcp/README.md` for available tools
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
- `apps/agent_memory/README_FILE_BASED.md` for complete guide
- `MEMORY_SYSTEM_COMPARISON.md` for comparison with alternatives

### Quick Integration (File-Based)

**Agents record memories as markdown files:**

1. **Record decisions**: Create files in `apps/agent_memory/memory/decisions/`
2. **Record patterns**: Create files in `apps/agent_memory/memory/patterns/`
3. **Save context**: Create files in `apps/agent_memory/memory/context/`

**Example - Recording a Decision:**

Create `apps/agent_memory/memory/decisions/2025-01-10-14-30-00-use-postgresql.md`:

```markdown
# Decision: Use PostgreSQL for database

**Date**: 2025-01-10 14:30:00
**Project**: trading-journal
**Importance**: 0.9

## Decision

Use PostgreSQL for trading journal database

## Rationale

Need ACID compliance and complex queries.

## Tags

- database
- architecture
```

### Benefits

- ✅ **Works with Cursor/Claude Desktop**: Agents can read/write files
- ✅ **Human readable**: Markdown files are easy to read
- ✅ **Version controlled**: Files can be committed to git
- ✅ **Simple**: No complex setup required
- ✅ **Searchable**: Index file enables quick queries

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

1. **Discover Skills and Tools First** (PRIMARY METHOD)
   - **Check Skills**: Review `server-management-skills/README.md` for workflows matching your task
   - **Check MCP Tools**: Review `server-management-mcp/README.md` for available tools
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

**Available Tools** (39 tools):
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
- Skills orchestrate MCP tools into workflows

**See**: 
- `server-management-mcp/README.md` for tool reference
- `apps/docs/MCP_SERVER_PLAN.md` for complete architecture and tool catalog
- `apps/docs/MCP_TOOL_DISCOVERY.md` for tool discovery guide

### Recommended Tools

1. **Server Management**: 
   - **Skills** (preferred for workflows) - `server-management-skills/README.md`
   - **MCP Tools** (preferred for operations) - `server-management-mcp/README.md`
   - SSH commands (last resort fallback)
2. **Task Tracking**: Markdown files (TASKS.md) or GitHub Issues
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

1. **Skills Catalog**: `server-management-skills/README.md`
   - Complete workflows for common tasks
   - Step-by-step guidance using MCP tools
   - Examples and error handling

2. **MCP Tools Reference**: `server-management-mcp/README.md`
   - All available tools with parameters
   - Usage examples
   - Tool categories

3. **Tool Discovery Guide**: `apps/docs/MCP_TOOL_DISCOVERY.md`
   - How to discover and use tools
   - When to create new tools
   - Tool creation workflow

4. **MCP Server Plan**: `apps/docs/MCP_SERVER_PLAN.md`
   - Complete tool catalog (implemented and planned)
   - Architecture and design
   - Implementation status

### Other Resources

- **Memory Integration**: See `AGENT_MEMORY_INTEGRATION.md` for mem-layer integration
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

