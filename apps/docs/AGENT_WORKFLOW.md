# AI Agent Workflow - Best Practices

## Overview

This document outlines a proven workflow for managing AI agents working on software projects. This approach ensures quality, consistency, and effective collaboration between multiple AI agents.

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

2. **Agent Reads Documentation**
   - STARTUP_GUIDE.md (first!)
   - IMPLEMENTATION_PLAN.md (relevant sections)
   - Agent prompt (guidelines)
   - Task details

3. **Agent Implements**
   - Follows coding standards
   - Uses patterns from examples
   - Documents as they go
   - Tests functionality

4. **Agent Self-Reviews**
   - Completes Pre-Submission Checklist
   - Runs self-review questions
   - Fixes obvious issues

5. **Agent Submits for Review**
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

**Solution**: Use a graph-based memory system like [mem-layer](https://github.com/0xSero/mem-layer) to:
- Track decisions across sessions
- Share knowledge between agents
- Recognize patterns and learn from mistakes
- Maintain context continuity
- Build knowledge graphs of project relationships

**See**: `AGENT_MEMORY_INTEGRATION.md` for complete integration guide.

### Quick Integration

1. **Install mem-layer**: `pip install mem-layer`
2. **Initialize**: `mem-layer init --scope [project]`
3. **Document decisions**: Agents create decision nodes
4. **Query context**: Agents load context at start
5. **Track patterns**: Reviewers document common issues

### Benefits

- ✅ Persistent memory across sessions
- ✅ Decision tracking and recall
- ✅ Agent-to-agent communication
- ✅ Pattern recognition
- ✅ Reduced repetition

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

1. **Read First**
   - STARTUP_GUIDE.md (essential)
   - IMPLEMENTATION_PLAN.md (context)
   - Agent prompt (guidelines)

2. **Follow Standards**
   - Coding standards
   - Patterns and examples
   - Documentation requirements

3. **Self-Review**
   - Complete checklists
   - Test thoroughly
   - Fix obvious issues

4. **Communicate**
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

### Recommended Tools

1. **Task Tracking**: Markdown files (TASKS.md) or GitHub Issues
2. **Code Review**: GitHub PRs or inline comments
3. **Automated Checks**: GitHub Actions, pre-commit hooks
4. **Documentation**: Markdown files, auto-generated API docs

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

- **Memory Integration**: See `AGENT_MEMORY_INTEGRATION.md` for mem-layer integration
- **Server Setup**: See `SERVER_AGENT_PROMPT.md` for server-specific context

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

