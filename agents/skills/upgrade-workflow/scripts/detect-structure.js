#!/usr/bin/env node

/**
 * detect-structure.js - Analyzes current framework structure
 * 
 * Detects old patterns and generates a migration plan:
 * - agents/tools/ → agents/skills/
 * - agents/tasks/ → agents/plans/ (tasks.md moved)
 * - agents/plans-local/ → agents/plans/local/
 * - Old claim-task.js script
 * - Old README.md structure
 */

const fs = require('fs-extra');
const path = require('path');
const glob = require('glob');

/**
 * Check if a path exists
 * @param {string} projectRoot - Project root
 * @param {string} relativePath - Path relative to root
 * @returns {boolean}
 */
function pathExists(projectRoot, relativePath) {
  return fs.existsSync(path.join(projectRoot, relativePath));
}

/**
 * Detect old structure patterns
 * @param {string} projectRoot - Root directory of the project
 * @returns {Promise<object>} Analysis results with migration plan
 */
async function detectStructure(projectRoot) {
  const analysis = {
    migrations: [],
    fileUpdates: [],
    newAdditions: [],
    legacyFiles: [],
    totalChanges: 0
  };

  // Check for old directory patterns
  const oldPatterns = {
    'agents/tools': 'agents/skills',
    'agents/tasks': 'agents/plans',
    'agents/plans-local': 'agents/plans/local'
  };

  for (const [oldPath, newPath] of Object.entries(oldPatterns)) {
    if (pathExists(projectRoot, oldPath)) {
      analysis.migrations.push({
        from: oldPath,
        to: newPath,
        type: 'directory'
      });
      analysis.totalChanges++;
    }
  }

  // Check for specific files that need migration
  const fileMigrations = {
    'agents/tasks/tasks.md': 'agents/plans/tasks.md',
    'agents/reference/tool-patterns.md': 'agents/reference/skill-patterns.md'
  };

  for (const [oldFile, newFile] of Object.entries(fileMigrations)) {
    if (pathExists(projectRoot, oldFile)) {
      analysis.migrations.push({
        from: oldFile,
        to: newFile,
        type: 'file'
      });
      analysis.totalChanges++;
    }
  }

  // Find all markdown files that might have references to update
  const mdFiles = glob.sync('**/*.md', {
    cwd: projectRoot,
    ignore: ['node_modules/**', '.git/**', 'agents/plans/local/**']
  });

  for (const mdFile of mdFiles) {
    const fullPath = path.join(projectRoot, mdFile);
    const content = await fs.readFile(fullPath, 'utf-8');
    
    // Check if file contains old patterns
    const hasOldReferences = 
      content.includes('agents/tools/') ||
      content.includes('agents/tasks/') ||
      content.includes('agents/plans-local/') ||
      /\btools?\b/.test(content); // Word boundaries for "tool" or "tools"
    
    if (hasOldReferences) {
      analysis.fileUpdates.push(mdFile);
      analysis.totalChanges++;
    }
  }

  // Check for old git skill claim-task.js
  const oldClaimTask = 'agents/tools/git/scripts/claim-task.js';
  if (pathExists(projectRoot, oldClaimTask)) {
    analysis.legacyFiles.push(oldClaimTask);
    analysis.totalChanges++;
  }

  // Check for new additions needed
  if (!pathExists(projectRoot, '.claude/skills')) {
    analysis.newAdditions.push('.claude/skills/ (Claude Skills symlinks)');
    analysis.totalChanges++;
  }

  if (!pathExists(projectRoot, '.claude/skills/README.md')) {
    analysis.newAdditions.push('.claude/skills/README.md');
    analysis.totalChanges++;
  }

  // Check if .gitignore needs updating
  const gitignorePath = path.join(projectRoot, '.gitignore');
  if (fs.existsSync(gitignorePath)) {
    const gitignoreContent = await fs.readFile(gitignorePath, 'utf-8');
    if (!gitignoreContent.includes('agents/plans/local/*')) {
      analysis.newAdditions.push('.gitignore (ephemeral plans pattern)');
      analysis.totalChanges++;
    }
  }

  return analysis;
}

// Allow direct execution for testing
if (require.main === module) {
  const projectRoot = process.argv[2] || process.cwd();
  detectStructure(projectRoot)
    .then(analysis => {
      console.log('Structure Analysis:');
      console.log(JSON.stringify(analysis, null, 2));
    })
    .catch(error => {
      console.error('Error detecting structure:', error);
      process.exit(1);
    });
}

module.exports = detectStructure;
