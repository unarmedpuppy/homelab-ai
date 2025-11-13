# Agent Workflow Templates

This directory contains templates for optimizing your AI agent workflow.

## Templates

### 1. Self-Review Checklist (`SELF_REVIEW_CHECKLIST.md`)
**Purpose**: Agents use this to review their own work before submitting for review.

**Usage**:
- Copy template for each task
- Fill out checklist before marking task as `[REVIEW]`
- Include link to completed checklist in task submission

**Benefits**:
- Catches 60-70% of issues before review
- Faster iteration cycles
- Higher quality submissions

---

### 2. Review Feedback Template (`REVIEW_FEEDBACK_TEMPLATE.md`)
**Purpose**: Reviewers use this to provide structured, actionable feedback.

**Usage**:
- Create one feedback doc per task: `review_feedback_T[X].[Y].md`
- Use numbered issues (Critical/Medium/Minor)
- Update status as agent addresses issues

**Benefits**:
- Clear priority for agents
- Easy to track what's fixed
- Consistent feedback format
- Faster re-review

---

### 3. Pre-Submission Check Script (`pre-submit-check.sh`)
**Purpose**: Automated checks before code reaches reviewer.

**Usage**:
```bash
chmod +x pre-submit-check.sh
./pre-submit-check.sh [backend|frontend|all]
```

**What it checks**:
- Syntax errors
- Type checking
- Linting
- Code formatting
- Common issues (console.log, hardcoded secrets, etc.)

**Benefits**:
- Catches 80% of issues automatically
- Reviewers focus on logic/architecture
- Consistent code quality

---

### 4. Task Dependency Template (`TASK_DEPENDENCY_TEMPLATE.md`)
**Purpose**: Structure tasks with explicit dependencies for parallel execution.

**Usage**:
- Use template format in your `TASKS.md`
- Mark dependencies and blockers
- Identify parallel execution opportunities

**Benefits**:
- Clear dependency graph
- Enable parallel work
- Prevent claiming tasks too early
- Better project flow

---

### 5. Batch Review Template (`BATCH_REVIEW_TEMPLATE.md`)
**Purpose**: Review multiple similar tasks together for efficiency.

**Usage**:
- Review agent identifies similar tasks in `[REVIEW]` status
- Creates batch review document
- Reviews tasks together, identifies patterns
- Creates individual review docs for each task

**Benefits**:
- More efficient reviews
- Consistent feedback across similar tasks
- Pattern recognition
- Faster overall progress

---

### 6. Feedback Resolution Tracking (`FEEDBACK_RESOLUTION_TRACKING.md`)
**Purpose**: Agents track how they address each feedback item.

**Usage**:
- Agent creates this doc when addressing feedback
- References issue numbers from review feedback
- Documents fixes with code changes
- Updates status for each issue

**Benefits**:
- Clear tracking of fixes
- Faster re-review (check specific items)
- Better communication
- Audit trail

---

## Quick Start

### For Coding Agents

1. **Before starting work**: Read task dependencies, claim task
2. **During work**: Follow coding standards, document decisions
3. **Before submission**: 
   - Run `pre-submit-check.sh`
   - Complete `SELF_REVIEW_CHECKLIST.md`
   - Mark task as `[REVIEW]`
4. **After feedback**: 
   - Create `FEEDBACK_RESOLUTION_TRACKING.md`
   - Address issues in order (Critical → Medium → Minor)
   - Update tracking doc with fixes
   - Resubmit for review

### For Review Agents

1. **Identify tasks**: Find all tasks in `[REVIEW]` status
2. **Batch similar tasks**: Group by type (API, frontend, etc.)
3. **Review batch**: Use `BATCH_REVIEW_TEMPLATE.md` for overview
4. **Individual reviews**: Create `review_feedback_T[X].[Y].md` for each task
5. **Track resolution**: Check `FEEDBACK_RESOLUTION_TRACKING.md` on re-review

---

## Integration with Workflow

### Standard Workflow with Templates

```
1. Planning Phase
   → Create tasks with dependencies (TASK_DEPENDENCY_TEMPLATE)

2. Agent Claims Task
   → Check dependencies
   → Start work

3. Agent Completes Task
   → Run pre-submit-check.sh
   → Complete SELF_REVIEW_CHECKLIST.md
   → Mark [REVIEW]

4. Review Agent Reviews
   → Batch similar tasks (BATCH_REVIEW_TEMPLATE)
   → Create review_feedback_T[X].[Y].md (REVIEW_FEEDBACK_TEMPLATE)

5. Agent Addresses Feedback
   → Create FEEDBACK_RESOLUTION_TRACKING.md
   → Fix issues, update tracking
   → Resubmit

6. Re-Review
   → Check FEEDBACK_RESOLUTION_TRACKING.md
   → Verify fixes
   → Approve or request more changes
```

---

## Customization

All templates can be customized for your project:

1. **Add project-specific checks** to `pre-submit-check.sh`
2. **Add project-specific criteria** to `SELF_REVIEW_CHECKLIST.md`
3. **Add project-specific review categories** to `REVIEW_FEEDBACK_TEMPLATE.md`
4. **Adjust dependency format** in `TASK_DEPENDENCY_TEMPLATE.md`

---

## Best Practices

1. **Use templates consistently**: Don't skip steps
2. **Update templates**: Improve based on learnings
3. **Track metrics**: Measure effectiveness
4. **Automate where possible**: Scripts > manual checks
5. **Document patterns**: Update templates with common issues

---

## Support

For questions or improvements to these templates, see:
- `AGENT_WORKFLOW.md` - Overall workflow documentation
- `agents/memory/README.md` - Memory system (SQLite-based)

---

**Last Updated**: `[DATE]`  
**Maintained By**: AI Agent Workflow Team

