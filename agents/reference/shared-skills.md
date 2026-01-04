# Shared Agent Skills

How to install and use shared-agent-skills in repositories.

## Quick Setup

```bash
# If no package.json exists
npm init -y

# Install from git (recommended - no auth needed)
npm install git+ssh://git@192.168.86.47:2223/unarmedpuppy/shared-agent-skills.git

# Create .claude/skills/ symlinks
npx link-skills

# Add to .gitignore
echo -e "\nnode_modules/\npackage-lock.json" >> .gitignore

# Commit
git add .gitignore package.json .claude/
git commit -m "feat: add shared-agent-skills"
```

## What Gets Created

```
your-repo/
├── package.json              # tracks dependency
├── node_modules/             # gitignored
│   └── shared-agent-skills/
└── .claude/skills/           # committed (symlinks)
    ├── plan-creator.md → ../../node_modules/.../SKILL.md
    ├── http-api-requests.md
    ├── terminal-ui-design.md
    ├── skill-creator.md
    ├── setup-gitea-workflow.md
    └── beads-task-management.md
```

## Available Skills

| Skill | Description |
|-------|-------------|
| `plan-creator` | Create implementation plans with interactive wizard |
| `http-api-requests` | curl-based HTTP request patterns |
| `terminal-ui-design` | TUI design guidelines |
| `skill-creator` | Create new agent skills |
| `setup-gitea-workflow` | Set up Gitea Actions CI/CD |
| `beads-task-management` | Beads distributed issue tracker |

## Updating Skills

```bash
npm update
npx link-skills  # recreate symlinks if new skills added
```

## After Cloning (on another machine)

```bash
npm install      # restores node_modules
npx link-skills  # recreates symlinks
```

## CLI Commands

| Command | Description |
|---------|-------------|
| `npx link-skills` | Create symlinks to skills |
| `npx link-skills --check` | Verify symlinks are correct |
| `npx link-skills --clean` | Remove managed symlinks |
| `npx link-skills --list` | List available skills |
| `npx link-skills --target DIR` | Custom target directory |

## How `npx link-skills` Works

1. **bin field in package.json** tells npm to expose the command:
   ```json
   "bin": { "link-skills": "./bin/link-skills.js" }
   ```

2. **npm creates a symlink** in `node_modules/.bin/`:
   ```
   node_modules/.bin/link-skills → ../shared-agent-skills/bin/link-skills.js
   ```

3. **The script**:
   - Finds skills in `node_modules/.../skills/`
   - Creates `.claude/skills/` directory
   - Creates relative symlinks: `.claude/skills/plan-creator.md → ../../node_modules/.../SKILL.md`

4. **Relative symlinks** work on any machine - when someone clones and runs `npm install`, symlinks still resolve.

## Troubleshooting

### "Package not found" after git install

Ensure SSH key is configured for Gitea access:
```bash
ssh -T git@192.168.86.47 -p 2223
```

### "Symlinks broken after npm install"

Re-run link-skills:
```bash
npx link-skills
```

### "Command not found: link-skills"

Ensure package is installed:
```bash
npm install
npx link-skills
```

## Alternative: Install from Gitea Registry

```bash
# Add auth token to ~/.npmrc (create token at Gitea → Settings → Applications)
echo "//gitea.server.unarmedpuppy.com/api/packages/unarmedpuppy/npm/:_authToken=YOUR_TOKEN" >> ~/.npmrc

# Install from registry
npm install shared-agent-skills --registry https://gitea.server.unarmedpuppy.com/api/packages/unarmedpuppy/npm/
```

## Adding Skills to the Package

See [shared-agent-skills/AGENTS.md](../../shared-agent-skills/AGENTS.md) for contributing new skills.
