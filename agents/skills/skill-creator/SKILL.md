---
name: skill-creator
description: Create, validate, and package Anthropic-compliant skills. Use when creating new skills, validating existing skills, or packaging skills for distribution. Implements Anthropic Skills Specification with JavaScript for offline capability.
---

# Skill Creator

Create, validate, and package skills following the Anthropic Skills Specification.

## Overview

This skill provides three core commands for skill lifecycle management:

1. **init** - Create a new skill with proper structure
2. **validate** - Verify skill follows Anthropic standards
3. **package** - Create distributable .skill file

All operations implemented in JavaScript for offline capability and cross-platform support.

## Commands

### Initialize a New Skill

Create a new skill with interactive prompts:

```bash
cd agents/skills/skill-creator
npm run init
```

**What it creates**:
- Skill directory with hyphen-case name
- SKILL.md with proper YAML frontmatter
- Directory structure (scripts/, references/, assets/ as needed)
- Basic validation passing structure

**Prompts**:
- Skill name (validates hyphen-case, max 64 chars)
- Description (ensures completeness with "when to use")

### Validate a Skill

Check skill compliance with Anthropic standards:

```bash
cd agents/skills/skill-creator
npm run validate path/to/skill
```

**Validation checks**:
- SKILL.md exists
- YAML frontmatter format correct
- Required fields present (name, description)
- Optional fields valid (license, allowed-tools, metadata)
- Name is hyphen-case, max 64 characters
- Name matches directory name
- Description includes "when to use" context
- No invalid frontmatter fields
- No auxiliary files (README.md, CHANGELOG.md forbidden)
- SKILL.md under 500 lines (warning if exceeded)

**Exit codes**:
- 0 = Valid
- 1 = Errors found
- 2 = Warnings only

### Package a Skill

Create distributable .skill file:

```bash
cd agents/skills/skill-creator
npm run package path/to/skill
```

**Process**:
1. Run validation first (fails if errors)
2. Create .skill file (zip with .skill extension)
3. Include all skill files (SKILL.md, scripts/, references/, assets/)
4. Exclude: node_modules, .git, temp files, .DS_Store
5. Output to dist/ directory

**Output**: `dist/skill-name.skill`

## Requirements

- Node.js 14 or higher
- npm or yarn

## Anthropic Standards

This skill implements the [Anthropic Skills Specification](references/anthropic-spec.md).

**Key principles**:
- SKILL.md is the only required file
- Frontmatter: name and description (required), license/allowed-skills/metadata (optional)
- Progressive disclosure: Keep SKILL.md concise (<500 lines)
- Imperative form: All instructions use imperative/infinitive voice
- No auxiliary files: No README.md, CHANGELOG.md, etc.

See [references/anthropic-spec.md](references/anthropic-spec.md) for complete specification.

## Examples

### Create a new skill

```bash
npm run init

? Enter skill name: example-workflow
? Enter description: Demonstrate example workflow patterns. Use when learning skill creation or testing skill-creator functionality.

✓ Created agents/skills/example-workflow/
✓ Created SKILL.md with proper frontmatter
✓ Skill passes validation
```

### Validate existing skill

```bash
npm run validate ../scaffold-workflow

✓ SKILL.md exists
✓ Frontmatter valid
✓ Name valid: scaffold-workflow
✓ Description complete
✓ No auxiliary files
✓ Structure valid

Skill is valid!
```

### Package for distribution

```bash
npm run package ../scaffold-workflow

✓ Validation passed
✓ Creating .skill file...
✓ Packaged: dist/scaffold-workflow.skill (42.3 KB)
```

## Troubleshooting

### Validation fails: "Name must be hyphen-case"

Use lowercase letters and hyphens only:
- ✓ `example-skill`
- ✗ `exampleSkill`
- ✗ `example_skill`

### Validation fails: "Description must include when to use"

Add context about when the skill should be invoked:
- ✓ "Create widgets. Use when initializing widget systems."
- ✗ "Create widgets."

### Windows: Packaging fails

Ensure you have write permissions to dist/ directory. Run as administrator if needed.

## Resources

- [Anthropic Skills Specification](references/anthropic-spec.md) - Complete spec
- [scripts/init-skill.js](scripts/init-skill.js) - Initialization implementation
- [scripts/validate.js](scripts/validate.js) - Validation implementation
- [scripts/package.js](scripts/package.js) - Packaging implementation
