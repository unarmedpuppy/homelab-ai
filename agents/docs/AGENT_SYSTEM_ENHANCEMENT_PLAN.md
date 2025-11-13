# Agent System Enhancement Plan

**Based on Claude Code Best Practices from 6-Month Production Experience**

**Date**: 2025-01-13  
**Source**: Analysis of production Claude Code workflow (300k LOC rewrite)  
**Purpose**: Extract actionable improvements for our agent system

---

## Executive Summary

After analyzing a detailed post from an experienced Claude Code user who successfully rewrote 300k LOC in 6 months, we've identified **10 key enhancement opportunities** that could significantly improve our agent system's effectiveness, consistency, and adherence to instructions.

**Key Finding**: The most critical gap is **skill auto-activation** - skills often sit unused unless explicitly forced to activate via hooks or reminders.

---

## Current State Analysis

### What We Have ✅

- ✅ Skills library with reusable workflows
- ✅ Task coordination system (central registry)
- ✅ Memory system for decisions/patterns
- ✅ Agent monitoring (observability)
- ✅ Agent communication protocol
- ✅ Agent lifecycle management
- ✅ Pattern learning and auto-skill creation
- ✅ Comprehensive documentation

### What We're Missing ❌

- ❌ **Skill auto-activation system** - Skills may not be used unless explicitly referenced
- ❌ **Context preservation system** - No structured way to prevent "losing the plot" during long sessions
- ❌ **Automated quality checks** - No hooks to catch errors/build failures immediately
- ❌ **Progressive skill disclosure** - Skills may be too large (should be <500 lines with resources)
- ❌ **Self-review workflows** - No systematic code review by agents
- ❌ **Real-time debugging tools** - No PM2/log access for backend debugging
- ❌ **Prompt injection system** - No pre-prompt hooks to remind agents of relevant skills

---

## Enhancement Opportunities

### 1. Skill Auto-Activation System ⭐⭐⭐ CRITICAL

**Problem**: Skills often sit unused. Agents may not check skills even when working on relevant files/topics.

**Solution**: Implement a pre-prompt reminder system that analyzes context and injects skill reminders.

**Implementation**:
- Create a pre-prompt analysis system (could be MCP tool or prompt enhancement)
- Analyze current file paths, prompt keywords, and intent patterns
- Inject formatted skill reminders before agent sees the prompt
- Reference relevant skills explicitly in context

**Example**:
```
🎯 SKILL ACTIVATION CHECK
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Working on backend code? Check: backend-dev-guidelines skill
Working on deployment? Check: standard-deployment skill
Working on subdomain setup? Check: add-subdomain skill
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

**Files Needed**:
- `agents/docs/SKILL_AUTO_ACTIVATION.md` - Guide for agents
- `agents/apps/agent-mcp/tools/skill_activation.py` - MCP tool for skill suggestions
- Update `AGENT_PROMPT.md` to include auto-activation instructions

**Effort**: Medium (2-3 days)  
**Impact**: High (ensures skills are actually used)

---

### 2. Context Preservation System (Dev Docs) ⭐⭐⭐ CRITICAL

**Problem**: Agents can "lose the plot" during long sessions, especially after auto-compaction. No structured way to preserve context across sessions.

**Solution**: Implement a dev docs system similar to their approach - structured task documentation that persists across sessions.

**Implementation**:
- Create `agents/active/{agent-id}/dev-docs/` directory structure
- Three core files for each major task:
  - `{task-name}-plan.md` - The accepted plan
  - `{task-name}-context.md` - Key files, decisions, next steps
  - `{task-name}-tasks.md` - Checklist of work with status
- MCP tools to create/update these files
- Agents instructed to read these files at session start

**Workflow**:
1. Agent creates plan (or human approves plan)
2. Agent runs `/create-dev-docs` (or MCP tool) to generate files
3. Agent references these files throughout work
4. Before compaction, agent runs `/update-dev-docs` to save context
5. In new session, agent reads dev-docs before continuing

**Files Needed**:
- `agents/docs/DEV_DOCS_SYSTEM.md` - Guide for agents
- `agents/apps/agent-mcp/tools/dev_docs.py` - MCP tools for dev docs
- Update `AGENT_PROMPT.md` with dev docs workflow
- Update `AGENT_WORKFLOW.md` with dev docs integration

**Effort**: Medium (2-3 days)  
**Impact**: High (prevents context loss, maintains focus)

---

### 3. Automated Quality Checks (Hooks/Post-Edit) ⭐⭐ HIGH

**Problem**: Agents may leave TypeScript errors, missing error handling, or formatting issues without catching them.

**Solution**: Implement post-edit quality checks that run automatically after agent actions.

**Implementation Options**:

**Option A: MCP Tool Wrapper** (Recommended)
- Create `check_code_quality()` MCP tool
- Agents instructed to call this after making edits
- Tool runs: build checks, linting, error detection
- Returns issues for agent to fix

**Option B: Prompt Reminders** (Simpler)
- Add to `AGENT_PROMPT.md`: "After making edits, always run build/lint checks"
- Create reminder checklist in prompt
- Less automated but easier to implement

**Option C: External Hook System** (Advanced)
- If we can hook into Cursor/Claude Desktop events
- Run checks automatically after file edits
- Most powerful but requires hook infrastructure

**What to Check**:
- TypeScript/build errors
- Missing error handling (try-catch, async operations)
- Code formatting (Prettier)
- Security patterns (input validation, SQL injection)

**Files Needed**:
- `agents/apps/agent-mcp/tools/quality_checks.py` - Quality check tools
- Update `AGENT_PROMPT.md` with quality check workflow
- Create quality check reminders in prompt

**Effort**: Medium (2-3 days)  
**Impact**: High (catches errors early, ensures quality)

---

### 4. Progressive Skill Disclosure ⭐ MEDIUM

**Problem**: Skills may be too large, loading unnecessary content and wasting tokens.

**Solution**: Restructure skills to follow Anthropic's best practices - main file <500 lines, use resource files for details.

**Implementation**:
- Review all skills in `agents/skills/`
- Split large skills into:
  - Main SKILL.md (<500 lines) - Core patterns, quick reference
  - Resource files - Detailed examples, edge cases, advanced patterns
- Update skill structure documentation
- Agents load main file first, pull in resources only when needed

**Example Structure**:
```
standard-deployment/
├── SKILL.md (300 lines - core workflow)
├── resources/
│   ├── docker-compose-patterns.md
│   ├── traefik-configuration.md
│   ├── error-handling.md
│   └── rollback-procedures.md
```

**Files Needed**:
- Review and restructure existing skills
- Update `agents/skills/README.md` with structure guidelines
- Create skill template with progressive disclosure

**Effort**: Medium (3-4 days to restructure all skills)  
**Impact**: Medium (token efficiency, better organization)

---

### 5. Self-Review Workflows ⭐⭐ HIGH

**Problem**: Agents don't systematically review their own code, leading to missed errors, inconsistencies, and security issues.

**Solution**: Create systematic self-review workflows and specialized review agents.

**Implementation**:
- Create `code-review-agent` skill/template
- MCP tool: `request_code_review()` - Triggers review process
- Review checklist covering:
  - Code quality and consistency
  - Error handling
  - Security patterns
  - Best practices adherence
  - Integration issues
- Agents instructed to request review before marking tasks complete

**Workflow**:
1. Agent completes implementation
2. Agent calls `request_code_review()` or uses review agent
3. Review agent analyzes code and provides feedback
4. Original agent addresses issues
5. Task marked complete

**Files Needed**:
- `agents/docs/CODE_REVIEW_WORKFLOW.md` - Review process
- `agents/apps/agent-mcp/tools/code_review.py` - Review tools
- Review agent template/prompt
- Update `AGENT_WORKFLOW.md` with review step

**Effort**: Medium (2-3 days)  
**Impact**: High (catches issues early, improves quality)

---

### 6. Real-Time Debugging Tools ⭐ MEDIUM

**Problem**: Agents can't easily access logs or debug running services. Manual log copying is inefficient.

**Solution**: Integrate PM2 or similar process management, expose log access via MCP tools.

**Implementation**:
- If using PM2: Create MCP tools for PM2 operations
- If using Docker: Enhance existing Docker log tools
- Create `get_service_logs()` MCP tool that:
  - Reads recent logs from services
  - Filters by error level
  - Returns formatted log output
- Create `restart_service()` MCP tool
- Create `monitor_service()` MCP tool for real-time monitoring

**MCP Tools Needed**:
- `get_service_logs(service_name, lines=200, level="error")`
- `restart_service(service_name)`
- `monitor_service_status(service_name)`
- `get_service_metrics(service_name)`

**Files Needed**:
- `agents/apps/agent-mcp/tools/service_debugging.py` - New tool file
- Update `agents/apps/agent-mcp/README.md`
- Update `AGENT_PROMPT.md` with debugging workflow

**Effort**: Low-Medium (1-2 days)  
**Impact**: Medium (improves debugging efficiency)

---

### 7. Prompt Enhancement System ⭐⭐ HIGH

**Problem**: Agents may not follow instructions consistently. Need better prompt structure and reminders.

**Solution**: Enhance agent prompts with:
- Explicit skill activation reminders
- Quality check reminders
- Context preservation instructions
- Better structure and emphasis

**Implementation**:
- Add "Skill Activation" section to `AGENT_PROMPT.md`
- Add "Quality Checks" section with explicit checklist
- Add "Context Preservation" section with dev docs workflow
- Use formatting (boxes, emojis) to emphasize critical sections
- Add examples of good vs bad prompts

**Key Additions**:
```markdown
## 🎯 CRITICAL: Skill Activation

Before starting any work, ALWAYS check for relevant skills:
1. Analyze your current task/file context
2. Check `agents/skills/README.md` for relevant skills
3. Load and review relevant skills BEFORE implementing
4. Reference skill patterns throughout implementation

## ✅ CRITICAL: Quality Checks

After EVERY edit, you MUST:
1. Run build/lint checks (if applicable)
2. Verify error handling is present
3. Check for security issues
4. Ensure code follows project patterns
```

**Files Needed**:
- Update `AGENT_PROMPT.md` with enhanced sections
- Update `SERVER_AGENT_PROMPT.md` similarly
- Create prompt best practices guide

**Effort**: Low (1 day)  
**Impact**: High (better instruction adherence)

---

### 8. Scripts Attached to Skills ⭐ MEDIUM

**Problem**: Agents recreate utility scripts instead of using existing ones.

**Solution**: Attach utility scripts to relevant skills, document them clearly.

**Implementation**:
- Review existing scripts in `agents/scripts/`
- Attach relevant scripts to skills (document in skill files)
- Create script catalog/reference
- Update skills to reference scripts explicitly

**Example**:
```markdown
## Testing Authenticated Routes

Use the provided test script:
```bash
./agents/scripts/test-auth-route.sh <endpoint>
```

This script handles:
- Authentication token retrieval
- Request signing
- Cookie header creation
```

**Files Needed**:
- Update skills to reference scripts
- Create `agents/scripts/README.md` - Script catalog
- Document script usage in relevant skills

**Effort**: Low (1 day)  
**Impact**: Medium (prevents script duplication)

---

### 9. Planning Mode Integration ⭐ MEDIUM

**Problem**: Agents may jump into implementation without proper planning, leading to poor results.

**Solution**: Emphasize planning mode usage and create planning workflows.

**Implementation**:
- Update `AGENT_PROMPT.md` to emphasize planning
- Create planning workflow in `AGENT_WORKFLOW.md`
- Create planning agent template
- Integrate planning with dev docs system

**Workflow**:
1. Agent enters planning mode (or uses planning agent)
2. Agent creates comprehensive plan
3. Human reviews plan
4. Agent creates dev docs from approved plan
5. Agent implements following dev docs

**Files Needed**:
- Update `AGENT_WORKFLOW.md` with planning emphasis
- Create planning agent template
- Update `AGENT_PROMPT.md` with planning instructions

**Effort**: Low (1 day)  
**Impact**: Medium (better planning, fewer mistakes)

---

### 10. Slash Commands / Quick Actions ⭐ LOW

**Problem**: Repetitive workflows require typing long prompts repeatedly.

**Solution**: Document common workflows as "quick commands" or create MCP tools for them.

**Implementation**:
- Create `QUICK_COMMANDS.md` - Common workflow shortcuts
- Document prompt templates for common tasks
- Consider MCP tools for repetitive workflows

**Example Quick Commands**:
```markdown
## Quick Commands

### Create Dev Docs
"Create dev docs for task [task-name] from the approved plan"

### Update Dev Docs
"Update dev docs with current progress and next steps"

### Request Code Review
"Request code review for changes in [files]"
```

**Files Needed**:
- `agents/docs/QUICK_COMMANDS.md` - Command reference
- Update `QUICK_START.md` with quick commands

**Effort**: Low (1 day)  
**Impact**: Low-Medium (convenience, time savings)

---

## Prioritized Implementation Plan

### Phase 1: Critical Foundations (Week 1)

**Priority**: Highest impact, foundational improvements

1. **Skill Auto-Activation System** (2-3 days)
   - Create skill activation MCP tool
   - Update agent prompts with activation reminders
   - Create skill activation guide

2. **Context Preservation System** (2-3 days)
   - Create dev docs MCP tools
   - Update agent workflow with dev docs
   - Create dev docs guide

3. **Prompt Enhancement** (1 day)
   - Enhance `AGENT_PROMPT.md` with critical sections
   - Add skill activation reminders
   - Add quality check reminders

**Total Effort**: 5-7 days  
**Impact**: Very High

---

### Phase 2: Quality & Consistency (Week 2)

**Priority**: High impact, improves output quality

4. **Automated Quality Checks** (2-3 days)
   - Create quality check MCP tools
   - Add quality check workflow to prompts
   - Create quality check guide

5. **Self-Review Workflows** (2-3 days)
   - Create code review MCP tools
   - Create review agent template
   - Integrate review into workflow

**Total Effort**: 4-6 days  
**Impact**: High

---

### Phase 3: Optimization & Polish (Week 3)

**Priority**: Medium impact, efficiency improvements

6. **Progressive Skill Disclosure** (3-4 days)
   - Review and restructure skills
   - Create skill template
   - Update skill guidelines

7. **Real-Time Debugging Tools** (1-2 days)
   - Create service debugging MCP tools
   - Update agent prompts

8. **Scripts Attached to Skills** (1 day)
   - Document scripts in skills
   - Create script catalog

**Total Effort**: 5-7 days  
**Impact**: Medium

---

### Phase 4: Convenience Features (Week 4)

**Priority**: Low impact, nice-to-have

9. **Planning Mode Integration** (1 day)
   - Update workflows with planning emphasis
   - Create planning templates

10. **Slash Commands / Quick Actions** (1 day)
    - Create quick commands guide
    - Document common workflows

**Total Effort**: 2 days  
**Impact**: Low-Medium

---

## Key Principles from Analysis

### 1. Force Skill Activation
**Learning**: Skills won't be used unless explicitly activated. Need reminders/injections.

**Our Approach**: 
- Pre-prompt skill reminders
- Explicit skill activation instructions
- MCP tools to suggest relevant skills

### 2. Preserve Context Across Sessions
**Learning**: Agents lose track during long sessions. Structured docs prevent this.

**Our Approach**:
- Dev docs system (plan, context, tasks)
- MCP tools to create/update dev docs
- Agents read dev docs at session start

### 3. Catch Errors Immediately
**Learning**: Agents leave errors behind. Automated checks catch them early.

**Our Approach**:
- Quality check MCP tools
- Post-edit reminders
- Build/lint integration

### 4. Review Your Own Work
**Learning**: Self-review catches many issues before they become problems.

**Our Approach**:
- Code review workflows
- Review agent templates
- Review checklists

### 5. Progressive Disclosure
**Learning**: Large skills waste tokens. Split into main + resources.

**Our Approach**:
- Restructure skills (<500 lines main)
- Use resource files for details
- Load resources only when needed

---

## Comparison: Their System vs Ours

| Feature | Their System | Our System | Gap |
|---------|-------------|------------|-----|
| **Skills** | Auto-activation via hooks | Manual reference | ⚠️ Need auto-activation |
| **Context Preservation** | Dev docs system | Task coordination only | ⚠️ Need dev docs |
| **Quality Checks** | Automated hooks | Manual | ⚠️ Need automation |
| **Self-Review** | Specialized agents | Not systematic | ⚠️ Need workflow |
| **Skill Structure** | <500 lines + resources | May be too large | ⚠️ Need review |
| **Debugging** | PM2 + log access | Docker tools exist | ✅ Similar |
| **Planning** | Planning mode emphasis | Mentioned but not emphasized | ⚠️ Need emphasis |
| **Observability** | Not mentioned | Full monitoring system | ✅ We're ahead |
| **Task Coordination** | Dev docs only | Central registry | ✅ We're ahead |
| **Memory System** | Memory MCP | Full memory system | ✅ We're ahead |
| **Communication** | Not mentioned | Full protocol | ✅ We're ahead |

---

## Implementation Recommendations

### Start with Phase 1 (Critical Foundations)

These three improvements will have the biggest impact:

1. **Skill Auto-Activation** - Ensures skills are actually used
2. **Context Preservation** - Prevents agents from losing track
3. **Prompt Enhancement** - Better instruction adherence

### Quick Wins (Can Do Immediately)

1. **Update `AGENT_PROMPT.md`** - Add skill activation and quality check reminders
2. **Create dev docs MCP tools** - Simple file creation/update tools
3. **Create quality check MCP tool** - Basic build/lint checking

### Longer-Term Improvements

1. **Restructure skills** - Progressive disclosure
2. **Create review workflows** - Systematic code review
3. **Enhance debugging tools** - Better log access

---

## Success Metrics

### Before Enhancements
- ❓ Skills may not be used consistently
- ❓ Agents may lose context during long sessions
- ❓ Errors may be left behind
- ❓ No systematic self-review

### After Enhancements
- ✅ Skills auto-activate when relevant
- ✅ Context preserved across sessions via dev docs
- ✅ Errors caught immediately via quality checks
- ✅ Systematic self-review before completion
- ✅ Better instruction adherence via enhanced prompts

---

## Next Steps

1. **Review this plan** - Validate priorities and approach
2. **Start Phase 1** - Implement critical foundations
3. **Test and iterate** - Refine based on results
4. **Document learnings** - Update guides as we learn

---

## References

- **Source Post**: Reddit post from experienced Claude Code user (6 months, 300k LOC)
- **Key Learnings**: Skill auto-activation, dev docs, quality checks, self-review
- **Our Current State**: Strong foundation, missing some automation/activation systems

---

**Last Updated**: 2025-01-13  
**Status**: Proposal - Ready for Review  
**Priority**: High - Critical improvements identified

