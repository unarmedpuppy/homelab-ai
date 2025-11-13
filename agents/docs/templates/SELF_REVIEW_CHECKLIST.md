# Self-Review Checklist Template

**Task ID**: `[TASK_ID]`  
**Agent**: `[AGENT_NAME]`  
**Date**: `[DATE]`  
**Status**: `[ ] Not Started | [ ] In Progress | [ ] Complete`

---

## Pre-Submission Self-Review

**Instructions**: Complete this checklist before marking your task as `[REVIEW]`. Check each item and provide evidence/documentation where applicable.

### Code Quality

- [ ] **Code compiles/runs without errors**
  - Backend: `python -m pytest` or `python main.py` runs successfully
  - Frontend: `npm run build` completes without errors
  - Evidence: `[Paste command output or screenshot]`

- [ ] **No TypeScript/Python linting errors**
  - Backend: `flake8 .` or `pylint .` passes
  - Frontend: `npm run lint` passes
  - Evidence: `[Paste command output]`

- [ ] **No type checking errors**
  - Backend: `mypy .` passes (if applicable)
  - Frontend: `npm run type-check` or `tsc --noEmit` passes
  - Evidence: `[Paste command output]`

- [ ] **Code formatting is consistent**
  - Backend: `black --check .` passes (or equivalent)
  - Frontend: `npm run format` or `prettier --check` passes
  - Evidence: `[Paste command output]`

### Type Safety

- [ ] **All functions have type hints/types**
  - Backend: All Python functions have type hints
  - Frontend: All TypeScript functions have explicit types (no `any`)
  - Evidence: `[List any exceptions with justification]`

- [ ] **Pydantic models used for validation** (Backend)
  - All API request/response models use Pydantic
  - Evidence: `[List models created]`

- [ ] **API response types match backend schemas** (Frontend)
  - Frontend types match backend Pydantic models
  - Evidence: `[List type definitions]`

### Error Handling

- [ ] **All API endpoints have error handling**
  - Backend: Try/except blocks or FastAPI exception handlers
  - Evidence: `[List endpoints with error handling]`

- [ ] **Frontend has error boundaries** (if applicable)
  - React error boundaries for component errors
  - Evidence: `[List error boundaries]`

- [ ] **Validation errors return proper status codes**
  - 400 for validation errors, 404 for not found, 500 for server errors
  - Evidence: `[List status codes used]`

- [ ] **User-friendly error messages**
  - Errors are clear and actionable
  - Evidence: `[Example error messages]`

### Documentation

- [ ] **All functions have docstrings/comments**
  - Backend: All functions have docstrings
  - Frontend: Complex functions have JSDoc comments
  - Evidence: `[List any undocumented functions with justification]`

- [ ] **Complex logic is explained**
  - Comments explain "why", not just "what"
  - Evidence: `[List complex sections with comments]`

- [ ] **API endpoints have OpenAPI descriptions** (Backend)
  - All endpoints documented in OpenAPI/Swagger
  - Evidence: `[List endpoints]`

- [ ] **README updated** (if applicable)
  - Setup instructions, usage examples, etc.
  - Evidence: `[List changes made]`

- [ ] **Task status updated in central registry**
  - Task status updated to `review` using `update_task_status()`
  - Completion summary added
  - Evidence: `[Task ID and status]`

### Testing

- [ ] **Manual testing completed**
  - Feature works as expected
  - Evidence: `[Describe what was tested]`

- [ ] **Edge cases tested**
  - Invalid inputs, empty data, boundary conditions
  - Evidence: `[List edge cases tested]`

- [ ] **Calculations verified** (if applicable)
  - Tested with known values/expected results
  - Evidence: `[Example calculations]`

- [ ] **Responsive design tested** (Frontend)
  - Works on mobile, tablet, desktop
  - Evidence: `[Screenshots or description]`

- [ ] **Integration tested** (if applicable)
  - Components work together correctly
  - Evidence: `[Describe integration tests]`

### API Completeness

- [ ] **All required endpoints implemented**
  - Checked against IMPLEMENTATION_PLAN.md
  - Evidence: `[List endpoints implemented]`

- [ ] **All endpoints documented in OpenAPI**
  - Swagger UI shows all endpoints
  - Evidence: `[Screenshot or list]`

- [ ] **API key authentication working** (if applicable)
  - All endpoints require authentication
  - Evidence: `[Test results]`

- [ ] **Pagination implemented** (if list endpoint)
  - Limit, offset, total, has_more in response
  - Evidence: `[Example paginated response]`

### Code Standards Compliance

- [ ] **Follows coding standards from guide**
  - Backend: Follows Python/FastAPI standards
  - Frontend: Follows React/TypeScript standards
  - Evidence: `[List any deviations with justification]`

- [ ] **Uses patterns from existing codebase**
  - Consistent with project patterns
  - Evidence: `[List patterns followed]`

- [ ] **No console.log/debug code left in**
  - All debug statements removed
  - Evidence: `[Search results: grep -r "console.log\|print("]`

- [ ] **No unused imports**
  - All imports are used
  - Evidence: `[Linter output]`

### Integration

- [ ] **Frontend connects to backend correctly**
  - API calls work, CORS configured
  - Evidence: `[Test results]`

- [ ] **Database operations work**
  - Queries execute, migrations applied
  - Evidence: `[Test results]`

- [ ] **Docker services communicate** (if applicable)
  - Services can reach each other
  - Evidence: `[Test results]`

- [ ] **No integration errors**
  - No connection errors, timeouts, etc.
  - Evidence: `[Logs or test results]`

### Security

- [ ] **No hardcoded secrets**
  - All secrets in environment variables
  - Evidence: `[Search results: grep -r "password\|secret\|key" --exclude-dir=node_modules]`

- [ ] **Input validation on backend**
  - All user inputs validated
  - Evidence: `[List validation rules]`

- [ ] **SQL injection prevention** (if applicable)
  - Using ORM, parameterized queries
  - Evidence: `[List database queries]`

### Performance

- [ ] **No obvious performance issues**
  - Queries optimized, no N+1 problems
  - Evidence: `[Performance considerations]`

- [ ] **Loading states implemented** (Frontend)
  - Users see loading indicators
  - Evidence: `[List loading states]`

---

## Self-Review Summary

**Total Items**: `[X]`  
**Completed**: `[Y]`  
**Completion Rate**: `[Y/X * 100]%`

**Issues Found**:
- [ ] No issues found - Ready for review
- [ ] Minor issues found - Will fix before submitting
- [ ] Major issues found - Need to address before submitting

**Issues to Fix** (if any):
1. `[Issue 1]`
2. `[Issue 2]`

**Confidence Level**:
- [ ] High - Ready for review
- [ ] Medium - Some concerns, but ready
- [ ] Low - Need to address issues first

---

## Notes

`[Any additional notes, concerns, or questions for the reviewer]`

---

**After completing this checklist**, update your task status to `review` using `update_task_status()` in the central task registry.

