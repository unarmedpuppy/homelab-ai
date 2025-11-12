# Task Dependency Template

This template shows how to structure tasks with explicit dependencies in your `TASKS.md` file.

## Task Format with Dependencies

```markdown
### T[X].[Y]: [Task Name]
**Status**: `[PENDING|CLAIMED|IN PROGRESS|REVIEW|COMPLETED|BLOCKED]`  
**Priority**: `[High|Medium|Low]`  
**Estimated Time**: `[X hours]`  
**Claimed By**: `[Agent Name]` (if claimed)

**Dependencies**:
- `T[A].[B]` - Must be `[COMPLETED]` (required)
- `T[C].[D]` - Must be `[COMPLETED]` (required)
- `T[E].[F]` - Should be `[COMPLETED]` (recommended, not blocking)

**Blocks**:
- `T[G].[H]` - This task blocks these tasks

**Description**: 
[Detailed description of what needs to be done]

**Acceptance Criteria**:
- [ ] Criterion 1
- [ ] Criterion 2
- [ ] Criterion 3

**Files to Create/Modify**:
- `path/to/file1.py`
- `path/to/file2.tsx`

**Completion Summary**: `[Summary when completed]`
```

## Example: Task with Dependencies

```markdown
### T1.7: Trade CRUD API Endpoints
**Status**: `[PENDING]`  
**Priority**: `High`  
**Estimated Time**: `4 hours`  
**Claimed By**: `[Not claimed]`

**Dependencies**:
- `T1.5` - SQLAlchemy Models - Must be `[COMPLETED]` (required)
- `T1.6` - Pydantic Schemas - Must be `[COMPLETED]` (required)
- `T1.4` - FastAPI Backend Foundation - Should be `[COMPLETED]` (recommended)

**Blocks**:
- `T1.8` - React Frontend Foundation (needs API endpoints)
- `T2.1` - P&L Calculation Utilities (needs trade endpoints)

**Description**: 
Implement all CRUD API endpoints for trades:
- GET /api/trades (list with filters)
- GET /api/trades/:id
- POST /api/trades
- PUT /api/trades/:id
- PATCH /api/trades/:id
- DELETE /api/trades/:id
- POST /api/trades/bulk
- GET /api/trades/search

**Acceptance Criteria**:
- [ ] All endpoints implemented and tested
- [ ] Pagination support for list endpoints
- [ ] API key authentication working
- [ ] OpenAPI documentation complete
- [ ] Error handling for all endpoints
- [ ] Input validation using Pydantic

**Files to Create/Modify**:
- `backend/app/api/routes/trades.py`
- `backend/app/services/trade_service.py`
- `backend/app/utils/calculations.py`

**Completion Summary**: `[To be filled when completed]`
```

## Dependency Graph Visualization

You can create a simple dependency graph in your TASKS.md:

```markdown
## Task Dependency Graph

```
Phase 1: Foundation
T1.1 (Project Structure)
  └─> T1.2 (Docker Compose)
       └─> T1.3 (PostgreSQL Setup)
            └─> T1.4 (FastAPI Foundation)
                 ├─> T1.5 (SQLAlchemy Models)
                 │    └─> T1.6 (Pydantic Schemas)
                 │         └─> T1.7 (Trade CRUD API)
                 │              └─> T1.8 (React Frontend)
                 └─> T1.9 (Trade Entry Form)
```

## Task Status Definitions

- **PENDING**: Not started, waiting for dependencies or assignment
- **CLAIMED**: An agent has claimed this task but not started work
- **IN PROGRESS**: Currently being worked on
- **REVIEW**: Completed and submitted for review
- **COMPLETED**: Approved and merged
- **BLOCKED**: Cannot proceed due to missing dependencies or blockers

## Dependency Types

### Required Dependencies (Must be COMPLETED)
Tasks that must be completed before this task can start. The task cannot be claimed if required dependencies are not `[COMPLETED]`.

### Recommended Dependencies (Should be COMPLETED)
Tasks that should be completed but are not blocking. The task can be claimed, but it's recommended to wait.

### Blocks
Tasks that depend on this task. When this task is completed, it unblocks these tasks.

## Dependency Checking Script

You can use this logic to check if a task can be claimed:

```python
def can_claim_task(task, all_tasks):
    """Check if a task can be claimed based on dependencies."""
    for dep_id in task.required_dependencies:
        dep_task = find_task(dep_id, all_tasks)
        if dep_task.status != "COMPLETED":
            return False, f"Required dependency {dep_id} is not completed"
    return True, "All dependencies met"
```

## Parallel Execution Opportunities

Tasks with **no dependencies** or **only completed dependencies** can run in parallel:

```markdown
## Tasks Ready for Parallel Execution

### Currently Available (No Blocking Dependencies):
- T2.1: P&L Calculation Utilities (depends on T1.7 - COMPLETED)
- T2.2: Dashboard Statistics Service (depends on T2.1 - COMPLETED)
- T3.1: Price Data Service (depends on T1.5 - COMPLETED)

### Can Start in Parallel:
- Agent A: T2.1
- Agent B: T2.2 (after T2.1 completes)
- Agent C: T3.1 (can start now)
```

## Task Claiming Rules

1. **Check Dependencies**: Before claiming, verify all required dependencies are `[COMPLETED]`
2. **Update Status**: Mark as `[CLAIMED]` and add your name
3. **Start Work**: Change to `[IN PROGRESS]` when you begin
4. **Complete**: Mark as `[REVIEW]` when ready for review
5. **Unblock**: When `[COMPLETED]`, other tasks can claim

## Example: Complete Task List with Dependencies

```markdown
# Tasks

## Phase 1: Foundation

### T1.1: Project Structure Setup
**Status**: `[COMPLETED]`  
**Dependencies**: None  
**Blocks**: T1.2

### T1.2: Docker Compose Configuration
**Status**: `[COMPLETED]`  
**Dependencies**: T1.1 (COMPLETED)  
**Blocks**: T1.3

### T1.3: PostgreSQL Database Setup
**Status**: `[COMPLETED]`  
**Dependencies**: T1.2 (COMPLETED)  
**Blocks**: T1.4

### T1.4: FastAPI Backend Foundation
**Status**: `[COMPLETED]`  
**Dependencies**: T1.3 (COMPLETED)  
**Blocks**: T1.5, T1.6

### T1.5: SQLAlchemy Models
**Status**: `[COMPLETED]`  
**Dependencies**: T1.4 (COMPLETED)  
**Blocks**: T1.6, T1.7, T3.1

### T1.6: Pydantic Schemas
**Status**: `[REVIEW]`  
**Dependencies**: T1.5 (COMPLETED)  
**Blocks**: T1.7  
**Claimed By**: Agent A

### T1.7: Trade CRUD API Endpoints
**Status**: `[PENDING]`  
**Dependencies**: 
- T1.5 (COMPLETED) ✅
- T1.6 (REVIEW) ⏳ - Waiting for completion
**Blocks**: T1.8, T2.1
```

---

**Usage**: Copy this template structure into your `TASKS.md` file and fill in the details for each task.

