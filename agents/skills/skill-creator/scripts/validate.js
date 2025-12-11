#!/usr/bin/env node

/**
 * Validate Anthropic Skills Specification compliance
 * Reimplementation of quick_validate.py in JavaScript
 */

const fs = require('fs-extra');
const path = require('path');
const yaml = require('js-yaml');
const chalk = require('chalk');

// Exit codes
const EXIT_SUCCESS = 0;
const EXIT_ERROR = 1;
const EXIT_WARNING = 2;

// Allowed frontmatter fields
const REQUIRED_FIELDS = ['name', 'description'];
const OPTIONAL_FIELDS = ['license', 'allowed-tools', 'metadata'];
const ALLOWED_FIELDS = [...REQUIRED_FIELDS, ...OPTIONAL_FIELDS];

// Forbidden files
const FORBIDDEN_FILES = [
  'README.md',
  'CHANGELOG.md',
  'CONTRIBUTING.md',
  'CODE_OF_CONDUCT.md',
  '.github'
];

/**
 * Main validation function
 * @param {string} skillPath - Path to skill directory
 * @returns {Promise<number>} - Exit code
 */
async function validateSkill(skillPath) {
  const errors = [];
  const warnings = [];
  
  console.log(chalk.blue(`\n🔍 Validating skill: ${skillPath}\n`));
  
  try {
    // Resolve absolute path
    const absolutePath = path.resolve(skillPath);
    
    // Check if directory exists
    if (!await fs.pathExists(absolutePath)) {
      errors.push(`Directory does not exist: ${absolutePath}`);
      printResults(errors, warnings);
      return EXIT_ERROR;
    }
    
    // Check if it's a directory
    const stats = await fs.stat(absolutePath);
    if (!stats.isDirectory()) {
      errors.push(`Path is not a directory: ${absolutePath}`);
      printResults(errors, warnings);
      return EXIT_ERROR;
    }
    
    // Check SKILL.md exists
    const skillMdPath = path.join(absolutePath, 'SKILL.md');
    if (!await fs.pathExists(skillMdPath)) {
      errors.push('SKILL.md does not exist');
      printResults(errors, warnings);
      return EXIT_ERROR;
    }
    console.log(chalk.green('✓ SKILL.md exists'));
    
    // Read SKILL.md content
    const content = await fs.readFile(skillMdPath, 'utf-8');
    
    // Parse frontmatter
    const frontmatter = parseFrontmatter(content, errors, warnings);
    
    // Validate frontmatter structure
    if (frontmatter) {
      validateFrontmatterFields(frontmatter, errors, warnings);
      
      // Validate name
      if (frontmatter.name) {
        validateName(frontmatter.name, path.basename(absolutePath), errors, warnings);
      }
      
      // Validate description
      if (frontmatter.description) {
        validateDescription(frontmatter.description, errors, warnings);
      }
    }
    
    // Check SKILL.md length
    const lineCount = content.split('\n').length;
    if (lineCount > 500) {
      warnings.push(`SKILL.md has ${lineCount} lines (recommended max: 500). Consider splitting content to references/`);
    } else {
      console.log(chalk.green(`✓ SKILL.md length OK (${lineCount} lines)`));
    }
    
    // Check for forbidden files
    await checkForbiddenFiles(absolutePath, errors, warnings);
    
    // Check directory structure
    await checkDirectoryStructure(absolutePath, warnings);
    
    // Print results
    printResults(errors, warnings);
    
    // Return exit code
    if (errors.length > 0) {
      return EXIT_ERROR;
    } else if (warnings.length > 0) {
      return EXIT_WARNING;
    } else {
      return EXIT_SUCCESS;
    }
    
  } catch (error) {
    console.error(chalk.red(`\n✗ Validation failed: ${error.message}`));
    return EXIT_ERROR;
  }
}

/**
 * Parse YAML frontmatter from SKILL.md
 * @param {string} content - SKILL.md content
 * @param {Array} errors - Errors array
 * @param {Array} warnings - Warnings array
 * @returns {Object|null} - Parsed frontmatter or null
 */
function parseFrontmatter(content, errors, warnings) {
  const frontmatterRegex = /^---\n([\s\S]*?)\n---/;
  const match = content.match(frontmatterRegex);
  
  if (!match) {
    errors.push('SKILL.md must start with YAML frontmatter (---\\n...\\n---)');
    return null;
  }
  
  console.log(chalk.green('✓ Frontmatter format valid'));
  
  try {
    const frontmatter = yaml.load(match[1]);
    return frontmatter;
  } catch (error) {
    errors.push(`Invalid YAML frontmatter: ${error.message}`);
    return null;
  }
}

/**
 * Validate frontmatter fields
 * @param {Object} frontmatter - Parsed frontmatter
 * @param {Array} errors - Errors array
 * @param {Array} warnings - Warnings array
 */
function validateFrontmatterFields(frontmatter, errors, warnings) {
  // Check required fields
  for (const field of REQUIRED_FIELDS) {
    if (!frontmatter[field]) {
      errors.push(`Missing required field: ${field}`);
    } else {
      console.log(chalk.green(`✓ Required field present: ${field}`));
    }
  }
  
  // Check for unexpected fields
  const actualFields = Object.keys(frontmatter);
  for (const field of actualFields) {
    if (!ALLOWED_FIELDS.includes(field)) {
      errors.push(`Unexpected frontmatter field: ${field} (allowed: ${ALLOWED_FIELDS.join(', ')})`);
    }
  }
}

/**
 * Validate skill name
 * @param {string} name - Skill name from frontmatter
 * @param {string} dirname - Directory name
 * @param {Array} errors - Errors array
 * @param {Array} warnings - Warnings array
 */
function validateName(name, dirname, errors, warnings) {
  // Check hyphen-case format
  const hyphenCaseRegex = /^[a-z0-9]+(-[a-z0-9]+)*$/;
  if (!hyphenCaseRegex.test(name)) {
    errors.push(`Name must be hyphen-case (lowercase letters, numbers, hyphens only): "${name}"`);
  } else {
    console.log(chalk.green(`✓ Name format valid: ${name}`));
  }
  
  // Check max length
  if (name.length > 64) {
    errors.push(`Name exceeds 64 characters: "${name}" (${name.length} chars)`);
  }
  
  // Check matches directory name
  if (name !== dirname) {
    errors.push(`Name "${name}" does not match directory name "${dirname}"`);
  } else {
    console.log(chalk.green(`✓ Name matches directory: ${name}`));
  }
}

/**
 * Validate description completeness
 * @param {string} description - Description from frontmatter
 * @param {Array} errors - Errors array
 * @param {Array} warnings - Warnings array
 */
function validateDescription(description, errors, warnings) {
  // Check if description includes "when to use" context
  const whenRegex = /\b(use|when|trigger|invoke|call|run)\b/i;
  if (!whenRegex.test(description)) {
    warnings.push('Description should include "when to use" context (e.g., "Use when...", "Invoke when...")');
  } else {
    console.log(chalk.green('✓ Description includes usage context'));
  }
  
  // Check minimum length
  if (description.length < 20) {
    warnings.push('Description is very short. Consider adding more context.');
  }
}

/**
 * Check for forbidden files
 * @param {string} skillPath - Skill directory path
 * @param {Array} errors - Errors array
 * @param {Array} warnings - Warnings array
 */
async function checkForbiddenFiles(skillPath, errors, warnings) {
  for (const forbiddenFile of FORBIDDEN_FILES) {
    const forbiddenPath = path.join(skillPath, forbiddenFile);
    if (await fs.pathExists(forbiddenPath)) {
      errors.push(`Forbidden file/directory found: ${forbiddenFile}`);
    }
  }
  console.log(chalk.green('✓ No forbidden files found'));
}

/**
 * Check directory structure
 * @param {string} skillPath - Skill directory path
 * @param {Array} warnings - Warnings array
 */
async function checkDirectoryStructure(skillPath, warnings) {
  const optionalDirs = ['scripts', 'references', 'assets'];
  
  for (const dir of optionalDirs) {
    const dirPath = path.join(skillPath, dir);
    if (await fs.pathExists(dirPath)) {
      // Check if directory is empty
      const files = await fs.readdir(dirPath);
      if (files.length === 0) {
        warnings.push(`Directory ${dir}/ is empty. Consider deleting it.`);
      } else {
        console.log(chalk.green(`✓ Directory ${dir}/ exists and has content`));
      }
    }
  }
}

/**
 * Print validation results
 * @param {Array} errors - Errors array
 * @param {Array} warnings - Warnings array
 */
function printResults(errors, warnings) {
  console.log('\n' + '='.repeat(60));
  
  if (errors.length > 0) {
    console.log(chalk.red.bold(`\n✗ ${errors.length} ERROR(S) FOUND:\n`));
    errors.forEach((error, index) => {
      console.log(chalk.red(`  ${index + 1}. ${error}`));
    });
  }
  
  if (warnings.length > 0) {
    console.log(chalk.yellow.bold(`\n⚠ ${warnings.length} WARNING(S):\n`));
    warnings.forEach((warning, index) => {
      console.log(chalk.yellow(`  ${index + 1}. ${warning}`));
    });
  }
  
  if (errors.length === 0 && warnings.length === 0) {
    console.log(chalk.green.bold('\n✓ SKILL IS VALID!\n'));
  } else if (errors.length === 0) {
    console.log(chalk.yellow.bold('\n⚠ SKILL IS VALID (with warnings)\n'));
  } else {
    console.log(chalk.red.bold('\n✗ SKILL IS INVALID\n'));
  }
  
  console.log('='.repeat(60) + '\n');
}

// CLI execution
if (require.main === module) {
  const args = process.argv.slice(2);
  
  if (args.length === 0) {
    console.error(chalk.red('Usage: node validate.js <skill-directory>'));
    process.exit(1);
  }
  
  const skillPath = args[0];
  
  validateSkill(skillPath)
    .then(exitCode => {
      process.exit(exitCode);
    })
    .catch(error => {
      console.error(chalk.red(`Fatal error: ${error.message}`));
      process.exit(EXIT_ERROR);
    });
}

module.exports = { validateSkill };
