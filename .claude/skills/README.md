# Claude Skills

This directory contains symlinks to skills in `agents/skills/` for Claude Code auto-detection.

## How It Works

Claude Code automatically discovers skills from `.claude/skills/` directory. Each `.md` file here is a symlink to the actual `SKILL.md` in `agents/skills/<skill-name>/`.

## Usage

Skills are automatically available when using Claude Code. They provide workflow guides with YAML frontmatter for discovery.

To use a skill, reference it by name or ask Claude about it:
- "Use the standard-deployment skill"
- "How do I deploy to the server?"
- "What skills are available?"

## Adding New Skills

1. Create skill in `agents/skills/<skill-name>/SKILL.md`
2. Run: `ln -sf ../../agents/skills/<skill-name>/SKILL.md .claude/skills/<skill-name>.md`

Or use the `skill-creator` skill to auto-generate both the skill and symlink.

## Structure

```
.claude/skills/
├── README.md                    # This file
├── standard-deployment.md       # -> ../../agents/skills/standard-deployment/SKILL.md
├── deploy-new-service.md        # -> ../../agents/skills/deploy-new-service/SKILL.md
└── ...
```

All symlinks point to `../../agents/skills/<name>/SKILL.md` which is the canonical location for skill documentation.
