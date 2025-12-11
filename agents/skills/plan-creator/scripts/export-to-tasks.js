#!/usr/bin/env node

/**
 * Export plan checklist items to task list format
 * Converts implementation plan checklists into task tracking format
 */

const fs = require('fs-extra');
const path = require('path');
const yaml = require('js-yaml');
const chalk = require('chalk');

/**
 * Extracts frontmatter from markdown content
 * @param {string} content - Full markdown content
 * @returns {object|null} - Parsed frontmatter or null
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
    return null;
  }
}

/**
 * Extracts all checklist items organized by section
 * @param {string} content - Full markdown content
 * @returns {Array} - Array of { section, tasks } objects
 */
function extractChecklists(content) {
  const lines = content.split('\n');
  const sections = [];
  let currentSection = null;
  let currentTasks = [];

  for (const line of lines) {
    // Check for section header (## Level)
    const headerMatch = line.match(/^##\s+(.+)$/);
    if (headerMatch) {
      // Save previous section if it has tasks
      if (currentSection && currentTasks.length > 0) {
        sections.push({
          section: currentSection,
          tasks: [...currentTasks]
        });
      }
      
      // Start new section
      currentSection = headerMatch[1];
      currentTasks = [];
      continue;
    }

    // Check for subsection header (### Level)
    const subheaderMatch = line.match(/^###\s+(.+)$/);
    if (subheaderMatch) {
      // Save previous section if it has tasks
      if (currentSection && currentTasks.length > 0) {
        sections.push({
          section: currentSection,
          tasks: [...currentTasks]
        });
      }
      
      // Use subsection as new section
      currentSection = subheaderMatch[1];
      currentTasks = [];
      continue;
    }

    // Check for checklist item
    const checklistMatch = line.match(/^[\s]*-\s+\[([ xX])\]\s+(.+)$/);
    if (checklistMatch && currentSection) {
      const [, status, task] = checklistMatch;
      currentTasks.push({
        completed: status.toLowerCase() === 'x',
        task: task.trim()
      });
    }
  }

  // Save last section
  if (currentSection && currentTasks.length > 0) {
    sections.push({
      section: currentSection,
      tasks: currentTasks
    });
  }

  return sections;
}

/**
 * Converts checklist sections to task list format
 * @param {Array} sections - Array of section objects with tasks
 * @param {object} frontmatter - Plan frontmatter
 * @param {string} planPath - Original plan file path
 * @returns {string} - Formatted task list markdown
 */
function convertToTaskList(sections, frontmatter, planPath) {
  const planTitle = frontmatter?.title || 'Untitled Plan';
  const planType = frontmatter?.type || 'unknown';
  const author = frontmatter?.author || '@unknown';
  
  let output = `# Tasks from: ${planTitle}\n\n`;
  output += `**Source Plan**: \`${planPath}\`\n`;
  output += `**Type**: ${planType}\n`;
  output += `**Author**: ${author}\n`;
  output += `**Created**: ${frontmatter?.created || 'unknown'}\n\n`;
  output += `---\n\n`;

  let taskNumber = 1;
  let totalTasks = 0;
  let completedTasks = 0;

  for (const { section, tasks } of sections) {
    if (tasks.length === 0) continue;

    output += `## ${section}\n\n`;

    for (const { completed, task } of tasks) {
      const status = completed ? 'COMPLETED' : 'AVAILABLE';
      const checkbox = completed ? '[x]' : '[ ]';
      
      output += `### Task ${taskNumber}: ${task}\n\n`;
      output += `**Status**: [${status}]\n`;
      output += `**Checklist**: ${checkbox} ${task}\n`;
      output += `**Section**: ${section}\n\n`;

      taskNumber++;
      totalTasks++;
      if (completed) completedTasks++;
    }
  }

  // Add summary
  const percentComplete = totalTasks > 0 
    ? Math.round((completedTasks / totalTasks) * 100) 
    : 0;

  output += `---\n\n`;
  output += `## Summary\n\n`;
  output += `- **Total Tasks**: ${totalTasks}\n`;
  output += `- **Completed**: ${completedTasks}\n`;
  output += `- **Remaining**: ${totalTasks - completedTasks}\n`;
  output += `- **Progress**: ${percentComplete}%\n`;

  return output;
}

/**
 * Exports plan to task list format
 * @param {string} planPath - Path to plan file
 * @param {string} outputPath - Optional output path (defaults to same dir with -tasks suffix)
 */
async function exportToTasks(planPath, outputPath = null) {
  console.log(chalk.blue.bold('\n📤 Exporting Plan to Task List\n'));
  console.log(chalk.gray(`Plan: ${planPath}\n`));

  try {
    // Validate plan file exists
    if (!await fs.pathExists(planPath)) {
      throw new Error(`Plan file not found: ${planPath}`);
    }

    // Read plan content
    const content = await fs.readFile(planPath, 'utf8');

    // Extract frontmatter and checklists
    const frontmatter = extractFrontmatter(content);
    const sections = extractChecklists(content);

    if (sections.length === 0) {
      console.log(chalk.yellow('⚠️  No checklist items found in plan.\n'));
      return;
    }

    // Generate task list
    const taskList = convertToTaskList(sections, frontmatter, planPath);

    // Determine output path
    if (!outputPath) {
      const dir = path.dirname(planPath);
      const basename = path.basename(planPath, '.md');
      outputPath = path.join(dir, `${basename}-tasks.md`);
    }

    // Write task list
    await fs.writeFile(outputPath, taskList, 'utf8');

    console.log(chalk.green('✅ Task list exported successfully!\n'));
    console.log(chalk.gray(`   Output: ${outputPath}\n`));

    // Display summary
    const totalTasks = sections.reduce((sum, s) => sum + s.tasks.length, 0);
    const completedTasks = sections.reduce(
      (sum, s) => sum + s.tasks.filter(t => t.completed).length, 
      0
    );

    console.log(chalk.blue('📊 Export Summary:\n'));
    console.log(chalk.gray(`   Sections: ${sections.length}`));
    console.log(chalk.gray(`   Total Tasks: ${totalTasks}`));
    console.log(chalk.gray(`   Completed: ${completedTasks}`));
    console.log(chalk.gray(`   Remaining: ${totalTasks - completedTasks}\n`));

  } catch (error) {
    console.error(chalk.red.bold('\n❌ Export failed:\n'));
    console.error(chalk.red(`   ${error.message}\n`));
    process.exit(1);
  }
}

/**
 * CLI entry point
 */
async function main() {
  const args = process.argv.slice(2);

  if (args.length === 0) {
    console.log(chalk.yellow('\nUsage: npm run export <path-to-plan.md> [output-path.md]\n'));
    console.log(chalk.gray('Example: npm run export ../../plans/add-user-auth.md\n'));
    console.log(chalk.gray('Default output: <plan-name>-tasks.md in same directory\n'));
    process.exit(1);
  }

  const planPath = path.resolve(args[0]);
  const outputPath = args[1] ? path.resolve(args[1]) : null;

  await exportToTasks(planPath, outputPath);
}

// Run if called directly
if (require.main === module) {
  main();
}

module.exports = { exportToTasks, extractChecklists };
