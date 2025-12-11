#!/usr/bin/env node

/**
 * Create a new implementation plan with interactive prompts
 * Supports feature, bug-fix, refactor, and custom plan types
 */

const fs = require('fs-extra');
const path = require('path');
const inquirer = require('inquirer');
const yaml = require('js-yaml');
const chalk = require('chalk');

/**
 * Validates plan name format (hyphen-case)
 * @param {string} name - The plan name to validate
 * @returns {boolean|string} - true if valid, error message if invalid
 */
function validatePlanName(name) {
  if (!name || name.trim().length === 0) {
    return 'Plan name is required';
  }
  
  if (!/^[a-z0-9]+(-[a-z0-9]+)*$/.test(name)) {
    return 'Plan name must be in hyphen-case (e.g., add-user-auth)';
  }
  
  if (name.length > 64) {
    return 'Plan name must be 64 characters or less';
  }
  
  return true;
}

/**
 * Gets the current date in YYYY-MM-DD format
 * @returns {string} - Current date string
 */
function getCurrentDate() {
  const now = new Date();
  return now.toISOString().split('T')[0];
}

/**
 * Generates feature plan template
 * @param {object} answers - User responses from prompts
 * @returns {string} - Complete plan markdown
 */
function generateFeaturePlan(answers) {
  const frontmatter = yaml.dump({
    title: answers.title,
    created: getCurrentDate(),
    status: 'draft',
    author: answers.author || '@agent',
    type: 'feature'
  });

  return `---
${frontmatter.trim()}
---

# Plan: ${answers.title}

## Objective

${answers.objective || '[Clear goal statement - what will this feature accomplish?]'}

## Requirements

${answers.requirements || '- [Requirement 1]\n- [Requirement 2]\n- [Requirement 3]'}

## Out of Scope

- [What is explicitly NOT included in this feature]
- [Helps prevent scope creep]

## Current State

### Existing Code
- [Relevant files and components]
- [Current functionality that will be extended]

### Dependencies
- [Libraries or services needed]
- [External dependencies]

## Implementation Plan

### Phase 1: [Phase Name]
- [ ] Task 1
- [ ] Task 2
- [ ] Task 3

### Phase 2: [Phase Name]
- [ ] Task 1
- [ ] Task 2
- [ ] Task 3

### Phase 3: [Phase Name]
- [ ] Task 1
- [ ] Task 2

## Test Strategy

### Unit Tests
- [What to unit test]

### Integration Tests
- [What to integration test]

### Edge Cases
- [Edge cases to handle]

## Documentation Updates

- [ ] Update relevant documentation files
- [ ] Add usage examples
- [ ] Update API documentation (if applicable)

## Success Criteria

- [ ] All tests pass
- [ ] Code review approved
- [ ] Documentation updated
- [ ] Deployed to staging
`;
}

/**
 * Generates bug fix plan template
 * @param {object} answers - User responses from prompts
 * @returns {string} - Complete plan markdown
 */
function generateBugFixPlan(answers) {
  const frontmatter = yaml.dump({
    title: answers.title,
    created: getCurrentDate(),
    status: 'draft',
    author: answers.author || '@agent',
    type: 'bug-fix',
    issue: answers.issueNumber || undefined
  });

  return `---
${frontmatter.trim()}
---

# Plan: ${answers.title}

## Bug Description

${answers.bugDescription || '[What is broken? What is the impact?]'}

## Steps to Reproduce

1. [Step 1]
2. [Step 2]
3. [Step 3]
4. [Observed result]

## Expected vs Actual

**Expected**: ${answers.expected || '[What should happen]'}
**Actual**: ${answers.actual || '[What actually happens]'}

## Root Cause Analysis

### Investigation
- [What was checked]
- [Findings from debugging]

### Cause
${answers.rootCause || '[Why the bug occurs]'}

## Fix Plan

- [ ] Fix implementation
- [ ] Add regression test
- [ ] Verify fix resolves issue
- [ ] Check for similar bugs elsewhere

## Testing Plan

- [ ] Verify fix resolves the bug
- [ ] Run full test suite (check for regressions)
- [ ] Add test to prevent recurrence
- [ ] Manual testing of affected features

## Files to Modify

- \`path/to/file.ts\` - [description of change]
- \`tests/path/test.ts\` - [regression test]

## Verification

- [ ] Bug no longer reproducible
- [ ] All tests pass
- [ ] No new issues introduced
`;
}

/**
 * Generates refactoring plan template
 * @param {object} answers - User responses from prompts
 * @returns {string} - Complete plan markdown
 */
function generateRefactorPlan(answers) {
  const frontmatter = yaml.dump({
    title: answers.title,
    created: getCurrentDate(),
    status: 'draft',
    author: answers.author || '@agent',
    type: 'refactor'
  });

  return `---
${frontmatter.trim()}
---

# Plan: ${answers.title}

## Motivation

${answers.motivation || '[Why is this refactoring needed?]'}

## Current Problems

- [Problem 1]
- [Problem 2]
- [Problem 3]

## Proposed Changes

${answers.proposedChanges || '[What will change? How will it be better?]'}

### New Structure
\`\`\`
[Directory structure or architecture diagram]
\`\`\`

## Migration Strategy

### Phase 1: Create New System
- [ ] Implement new structure
- [ ] Add tests for new code
- [ ] Validate new approach

### Phase 2: Migrate Usage
- [ ] Migrate module 1
- [ ] Migrate module 2
- [ ] Migrate module 3
- [ ] Update all imports

### Phase 3: Cleanup
- [ ] Remove old code
- [ ] Update documentation
- [ ] Deploy and monitor

## Testing Strategy

- [ ] All existing tests pass unchanged
- [ ] No behavior changes in functionality
- [ ] Performance not degraded (benchmark)
- [ ] New code has good test coverage

## Rollback Plan

${answers.rollbackPlan || '[How to revert if issues arise]'}

## Files to Modify

### Create
- \`path/to/new/file.ts\`

### Modify
- \`path/to/existing/file.ts\`

### Delete
- \`path/to/deprecated/file.ts\`

## Success Criteria

- [ ] Code is cleaner and more maintainable
- [ ] All tests pass
- [ ] Performance maintained or improved
- [ ] Team approves new structure
`;
}

/**
 * Generates custom plan template
 * @param {object} answers - User responses from prompts
 * @returns {string} - Complete plan markdown
 */
function generateCustomPlan(answers) {
  const frontmatter = yaml.dump({
    title: answers.title,
    created: getCurrentDate(),
    status: 'draft',
    author: answers.author || '@agent',
    type: 'custom'
  });

  return `---
${frontmatter.trim()}
---

# Plan: ${answers.title}

## Overview

${answers.overview || '[High-level description of this plan]'}

## Goals

- [Goal 1]
- [Goal 2]
- [Goal 3]

## Implementation Plan

### Phase 1: [Phase Name]
- [ ] Task 1
- [ ] Task 2

### Phase 2: [Phase Name]
- [ ] Task 1
- [ ] Task 2

## Success Criteria

- [ ] Criterion 1
- [ ] Criterion 2
- [ ] Criterion 3
`;
}

/**
 * Main function to run the plan creation wizard
 */
async function main() {
  console.log(chalk.blue.bold('\n📋 Plan Creator\n'));

  try {
    // Get workspace root (3 levels up from scripts/)
    const workspaceRoot = path.join(__dirname, '../../..');
    const plansDir = path.join(workspaceRoot, 'agents/plans');
    const plansLocalDir = path.join(workspaceRoot, 'agents/plans-local');

    // Ensure directories exist
    await fs.ensureDir(plansDir);
    await fs.ensureDir(plansLocalDir);

    // Prompt for plan type and basic info
    const basicAnswers = await inquirer.prompt([
      {
        type: 'list',
        name: 'planType',
        message: 'What type of plan do you want to create?',
        choices: [
          { name: 'Feature - New functionality', value: 'feature' },
          { name: 'Bug Fix - Fix a defect', value: 'bug-fix' },
          { name: 'Refactor - Code restructuring', value: 'refactor' },
          { name: 'Custom - Blank template', value: 'custom' }
        ]
      },
      {
        type: 'input',
        name: 'planName',
        message: 'Plan name (hyphen-case):',
        validate: validatePlanName
      },
      {
        type: 'list',
        name: 'storage',
        message: 'Where should this plan be stored?',
        choices: [
          { name: 'agents/plans/ (committed, collaborative)', value: 'plans' },
          { name: 'agents/plans-local/ (gitignored, scratch)', value: 'plans-local' }
        ]
      },
      {
        type: 'input',
        name: 'title',
        message: 'Plan title (human-readable):',
        default: (answers) => answers.planName.split('-').map(w => 
          w.charAt(0).toUpperCase() + w.slice(1)
        ).join(' ')
      },
      {
        type: 'input',
        name: 'author',
        message: 'Author (e.g., @copilot):',
        default: '@agent'
      }
    ]);

    // Get type-specific details
    let typeSpecificAnswers = {};
    
    if (basicAnswers.planType === 'feature') {
      typeSpecificAnswers = await inquirer.prompt([
        {
          type: 'input',
          name: 'objective',
          message: 'Feature objective (one sentence):'
        },
        {
          type: 'editor',
          name: 'requirements',
          message: 'Requirements (opens editor, use bullet points):',
          default: '- Requirement 1\n- Requirement 2\n- Requirement 3'
        }
      ]);
    } else if (basicAnswers.planType === 'bug-fix') {
      typeSpecificAnswers = await inquirer.prompt([
        {
          type: 'input',
          name: 'issueNumber',
          message: 'Issue number (optional, e.g., #123):'
        },
        {
          type: 'input',
          name: 'bugDescription',
          message: 'Bug description:'
        },
        {
          type: 'input',
          name: 'expected',
          message: 'Expected behavior:'
        },
        {
          type: 'input',
          name: 'actual',
          message: 'Actual behavior:'
        }
      ]);
    } else if (basicAnswers.planType === 'refactor') {
      typeSpecificAnswers = await inquirer.prompt([
        {
          type: 'input',
          name: 'motivation',
          message: 'Why refactor?'
        },
        {
          type: 'editor',
          name: 'proposedChanges',
          message: 'Proposed changes (opens editor):'
        }
      ]);
    } else if (basicAnswers.planType === 'custom') {
      typeSpecificAnswers = await inquirer.prompt([
        {
          type: 'editor',
          name: 'overview',
          message: 'Plan overview (opens editor):'
        }
      ]);
    }

    const answers = { ...basicAnswers, ...typeSpecificAnswers };

    // Generate plan content
    let planContent;
    switch (answers.planType) {
      case 'feature':
        planContent = generateFeaturePlan(answers);
        break;
      case 'bug-fix':
        planContent = generateBugFixPlan(answers);
        break;
      case 'refactor':
        planContent = generateRefactorPlan(answers);
        break;
      case 'custom':
        planContent = generateCustomPlan(answers);
        break;
    }

    // Determine output path
    const baseDir = answers.storage === 'plans' ? plansDir : plansLocalDir;
    const outputPath = path.join(baseDir, `${answers.planName}.md`);

    // Check if file exists
    if (await fs.pathExists(outputPath)) {
      const { overwrite } = await inquirer.prompt([
        {
          type: 'confirm',
          name: 'overwrite',
          message: `Plan file already exists at ${outputPath}. Overwrite?`,
          default: false
        }
      ]);

      if (!overwrite) {
        console.log(chalk.yellow('\n✋ Plan creation cancelled.'));
        return;
      }
    }

    // Write plan file
    await fs.writeFile(outputPath, planContent, 'utf8');

    console.log(chalk.green('\n✅ Plan created successfully!'));
    console.log(chalk.gray(`   ${outputPath}\n`));
    console.log(chalk.blue('Next steps:'));
    console.log(chalk.gray('  1. Review and customize the plan'));
    console.log(chalk.gray('  2. Update status to "in-progress" when starting'));
    console.log(chalk.gray('  3. Check off tasks as you complete them'));
    console.log(chalk.gray('  4. Mark status "completed" when done\n'));

  } catch (error) {
    console.error(chalk.red('\n❌ Error creating plan:'), error.message);
    process.exit(1);
  }
}

// Run if called directly
if (require.main === module) {
  main();
}

module.exports = { main, validatePlanName };
