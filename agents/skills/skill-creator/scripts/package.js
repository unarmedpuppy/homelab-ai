#!/usr/bin/env node

/**
 * Package Anthropic-compliant skill into .skill file
 * Creates zip file with .skill extension
 */

const fs = require('fs-extra');
const path = require('path');
const archiver = require('archiver');
const chalk = require('chalk');
const { validateSkill } = require('./validate');

// Files/directories to exclude from package
const EXCLUDE_PATTERNS = [
  'node_modules',
  '.git',
  '.gitignore',
  '.DS_Store',
  'dist',
  '*.log',
  'package-lock.json',
  'yarn.lock',
  '.env',
  '.env.local',
  'tmp',
  'temp',
  '.cache'
];

/**
 * Check if file/directory should be excluded
 * @param {string} filePath - File path to check
 * @returns {boolean} - True if should be excluded
 */
function shouldExclude(filePath) {
  const basename = path.basename(filePath);
  
  for (const pattern of EXCLUDE_PATTERNS) {
    if (pattern.includes('*')) {
      // Simple wildcard matching
      const regex = new RegExp('^' + pattern.replace('*', '.*') + '$');
      if (regex.test(basename)) {
        return true;
      }
    } else if (basename === pattern || filePath.includes(`/${pattern}/`) || filePath.includes(`\\${pattern}\\`)) {
      return true;
    }
  }
  
  return false;
}

/**
 * Package skill into .skill file
 * @param {string} skillPath - Path to skill directory
 * @param {string} outputDir - Output directory for .skill file (default: dist/)
 * @returns {Promise<string>} - Path to created .skill file
 */
async function packageSkill(skillPath, outputDir = null) {
  console.log(chalk.blue(`\n📦 Packaging skill: ${skillPath}\n`));
  
  try {
    // Resolve absolute path
    const absolutePath = path.resolve(skillPath);
    const skillName = path.basename(absolutePath);
    
    // Determine output directory
    if (!outputDir) {
      outputDir = path.join(absolutePath, 'dist');
    }
    
    // Ensure output directory exists
    await fs.ensureDir(outputDir);
    
    // Output file path
    const outputFile = path.join(outputDir, `${skillName}.skill`);
    
    // Step 1: Validate skill first
    console.log(chalk.blue('Step 1: Validating skill...\n'));
    const validationExitCode = await validateSkill(absolutePath);
    
    if (validationExitCode === 1) {
      throw new Error('Skill validation failed with errors. Fix errors before packaging.');
    }
    
    if (validationExitCode === 2) {
      console.log(chalk.yellow('\n⚠ Skill has warnings but will continue packaging...\n'));
    }
    
    // Step 2: Create archive
    console.log(chalk.blue('Step 2: Creating .skill file...\n'));
    
    const output = fs.createWriteStream(outputFile);
    const archive = archiver('zip', {
      zlib: { level: 9 } // Maximum compression
    });
    
    // Listen for archive events
    output.on('close', () => {
      const sizeKB = (archive.pointer() / 1024).toFixed(1);
      console.log(chalk.green.bold(`\n✓ SUCCESS!`));
      console.log(chalk.green(`✓ Packaged: ${outputFile}`));
      console.log(chalk.green(`✓ Size: ${sizeKB} KB`));
      console.log(chalk.green(`✓ Total bytes: ${archive.pointer()}\n`));
    });
    
    archive.on('warning', (err) => {
      if (err.code === 'ENOENT') {
        console.warn(chalk.yellow(`Warning: ${err.message}`));
      } else {
        throw err;
      }
    });
    
    archive.on('error', (err) => {
      throw err;
    });
    
    // Pipe archive data to the file
    archive.pipe(output);
    
    // Add files to archive
    const files = await fs.readdir(absolutePath);
    
    for (const file of files) {
      const filePath = path.join(absolutePath, file);
      const relativePath = path.relative(absolutePath, filePath);
      
      // Skip excluded files/directories
      if (shouldExclude(filePath)) {
        console.log(chalk.gray(`  Skipping: ${relativePath}`));
        continue;
      }
      
      const stats = await fs.stat(filePath);
      
      if (stats.isDirectory()) {
        // Add directory recursively
        archive.directory(filePath, relativePath, (entry) => {
          // Filter out excluded files from subdirectories
          if (shouldExclude(entry.name)) {
            return false;
          }
          console.log(chalk.green(`  Adding: ${path.join(relativePath, path.basename(entry.name))}`));
          return entry;
        });
      } else {
        // Add single file
        archive.file(filePath, { name: relativePath });
        console.log(chalk.green(`  Adding: ${relativePath}`));
      }
    }
    
    // Finalize the archive
    await archive.finalize();
    
    // Wait for the output stream to close
    await new Promise((resolve) => output.on('close', resolve));
    
    return outputFile;
    
  } catch (error) {
    console.error(chalk.red(`\n✗ Packaging failed: ${error.message}\n`));
    throw error;
  }
}

// CLI execution
if (require.main === module) {
  const args = process.argv.slice(2);
  
  if (args.length === 0) {
    console.error(chalk.red('Usage: node package.js <skill-directory> [output-directory]'));
    process.exit(1);
  }
  
  const skillPath = args[0];
  const outputDir = args[1] || null;
  
  packageSkill(skillPath, outputDir)
    .then(outputFile => {
      console.log(chalk.blue('Next steps:'));
      console.log(chalk.gray(`  - Test: Unzip ${path.basename(outputFile)} and verify contents`));
      console.log(chalk.gray(`  - Distribute: Share the .skill file\n`));
      process.exit(0);
    })
    .catch(error => {
      console.error(chalk.red(`Fatal error: ${error.message}`));
      process.exit(1);
    });
}

module.exports = { packageSkill };
