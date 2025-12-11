# Anthropic Skills Specification

**Source**: [anthropics/skills](https://github.com/anthropics/skills) repository (reference only)  
**Implementation**: JavaScript reimplementation for offline capability  
**Version**: Based on Anthropic patterns as of December 2025

## Overview

The Anthropic Skills Specification defines a standard format for creating reusable, discoverable skills that AI agents can invoke. Skills package instructions, scripts, and resources into a single unit.

## Directory Structure

```
skill-name/
├── SKILL.md          (required - main documentation)
└── Optional bundled resources:
    ├── scripts/      - Executable code (JavaScript, Python, Bash, etc.)
    ├── references/   - Documentation loaded into context as needed
    └── assets/       - Files used in output (templates, configs, etc.)
```

**Rules**:
- SKILL.md is the only required file
- Delete unused directories (don't leave empty scripts/, references/, assets/)
- No auxiliary files (README.md, CHANGELOG.md, etc. are forbidden)

## SKILL.md Format

### YAML Frontmatter

Required at the top of SKILL.md:

```yaml
---
name: skill-name
description: Complete description including when to use this skill
---
```

**Required Fields**:
- `name` (string): Skill identifier
  - Format: hyphen-case (lowercase letters and hyphens only)
  - Max length: 64 characters
  - Must match directory name
  - Examples: `scaffold-workflow`, `skill-creator`, `deploy-aws`
  
- `description` (string): Complete skill description
  - Must include WHEN to use the skill (triggers, contexts)
  - Should be 1-3 sentences
  - Example: "Create new skills following Anthropic standards. Use when building custom skills or learning skill creation patterns."

**Optional Fields**:
- `license` (string): License name or reference to LICENSE file
  - Example: `MIT` or `See LICENSE file`
  
- `allowed-tools` (array): Pre-approved tools for Claude Code
  - Only relevant for Claude Code integration
  - Example: `[bash, file_editor]`
  
- `metadata` (object): Custom key-value pairs
  - Arbitrary metadata for skill management
  - Example: `{category: "development", version: "1.0.0"}`

**Forbidden Fields**:
- No other fields allowed in frontmatter
- Validation will fail if unexpected fields present

### Body Content

After frontmatter, write skill instructions in Markdown.

**Requirements**:
- Use imperative/infinitive form for all instructions
  - ✓ "Create a file"
  - ✗ "Creates a file"
  - ✓ "Run the script"
  - ✗ "Runs the script"
  
- Keep under 500 lines
  - If longer, split detailed content to references/
  - Link to references for advanced topics
  
- Use progressive disclosure
  - Basic instructions in SKILL.md
  - Detailed documentation in references/
  - Link to references when needed

**Structure** (recommended):
```markdown
# Skill Name

Brief overview (1-2 sentences)

## Usage

Step-by-step instructions

## Examples

Concrete examples with expected output

## Troubleshooting

Common issues and solutions

## Resources

Links to scripts/, references/, assets/
```

## Progressive Disclosure Patterns

### Pattern 1: High-Level Guide with References

SKILL.md contains overview and basic usage. References contain deep details.

```markdown
# deploy-aws

Deploy applications to AWS. Use when deploying to production environments.

## Basic Deployment

1. Configure AWS credentials
2. Run deployment script
3. Verify deployment

See [references/advanced-deployment.md](references/advanced-deployment.md) for:
- Multi-region deployments
- Blue-green strategies
- Rollback procedures
```

### Pattern 2: Domain-Specific Organization

Split by domain when skill covers multiple areas.

```markdown
# cloud-deploy

Deploy to multiple cloud providers.

## Providers

- [AWS](references/aws.md) - Amazon Web Services
- [GCP](references/gcp.md) - Google Cloud Platform
- [Azure](references/azure.md) - Microsoft Azure

Choose your provider and see corresponding reference.
```

### Pattern 3: Conditional Details

Basic content in SKILL.md, advanced in references.

```markdown
# database-migrate

Run database migrations.

## Basic Usage

For standard migrations, run:
```bash
npm run migrate
```

For advanced scenarios (rollbacks, partial migrations, production safeguards), see [references/advanced-migrations.md](references/advanced-migrations.md).
```

## Naming Conventions

### Skill Names

- **Format**: hyphen-case
- **Max length**: 64 characters
- **Characters**: Lowercase letters (a-z), hyphens (-), numbers (0-9)
- **Must match**: Directory name

**Examples**:
- ✓ `skill-creator`
- ✓ `scaffold-workflow`
- ✓ `deploy-aws-lambda`
- ✗ `skillCreator` (camelCase)
- ✗ `skill_creator` (snake_case)
- ✗ `Skill-Creator` (capitals)

### File Names

- `SKILL.md` - Exactly this (all caps, .md extension)
- Scripts: Any name, recommend hyphen-case
- References: Any name, recommend hyphen-case .md files
- Assets: Any name appropriate for asset type

## Scripts Directory

Optional directory for executable code.

**Purpose**:
- Deterministic operations
- Code that agents would repeatedly rewrite
- Critical operations requiring exact execution

**Languages**: Any executable language
- JavaScript/TypeScript (Node.js)
- Python
- Bash/Shell
- Others as needed

**Organization**:
```
scripts/
├── init-skill.js      - Initialization
├── validate.js        - Validation
├── package.js         - Packaging
└── helpers/           - Shared utilities
    └── yaml-parser.js
```

**Best Practice**: Keep scripts focused and modular.

## References Directory

Optional directory for detailed documentation.

**Purpose**:
- Deep documentation loaded only when needed
- Advanced topics beyond basic usage
- Domain-specific details
- Design docs, architecture guides

**Format**: Markdown files

**Organization**:
```
references/
├── anthropic-spec.md     - Specifications
├── advanced-usage.md     - Advanced patterns
├── troubleshooting.md    - Detailed debugging
└── api-reference.md      - API documentation
```

**Loading**: Claude loads references into context when needed (not all at once).

## Assets Directory

Optional directory for files used in skill output.

**Purpose**:
- Templates that skills copy/modify
- Configuration files
- Images for documentation
- Data files

**Not Loaded**: Assets are NOT loaded into context automatically.

**Organization**:
```
assets/
├── templates/
│   ├── config.template.json
│   └── component.template.tsx
└── images/
    └── architecture-diagram.png
```

## Key Principles

### 1. Concise is Key

Shorter is better. Every word should earn its place.

- Remove unnecessary explanation
- Use concrete examples over abstract description
- Link to references for depth

### 2. Degrees of Freedom

Match specificity to fragility:

- **High freedom**: Text instructions for flexible approaches
  - "Configure database connection using environment variables"
  
- **Medium freedom**: Pseudocode or parameterized scripts
  - "Run migration script with --env=<environment> flag"
  
- **Low freedom**: Exact scripts for critical operations
  - Provide exact script that must run unchanged

### 3. When to Use Scripts

Use scripts when:
- Operation must be deterministic
- Agent would repeatedly rewrite the same code
- Operation is complex and error-prone
- Exact execution matters (security, production, etc.)

Avoid scripts when:
- Simple text instructions suffice
- Agent needs flexibility
- Operation varies by context

### 4. When to Use References

Use references/ when:
- Content exceeds 500 lines
- Topic is advanced/optional
- Multiple domains covered
- Deep documentation needed

Keep in SKILL.md when:
- Content is core to skill usage
- Instructions are brief
- Agent needs info immediately

### 5. When to Use Assets

Use assets/ when:
- Skill outputs files (templates, configs)
- Files are copied/modified by skill
- Binary resources needed (images, data files)

Don't use assets/ for:
- Documentation (use references/)
- Executable code (use scripts/)

## Validation

Skills should pass validation before packaging.

**Validation checks**:
- SKILL.md exists
- YAML frontmatter format correct
- Required fields present (name, description)
- Name is hyphen-case, max 64 chars
- Name matches directory name
- No unexpected frontmatter fields
- Description includes "when to use" context
- No auxiliary files (README.md, etc.)
- SKILL.md under 500 lines (warning)

**Validation tool**: `node scripts/validate.js path/to/skill`

## Packaging

Create distributable .skill files (zip with .skill extension).

**Process**:
1. Validate skill first
2. Create zip archive
3. Include all skill files
4. Exclude: node_modules, .git, temp files, .DS_Store, etc.
5. Rename .zip to .skill

**Packaging tool**: `node scripts/package.js path/to/skill`

**Output**: `dist/skill-name.skill`

## Imperative Form Guidelines

All instructions should use imperative/infinitive voice:

**Imperative** (commands):
- "Create a new file"
- "Run the script"
- "Configure the database"
- "Deploy to production"

**Infinitive** (actions):
- "To create a widget"
- "To configure settings"

**Avoid** (present tense, gerunds):
- ✗ "Creates a new file"
- ✗ "Running the script"
- ✗ "Configures the database"
- ✗ "Creating a widget"

**Why**: Imperative form is clearer for AI agents to parse and execute.

## Forbidden Practices

### No Auxiliary Files

These files are forbidden:
- README.md (use SKILL.md instead)
- CHANGELOG.md (use git history)
- CONTRIBUTING.md (not applicable to skills)
- LICENSE.md (use frontmatter: `license: MIT` or single LICENSE file)
- .github/ workflows
- Excessive configuration files

**Rationale**: Skills should be lean. Everything belongs in SKILL.md or optional directories.

### No Bloat

Keep skills focused:
- One clear purpose per skill
- Don't combine unrelated functionality
- Split large skills into multiple skills

### No Duplication

Don't duplicate:
- SKILL.md content in README.md
- Same info in multiple references
- Templates that could be generated

## Examples

### Minimal Skill

```
hello-skill/
└── SKILL.md
```

```yaml
---
name: hello-skill
description: Print hello world message. Use when testing skill functionality or learning skill creation.
---

# Hello Skill

Print a hello world message.

## Usage

Run:
```bash
echo "Hello, World!"
```

That's it!
```

### Full-Featured Skill

```
deploy-workflow/
├── SKILL.md
├── scripts/
│   ├── deploy.js
│   ├── validate-env.js
│   └── rollback.js
├── references/
│   ├── deployment-strategies.md
│   ├── environment-config.md
│   └── troubleshooting.md
└── assets/
    └── templates/
        ├── docker-compose.yml
        └── nginx.conf
```

## Compliance Checklist

Before packaging a skill, verify:

- [ ] SKILL.md exists with proper YAML frontmatter
- [ ] Name is hyphen-case, max 64 characters
- [ ] Name matches directory name
- [ ] Description includes "when to use"
- [ ] Only allowed frontmatter fields used
- [ ] All instructions use imperative form
- [ ] SKILL.md under 500 lines (or content split to references/)
- [ ] No auxiliary files (README.md, CHANGELOG.md, etc.)
- [ ] Unused directories deleted (empty scripts/, references/, assets/)
- [ ] Skill passes validation script
- [ ] Examples provided
- [ ] Troubleshooting section included (if applicable)

## Reference Links

- **Anthropic Skills Repository**: https://github.com/anthropics/skills
  - Source of patterns (we reimplement in JavaScript)
  - Reference for standards, not code copy
  
- **skill-creator Skill**: This skill implements the spec
  - JavaScript validation and packaging
  - Offline-capable
  - Cross-platform support

## Updates

This specification is based on Anthropic patterns as of December 2025. As Anthropic updates their standards, this document should be reviewed and updated accordingly.

**Current Implementation**: JavaScript reimplementation for offline capability and consistency with project tech stack.
