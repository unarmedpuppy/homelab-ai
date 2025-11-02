# Agent Coordination System

**Purpose**: Coordinate multiple Cursor agents working on the trading bot project through file-based communication.

**Last Updated**: December 19, 2024

---

## 🔄 How Coordination Works

### My Capabilities

**What I CAN do:**
- ✅ Read files that other agents create/update (when explicitly asked)
- ✅ Update shared documentation files (`PROJECT_TODO.md`, checklists)
- ✅ Review code changes in the repository
- ✅ Create coordination files that other agents can read
- ✅ Provide guidance through documentation updates

**What I CANNOT do:**
- ❌ Direct real-time communication with other agents
- ❌ Approve actions as they happen automatically
- ❌ Poll files continuously or monitor changes in real-time
- ❌ Maintain persistent state between sessions
- ❌ See what other agents are doing unless they write to files AND I'm asked to check

### ⚠️ Important Limitation: No Persistent Polling

**I cannot stay in a polling state** waiting for files to change. Each conversation/session is independent, and I don't have background processes or continuous monitoring capabilities.

**How it actually works:**
- **You** (or another agent/user) need to **explicitly ask me** to check for updates
- I will then read status files, review code, and provide feedback
- I can create scripts you can run to check for changes
- The file-based system still works - it just requires explicit check-ins

### Practical Workflow

**Option 1: Manual Check-ins**
- Periodically ask me: "Check for agent updates and review pending work"
- I'll read status files and PROJECT_TODO.md
- I'll provide feedback and next steps

**Option 2: Script-Based Monitoring** (I can create)
- Script that checks for new/modified agent status files
- Script that checks for review requests
- You run the script periodically, then ask me to review findings

**Option 3: Git-Based Triggers**
- Agents commit changes with specific commit messages
- You can ask me to review git log/changes since last review
- I'll check what's changed and provide guidance

### File-Based Coordination

Since I cannot directly communicate with other agents, we use **shared files** as the coordination mechanism:

1. **Shared Status File**: `docs/PROJECT_TODO.md` - Master task tracker
2. **Agent Status Files**: Agents create status files in `docs/agent_status/`
3. **Review Queue**: File-based review and approval system

---

## 📋 Coordination Workflow

### For Agents Working on Tasks

1. **Check PROJECT_TODO.md** for available tasks
2. **Claim a task** by updating `PROJECT_TODO.md`:
   - Update status to `🔄 In Progress`
   - Add entry to "Active Tasks" table
   - Include your agent ID and documentation links
3. **Create status file** in `docs/agent_status/[AGENT_ID]_[TASK_NAME].md`
4. **Update status regularly** as you make progress
5. **Request review** by updating status file when ready for review
6. **Complete task** by updating PROJECT_TODO.md to `✅ Complete`

### For Me (Coordinator)

1. **Monitor PROJECT_TODO.md** for task claims and status updates
2. **Read agent status files** to see progress
3. **Review completed work** by examining:
   - Code changes
   - Documentation updates
   - Test results
4. **Update PROJECT_TODO.md** with feedback/approval
5. **Prompt next actions** through documentation updates

---

## 📁 File Structure for Coordination

```
docs/
├── PROJECT_TODO.md                    # Master task tracker (shared)
├── AGENT_COORDINATION.md              # This file
├── agent_status/                      # Agent status files
│   ├── agent_001_metrics_pipeline.md
│   ├── agent_002_cash_account_rules.md
│   └── ...
├── reviews/                           # Review queue
│   ├── pending/                       # Pending reviews
│   └── approved/                      # Approved work
└── [feature docs]/                    # Implementation docs
```

---

## 🎯 Agent Status File Template

When claiming a task, create: `docs/agent_status/[AGENT_ID]_[TASK_NAME].md`

```markdown
# Agent Status: [Task Name]

**Agent ID**: [Your ID]
**Task**: [Task name from PROJECT_TODO.md]
**Status**: 🔄 In Progress
**Start Date**: [Date]
**Estimated Completion**: [Date]

## Progress Updates

### [Date] - Initial Claim
- Task claimed
- Documentation reviewed
- Starting implementation

### [Date] - [Milestone]
- [What you completed]
- [What you learned]
- [Next steps]

## Current Status

**Phase**: [Planning/Implementation/Testing/Review]

**Blockers**: 
- None / [List any blockers]

**Questions**: 
- None / [List any questions]

## Documentation Created

- `docs/[FEATURE]_IMPLEMENTATION_PLAN.md`
- `docs/[FEATURE]_PROGRESS.md` (optional)
- `docs/[FEATURE]_REVIEW_CHECKLIST.md` (when ready for review)

## Code Changes

**Files Modified**:
- `path/to/file.py` - [Brief description]

**Files Created**:
- `path/to/new_file.py` - [Brief description]

## Review Request

**Status**: ⏳ Not Ready / 🔍 Ready for Review

**Review Needed For**:
- [ ] Code review
- [ ] Architecture review
- [ ] Documentation review
- [ ] Testing review

**Notes for Reviewer**:
[Any specific areas you want reviewed or questions]

---

**Last Updated**: [Date]
```

---

## 🔍 Review & Approval Process

### Step 1: Agent Requests Review

1. Update agent status file:
   - Set "Review Request" status to `🔍 Ready for Review`
   - Check relevant review checkboxes
   - Add notes for reviewer

2. Update PROJECT_TODO.md:
   - Update task status to `🔍 Review`
   - Add note in "Active Tasks" that review is requested

### Step 2: Coordinator Review

I will:
1. Read the agent's status file
2. Review code changes
3. Check documentation
4. Run tests if applicable
5. Update PROJECT_TODO.md with review feedback:
   - ✅ Approved - Move to complete
   - 🔄 Needs Changes - Add feedback
   - ❌ Blocked - Explain blocker

### Step 3: Agent Addresses Feedback

If changes needed:
1. Agent reads feedback in PROJECT_TODO.md
2. Makes necessary changes
3. Updates status file
4. Requests review again

If approved:
1. Agent updates PROJECT_TODO.md to `✅ Complete`
2. Moves entry to "Recently Completed"
3. Consolidates documentation per workflow

---

## 🚦 Status Indicators

Tasks can be in these states:

- ⏳ **Planned** - Not yet started
- 🔄 **In Progress** - Agent actively working (claimed in PROJECT_TODO.md)
- 🔍 **Review** - Ready for review or under review
- ✅ **Complete** - Approved and completed
- ❌ **Blocked** - Cannot proceed (dependency/issue)
- ⏸️ **Paused** - Temporarily paused

---

## 📝 Instructions for Agents

### When Starting Work

1. **Read PROJECT_TODO.md** - Find an unclaimed task
2. **Check Dependencies** - Ensure prerequisites are met
3. **Claim the Task**:
   ```
   - Update status: ⏳ Planned → 🔄 In Progress
   - Add to "Active Tasks" table with your info
   - Create agent status file
   ```
4. **Start Working** - Follow workflow in `docs/AGENT_START_PROMPT.md`

### During Work

1. **Update Status File** - Regular progress updates (daily or per milestone)
2. **Update PROJECT_TODO.md** - When significant progress made
3. **Create Documentation** - As specified in workflow guide

### When Ready for Review

1. **Update Status File** - Set review request
2. **Update PROJECT_TODO.md** - Status to `🔍 Review`
3. **Wait for Review** - Coordinator will review and provide feedback

### After Approval

1. **Finalize Documentation** - Consolidate per workflow
2. **Update PROJECT_TODO.md** - Mark as `✅ Complete`
3. **Archive Work Files** - Move to archive per workflow

---

## 🔔 How Coordination Works in Practice

### For You (User/Coordinator)

**I cannot poll continuously**, so you need to explicitly ask me to check status. Here's how:

**Regular Check-ins**:
```
Ask me: "Check agent status and review pending work"
```

I will:
1. Read all agent status files in `docs/agent_status/`
2. Check for review requests
3. Review code changes
4. Update PROJECT_TODO.md with feedback
5. Create review files if needed

**Quick Status Check** (without full review):
```bash
# Run the status check script
./scripts/check_agent_status.sh

# Or ask me:
# "Show me current agent status"
```

**Review Specific Task**:
```
Ask me: "Review the metrics pipeline task and provide feedback"
```

### For Agents

**Agents should**:
- Check PROJECT_TODO.md regularly for coordinator updates
- Read review files in `docs/reviews/pending/` after requesting review
- Follow any instructions added to their task description
- Update status files regularly so coordinator can see progress when checking

**After requesting review**:
- Wait for user to ask coordinator to review
- Check PROJECT_TODO.md for feedback
- Check `docs/reviews/pending/` for review feedback
- Address feedback and update status

### Check-in Frequency Recommendation

**Suggested schedule**:
- **Daily**: Check for agent updates
- **On request**: When agent requests review
- **Before starting new work**: Check what's available

**Command to trigger review**:
```bash
# Quick check
./scripts/check_agent_status.sh

# Then ask coordinator:
# "Check agent status and review pending work"
```

---

## 📊 Example: Task Claim

An agent claims "Metrics Pipeline" task:

**In PROJECT_TODO.md**:
```markdown
| Feature/Task | Status | Agent | Start Date | Documentation | Estimated Completion |
|--------------|--------|-------|------------|---------------|---------------------|
| Metrics Pipeline | 🔄 In Progress | Agent-001 | 2024-12-19 | `docs/METRICS_IMPLEMENTATION_PLAN.md` | 2024-12-26 |
```

**Agent creates**: `docs/agent_status/Agent-001_Metrics_Pipeline.md`

**I can then**:
- Read the agent status file
- Review their progress
- Update PROJECT_TODO.md with guidance
- Provide feedback through documentation

---

## ⚠️ Limitations & Best Practices

### Limitations

- **No Real-Time Communication**: Coordination happens through file updates
- **No Automatic Approval**: All reviews require manual file reading
- **Sequential Updates**: Agents may need to wait for file updates

### Best Practices

1. **Update Files Regularly** - Don't wait days between updates
2. **Be Explicit** - Clearly document what you're doing and why
3. **Check PROJECT_TODO.md Daily** - Look for coordinator feedback
4. **Follow Status Indicators** - Keep status accurate
5. **Document Everything** - Help coordinator understand your work

---

## 🎯 Current Coordination Status

**Active Agents**: Check `docs/PROJECT_TODO.md` "Active Tasks" section

**Pending Reviews**: Check `docs/reviews/pending/` directory

**Approved Work**: Check `docs/PROJECT_TODO.md` "Recently Completed" section

---

**Note**: This coordination system relies on file-based communication. Agents should check PROJECT_TODO.md and their status files regularly for updates and guidance.

