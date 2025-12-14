# Life OS - Session Context for Next Agent

**Created**: 2025-12-12
**Purpose**: Capture context from planning session for implementation agent

---

## What This Is

Life OS is a personal knowledge base / "second brain" system for Joshua. It will be a **new repository** called `life-os` that manages all aspects of life through structured markdown files, assisted by an AI agent named **Jobin**.

## Key Decisions Made

| Decision | Choice | Notes |
|----------|--------|-------|
| Repo name | `life-os` | New repo, separate from home-server |
| Storage | Single private repo | Will use local Gitea (not GitHub) for privacy |
| Link style | Standard markdown | `[text](path/to/file.md)` - NOT wiki-style `[[links]]` |
| Git hosting | Local Gitea | Don't push to GitHub - data is personal/private |
| Photo storage | Immich references | Photos stay in Immich at `/jenquist-cloud`, Life OS stores links only |

## User Context

- Joshua is 38 years old
- Has kids (fatherhood tracking is important)
- Owns rental properties (real estate tracking needed)
- Uses home server with Docker services (trading bot, media, etc.)
- Photos are in Immich on the server
- Wants to eventually automate with n8n and access Jobin via Telegram

## The Agent: Jobin

- **Name**: Jobin
- **Personality**: Conversational, friendly, proactive
- **Tone**: Warm but efficient, like a trusted executive assistant
- **File**: Will live at `life-os/agents/personas/jobin.md`

## Era Structure (Biography)

Special note: User wanted a **parenting era** added that overlaps with other eras:

```
00-childhood      (birth - ~12)
01-teenage        (~13-17)
02-college        (~18-22)
03-early-career   (~23-27)
04-establishing   (~28-32)
05-current        (~33-present)
06-parenting      (overlapping - dedicated fatherhood journey)
```

## Family Tree

- Should link to contact files in `people/family/`
- Located at `biography/family-tree/tree.md`
- Include parents, siblings, extended family
- Links bidirectionally with contacts

## Photo Integration

- Photos stored in Immich at `/jenquist-cloud` on home server
- Life OS only stores references, NOT actual image files
- Reference format in frontmatter:
  ```yaml
  photos:
    album: "Album Name"
    immich_album_id: "abc123"
  ```
- Future dashboard can pull from Immich API

## Implementation Phases

1. **Phase 1: Foundation** - Create repo, templates, Jobin persona, basic skills, biography stubs
2. **Phase 2: Expansion** - All domain templates, calendar integration, weekly summaries
3. **Phase 3: Automation** - n8n workflows, Telegram bot for Jobin
4. **Phase 4: Dashboard** - Web UI to visualize the markdown data

## Files to Reference

All planning docs are in `agents/plans/life-os/`:

| File | Purpose |
|------|---------|
| `overview.md` | Master architecture and vision |
| `phase-1-foundation.md` | **START HERE** - Actionable implementation tasks |
| `phase-2-expansion.md` | Domain expansion details |
| `phase-3-automation.md` | n8n integration spec |
| `phase-4-dashboard.md` | Dashboard design |
| `biography-system.md` | Historical memory system spec |
| `domains.md` | Complete domain reference |

## What the Next Agent Should Do

1. **Read** `phase-1-foundation.md` for the task list
2. **Create** the `life-os` repository (locally, don't push anywhere yet)
3. **Build** directory structure and templates
4. **Create** Jobin persona file
5. **Create** basic skills
6. **Initialize** biography with stubs
7. **Test** the manual workflow

## Important Reminders

- **DO NOT push to GitHub** - User wants local Gitea for privacy
- **Photos stay in Immich** - Only store references/links
- **Jobin is conversational** - Not robotic, friendly assistant vibe
- **Biography has overlapping eras** - Parenting era runs parallel to others
- **Family tree links to contacts** - Bidirectional relationship

---

## Quick Start Command

```bash
# Create the new repo
mkdir -p ~/repos/personal/life-os
cd ~/repos/personal/life-os
git init

# Then follow phase-1-foundation.md tasks
```
