#!/usr/bin/env node

/**
 * migrate-legacy.js - Handles unmapped files by moving them to agents/legacy/
 * 
 * Moves files that don't fit the new structure to a legacy directory
 * with documentation of what was moved and why.
 */

const fs = require('fs-extra');
const path = require('path');
const chalk = require('chalk');

/**
 * Migrate legacy files to agents/legacy/
 * @param {string} projectRoot - Root directory of the project
 * @param {object} analysis - Structure analysis results
 * @returns {Promise<object>} Migration results
 */
async function migrateLegacy(projectRoot, analysis) {
  const results = {
    filesMoved: 0,
    errors: [],
    movedFiles: []
  };

  const legacyDir = path.join(projectRoot, 'agents/legacy');
  await fs.ensureDir(legacyDir);

  for (const legacyFile of analysis.legacyFiles) {
    const sourcePath = path.join(projectRoot, legacyFile);

    // Skip if file doesn't exist
    if (!await fs.pathExists(sourcePath)) {
      console.log(chalk.gray(`   Skipped (not found): ${legacyFile}`));
      continue;
    }

    try {
      // Preserve directory structure within legacy/
      // e.g., agents/tools/git/scripts/claim-task.js → agents/legacy/tools/git/scripts/claim-task.js
      const relativePath = legacyFile.startsWith('agents/') 
        ? legacyFile.substring('agents/'.length)
        : legacyFile;
      
      const destPath = path.join(legacyDir, relativePath);
      
      // Ensure destination directory exists
      await fs.ensureDir(path.dirname(destPath));
      
      // Move file
      await fs.move(sourcePath, destPath, { overwrite: false });
      
      console.log(chalk.gray(`   Moved to legacy: ${legacyFile}`));
      results.filesMoved++;
      results.movedFiles.push({
        from: legacyFile,
        to: path.relative(projectRoot, destPath)
      });
      
    } catch (error) {
      console.error(chalk.red(`   Error moving ${legacyFile}: ${error.message}`));
      results.errors.push({
        file: legacyFile,
        error: error.message
      });
    }
  }

  return results;
}

// Allow direct execution for testing
if (require.main === module) {
  const projectRoot = process.argv[2] || process.cwd();
  const analysis = {
    legacyFiles: ['agents/tools/git/scripts/claim-task.js']
  };

  migrateLegacy(projectRoot, analysis)
    .then(results => {
      console.log('Legacy Migration Results:');
      console.log(JSON.stringify(results, null, 2));
    })
    .catch(error => {
      console.error('Error migrating legacy files:', error);
      process.exit(1);
    });
}

module.exports = migrateLegacy;
