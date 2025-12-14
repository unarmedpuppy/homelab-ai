# Phase 1: Foundation

**Status**: Ready to Start
**Goal**: Create the repository structure, core templates, Jobin persona, and basic skills for manual operation

---

## Deliverables

1. New git repository with directory structure
2. Core templates (journal, contact, event, biography)
3. Jobin persona file
4. Basic skills for CRUD operations
5. Biography foundation (overview + era stubs)
6. Working manual workflow

---

## Tasks

### 1. Create Repository

```bash
# Create and initialize repo
mkdir ~/repos/personal/life-os
cd ~/repos/personal/life-os
git init

# Create .gitignore
cat > .gitignore << 'EOF'
# Local agent files
agents/plans/local/

# Secrets (if any local config)
.env
*.local.md

# OS files
.DS_Store
Thumbs.db

# Editor
.vscode/
.idea/
*.swp
EOF

git add .gitignore
git commit -m "Initial commit with .gitignore"
```

**Checklist:**
- [ ] Create repository locally
- [ ] Initialize git
- [ ] Create .gitignore
- [ ] Create GitHub remote (optional, can be private)
- [ ] Push initial commit

### 2. Create Directory Structure

```bash
cd ~/repos/personal/life-os

# Core directories
mkdir -p journal/{2025/12,templates}
mkdir -p people/{family,friends,professional,templates}
mkdir -p fatherhood/{milestones,activities,lessons}
mkdir -p finance/{accounts,properties,budgets,taxes}
mkdir -p assets/{vehicles,electronics}
mkdir -p inventory/{video-games,electronics,collectibles}
mkdir -p health/{medical-records,fitness}
mkdir -p career
mkdir -p learning/{books,courses,notes}
mkdir -p projects/{active,completed,someday}
mkdir -p travel/{trips,packing-lists}
mkdir -p home/{projects,warranties}
mkdir -p legal/contracts
mkdir -p subscriptions
mkdir -p goals/reviews
mkdir -p ideas
mkdir -p events/{2025,templates}
mkdir -p memories/2025
mkdir -p changelog
mkdir -p agents/{personas,skills,reference}
mkdir -p scripts
mkdir -p biography/{eras,themes,stories}
```

**Checklist:**
- [ ] Create all directories
- [ ] Add placeholder README.md in root
- [ ] Commit structure

### 3. Create Core Templates

#### Daily Journal Template (`journal/templates/daily.md`)

```markdown
---
date: {{DATE}}
mood:
energy: /10
weather:
---

# {{DAY_NAME}}, {{MONTH}} {{DAY}}, {{YEAR}}

## Morning Intentions
- [ ]

## Schedule
<!-- Pulled from calendar or manual entry -->

## Interactions
<!-- Format: ### [Name](link) followed by notes -->

## Accomplishments
-

## Reflections


## Tomorrow
- [ ]
```

#### Contact Template (`people/templates/contact.md`)

```markdown
---
name:
relationship: # family, friend, professional, acquaintance
category: # family, friends, professional (matches folder)
met: # YYYY-MM-DD
birthday: # YYYY-MM-DD or MM-DD if year unknown
contact:
  email:
  phone:
  address:
tags: []
last_contact:
---

# {{NAME}}

## About


## Gift Ideas
-

## Key Notes
<!-- Important things to remember -->

## Interaction History
<!-- Links to journal entries, auto-maintained -->
```

#### Event Template (`events/templates/event.md`)

```markdown
---
date: {{DATE}}
type: # gathering, trip, milestone, celebration, other
participants: [] # list of contact links
location:
tags: []
---

# {{EVENT_TITLE}}

## Summary


## Participants
<!-- Links to contacts -->

## Photos
<!-- Links to photos if stored externally -->

## Notes


## Memories
<!-- Special moments to remember -->
```

#### Biography Overview Template (`biography/overview.md`)

```markdown
---
name: [Your Name]
born: YYYY-MM-DD
birthplace: City, State
current_age: 38
updated: YYYY-MM-DD
---

# Life Overview

## Quick Facts
- Born: [Date], [Place]
- Current: [City, State]
- Family: [Spouse], [Kids ages]
- Career: [Current role/industry]

## Timeline

| Era | Years | Key Events |
|-----|-------|------------|
| Childhood | YYYY-YYYY | |
| Teenage | YYYY-YYYY | |
| College | YYYY-YYYY | |
| Early Career | YYYY-YYYY | |
| Establishing | YYYY-YYYY | |
| Current | YYYY-now | |

## For Jobin
Key context for daily interactions:
- [Important background]
- [Key relationships]
- [Things to remember]
```

#### Era Template (`biography/eras/_template.md`)

```markdown
---
era: [Era Name]
years: YYYY-YYYY
age_range: X-Y
locations: []
updated: YYYY-MM-DD
---

# [Era Name] (YYYY-YYYY)

## Overview
[2-3 paragraph summary of this life chapter]

## Where I Lived
- [City] (YYYY-YYYY)

## Key People
- [Name] - [Relationship, significance]

## Education
- [School] (YYYY-YYYY)

## Work
- [Job/Company] (YYYY-YYYY)

## Major Events
| Year | Event | Significance |
|------|-------|--------------|
| | | |

## Memorable Experiences

## What I Learned

## Connections to Present
```

#### Story Template (`biography/stories/_template.md`)

```markdown
---
title: [Story Title]
era: [era-name]
year: ~YYYY
people: []
location:
tags: []
---

# [Story Title]

[The story]

## Why This Matters

## People Involved
```

**Checklist:**
- [ ] Create daily journal template
- [ ] Create contact template
- [ ] Create event template
- [ ] Create weekly summary template
- [ ] Create biography overview template
- [ ] Create era template
- [ ] Create story template
- [ ] Commit templates

### 4. Create AGENTS.md

Root-level agent instructions file (following home-server pattern):

```markdown
# Life OS - Agent Instructions

**Read this file first.** Entry point for AI assistants working with this repository.

## Overview

This is a personal knowledge base system managed through structured markdown files. The primary agent is **Jobin**, a life assistant who helps maintain and update the system.

## Quick Reference

```bash
# Journal operations
agents/skills/daily-journal/       # Create/update daily entries
agents/skills/weekly-summary/      # Generate weekly summaries

# Contact operations
agents/skills/update-contact/      # Add interactions, notes
agents/skills/log-event/           # Create events linked to contacts

# Review operations
agents/skills/morning-briefing/    # Daily briefing generation
agents/skills/evening-review/      # Process daily input
```

## Directory Structure

| Directory | Purpose |
|-----------|---------|
| `journal/` | Daily and weekly entries |
| `people/` | Contact sheets by category |
| `fatherhood/` | Parenting goals, milestones, activities |
| `finance/` | Accounts, properties, budgets |
| `assets/` | Vehicles, real estate, major items |
| `inventory/` | Collections, electronics, smaller items |
| `events/` | Shared events and memories |
| `goals/` | Annual and life goals |
| `changelog/` | Daily change summaries |

## Conventions

### File Naming
- Journal: `YYYY-MM-DD.md`
- Contacts: `lowercase-hyphenated-name.md`
- Events: `YYYY-MM-DD-event-name.md`
- Changelog: `YYYY-MM-DD.md`

### Linking
Use relative markdown links:
```markdown
[John Smith](../people/professional/john-smith.md)
```

### Frontmatter
All files use YAML frontmatter for metadata.

### Changelog
Every session that modifies files should update the daily changelog:
`changelog/YYYY-MM-DD.md`

## Workflow

### Daily Input (Evening)
1. User provides summary of day (text dump, voice notes, etc.)
2. Jobin processes and updates:
   - Today's journal entry
   - Contact last_contact dates
   - Contact interaction history
   - New events if applicable
3. Jobin generates changelog

### Morning Briefing
1. Review calendar (when integrated)
2. Check birthdays in next 7 days
3. Review open tasks/reminders
4. Summarize goals progress

## Boundaries

### Always Do
- Update last_contact when logging interactions
- Link journal entries to contacts mentioned
- Generate changelog after modifications
- Use templates for new files

### Never Do
- Delete files without explicit request
- Modify financial figures without confirmation
- Share or expose sensitive personal data
```

**Checklist:**
- [ ] Create AGENTS.md
- [ ] Commit

### 5. Create Jobin Persona

`agents/personas/jobin.md`:

```markdown
# Jobin - Life Assistant

## Identity

**Name**: Jobin
**Role**: Personal life assistant and knowledge base manager
**Personality**: Warm, conversational, proactive, organized

## Voice & Tone

- Friendly and approachable, like a trusted friend who happens to be incredibly organized
- Uses casual language but stays focused on being helpful
- Celebrates wins, offers gentle reminders without nagging
- Asks clarifying questions when input is ambiguous

### Example Interactions

**Processing daily input:**
```
User: Had coffee with Sarah this morning, she's doing well. Kids had
a half day, took them to the park. Need to remember to call the
plumber about the leak.

Jobin: Nice! Here's what I've logged:

📝 Journal (Dec 12):
- Coffee with Sarah (morning)
- Park with kids (afternoon half-day)

👥 Contacts updated:
- Sarah: last contact → today

📋 Added reminder:
- Call plumber about leak

Want me to add any details about the park trip or your chat with Sarah?
```

**Morning briefing:**
```
Jobin: Good morning! Here's your Thursday:

📅 Today:
- 9:00 AM: Team standup
- 12:00 PM: Lunch with John (he mentioned job hunting last time)
- 6:00 PM: Soccer practice

🎂 Coming up:
- Mom's birthday in 3 days (Saturday)

🎯 Goal check-in:
- Weekly 1:1 with kids: ✓ Done Monday, one more needed
- Reading goal: 2/3 sessions this week

Anything you want to focus on today?
```

## Capabilities

### Core Skills
1. **daily-journal** - Create and update daily journal entries
2. **update-contact** - Add notes, interactions, update metadata
3. **log-event** - Create event entries linked to participants
4. **morning-briefing** - Generate daily overview
5. **evening-review** - Process daily input dump

### Data Sources (Future)
- Google Calendar
- Screen time reports
- Git activity
- Gaming activity (Discord, Xbox)
- Text message summaries

## Operating Principles

1. **Capture first, organize second** - Never lose information
2. **Link everything** - Contacts to events, events to journal, etc.
3. **Changelog always** - Document what changed each session
4. **Confirm destructive actions** - Deletions, financial changes
5. **Proactive reminders** - Surface relevant context without being asked

## Interaction Modes

### Manual (Current)
User dumps information, Jobin processes and confirms updates.

### Automated (Future)
Scheduled briefings, automatic data aggregation, Telegram interface.

## Context Awareness

Jobin should remember:
- Recent interactions with contacts
- Upcoming events and birthdays
- Active goals and their status
- Ongoing projects
- Family context (kids' ages, activities, school schedule)
```

**Checklist:**
- [ ] Create jobin.md persona
- [ ] Commit

### 6. Create Basic Skills

#### Daily Journal Skill (`agents/skills/daily-journal/SKILL.md`)

```markdown
---
name: daily-journal
description: Create or update daily journal entries. Use for logging daily activities, interactions, accomplishments, and reflections.
when_to_use: When processing daily input, logging interactions, or starting a new day's entry
---

# Daily Journal Skill

Create and manage daily journal entries.

## Usage

### Create Today's Entry

1. Check if entry exists:
   ```bash
   ls journal/$(date +%Y)/$(date +%m)/$(date +%Y-%m-%d).md
   ```

2. If not exists, create from template:
   ```bash
   YEAR=$(date +%Y)
   MONTH=$(date +%m)
   DAY=$(date +%d)
   DAY_NAME=$(date +%A)
   MONTH_NAME=$(date +%B)

   mkdir -p journal/$YEAR/$MONTH

   # Copy and populate template
   sed -e "s/{{DATE}}/$YEAR-$MONTH-$DAY/" \
       -e "s/{{DAY_NAME}}/$DAY_NAME/" \
       -e "s/{{MONTH}}/$MONTH_NAME/" \
       -e "s/{{DAY}}/$DAY/" \
       -e "s/{{YEAR}}/$YEAR/" \
       journal/templates/daily.md > journal/$YEAR/$MONTH/$YEAR-$MONTH-$DAY.md
   ```

### Update Entry

When processing user input:

1. Parse interactions, accomplishments, events
2. For each contact mentioned:
   - Add to Interactions section with link
   - Update contact's `last_contact` field
   - Add journal link to contact's Interaction History
3. Add accomplishments to Accomplishments section
4. Add reflections if provided
5. Update Tomorrow section with any mentioned tasks

### Entry Structure

```markdown
## Interactions
### [Contact Name](../people/category/contact-name.md)
- Notes from interaction

## Accomplishments
- What was completed

## Reflections
Free-form thoughts
```

## Examples

**User input:**
"Had lunch with John Smith, talked about his startup ideas"

**Actions:**
1. Add to today's journal:
   ```markdown
   ## Interactions
   ### [John Smith](../../people/professional/john-smith.md)
   - Lunch meeting
   - Discussed his startup ideas
   ```

2. Update `people/professional/john-smith.md`:
   - Set `last_contact: 2025-12-12`
   - Add to Interaction History:
     ```markdown
     - [2025-12-12](../../journal/2025/12/2025-12-12.md) - Lunch, discussed startup ideas
     ```
```

#### Update Contact Skill (`agents/skills/update-contact/SKILL.md`)

```markdown
---
name: update-contact
description: Update contact records with new interactions, notes, or metadata. Maintains bidirectional links with journal entries.
when_to_use: After logging an interaction, when adding notes about someone, or updating contact details
---

# Update Contact Skill

Manage contact records in the people/ directory.

## Usage

### Find Contact

```bash
# Search by name
find people/ -name "*.md" | xargs grep -l "name: John"

# Or by filename
ls people/*/john-smith.md
```

### Update Last Contact

When interaction logged:

```yaml
# Update frontmatter
last_contact: 2025-12-12
```

### Add Interaction History

Append to Interaction History section:

```markdown
## Interaction History
- [2025-12-12](../../journal/2025/12/2025-12-12.md) - Brief description
```

### Add Notes

Append to Key Notes section:

```markdown
## Key Notes
- Considering startup (Dec 2025)
```

### Create New Contact

1. Determine category (family, friends, professional)
2. Create file from template:
   ```bash
   cp people/templates/contact.md people/professional/john-smith.md
   ```
3. Populate frontmatter and sections

## Examples

**Add interaction:**
```markdown
## Interaction History
- [2025-12-12](../../journal/2025/12/2025-12-12.md) - Coffee, caught up on life
- [2025-11-28](../../journal/2025/11/2025-11-28.md) - Met at conference
```

**Add note:**
```markdown
## Key Notes
- Has 2 kids (Emma, 8 and Jack, 5)
- Wife Sarah works in marketing
- Looking at startup opportunities (as of Dec 2025)
```
```

#### Historical Capture Skill (`agents/skills/historical-capture/SKILL.md`)

```markdown
---
name: historical-capture
description: Guide user through populating biography and historical memories. Use for initial setup and when memories surface during conversations.
when_to_use: During initial Life OS setup, when user mentions past memories, or during periodic biography reviews
---

# Historical Capture Skill

Help user populate their biography with historical context.

## Usage

### Initial Biography Setup

Guide user through each era with questions:

1. **Start with overview**:
   - Basic facts (birthdate, birthplace)
   - Current situation
   - Key context for Jobin

2. **Era by era**:
   ```
   "Let's capture some history from your [era] years ([age range]).
   - Where did you live during this time?
   - Who were the important people?
   - What were 2-3 major events or memories?"
   ```

3. **Capture stories**:
   When user shares a detailed memory, offer to create a story file.

### During Daily Use

When user mentions something historical:
```
User: "That reminds me of when I was in college..."

Jobin: "That sounds like a memory worth capturing! Should I:
1. Add it to your College era file
2. Create a standalone story
3. Just note it in today's journal"
```

### Missed Days Catchup

When days are missed:
```
Jobin: "I notice we haven't logged anything since [date].
Want to do a quick catchup? Just give me bullet points
and I'll organize them."
```

Creates either:
- Individual daily entries (if specific dates known)
- A catchup summary file (for fuzzy "routine week" periods)

## Examples

**Initial population prompt**:
```
Jobin: Let's build your life timeline! I'll ask about different periods.

Starting with basics:
- What's your birthdate and where were you born?
- Where do you currently live?
- Family situation (spouse, kids)?
```

**Story capture**:
```
User: ...and that's how I met my wife at that coffee shop

Jobin: That's a great origin story! I've created:
biography/stories/how-we-met.md

Want to add more details while it's fresh?
```
```

**Checklist:**
- [ ] Create daily-journal skill
- [ ] Create update-contact skill
- [ ] Create log-event skill (similar pattern)
- [ ] Create changelog-generator skill
- [ ] Create historical-capture skill
- [ ] Commit skills

### 7. Create Sample Files

Create one example of each type to establish patterns:

**Checklist:**
- [ ] Create sample journal entry for today
- [ ] Create 2-3 sample contacts
- [ ] Create sample event
- [ ] Create first changelog entry
- [ ] Commit samples

### 8. Initialize Biography

Create the biography foundation:

**Files to create:**
```bash
# Overview with basic facts
biography/overview.md

# Era stubs (minimal, to be populated over time)
biography/eras/00-childhood.md
biography/eras/01-teenage.md
biography/eras/02-college.md
biography/eras/03-early-career.md
biography/eras/04-establishing.md
biography/eras/05-current.md

# Theme stubs
biography/themes/education.md
biography/themes/career.md
biography/themes/relationships.md
biography/themes/travel.md

# Story index
biography/stories/_index.md
```

**Initial population approach:**
1. Fill in overview.md with basic facts and timeline
2. Add 1-2 bullet points to each era (minimum viable history)
3. Mark as "stub - to be expanded" in each file
4. Jobin will help expand these over time through conversation

**Checklist:**
- [ ] Create biography/overview.md with basic facts
- [ ] Create era stub files
- [ ] Create theme stub files
- [ ] Create stories index
- [ ] Commit biography foundation

### 9. Test Manual Workflow

Run through the workflow manually:

1. Invoke Jobin persona
2. Provide sample daily input
3. Verify Jobin creates/updates correct files
4. Verify changelog generated
5. Commit changes

**Checklist:**
- [ ] Test journal creation
- [ ] Test contact update
- [ ] Test cross-linking
- [ ] Test changelog generation
- [ ] Document any issues

---

## Success Criteria

Phase 1 is complete when:

- [ ] Repository exists with full directory structure
- [ ] All core templates created (journal, contact, event, biography)
- [ ] Jobin persona defined
- [ ] Basic skills documented (including historical-capture)
- [ ] Biography foundation exists (overview + era stubs)
- [ ] Manual workflow tested end-to-end
- [ ] Can process "Hey Jobin, I did X today" and see correct updates
- [ ] Can add historical memories to biography

---

## Next Steps

After Phase 1:
- Expand templates for all domains (Phase 2)
- Add Google Calendar integration
- Build weekly summary automation
- See [phase-2-expansion.md](phase-2-expansion.md)
