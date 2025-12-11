---
title: Fix Bug Name
created: YYYY-MM-DD
status: draft
author: @agent-id
type: bug-fix
issue: #123
severity: low|medium|high|critical
---

# Plan: Fix Bug Name

## Bug Description

[Clear description of what is broken and the impact on users/system]

## Steps to Reproduce

1. [Step 1]
2. [Step 2]
3. [Step 3]
4. [Observed result]

## Expected vs Actual

**Expected**: [What should happen]

**Actual**: [What actually happens]

## Impact

- **Severity**: [low|medium|high|critical]
- **Affected Users**: [Who is impacted]
- **Workaround**: [Temporary workaround if available, or "None"]

## Root Cause Analysis

### Investigation Steps
- [What was checked]
- [Debugging approach]
- [Findings from logs/tests]

### Root Cause
[Why the bug occurs - be specific about the code/logic issue]

### Why It Wasn't Caught
- [Why tests didn't catch this]
- [What to improve in testing]

## Fix Plan

### Implementation
- [ ] Fix the core issue in `path/to/file.ts`
- [ ] Update related code if needed
- [ ] Add regression test to prevent recurrence
- [ ] Verify fix resolves the issue

### Testing
- [ ] Manual verification of bug fix
- [ ] Run full test suite (check for regressions)
- [ ] Test edge cases
- [ ] Verify workaround no longer needed

## Files to Modify

- `path/to/buggy/file.ts` - [Description of fix]
- `tests/path/test.ts` - [Add regression test]
- `docs/path/doc.md` - [Update if behavior documented]

## Verification Checklist

- [ ] Bug no longer reproducible
- [ ] All tests pass
- [ ] No new issues introduced
- [ ] Related functionality still works
- [ ] Performance not degraded

## Prevention

[How to prevent similar bugs in the future]
- [ ] Add test coverage for this scenario
- [ ] Update validation logic
- [ ] Add documentation about edge case
- [ ] Review similar code for same issue

## Notes

[Any additional context, related issues, etc.]
