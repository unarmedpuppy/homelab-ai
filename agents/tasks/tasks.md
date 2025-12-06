# Tasks

Task tracking for Home Server.

**Status**: Active development
**Last Updated**: 2024-11-27

## Task Claiming Protocol

```bash
# 1. Pull latest
git pull origin main

# 2. Check task status - only claim [AVAILABLE] tasks

# 3. Edit this file: change [AVAILABLE] → [CLAIMED by @your-id]

# 4. Commit and push within 1 minute (creates "lock")
git add agents/tasks/tasks.md
git commit -m "claim: Task X - Description"
git push origin main

# 5. Create feature branch
git checkout -b feature/task-x-description
```

## Task Status Legend

- `[AVAILABLE]` - Ready to claim
- `[CLAIMED by @id]` - Locked by an agent
- `[IN PROGRESS - X%]` - Work underway
- `[COMPLETE]` - Finished
- `[BLOCKED]` - Waiting on dependency

---

## Current Tasks

| Task | Description | Status | Priority |
|------|-------------|--------|----------|
| T1 | Consolidate metrics system (8 files → 3) | [AVAILABLE] | P0 |
| T2 | Remove backward compat duplication in strategy.py | [AVAILABLE] | P1 |
| T3 | Standardize import patterns | [AVAILABLE] | P2 |
| T4 | Add missing type hints | [AVAILABLE] | P2 |
| T5 | Standardize error handling | [AVAILABLE] | P1 |
| T6 | WebSocket data producer integration | [AVAILABLE] | P0 |
| T7 | UI WebSocket integration | [AVAILABLE] | P1 |
| T8 | WebSocket testing | [AVAILABLE] | P1 |
| T9 | IBKR integration testing | [AVAILABLE] | P0 |
| T10 | Strategy-to-execution pipeline | [AVAILABLE] | P0 |
| T11 | Sentiment provider base class | [AVAILABLE] | P1 |

### Task T1: Consolidate metrics system (8 files → 3)
**Priority**: P0
**Dependencies**: None
**Effort**: High
**Project**: trading-bot

**Objective**: Reduce metrics system from 8 files to 3 for better code quality. Biggest code quality win. See IMPLEMENTATION_ROADMAP.md

**Files to modify**:
- Metrics-related files in trading-bot

**Success Criteria**:
- [ ] Metrics system consolidated to 3 files
- [ ] All functionality preserved
- [ ] Tests pass

### Task T2: Remove backward compat duplication in strategy.py
**Priority**: P1
**Dependencies**: None
**Effort**: Medium
**Project**: trading-bot

**Objective**: Remove duplicate enums in src/core/strategy.py

**Files to modify**:
- `apps/trading-bot/src/core/strategy.py`

**Success Criteria**:
- [ ] Duplicate enums removed
- [ ] Backward compatibility maintained if needed
- [ ] Tests pass

### Task T3: Standardize import patterns
**Priority**: P2
**Dependencies**: None
**Effort**: Low
**Project**: trading-bot

**Objective**: Standardize import patterns, focus on sentiment providers

**Files to modify**:
- Sentiment provider files

**Success Criteria**:
- [ ] Consistent import patterns
- [ ] Code style guide followed

### Task T4: Add missing type hints
**Priority**: P2
**Dependencies**: None
**Effort**: Low
**Project**: trading-bot

**Objective**: Add missing type hints to range_bound.py and sentiment providers

**Files to modify**:
- `apps/trading-bot/src/.../range_bound.py`
- Sentiment provider files

**Success Criteria**:
- [ ] All type hints added
- [ ] Type checking passes

### Task T5: Standardize error handling
**Priority**: P1
**Dependencies**: None
**Effort**: Medium
**Project**: trading-bot

**Objective**: Replace broad `except Exception` with specific exception handling

**Files to modify**:
- Files with broad exception handling

**Success Criteria**:
- [ ] Specific exception types used
- [ ] Error handling consistent
- [ ] Tests pass

### Task T6: WebSocket data producer integration
**Priority**: P0
**Dependencies**: None
**Effort**: High
**Project**: trading-bot

**Objective**: Connect data to WebSocket streams

**Files to modify**:
- WebSocket producer files

**Success Criteria**:
- [ ] Data flows through WebSocket
- [ ] Integration tested

### Task T7: UI WebSocket integration
**Priority**: P1
**Dependencies**: T6
**Effort**: Medium
**Project**: trading-bot

**Objective**: Dashboard real-time updates via WebSocket

**Files to modify**:
- UI/frontend files

**Success Criteria**:
- [ ] Real-time updates working
- [ ] UI responsive

### Task T8: WebSocket testing
**Priority**: P1
**Dependencies**: T6, T7
**Effort**: Medium
**Project**: trading-bot

**Objective**: Add WebSocket tests (no WS tests currently)

**Files to modify**:
- Test files

**Success Criteria**:
- [ ] WebSocket tests added
- [ ] Test coverage adequate

### Task T9: IBKR integration testing
**Priority**: P0
**Dependencies**: None
**Effort**: High
**Project**: trading-bot

**Objective**: Paper trading validation for IBKR integration

**Files to modify**:
- IBKR integration files

**Success Criteria**:
- [ ] Paper trading validated
- [ ] Integration tested

### Task T10: Strategy-to-execution pipeline
**Priority**: P0
**Dependencies**: None
**Effort**: High
**Project**: trading-bot

**Objective**: Signal → order with safety checks

**Files to modify**:
- Strategy and execution files

**Success Criteria**:
- [ ] Pipeline working end-to-end
- [ ] Safety checks in place
- [ ] Tests pass

### Task T11: Sentiment provider base class
**Priority**: P1
**Dependencies**: None
**Effort**: Medium
**Project**: trading-bot

**Objective**: Reduce boilerplate in 13 providers

**Files to modify**:
- Sentiment provider files

**Success Criteria**:
- [ ] Base class created
- [ ] Providers refactored
- [ ] Boilerplate reduced

---

## Priority Order

**Immediate (This Session):**
1. T1 - Metrics consolidation
2. T2 - Strategy.py cleanup

**Next Session:**
3. T6 - WebSocket producers
4. T9 - IBKR testing
5. T10 - Execution pipeline

**Later:**
- T3, T4, T5 - Style cleanup
- T7, T8 - UI and tests
- T11 - Provider refactor

---

## Completed Tasks

| ID | Task | Project | Completed | Notes |
|----|------|---------|-----------|-------|
| - | Agents system cleanup | agents | 2024-11-27 | Simplified from 600MB to 272KB |

