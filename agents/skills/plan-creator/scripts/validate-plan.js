#!/usr/bin/env node

/**
 * Validate implementation plan structure and completeness
 * Checks YAML frontmatter, required sections, and checklist formatting
 */

const fs = require('fs-extra');
const path = require('path');
const yaml = require('js-yaml');
const chalk = require('chalk');

/**
 * Validates that a plan file exists and is readable
 * @param {string} planPath - Path to the plan file
 * @returns {Promise<boolean>} - true if valid, throws error if not
 */
async function validateFileExists(planPath) {
  if (!await fs.pathExists(planPath)) {
    throw new Error(`Plan file not found: ${planPath}`);
  }

  const stats = await fs.stat(planPath);
  if (!stats.isFile()) {
    throw new Error(`Path is not a file: ${planPath}`);
  }

  if (!planPath.endsWith('.md')) {
    throw new Error(`Plan must be a markdown file (.md): ${planPath}`);
  }

  return true;
}

/**
 * Extracts and parses YAML frontmatter from markdown content
 * @param {string} content - Full markdown content
 * @returns {object|null} - Parsed frontmatter or null if not found
 */
function extractFrontmatter(content) {
  const frontmatterRegex = /^---\s*\n([\s\S]*?)\n---\s*\n/;
  const match = content.match(frontmatterRegex);

  if (!match) {
    return null;
  }

  try {
    return yaml.load(match[1]);
  } catch (error) {
    throw new Error(`Invalid YAML frontmatter: ${error.message}`);
  }
}

/**
 * Validates frontmatter structure and required fields
 * @param {object} frontmatter - Parsed frontmatter object
 * @returns {object} - { valid: boolean, errors: string[], warnings: string[] }
 */
function validateFrontmatter(frontmatter) {
  const errors = [];
  const warnings = [];

  if (!frontmatter) {
    errors.push('Missing YAML frontmatter');
    return { valid: false, errors, warnings };
  }

  // Required fields
  const requiredFields = ['title', 'created', 'status'];
  for (const field of requiredFields) {
    if (!frontmatter[field]) {
      errors.push(`Missing required field: ${field}`);
    }
  }

  // Validate status
  const validStatuses = ['draft', 'in-progress', 'blocked', 'completed'];
  if (frontmatter.status && !validStatuses.includes(frontmatter.status)) {
    errors.push(`Invalid status: ${frontmatter.status}. Must be one of: ${validStatuses.join(', ')}`);
  }

  // Validate date format (YYYY-MM-DD)
  if (frontmatter.created && !/^\d{4}-\d{2}-\d{2}$/.test(frontmatter.created)) {
    errors.push(`Invalid date format for "created": ${frontmatter.created}. Use YYYY-MM-DD`);
  }

  // Optional field validation
  if (frontmatter.type) {
    const validTypes = ['feature', 'bug-fix', 'refactor', 'custom'];
    if (!validTypes.includes(frontmatter.type)) {
      warnings.push(`Uncommon type: ${frontmatter.type}. Common types: ${validTypes.join(', ')}`);
    }
  }

  // Check for author
  if (!frontmatter.author) {
    warnings.push('Missing optional field: author (recommended for collaborative work)');
  }

  return { 
    valid: errors.length === 0, 
    errors, 
    warnings 
  };
}

/**
 * Validates plan structure based on type
 * @param {string} content - Full markdown content
 * @param {object} frontmatter - Parsed frontmatter
 * @returns {object} - { valid: boolean, errors: string[], warnings: string[] }
 */
function validateStructure(content, frontmatter) {
  const errors = [];
  const warnings = [];

  const planType = frontmatter.type || 'unknown';

  // Common sections that should exist in most plans
  const hasImplementationPlan = /##\s+Implementation Plan/i.test(content);
  const hasTestStrategy = /##\s+(Test|Testing) (Strategy|Plan)/i.test(content);

  // Type-specific validation
  if (planType === 'feature') {
    if (!/##\s+Objective/i.test(content)) {
      warnings.push('Feature plan should have "Objective" section');
    }
    if (!/##\s+Requirements/i.test(content)) {
      warnings.push('Feature plan should have "Requirements" section');
    }
    if (!/##\s+Out of Scope/i.test(content)) {
      warnings.push('Feature plan should have "Out of Scope" section');
    }
    if (!hasImplementationPlan) {
      errors.push('Feature plan must have "Implementation Plan" section');
    }
  } else if (planType === 'bug-fix') {
    if (!/##\s+Bug Description/i.test(content)) {
      warnings.push('Bug fix plan should have "Bug Description" section');
    }
    if (!/##\s+Root Cause/i.test(content)) {
      warnings.push('Bug fix plan should have "Root Cause Analysis" section');
    }
    if (!/##\s+Fix Plan/i.test(content)) {
      errors.push('Bug fix plan must have "Fix Plan" section');
    }
  } else if (planType === 'refactor') {
    if (!/##\s+Motivation/i.test(content)) {
      warnings.push('Refactor plan should have "Motivation" section');
    }
    if (!/##\s+Proposed Changes/i.test(content)) {
      warnings.push('Refactor plan should have "Proposed Changes" section');
    }
    if (!/##\s+Migration Strategy/i.test(content)) {
      errors.push('Refactor plan must have "Migration Strategy" section');
    }
  }

  // General validation
  if (!hasTestStrategy) {
    warnings.push('Plan should have "Test Strategy" or "Testing Plan" section');
  }

  return { 
    valid: errors.length === 0, 
    errors, 
    warnings 
  };
}

/**
 * Validates checklist items in the plan
 * @param {string} content - Full markdown content
 * @returns {object} - { valid: boolean, errors: string[], warnings: string[], stats: object }
 */
function validateChecklists(content) {
  const errors = [];
  const warnings = [];

  // Find all checklist items
  const checklistRegex = /^[\s]*-\s+\[([ xX])\]\s+(.+)$/gm;
  const matches = [...content.matchAll(checklistRegex)];

  if (matches.length === 0) {
    warnings.push('No checklist items found. Plans should have actionable tasks.');
  }

  // Count completed vs total
  const totalTasks = matches.length;
  const completedTasks = matches.filter(m => m[1].toLowerCase() === 'x').length;

  // Check for malformed checklist items
  const malformedRegex = /^[\s]*-\s+\[[^\sxX ]\]/gm;
  const malformed = [...content.matchAll(malformedRegex)];
  
  if (malformed.length > 0) {
    errors.push(`Found ${malformed.length} malformed checklist items. Use [ ], [x], or [X]`);
  }

  // Check for orphaned todos (not in checklist format)
  const orphanedTodoRegex = /^[\s]*-\s+(?!\[)(TODO|FIXME|XXX):/gmi;
  const orphanedTodos = [...content.matchAll(orphanedTodoRegex)];
  
  if (orphanedTodos.length > 0) {
    warnings.push(`Found ${orphanedTodos.length} orphaned TODO items. Convert to checklists [ ]`);
  }

  const stats = {
    totalTasks,
    completedTasks,
    percentComplete: totalTasks > 0 ? Math.round((completedTasks / totalTasks) * 100) : 0
  };

  return { 
    valid: errors.length === 0, 
    errors, 
    warnings,
    stats
  };
}

/**
 * Validates overall plan quality
 * @param {string} content - Full markdown content
 * @param {object} frontmatter - Parsed frontmatter
 * @returns {object} - { errors: string[], warnings: string[] }
 */
function validateQuality(content, frontmatter) {
  const errors = [];
  const warnings = [];

  // Check for placeholder text that should be replaced
  const placeholders = [
    '[TODO',
    '[FIXME',
    '[Add',
    '[Insert',
    '[Fill',
    '[Your',
    '[Description',
    '[What',
    '[Why',
    '[How'
  ];

  let placeholderCount = 0;
  for (const placeholder of placeholders) {
    const regex = new RegExp(`\\${placeholder}`, 'gi');
    const matches = content.match(regex);
    if (matches) {
      placeholderCount += matches.length;
    }
  }

  if (placeholderCount > 0) {
    warnings.push(`Found ${placeholderCount} placeholder sections that should be filled in`);
  }

  // Check plan length
  const lines = content.split('\n').length;
  if (lines > 500) {
    warnings.push(`Plan is ${lines} lines long. Consider breaking into multiple files if over 500 lines.`);
  }

  // Check if plan is too short (likely incomplete)
  if (lines < 20) {
    warnings.push('Plan seems very short. Ensure all necessary sections are included.');
  }

  return { errors, warnings };
}

/**
 * Main validation function
 * @param {string} planPath - Path to the plan file to validate
 * @returns {Promise<number>} - Exit code (0 = valid, 1 = errors, 2 = warnings only)
 */
async function validatePlan(planPath) {
  console.log(chalk.blue.bold('\n🔍 Validating Plan\n'));
  console.log(chalk.gray(`File: ${planPath}\n`));

  try {
    // Validate file exists
    await validateFileExists(planPath);

    // Read file content
    const content = await fs.readFile(planPath, 'utf8');

    // Extract frontmatter
    const frontmatter = extractFrontmatter(content);

    // Run all validations
    const frontmatterValidation = validateFrontmatter(frontmatter);
    const structureValidation = validateStructure(content, frontmatter || {});
    const checklistValidation = validateChecklists(content);
    const qualityValidation = validateQuality(content, frontmatter || {});

    // Collect all errors and warnings
    const allErrors = [
      ...frontmatterValidation.errors,
      ...structureValidation.errors,
      ...checklistValidation.errors,
      ...qualityValidation.errors
    ];

    const allWarnings = [
      ...frontmatterValidation.warnings,
      ...structureValidation.warnings,
      ...checklistValidation.warnings,
      ...qualityValidation.warnings
    ];

    // Display results
    if (allErrors.length > 0) {
      console.log(chalk.red.bold('❌ Validation Errors:\n'));
      allErrors.forEach(error => {
        console.log(chalk.red(`   • ${error}`));
      });
      console.log('');
    }

    if (allWarnings.length > 0) {
      console.log(chalk.yellow.bold('⚠️  Warnings:\n'));
      allWarnings.forEach(warning => {
        console.log(chalk.yellow(`   • ${warning}`));
      });
      console.log('');
    }

    // Display stats
    if (checklistValidation.stats) {
      const { totalTasks, completedTasks, percentComplete } = checklistValidation.stats;
      console.log(chalk.blue.bold('📊 Plan Statistics:\n'));
      console.log(chalk.gray(`   Tasks: ${completedTasks}/${totalTasks} complete (${percentComplete}%)`));
      console.log(chalk.gray(`   Status: ${frontmatter?.status || 'unknown'}`));
      console.log(chalk.gray(`   Type: ${frontmatter?.type || 'unspecified'}\n`));
    }

    // Final verdict
    if (allErrors.length === 0 && allWarnings.length === 0) {
      console.log(chalk.green.bold('✅ Plan is valid and complete!\n'));
      return 0;
    } else if (allErrors.length === 0) {
      console.log(chalk.yellow.bold('✅ Plan is valid but has warnings.\n'));
      return 2;
    } else {
      console.log(chalk.red.bold('❌ Plan has errors that must be fixed.\n'));
      return 1;
    }

  } catch (error) {
    console.error(chalk.red.bold('\n❌ Validation failed:\n'));
    console.error(chalk.red(`   ${error.message}\n`));
    return 1;
  }
}

/**
 * CLI entry point
 */
async function main() {
  const args = process.argv.slice(2);

  if (args.length === 0) {
    console.log(chalk.yellow('\nUsage: npm run validate <path-to-plan.md>\n'));
    console.log(chalk.gray('Example: npm run validate ../../plans/add-user-auth.md\n'));
    process.exit(1);
  }

  const planPath = path.resolve(args[0]);
  const exitCode = await validatePlan(planPath);
  process.exit(exitCode);
}

// Run if called directly
if (require.main === module) {
  main();
}

module.exports = { validatePlan, validateFrontmatter, validateChecklists };
