#!/usr/bin/env node

/**
 * update-references.js - Updates internal references in markdown files
 * 
 * Finds and replaces old paths and terminology:
 * - agents/tools/ → agents/skills/
 * - agents/tasks/ → agents/plans/
 * - agents/plans-local/ → agents/plans/local/
 * - "tool" → "skill" (contextual, not blind replace)
 */

const fs = require('fs-extra');
const path = require('path');
const chalk = require('chalk');

/**
 * Reference replacement patterns
 * Order matters - more specific patterns first
 */
const REPLACEMENTS = [
  // Path replacements
  { pattern: /agents\/tools\//g, replacement: 'agents/skills/', description: 'paths: agents/tools/ → agents/skills/' },
  { pattern: /agents\/tasks\//g, replacement: 'agents/plans/', description: 'paths: agents/tasks/ → agents/plans/' },
  { pattern: /agents\/plans-local\//g, replacement: 'agents/plans/local/', description: 'paths: agents/plans-local/ → agents/plans/local/' },
  
  // Specific file references
  { pattern: /agents\/tasks\/tasks\.md/g, replacement: 'agents/plans/tasks.md', description: 'file: tasks.md location' },
  { pattern: /agents\/reference\/tool-patterns\.md/g, replacement: 'agents/reference/skill-patterns.md', description: 'file: tool-patterns.md → skill-patterns.md' },
  
  // Directory references (no trailing slash)
  { pattern: /`agents\/tools`/g, replacement: '`agents/skills`', description: 'dir ref: agents/tools' },
  { pattern: /`agents\/tasks`/g, replacement: '`agents/plans`', description: 'dir ref: agents/tasks' },
  { pattern: /`agents\/plans-local`/g, replacement: '`agents/plans/local`', description: 'dir ref: agents/plans-local' },
  
  // Terminology in specific contexts (more careful)
  { pattern: /tool-patterns\.md/g, replacement: 'skill-patterns.md', description: 'filename: tool-patterns' },
  { pattern: /tools\/ directory/g, replacement: 'skills/ directory', description: 'phrase: tools/ directory' },
  { pattern: /\btools\/\b/g, replacement: 'skills/', description: 'word: tools/' },
  
  // Headings and titles
  { pattern: /# Tools/g, replacement: '# Skills', description: 'heading: Tools' },
  { pattern: /## Tools/g, replacement: '## Skills', description: 'heading: Tools' },
  { pattern: /### Tools/g, replacement: '### Skills', description: 'heading: Tools' },
];

/**
 * Update references in a single file
 * @param {string} filePath - Absolute path to the file
 * @returns {Promise<object>} Update results
 */
async function updateFileReferences(filePath) {
  const content = await fs.readFile(filePath, 'utf-8');
  let updatedContent = content;
  const appliedReplacements = [];

  for (const { pattern, replacement, description } of REPLACEMENTS) {
    const before = updatedContent;
    updatedContent = updatedContent.replace(pattern, replacement);
    
    if (updatedContent !== before) {
      appliedReplacements.push(description);
    }
  }

  if (appliedReplacements.length > 0) {
    await fs.writeFile(filePath, updatedContent, 'utf-8');
    return {
      updated: true,
      replacements: appliedReplacements.length
    };
  }

  return {
    updated: false,
    replacements: 0
  };
}

/**
 * Update references across all relevant files
 * @param {string} projectRoot - Root directory of the project
 * @param {object} analysis - Structure analysis results
 * @returns {Promise<object>} Update results
 */
async function updateReferences(projectRoot, analysis) {
  const results = {
    filesUpdated: 0,
    filesSkipped: 0,
    totalReplacements: 0,
    details: []
  };

  for (const relativeFilePath of analysis.fileUpdates) {
    const fullPath = path.join(projectRoot, relativeFilePath);

    // Skip if file doesn't exist
    if (!await fs.pathExists(fullPath)) {
      console.log(chalk.gray(`   Skipped (not found): ${relativeFilePath}`));
      results.filesSkipped++;
      continue;
    }

    try {
      const updateResult = await updateFileReferences(fullPath);
      
      if (updateResult.updated) {
        console.log(chalk.gray(`   Updated: ${relativeFilePath} (${updateResult.replacements} changes)`));
        results.filesUpdated++;
        results.totalReplacements += updateResult.replacements;
        results.details.push({
          file: relativeFilePath,
          replacements: updateResult.replacements
        });
      } else {
        results.filesSkipped++;
      }
    } catch (error) {
      console.error(chalk.red(`   Error updating ${relativeFilePath}: ${error.message}`));
      results.filesSkipped++;
    }
  }

  // Also update breadcrumb files if they exist
  const breadcrumbs = ['CLAUDE.md', 'GEMINI.md', '.cursor/rules/project.mdc', '.github/copilot-instructions.md'];
  for (const breadcrumb of breadcrumbs) {
    const breadcrumbPath = path.join(projectRoot, breadcrumb);
    if (await fs.pathExists(breadcrumbPath)) {
      try {
        const updateResult = await updateFileReferences(breadcrumbPath);
        if (updateResult.updated) {
          console.log(chalk.gray(`   Updated breadcrumb: ${breadcrumb}`));
          results.filesUpdated++;
          results.totalReplacements += updateResult.replacements;
        }
      } catch (error) {
        console.warn(chalk.yellow(`   Warning: Could not update ${breadcrumb}: ${error.message}`));
      }
    }
  }

  return results;
}

// Allow direct execution for testing
if (require.main === module) {
  const projectRoot = process.argv[2] || process.cwd();
  const testFilePath = process.argv[3];

  if (testFilePath) {
    // Test single file
    updateFileReferences(path.join(projectRoot, testFilePath))
      .then(result => {
        console.log('Update Result:');
        console.log(JSON.stringify(result, null, 2));
      })
      .catch(error => {
        console.error('Error:', error);
        process.exit(1);
      });
  } else {
    console.error('Usage: node update-references.js <projectRoot> <testFile>');
    process.exit(1);
  }
}

module.exports = updateReferences;
