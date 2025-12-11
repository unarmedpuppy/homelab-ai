#!/usr/bin/env node

/**
 * upgrade.js - Main orchestrator for upgrade-workflow skill
 * 
 * Coordinates the complete framework upgrade process:
 * 1. Detects current structure and generates migration plan
 * 2. Confirms changes with user (unless --auto flag)
 * 3. Migrates files using git mv to preserve history
 * 4. Updates all internal references (paths, terminology)
 * 5. Handles legacy/unmapped files
 * 6. Creates Claude Skills symlinks
 * 7. Generates comprehensive migration report
 */

const fs = require('fs-extra');
const path = require('path');
const chalk = require('chalk');
const readline = require('readline');
const detectStructure = require('./detect-structure');
const migrateFiles = require('./migrate-files');
const updateReferences = require('./update-references');
const migrateLegacy = require('./migrate-legacy');
const createMigrationReport = require('./create-migration-report');

// Reuse create-symlinks from scaffold-workflow
const createSymlinks = require('../../scaffold-workflow/scripts/create-symlinks');

/**
 * Parse command line arguments
 * @returns {object} Parsed options
 */
function parseArgs() {
  const args = process.argv.slice(2);
  return {
    dryRun: args.includes('--dry-run'),
    auto: args.includes('--auto'),
    projectRoot: args.find(arg => !arg.startsWith('--')) || process.cwd()
  };
}

/**
 * Prompt user for confirmation
 * @param {string} question - Question to ask
 * @returns {Promise<boolean>} True if user confirms
 */
function askConfirmation(question) {
  const rl = readline.createInterface({
    input: process.stdin,
    output: process.stdout
  });

  return new Promise(resolve => {
    rl.question(question + ' (y/N): ', answer => {
      rl.close();
      resolve(answer.toLowerCase() === 'y' || answer.toLowerCase() === 'yes');
    });
  });
}

/**
 * Check if git repository is clean
 * @param {string} projectRoot - Project root directory
 * @returns {boolean} True if clean
 */
function isGitClean(projectRoot) {
  try {
    const { execSync } = require('child_process');
    const output = execSync('git status --porcelain', {
      cwd: projectRoot,
      encoding: 'utf-8'
    });
    return output.trim().length === 0;
  } catch (error) {
    // Not a git repo or git not available
    return true; // Don't block upgrade
  }
}

/**
 * Display migration plan summary
 * @param {object} analysis - Structure analysis results
 */
function displayMigrationPlan(analysis) {
  console.log(chalk.cyan.bold('\n📋 Migration Plan:\n'));

  if (analysis.migrations.length > 0) {
    console.log(chalk.yellow('Directory Migrations:'));
    analysis.migrations.forEach(m => {
      console.log(chalk.white(`  ${m.from} → ${m.to}`));
    });
  }

  if (analysis.fileUpdates.length > 0) {
    console.log(chalk.yellow('\nFile Updates:'));
    console.log(chalk.white(`  ${analysis.fileUpdates.length} files will be updated`));
  }

  if (analysis.newAdditions.length > 0) {
    console.log(chalk.yellow('\nNew Additions:'));
    analysis.newAdditions.forEach(item => {
      console.log(chalk.white(`  ${item}`));
    });
  }

  if (analysis.legacyFiles.length > 0) {
    console.log(chalk.yellow('\nLegacy Files (will move to agents/legacy/):'));
    analysis.legacyFiles.forEach(file => {
      console.log(chalk.white(`  ${file}`));
    });
  }

  console.log(chalk.gray(`\nEstimated changes: ${analysis.totalChanges} operations`));
}

/**
 * Main upgrade function
 * @param {string} projectRoot - Root directory of the project
 * @param {object} options - Upgrade options
 */
async function upgrade(projectRoot = process.cwd(), options = {}) {
  const { dryRun = false, auto = false } = options;

  console.log(chalk.blue.bold('\n🔄 Upgrading Local Agent Development Workflow\n'));

  // Step 1: Verify agents/ directory exists
  const agentsDir = path.join(projectRoot, 'agents');
  if (!fs.existsSync(agentsDir)) {
    console.error(chalk.red('❌ Error: No agents/ directory found!'));
    console.error(chalk.yellow('   Use scaffold-workflow skill to create a new framework.'));
    process.exit(1);
  }

  // Step 2: Check git status
  if (!isGitClean(projectRoot)) {
    console.warn(chalk.yellow('⚠️  Warning: Git working directory has uncommitted changes.'));
    console.warn(chalk.white('   Recommend committing or stashing changes before upgrade.'));
    if (!auto) {
      const proceed = await askConfirmation('\nContinue anyway?');
      if (!proceed) {
        console.log(chalk.gray('Upgrade cancelled.'));
        process.exit(0);
      }
    }
  }

  try {
    // Step 3: Detect current structure
    console.log(chalk.cyan('🔍 Analyzing current structure...'));
    const analysis = await detectStructure(projectRoot);
    console.log(chalk.green('   ✓ Analysis complete'));

    // Check if upgrade is needed
    if (analysis.totalChanges === 0) {
      console.log(chalk.green.bold('\n✅ Framework is already up to date!\n'));
      console.log(chalk.white('No changes needed.'));
      return;
    }

    // Step 4: Display migration plan and confirm
    displayMigrationPlan(analysis);

    if (dryRun) {
      console.log(chalk.yellow.bold('\n🔍 Dry-run mode: No changes applied\n'));
      return;
    }

    if (!auto) {
      console.log();
      const proceed = await askConfirmation(chalk.cyan('Proceed with upgrade?'));
      if (!proceed) {
        console.log(chalk.gray('\nUpgrade cancelled.'));
        process.exit(0);
      }
    }

    // Step 5: Execute migration
    console.log(chalk.cyan('\n📦 Migrating files...'));
    const migrationResults = await migrateFiles(projectRoot, analysis);
    console.log(chalk.green('   ✓ Files migrated'));

    // Step 6: Update references
    console.log(chalk.cyan('\n📝 Updating references...'));
    const updateResults = await updateReferences(projectRoot, analysis);
    console.log(chalk.green(`   ✓ Updated ${updateResults.filesUpdated} files`));

    // Step 7: Handle legacy files
    if (analysis.legacyFiles.length > 0) {
      console.log(chalk.cyan('\n📂 Moving legacy files...'));
      const legacyResults = await migrateLegacy(projectRoot, analysis);
      console.log(chalk.green(`   ✓ Moved ${legacyResults.filesMoved} files to agents/legacy/`));
    }

    // Step 8: Create symlinks
    console.log(chalk.cyan('\n🔗 Creating Claude Skills symlinks...'));
    await createSymlinks(projectRoot);
    console.log(chalk.green('   ✓ Symlinks created'));

    // Step 9: Generate migration report
    console.log(chalk.cyan('\n📄 Generating migration report...'));
    const reportPath = await createMigrationReport(projectRoot, {
      analysis,
      migrationResults,
      updateResults,
      legacyResults: analysis.legacyFiles.length > 0 ? { filesMoved: analysis.legacyFiles.length } : null
    });
    console.log(chalk.green(`   ✓ Report saved: ${reportPath}`));

    // Step 10: Success message
    console.log(chalk.green.bold('\n✅ Framework upgrade complete!\n'));
    console.log(chalk.cyan('Next steps:'));
    console.log(chalk.white('  1. Review migration report: agents/legacy/MIGRATION.md'));
    console.log(chalk.white('  2. Check agents/legacy/ for files needing manual review'));
    console.log(chalk.white('  3. Test your workflows to ensure everything works'));
    console.log(chalk.white('  4. Commit changes: git add . && git commit -m "refactor: upgrade agent workflow"'));
    console.log(chalk.white('  5. (Optional) Enable Claude Skills: chat.useClaudeSkills = true\n'));

  } catch (error) {
    console.error(chalk.red.bold('\n❌ Upgrade failed!\n'));
    console.error(chalk.red(`Error: ${error.message}`));
    console.error(chalk.yellow('\nStack trace:'));
    console.error(error.stack);
    console.error(chalk.yellow('\nYou may need to manually revert changes.'));
    process.exit(1);
  }
}

// Run upgrade if called directly
if (require.main === module) {
  const options = parseArgs();
  upgrade(options.projectRoot, options).catch(error => {
    console.error(chalk.red('Fatal error:'), error);
    process.exit(1);
  });
}

module.exports = upgrade;
