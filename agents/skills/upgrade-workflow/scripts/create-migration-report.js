#!/usr/bin/env node

/**
 * create-migration-report.js - Generates comprehensive migration report
 * 
 * Creates agents/legacy/MIGRATION.md documenting:
 * - Files moved (old → new paths)
 * - References updated (count per file)
 * - Legacy files requiring manual review
 * - Rollback instructions
 * - Next steps
 */

const fs = require('fs-extra');
const path = require('path');
const chalk = require('chalk');

/**
 * Generate migration report content
 * @param {object} data - Migration data
 * @returns {string} Markdown content
 */
function generateReportContent(data) {
  const { analysis, migrationResults, updateResults, legacyResults } = data;
  const date = new Date().toISOString().split('T')[0];

  let report = `# Local Agent Development Workflow - Migration Report

**Date**: ${date}
**Status**: ${migrationResults.failed.length === 0 ? '✅ Complete' : '⚠️ Complete with warnings'}

## Overview

This report documents the automatic upgrade of the Local Agent Development Workflow framework from the old structure to the new skills-based architecture.

### Summary

- **Directories migrated**: ${analysis.migrations.filter(m => m.type === 'directory').length}
- **Files migrated**: ${analysis.migrations.filter(m => m.type === 'file').length}
- **Files updated**: ${updateResults.filesUpdated}
- **Total reference changes**: ${updateResults.totalReplacements}
- **Legacy files moved**: ${legacyResults ? legacyResults.filesMoved : 0}
- **Git history preserved**: ${migrationResults.gitHistoryPreserved ? 'Yes' : 'No'}

## Files Moved

### Directory Migrations

`;

  // Directory migrations
  const dirMigrations = migrationResults.successful.filter(m => 
    analysis.migrations.find(am => am.from === m.from && am.type === 'directory')
  );
  
  if (dirMigrations.length > 0) {
    report += '| Old Path | New Path | Method |\n';
    report += '|----------|----------|--------|\n';
    for (const migration of dirMigrations) {
      report += `| \`${migration.from}\` | \`${migration.to}\` | ${migration.method} |\n`;
    }
  } else {
    report += '*No directory migrations were needed.*\n';
  }

  report += '\n### File Migrations\n\n';

  // File migrations
  const fileMigrations = migrationResults.successful.filter(m => 
    analysis.migrations.find(am => am.from === m.from && am.type === 'file')
  );
  
  if (fileMigrations.length > 0) {
    report += '| Old Path | New Path | Method |\n';
    report += '|----------|----------|--------|\n';
    for (const migration of fileMigrations) {
      report += `| \`${migration.from}\` | \`${migration.to}\` | ${migration.method} |\n`;
    }
  } else {
    report += '*No file migrations were needed.*\n';
  }

  // Failed migrations
  if (migrationResults.failed.length > 0) {
    report += '\n### ⚠️ Failed Migrations\n\n';
    report += '| Path | Reason |\n';
    report += '|------|--------|\n';
    for (const failure of migrationResults.failed) {
      report += `| \`${failure.from}\` | ${failure.reason} |\n`;
    }
    report += '\n*These files may need manual attention.*\n';
  }

  // Reference updates
  report += '\n## References Updated\n\n';
  
  if (updateResults.details.length > 0) {
    report += `Updated ${updateResults.filesUpdated} files with ${updateResults.totalReplacements} total changes:\n\n`;
    report += '| File | Changes |\n';
    report += '|------|--------:|\n';
    for (const detail of updateResults.details) {
      report += `| \`${detail.file}\` | ${detail.replacements} |\n`;
    }
  } else {
    report += '*No reference updates were needed.*\n';
  }

  // Legacy files
  if (legacyResults && legacyResults.movedFiles && legacyResults.movedFiles.length > 0) {
    report += '\n## Legacy Files (Manual Review Needed)\n\n';
    report += 'The following files were moved to `agents/legacy/` because they don\'t fit the new structure:\n\n';
    report += '| Original Path | Legacy Path |\n';
    report += '|---------------|-------------|\n';
    for (const moved of legacyResults.movedFiles) {
      report += `| \`${moved.from}\` | \`${moved.to}\` |\n`;
    }
    report += '\n**Action Required**: Review these files and decide whether to:\n';
    report += '- Update them to match the new structure\n';
    report += '- Keep them as legacy documentation\n';
    report += '- Delete them if no longer needed\n';
  }

  // Next steps
  report += '\n## Next Steps\n\n';
  report += '1. **Review this report** - Understand what changed\n';
  report += '2. **Check agents/legacy/** - Review files that need manual attention\n';
  report += '3. **Test workflows** - Ensure everything still works\n';
  report += '4. **Update custom scripts** - If you have custom tooling, update paths\n';
  report += '5. **Commit changes** - Save the upgraded framework:\n';
  report += '   ```bash\n';
  report += '   git add .\n';
  report += '   git commit -m "refactor: upgrade agent workflow framework"\n';
  report += '   ```\n';
  report += '6. **(Optional) Enable Claude Skills** - In VS Code settings:\n';
  report += '   ```json\n';
  report += '   "chat.useClaudeSkills": true\n';
  report += '   ```\n';

  // Rollback instructions
  report += '\n## Rollback Instructions\n\n';
  report += '### Before Committing\n\n';
  report += 'If you haven\'t committed yet, you can reset:\n\n';
  report += '```bash\n';
  report += 'git reset --hard HEAD\n';
  report += '```\n\n';
  
  report += '### After Committing\n\n';
  report += 'If you\'ve already committed, you can revert:\n\n';
  report += '```bash\n';
  report += '# Find the commit hash\n';
  report += 'git log --oneline\n\n';
  report += '# Revert the upgrade commit\n';
  report += 'git revert <commit-hash>\n';
  report += '```\n\n';
  
  if (migrationResults.gitHistoryPreserved) {
    report += '### Manual Rollback\n\n';
    report += 'You can also manually undo the migrations:\n\n';
    report += '```bash\n';
    for (const migration of migrationResults.successful) {
      report += `git mv "${migration.to}" "${migration.from}"\n`;
    }
    report += '```\n';
  }

  // Footer
  report += '\n---\n\n';
  report += `*Migration report generated by upgrade-workflow skill on ${date}*\n`;

  return report;
}

/**
 * Create migration report file
 * @param {string} projectRoot - Root directory of the project
 * @param {object} data - Migration data
 * @returns {Promise<string>} Path to created report
 */
async function createMigrationReport(projectRoot, data) {
  const reportPath = path.join(projectRoot, 'agents/legacy/MIGRATION.md');
  const reportContent = generateReportContent(data);

  await fs.ensureDir(path.dirname(reportPath));
  await fs.writeFile(reportPath, reportContent, 'utf-8');

  return path.relative(projectRoot, reportPath);
}

// Allow direct execution for testing
if (require.main === module) {
  const projectRoot = process.argv[2] || process.cwd();
  const testData = {
    analysis: {
      migrations: [
        { from: 'agents/tools', to: 'agents/skills', type: 'directory' }
      ]
    },
    migrationResults: {
      successful: [
        { from: 'agents/tools', to: 'agents/skills', method: 'git mv' }
      ],
      failed: [],
      gitHistoryPreserved: true
    },
    updateResults: {
      filesUpdated: 5,
      totalReplacements: 12,
      details: [
        { file: 'AGENTS.md', replacements: 3 }
      ]
    },
    legacyResults: {
      filesMoved: 1,
      movedFiles: [
        { from: 'agents/tools/git/scripts/claim-task.js', to: 'agents/legacy/tools/git/scripts/claim-task.js' }
      ]
    }
  };

  createMigrationReport(projectRoot, testData)
    .then(reportPath => {
      console.log(`Migration report created: ${reportPath}`);
    })
    .catch(error => {
      console.error('Error creating report:', error);
      process.exit(1);
    });
}

module.exports = createMigrationReport;
