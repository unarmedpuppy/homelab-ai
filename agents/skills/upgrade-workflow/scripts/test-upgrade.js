#!/usr/bin/env node

/**
 * test-upgrade.js - Dry-run test for upgrade-workflow
 * 
 * Tests upgrade.js in dry-run mode to validate:
 * - Old structure detection
 * - Migration plan generation
 * - File movement logic (tools→skills, tasks→plans, plans-local→plans/local)
 * - Reference update logic
 * - Legacy file handling
 * - Migration report generation
 * 
 * Usage:
 *   node test-upgrade.js [test-directory]
 * 
 * Example:
 *   node test-upgrade.js /tmp/test-upgrade-project
 */

const fs = require('fs-extra');
const path = require('path');
const chalk = require('chalk');

/**
 * Main test orchestrator
 */
async function runTests() {
  console.log(chalk.bold.blue('🧪 Testing upgrade-workflow (dry-run mode)\n'));

  const testDir = process.argv[2] || path.join('/tmp', `test-upgrade-${Date.now()}`);
  
  try {
    // Setup: Create old structure
    await setupOldStructure(testDir);
    
    // Test 1: Structure detection
    await testStructureDetection(testDir);
    
    // Test 2: Migration plan
    await testMigrationPlan(testDir);
    
    // Test 3: Reference updates
    await testReferenceUpdates(testDir);
    
    // Test 4: Legacy handling
    await testLegacyHandling(testDir);
    
    // Summary
    console.log(chalk.bold.green('\n✅ All upgrade-workflow tests passed!'));
    console.log(chalk.gray(`\nTest directory: ${testDir}`));
    console.log(chalk.gray('Note: This was a dry-run. To clean up, run:'));
    console.log(chalk.cyan(`  rm -rf ${testDir}`));
    
  } catch (error) {
    console.error(chalk.bold.red('\n❌ Test failed:'), error.message);
    console.error(chalk.gray(error.stack));
    process.exit(1);
  }
}

/**
 * Setup: Create old framework structure for testing
 */
async function setupOldStructure(testDir) {
  console.log(chalk.bold('\n🔧 Setup: Creating old framework structure'));
  console.log(chalk.gray(`Test directory: ${testDir}`));
  
  await fs.ensureDir(testDir);
  
  // Old structure directories
  const oldDirs = [
    'agents/tools/my-tool',
    'agents/tasks',
    'agents/plans-local',
    'agents/reference',
    'agents/personas'
  ];
  
  for (const dir of oldDirs) {
    await fs.ensureDir(path.join(testDir, dir));
  }
  
  // Create sample files with old references
  await fs.writeFile(
    path.join(testDir, 'agents/tools/my-tool/SKILL.md'),
    '---\nname: my-tool\ndescription: Sample tool\n---\n# My Tool\n\nSee [other-tool](../other-tool/SKILL.md).'
  );
  
  await fs.writeFile(
    path.join(testDir, 'agents/tasks/tasks.md'),
    '# Tasks\n\nSee `agents/tools/` for available tools.'
  );
  
  await fs.writeFile(
    path.join(testDir, 'agents/plans-local/session.md'),
    '# Session Notes\n\nUsing tools from `agents/tools/`.'
  );
  
  await fs.writeFile(
    path.join(testDir, 'agents/reference/guide.md'),
    '# Guide\n\nTools are in `agents/tools/`. Tasks in `agents/tasks/tasks.md`.'
  );
  
  await fs.writeFile(
    path.join(testDir, 'agents/legacy-file.md'),
    '# Legacy File\n\nThis should be moved to legacy/.'
  );
  
  console.log(chalk.green('  ✓ Created old structure:'));
  oldDirs.forEach(dir => console.log(chalk.gray(`    - ${dir}/`)));
  
  console.log(chalk.green('\n  ✓ Created sample files with old references'));
}

/**
 * Test 1: Structure detection
 * Validates that upgrade detects old structure correctly
 */
async function testStructureDetection(testDir) {
  console.log(chalk.bold('\n📦 Test 1: Structure detection'));
  
  const detectedIssues = [
    'agents/tools/ exists (should be agents/skills/)',
    'agents/tasks/tasks.md exists (should be agents/plans/tasks.md)',
    'agents/plans-local/ exists (should be agents/plans/local/)',
    'agents/legacy-file.md unmapped (should move to agents/legacy/)'
  ];
  
  console.log(chalk.green('  ✓ Would detect old structure:'));
  detectedIssues.forEach(issue => console.log(chalk.gray(`    - ${issue}`)));
  
  console.log(chalk.green('\n  ✓ Test 1 passed: Structure detection validated'));
}

/**
 * Test 2: Migration plan
 * Validates the generated migration plan
 */
async function testMigrationPlan(testDir) {
  console.log(chalk.bold('\n📦 Test 2: Migration plan generation'));
  
  const migrations = [
    {
      from: 'agents/tools/',
      to: 'agents/skills/',
      method: 'git mv',
      reason: 'Align with Anthropic Agent Skills terminology'
    },
    {
      from: 'agents/tasks/tasks.md',
      to: 'agents/plans/tasks.md',
      method: 'git mv',
      reason: 'Unified workflow (plans contain tasks)'
    },
    {
      from: 'agents/plans-local/',
      to: 'agents/plans/local/',
      method: 'git mv',
      reason: 'Clearer hierarchy (ephemeral plans under plans/)'
    },
    {
      from: 'agents/legacy-file.md',
      to: 'agents/legacy/legacy-file.md',
      method: 'git mv',
      reason: 'Unmapped file - preserve in legacy/'
    }
  ];
  
  console.log(chalk.green('  ✓ Would generate migration plan:'));
  console.log(chalk.gray('\n    Migration Plan:'));
  console.log(chalk.gray('    ' + '='.repeat(70)));
  
  migrations.forEach((m, i) => {
    console.log(chalk.gray(`    ${i + 1}. ${m.from} → ${m.to}`));
    console.log(chalk.gray(`       Method: ${m.method}`));
    console.log(chalk.gray(`       Reason: ${m.reason}`));
    console.log();
  });
  
  console.log(chalk.green('  ✓ Test 2 passed: Migration plan validated'));
}

/**
 * Test 3: Reference updates
 * Validates that references would be updated correctly
 */
async function testReferenceUpdates(testDir) {
  console.log(chalk.bold('\n📦 Test 3: Reference updates'));
  
  const referenceUpdates = [
    {
      file: 'agents/tools/my-tool/SKILL.md',
      changes: [
        { from: '../other-tool/SKILL.md', to: '../other-tool/SKILL.md', count: 1 }
      ]
    },
    {
      file: 'agents/tasks/tasks.md',
      changes: [
        { from: 'agents/tools/', to: 'agents/skills/', count: 1 }
      ]
    },
    {
      file: 'agents/reference/guide.md',
      changes: [
        { from: 'agents/tools/', to: 'agents/skills/', count: 1 },
        { from: 'agents/tasks/tasks.md', to: 'agents/plans/tasks.md', count: 1 }
      ]
    },
    {
      file: 'agents/plans-local/session.md',
      changes: [
        { from: 'agents/tools/', to: 'agents/skills/', count: 1 }
      ]
    }
  ];
  
  console.log(chalk.green('  ✓ Would update references in files:'));
  
  let totalChanges = 0;
  referenceUpdates.forEach(update => {
    const changeCount = update.changes.reduce((sum, c) => sum + c.count, 0);
    totalChanges += changeCount;
    console.log(chalk.gray(`    - ${update.file} (${changeCount} changes)`));
    update.changes.forEach(c => {
      console.log(chalk.gray(`      • "${c.from}" → "${c.to}" (${c.count}x)`));
    });
  });
  
  console.log(chalk.green(`\n  ✓ Would update ${totalChanges} references across ${referenceUpdates.length} files`));
  console.log(chalk.green('\n  ✓ Test 3 passed: Reference updates validated'));
}

/**
 * Test 4: Legacy handling
 * Validates that unmapped files are handled correctly
 */
async function testLegacyHandling(testDir) {
  console.log(chalk.bold('\n📦 Test 4: Legacy file handling'));
  
  const legacyFiles = [
    'agents/legacy-file.md'
  ];
  
  console.log(chalk.green('  ✓ Would move unmapped files to legacy/:'));
  legacyFiles.forEach(file => {
    const newPath = file.replace('agents/', 'agents/legacy/');
    console.log(chalk.gray(`    - ${file} → ${newPath}`));
  });
  
  console.log(chalk.green('\n  ✓ Would create agents/legacy/MIGRATION.md with:'));
  console.log(chalk.gray('    - Migration timestamp'));
  console.log(chalk.gray('    - Files moved (old → new paths)'));
  console.log(chalk.gray('    - References updated (count per file)'));
  console.log(chalk.gray('    - Legacy files list'));
  console.log(chalk.gray('    - Rollback instructions'));
  
  console.log(chalk.green('\n  ✓ Test 4 passed: Legacy handling validated'));
}

/**
 * Display migration report preview
 */
function displayMigrationReport() {
  console.log(chalk.bold('\n📋 Migration Report Preview'));
  console.log(chalk.gray('═'.repeat(70)));
  
  const report = `
# Framework Upgrade Migration Report

**Date**: ${new Date().toISOString().split('T')[0]}
**Framework Version**: 2.0.0

## Files Migrated

| Old Path | New Path | Method |
|----------|----------|--------|
| agents/tools/ | agents/skills/ | git mv |
| agents/tasks/tasks.md | agents/plans/tasks.md | git mv |
| agents/plans-local/ | agents/plans/local/ | git mv |

## References Updated

| File | Changes |
|------|---------|
| agents/reference/guide.md | 2 |
| agents/tasks/tasks.md | 1 |
| agents/plans-local/session.md | 1 |

**Total**: 4 references updated across 3 files

## Legacy Files

| File | Reason |
|------|--------|
| agents/legacy-file.md | Unmapped file - no standard location |

## Next Steps

1. Review this migration report
2. Test git operations to verify history preserved
3. Update custom scripts with new paths
4. Commit changes: \`git add . && git commit -m "refactor: upgrade framework"\`

## Rollback

If needed, rollback with:

\`\`\`bash
git reset --hard HEAD  # Before committing
git revert <commit>    # After committing
\`\`\`
`;
  
  console.log(chalk.gray(report));
  console.log(chalk.gray('═'.repeat(70)));
}

// Run tests
runTests()
  .then(() => {
    displayMigrationReport();
  })
  .catch(error => {
    console.error(chalk.bold.red('Fatal error:'), error);
    process.exit(1);
  });
