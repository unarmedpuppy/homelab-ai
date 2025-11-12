# Review Feedback Template

**Task ID**: `[TASK_ID]`  
**Task Name**: `[TASK_NAME]`  
**Reviewed By**: `[REVIEWER_NAME]`  
**Review Date**: `[DATE]`  
**Review Duration**: `[TIME]`

---

## Review Status

- [ ] **APPROVED** ✅ - Ready to merge, no changes needed
- [ ] **NEEDS REVISION** ⚠️ - Minor issues, fix and resubmit
- [ ] **REJECTED** ❌ - Major issues, significant rework required

---

## Executive Summary

**Overall Assessment**: `[Brief summary of review findings]`

**Key Strengths**:
- `[Strength 1]`
- `[Strength 2]`
- `[Strength 3]`

**Key Concerns**:
- `[Concern 1]`
- `[Concern 2]`
- `[Concern 3]`

**Recommendation**: `[APPROVED / NEEDS REVISION / REJECTED]`

---

## Critical Issues (Must Fix)

**These issues must be addressed before approval. Code cannot be merged with these issues.**

### Issue #1: `[Issue Title]`
- **Severity**: Critical
- **Location**: `[File:Line]` or `[Component/Endpoint]`
- **Description**: `[Detailed description of the issue]`
- **Impact**: `[What happens if not fixed]`
- **Example**: 
  ```[code example or screenshot]```
- **Recommendation**: `[How to fix]`
- **Status**: `[ ] Not Fixed | [ ] Fixed | [ ] Partially Fixed`

### Issue #2: `[Issue Title]`
- **Severity**: Critical
- **Location**: `[File:Line]`
- **Description**: `[Description]`
- **Impact**: `[Impact]`
- **Recommendation**: `[Fix]`
- **Status**: `[ ] Not Fixed | [ ] Fixed | [ ] Partially Fixed`

---

## Medium Issues (Should Fix)

**These issues should be addressed but are not blocking. Code can be merged after addressing these.**

### Issue #3: `[Issue Title]`
- **Severity**: Medium
- **Location**: `[File:Line]`
- **Description**: `[Description]`
- **Impact**: `[Impact]`
- **Recommendation**: `[Fix]`
- **Status**: `[ ] Not Fixed | [ ] Fixed | [ ] Partially Fixed`

### Issue #4: `[Issue Title]`
- **Severity**: Medium
- **Location**: `[File:Line]`
- **Description**: `[Description]`
- **Impact**: `[Impact]`
- **Recommendation**: `[Fix]`
- **Status**: `[ ] Not Fixed | [ ] Fixed | [ ] Partially Fixed`

---

## Minor Issues (Nice to Have)

**These are suggestions for improvement. Not required for approval.**

### Issue #5: `[Issue Title]`
- **Severity**: Minor
- **Location**: `[File:Line]`
- **Description**: `[Description]`
- **Suggestion**: `[Improvement]`
- **Status**: `[ ] Not Fixed | [ ] Fixed | [ ] Partially Fixed`

---

## Approved Aspects

**What was done well:**

- ✅ **Aspect 1**: `[Description]`
- ✅ **Aspect 2**: `[Description]`
- ✅ **Aspect 3**: `[Description]`

---

## Detailed Review by Category

### Backend Code Review

#### Code Quality
- [ ] Type hints present on all functions
- [ ] Async/await used correctly
- [ ] Business logic in services (not routes)
- [ ] Error handling for all endpoints
- [ ] Pydantic validation for all inputs
- [ ] SQLAlchemy ORM (no raw SQL)
- [ ] Docstrings on all functions
- [ ] OpenAPI documentation complete

**Issues Found**: `[List any issues]`

#### Security
- [ ] No hardcoded secrets
- [ ] Input validation on all endpoints
- [ ] SQL injection prevention
- [ ] Authentication/authorization working
- [ ] Rate limiting (if applicable)

**Issues Found**: `[List any issues]`

#### Performance
- [ ] Database queries optimized
- [ ] No N+1 query problems
- [ ] Proper indexing
- [ ] Caching where appropriate

**Issues Found**: `[List any issues]`

### Frontend Code Review

#### Code Quality
- [ ] TypeScript strict mode (no `any` types)
- [ ] All API calls through API client
- [ ] Loading states for async operations
- [ ] Error handling and error boundaries
- [ ] Responsive design (mobile-friendly)
- [ ] Proper React patterns (hooks, memoization)
- [ ] Component documentation

**Issues Found**: `[List any issues]`

#### User Experience
- [ ] Intuitive navigation
- [ ] Clear error messages
- [ ] Loading indicators
- [ ] Form validation
- [ ] Accessibility considerations

**Issues Found**: `[List any issues]`

### API Review

#### Design
- [ ] Every UI action has corresponding API endpoint
- [ ] RESTful conventions followed
- [ ] Consistent URL patterns
- [ ] Pagination for list endpoints
- [ ] API key authentication working
- [ ] OpenAPI documentation complete

**Issues Found**: `[List any issues]`

#### Integration
- [ ] Frontend types match backend schemas
- [ ] API URLs are correct
- [ ] Error responses are consistent
- [ ] Response formats are consistent

**Issues Found**: `[List any issues]`

### Integration Review

- [ ] Frontend connects to backend correctly
- [ ] Database schema matches models
- [ ] Docker configuration is correct
- [ ] Services communicate properly
- [ ] No integration errors

**Issues Found**: `[List any issues]`

### Documentation Review

- [ ] All functions have docstrings
- [ ] Complex logic has comments
- [ ] README is updated
- [ ] TASKS.md is updated
- [ ] API documentation complete

**Issues Found**: `[List any issues]`

### Testing Review

- [ ] Manual testing completed
- [ ] Edge cases tested
- [ ] Calculations verified (if applicable)
- [ ] Responsive design tested
- [ ] Integration tested

**Issues Found**: `[List any issues]`

---

## Requirements Compliance

### Implementation Plan Compliance
- [ ] All requirements from IMPLEMENTATION_PLAN.md met
- [ ] Architecture matches specification
- [ ] Database schema matches specification
- [ ] API endpoints match specification

**Missing Requirements**: `[List any missing requirements]`

### Coding Standards Compliance
- [ ] Follows coding standards guide
- [ ] Uses patterns from codebase
- [ ] Consistent with project style

**Deviations**: `[List any deviations]`

---

## Recommendations

### Immediate Actions
1. `[Action 1]`
2. `[Action 2]`
3. `[Action 3]`

### Future Improvements
1. `[Improvement 1]`
2. `[Improvement 2]`
3. `[Improvement 3]`

---

## Re-Review Checklist

**When agent addresses feedback, reviewer should check:**

- [ ] All Critical issues fixed
- [ ] All Medium issues addressed (or justified)
- [ ] Code still compiles/runs
- [ ] No new issues introduced
- [ ] Previous approved aspects still good

---

## Review History

| Date | Reviewer | Status | Notes |
|------|----------|--------|-------|
| `[DATE]` | `[REVIEWER]` | `[STATUS]` | `[NOTES]` |
| `[DATE]` | `[REVIEWER]` | `[STATUS]` | `[NOTES]` |

---

## Next Steps

**For Agent**:
1. Address Critical issues first
2. Address Medium issues
3. Consider Minor issues (optional)
4. Update this document with fix status
5. Mark task as `[REVIEW]` again when ready

**For Reviewer**:
1. Wait for agent to address feedback
2. Re-review using Re-Review Checklist
3. Update status (APPROVED/NEEDS REVISION/REJECTED)
4. Close review if APPROVED

---

**Review Complete**: `[ ] Yes | [ ] No`  
**Ready for Re-Review**: `[ ] Yes | [ ] No`

