#!/usr/bin/env node

/**
 * migrate-files.js - Migrates files and directories with git history preservation
 * 
 * Uses `git mv` to preserve file history when moving:
 * - agents/tools/ → agents/skills/
 * - agents/tasks/tasks.md → agents/plans/tasks.md
 * - agents/plans-local/ → agents/plans/local/
 */

const fs = require('fs-extra');
const path = require('path');
const { execSync } = require('child_process');
const chalk = require('chalk');

/**
 * Check if git is available and repo is initialized
 * @param {string} projectRoot - Project root directory
 * @returns {boolean}
 */
function isGitRepo(projectRoot) {
  try {
    execSync('git rev-parse --git-dir', {
      cwd: projectRoot,
      stdio: 'ignore'
    });
    return true;
  } catch (error) {
    return false;
  }
}

/**
 * Execute git mv command
 * @param {string} projectRoot - Project root
 * @param {string} from - Source path (relative to root)
 * @param {string} to - Destination path (relative to root)
 * @returns {boolean} Success
 */
function gitMove(projectRoot, from, to) {
  try {
    // Ensure destination directory exists
    const toDir = path.dirname(path.join(projectRoot, to));
    fs.ensureDirSync(toDir);

    execSync(`git mv "${from}" "${to}"`, {
      cwd: projectRoot,
      stdio: 'pipe'
    });
    console.log(chalk.gray(`   git mv: ${from} → ${to}`));
    return true;
  } catch (error) {
    console.warn(chalk.yellow(`   Failed git mv for ${from}: ${error.message}`));
    return false;
  }
}

/**
 * Fallback: regular move (no git history)
 * @param {string} projectRoot - Project root
 * @param {string} from - Source path
 * @param {string} to - Destination path
 */
async function regularMove(projectRoot, from, to) {
  const fromPath = path.join(projectRoot, from);
  const toPath = path.join(projectRoot, to);

  await fs.ensureDir(path.dirname(toPath));
  await fs.move(fromPath, toPath, { overwrite: false });
  console.log(chalk.gray(`   moved: ${from} → ${to}`));
}

/**
 * Migrate files according to analysis
 * @param {string} projectRoot - Root directory of the project
 * @param {object} analysis - Structure analysis results
 * @returns {Promise<object>} Migration results
 */
async function migrateFiles(projectRoot, analysis) {
  const results = {
    successful: [],
    failed: [],
    gitHistoryPreserved: false
  };

  const useGit = isGitRepo(projectRoot);
  results.gitHistoryPreserved = useGit;

  if (!useGit) {
    console.warn(chalk.yellow('   Not a git repository - history will not be preserved'));
  }

  for (const migration of analysis.migrations) {
    const { from, to } = migration;

    // Check if source exists
    if (!fs.existsSync(path.join(projectRoot, from))) {
      console.log(chalk.gray(`   Skipped (not found): ${from}`));
      continue;
    }

    // Check if destination already exists
    if (fs.existsSync(path.join(projectRoot, to))) {
      console.log(chalk.yellow(`   Skipped (exists): ${to}`));
      results.failed.push({ from, to, reason: 'destination exists' });
      continue;
    }

    try {
      if (useGit) {
        const success = gitMove(projectRoot, from, to);
        if (success) {
          results.successful.push({ from, to, method: 'git mv' });
        } else {
          // Fallback to regular move
          await regularMove(projectRoot, from, to);
          results.successful.push({ from, to, method: 'fs move' });
        }
      } else {
        await regularMove(projectRoot, from, to);
        results.successful.push({ from, to, method: 'fs move' });
      }
    } catch (error) {
      console.error(chalk.red(`   Error migrating ${from}: ${error.message}`));
      results.failed.push({ from, to, reason: error.message });
    }
  }

  // Clean up empty old directories
  const oldDirs = ['agents/tools', 'agents/tasks', 'agents/plans-local'];
  for (const oldDir of oldDirs) {
    const oldDirPath = path.join(projectRoot, oldDir);
    if (fs.existsSync(oldDirPath)) {
      const entries = await fs.readdir(oldDirPath);
      if (entries.length === 0) {
        await fs.remove(oldDirPath);
        console.log(chalk.gray(`   Removed empty: ${oldDir}/`));
      }
    }
  }

  // Update .gitignore
  const gitignorePath = path.join(projectRoot, '.gitignore');
  if (await fs.pathExists(gitignorePath)) {
    let content = await fs.readFile(gitignorePath, 'utf-8');
    
    // Replace old patterns with new
    if (content.includes('agents/plans-local/*')) {
      content = content.replace(/agents\/plans-local\/\*/g, 'agents/plans/local/*');
      content = content.replace(/!agents\/plans-local\/\.gitkeep/g, '!agents/plans/local/.gitkeep');
      await fs.writeFile(gitignorePath, content);
      console.log(chalk.gray('   Updated: .gitignore'));
    } else if (!content.includes('agents/plans/local/*')) {
      // Add new pattern if not present
      const newPattern = '\n# Local Agent Development Workflow - ephemeral plans\nagents/plans/local/*\n!agents/plans/local/.gitkeep\n';
      content = content.trimEnd() + newPattern;
      await fs.writeFile(gitignorePath, content);
      console.log(chalk.gray('   Updated: .gitignore (added ephemeral plans pattern)'));
    }
  }

  return results;
}

// Allow direct execution for testing
if (require.main === module) {
  const projectRoot = process.argv[2] || process.cwd();
  const analysis = {
    migrations: [
      { from: 'agents/tools', to: 'agents/skills', type: 'directory' },
      { from: 'agents/tasks/tasks.md', to: 'agents/plans/tasks.md', type: 'file' }
    ]
  };

  migrateFiles(projectRoot, analysis)
    .then(results => {
      console.log('Migration Results:');
      console.log(JSON.stringify(results, null, 2));
    })
    .catch(error => {
      console.error('Error migrating files:', error);
      process.exit(1);
    });
}

module.exports = migrateFiles;
