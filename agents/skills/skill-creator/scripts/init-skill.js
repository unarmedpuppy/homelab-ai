#!/usr/bin/env node

/**
 * Initialize a new Anthropic-compliant skill
 * Interactive prompts for skill creation
 */

const fs = require('fs-extra');
const path = require('path');
const inquirer = require('inquirer');
const chalk = require('chalk');
const { validateSkill } = require('./validate');

/**
 * Validate skill name format
 * @param {string} name - Skill name
 * @returns {boolean|string} - true if valid, error message if invalid
 */
function validateNameFormat(name) {
  const hyphenCaseRegex = /^[a-z0-9]+(-[a-z0-9]+)*$/;
  
  if (!name) {
    return 'Name is required';
  }
  
  if (!hyphenCaseRegex.test(name)) {
    return 'Name must be hyphen-case (lowercase letters, numbers, hyphens only)';
  }
  
  if (name.length > 64) {
    return `Name must be 64 characters or less (current: ${name.length})`;
  }
  
  return true;
}

/**
 * Validate description completeness
 * @param {string} description - Description
 * @returns {boolean|string} - true if valid, error message if invalid
 */
function validateDescriptionFormat(description) {
  if (!description) {
    return 'Description is required';
  }
  
  if (description.length < 20) {
    return 'Description should be at least 20 characters';
  }
  
  // Check for "when to use" context
  const whenRegex = /\b(use|when|trigger|invoke|call|run)\b/i;
  if (!whenRegex.test(description)) {
    return 'Description should include "when to use" context (e.g., "Use when...")';
  }
  
  return true;
}

/**
 * Create skill directory and files
 * @param {string} name - Skill name
 * @param {string} description - Skill description
 * @param {string} targetDir - Target directory (default: current/../../<name>)
 */
async function createSkill(name, description, targetDir = null) {
  console.log(chalk.blue('\n📦 Creating skill...\n'));
  
  // Determine target directory
  if (!targetDir) {
    // Default: agents/skills/<name>
    const currentDir = process.cwd();
    // Assuming we're in agents/skills/skill-creator
    const skillsDir = path.resolve(currentDir, '..');
    targetDir = path.join(skillsDir, name);
  }
  
  try {
    // Check if directory already exists
    if (await fs.pathExists(targetDir)) {
      throw new Error(`Directory already exists: ${targetDir}`);
    }
    
    // Create directory structure
    await fs.ensureDir(targetDir);
    await fs.ensureDir(path.join(targetDir, 'scripts'));
    console.log(chalk.green(`✓ Created ${targetDir}/`));
    console.log(chalk.green(`✓ Created ${targetDir}/scripts/`));
    
    // Create SKILL.md with frontmatter
    const skillMdContent = `---
name: ${name}
description: ${description}
---

# ${name.split('-').map(word => word.charAt(0).toUpperCase() + word.slice(1)).join(' ')}

Brief overview of what this skill does.

## Usage

Describe how to use this skill step-by-step.

\`\`\`bash
# Example command
npm run some-command
\`\`\`

## Examples

Provide concrete examples with expected output.

## Troubleshooting

Common issues and solutions.

## Resources

- [scripts/](scripts/) - Executable scripts
- Add references to other resources as needed
`;
    
    await fs.writeFile(path.join(targetDir, 'SKILL.md'), skillMdContent);
    console.log(chalk.green(`✓ Created SKILL.md with proper frontmatter`));
    
    // Create a basic package.json
    const packageJson = {
      name,
      version: '1.0.0',
      description,
      scripts: {}
    };
    
    await fs.writeFile(
      path.join(targetDir, 'scripts', 'package.json'),
      JSON.stringify(packageJson, null, 2)
    );
    console.log(chalk.green(`✓ Created scripts/package.json`));
    
    // Create README note in scripts directory
    const scriptsReadme = `# Scripts

Add executable scripts here for deterministic operations.

## Guidelines

- Keep scripts focused and modular
- Use any language (JavaScript, Python, Bash, etc.)
- Document usage in main SKILL.md
- Provide clear error messages
`;
    
    await fs.writeFile(path.join(targetDir, 'scripts', 'README.md'), scriptsReadme);
    console.log(chalk.green(`✓ Created scripts/README.md (helper, will be removed for compliance)`));
    
    console.log(chalk.blue('\n🔍 Validating new skill...\n'));
    
    // First, remove scripts/README.md for validation
    await fs.remove(path.join(targetDir, 'scripts', 'README.md'));
    
    // Validate the created skill
    const exitCode = await validateSkill(targetDir);
    
    if (exitCode === 0) {
      console.log(chalk.green.bold('\n✓ SUCCESS! Skill created and validated.\n'));
      console.log(chalk.blue('Next steps:'));
      console.log(chalk.gray(`  1. cd ${path.relative(process.cwd(), targetDir)}`));
      console.log(chalk.gray(`  2. Edit SKILL.md with your skill's details`));
      console.log(chalk.gray(`  3. Add scripts to scripts/ directory as needed`));
      console.log(chalk.gray(`  4. Run validation: npm run validate from skill-creator`));
      console.log(chalk.gray(`  5. Package: npm run package from skill-creator\n`));
    } else {
      console.log(chalk.yellow('\n⚠ Skill created but has validation issues. Please review and fix.\n'));
    }
    
    return targetDir;
    
  } catch (error) {
    console.error(chalk.red(`\n✗ Failed to create skill: ${error.message}\n`));
    throw error;
  }
}

/**
 * Main CLI function
 */
async function main() {
  console.log(chalk.blue.bold('\n🎨 Skill Creator - Initialize New Skill\n'));
  console.log(chalk.gray('Create a new Anthropic-compliant skill with proper structure.\n'));
  
  try {
    // Prompt for skill details
    const answers = await inquirer.prompt([
      {
        type: 'input',
        name: 'name',
        message: 'Enter skill name (hyphen-case):',
        validate: validateNameFormat
      },
      {
        type: 'input',
        name: 'description',
        message: 'Enter skill description (include "when to use"):',
        validate: validateDescriptionFormat
      },
      {
        type: 'confirm',
        name: 'confirm',
        message: (answers) => `Create skill "${answers.name}" in agents/skills/?`,
        default: true
      }
    ]);
    
    if (!answers.confirm) {
      console.log(chalk.yellow('\nCancelled.'));
      process.exit(0);
    }
    
    // Create the skill
    await createSkill(answers.name, answers.description);
    
  } catch (error) {
    if (error.isTtyError) {
      console.error(chalk.red('Prompt could not be rendered in this environment'));
    } else {
      console.error(chalk.red(`Error: ${error.message}`));
    }
    process.exit(1);
  }
}

// CLI execution
if (require.main === module) {
  main().catch(error => {
    console.error(chalk.red(`Fatal error: ${error.message}`));
    process.exit(1);
  });
}

module.exports = { createSkill };
