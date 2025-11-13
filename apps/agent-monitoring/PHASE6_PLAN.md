# Phase 6: Complete Monitoring Integration Plan

## Current Status

✅ **Phase 1**: Database initialization - COMPLETE
✅ **Phase 2**: Automatic logging decorator - COMPLETE  
✅ **Phase 3**: Docker tools integration - COMPLETE (8 tools)
⏳ **Phase 4**: Remaining tools integration - IN PROGRESS (~88 tools remaining)
⏳ **Phase 5**: Agent ID context handling - PENDING
⏳ **Phase 6**: Testing and verification - PENDING

## Phase 4: Apply Decorator to All Tools

### Priority Order

**High Priority** (Most commonly used):
1. ✅ `docker.py` - 8 tools (DONE)
2. ⏳ `git.py` - 4 tools (deployment workflow)
3. ⏳ `monitoring.py` - 5 tools (system health)
4. ⏳ `memory.py` - 9 tools (memory operations - may already log)
5. ⏳ `task_coordination.py` - 6 tools (task management)

**Medium Priority**:
6. ⏳ `media_download.py` - 11 tools (media operations)
7. ⏳ `networking.py` - 4 tools (network operations)
8. ⏳ `system.py` - 3 tools (system utilities)
9. ⏳ `troubleshooting.py` - 3 tools (diagnostics)
10. ⏳ `service_debugging.py` - 4 tools (service debugging)

**Lower Priority** (Specialized):
11. ⏳ `agent_management.py` - 6 tools
12. ⏳ `skill_management.py` - 5 tools
13. ⏳ `communication.py` - 5 tools
14. ⏳ `skill_activation.py` - 2 tools
15. ⏳ `dev_docs.py` - 4 tools
16. ⏳ `quality_checks.py` - 2 tools
17. ⏳ `code_review.py` - 2 tools
18. ⏳ `agent_documentation.py` - 5 tools

**Skip** (Already have logging):
- ⏳ `activity_monitoring.py` - 4 tools (these tools ARE the logging system)

### Implementation Steps

For each tool file:
1. Add import: `from tools.logging_decorator import with_automatic_logging`
2. Add decorator before each `@server.tool()`:
   ```python
   @server.tool()
   @with_automatic_logging()
   async def tool_name(...):
   ```
3. Test one tool from the file
4. Commit changes

## Phase 5: Agent ID Context Handling

### Current Issue
- Tools default to `"agent-001"` if no agent_id in parameters
- Most tools don't have agent_id as a parameter
- Need better way to identify the calling agent

### Solutions to Consider

**Option A: MCP Request Context** (Preferred if available)
- Check if MCP server provides request context/metadata
- Extract agent_id from MCP request headers/metadata
- Requires MCP protocol investigation

**Option B: Environment Variable**
- Set agent_id in environment when agent starts
- Tools read from environment
- Simple but requires agent setup

**Option C: Agent ID Parameter** (Current)
- Add optional `agent_id` parameter to all tools
- Agents pass their ID when calling tools
- Works but requires agent awareness

**Option D: Session-Based**
- Agents call `start_agent_session(agent_id)` first
- Store agent_id in thread-local or context
- Tools read from context
- Most elegant but requires context management

### Recommendation
Start with **Option C** (add optional agent_id parameter) as it's simplest and works immediately. Then investigate **Option A** for a better long-term solution.

## Phase 6: Testing and Verification

### Test Plan

1. **Unit Tests**
   - Test decorator with various tool signatures
   - Test agent_id extraction logic
   - Test parameter redaction
   - Test error handling

2. **Integration Tests**
   - Call tools via MCP
   - Verify actions appear in dashboard
   - Check parameter logging
   - Verify duration tracking
   - Test error logging

3. **Dashboard Verification**
   - Check actions appear in real-time
   - Verify tool usage statistics
   - Check agent status updates
   - Verify filtering works

4. **Performance Tests**
   - Measure logging overhead
   - Check database write performance
   - Verify no tool slowdown

### Success Criteria

- ✅ All tool calls are logged
- ✅ Agent IDs are correctly identified
- ✅ Parameters are logged (sensitive data redacted)
- ✅ Duration is tracked
- ✅ Errors are logged
- ✅ Dashboard shows all activity
- ✅ No performance degradation

## Quick Wins

1. **Apply to high-priority tools first** (git, monitoring, memory, task_coordination)
2. **Test with one agent session** to verify end-to-end
3. **Document agent_id usage** in AGENT_PROMPT.md
4. **Create helper script** to batch-apply decorator (optional)

## Estimated Effort

- **Phase 4**: ~2-3 hours (applying decorator to ~88 tools)
- **Phase 5**: ~1-2 hours (agent_id context solution)
- **Phase 6**: ~1-2 hours (testing and verification)

**Total**: ~4-7 hours to complete all phases

