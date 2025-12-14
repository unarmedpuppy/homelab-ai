# Life OS - Personal Knowledge Base System

**Created**: 2025-12-12
**Status**: Planning
**Goal**: Build a comprehensive, agent-managed personal knowledge base using structured markdown files

## Vision

A "second brain" system that serves as the single source of truth for everything in your life - relationships, finances, assets, goals, memories, and daily activities. Managed through structured markdown files, updated by an AI assistant (Jobin), and eventually visualized through a custom dashboard.

### Core Principles

1. **Plain text first** - All data in markdown for portability and longevity
2. **Git-backed** - Full history, branching, collaboration
3. **Agent-friendly** - Consistent structure enables AI assistance
4. **Progressive complexity** - Start simple, expand as needed
5. **Linked knowledge** - Events, memories, and notes connect to people/assets

---

## Architecture Overview

```
life-os/                          # New repository
├── README.md                     # System overview and quick reference
├── AGENTS.md                     # Agent instructions (inherited pattern)
├── .gitignore                    # Ignore secrets, local files
│
├── journal/                      # Daily entries
│   ├── 2025/
│   │   ├── 12/
│   │   │   ├── 2025-12-12.md    # Daily journal entry
│   │   │   └── ...
│   │   └── weekly/
│   │       └── 2025-W50.md      # Weekly summary (auto-generated)
│   └── templates/
│       ├── daily.md
│       └── weekly.md
│
├── people/                       # Contact sheets
│   ├── family/
│   │   ├── _index.md            # Family overview
│   │   ├── spouse-name.md
│   │   └── child-name.md
│   ├── friends/
│   ├── professional/
│   └── templates/
│       └── contact.md
│
├── fatherhood/                   # Dedicated parenting section
│   ├── goals.md                  # Fatherhood goals and values
│   ├── milestones/
│   │   └── child-name/
│   │       └── 2025.md          # Milestones by year
│   ├── activities/
│   │   └── activity-log.md      # Activities done together
│   └── lessons/
│       └── lessons-to-teach.md  # Things to pass on
│
├── finance/                      # Financial tracking
│   ├── overview.md              # Net worth summary, links to details
│   ├── accounts/
│   │   ├── checking-bank.md
│   │   ├── savings-bank.md
│   │   └── investment-brokerage.md
│   ├── properties/
│   │   └── property-address/
│   │       ├── overview.md      # Property details
│   │       ├── tenants.md       # Current/past tenants
│   │       ├── maintenance.md   # Maintenance history
│   │       └── financials.md    # Income/expenses
│   ├── budgets/
│   └── taxes/
│       └── 2024/
│
├── assets/                       # Big-ticket items
│   ├── vehicles/
│   │   └── 2022-car-model/
│   │       ├── overview.md      # VIN, registration, insurance
│   │       └── maintenance.md   # Service history
│   ├── real-estate/             # Links to finance/properties
│   └── electronics/
│       └── major-items.md       # Laptops, TVs, etc.
│
├── inventory/                    # Collections and smaller items
│   ├── video-games/
│   │   └── games.md             # Game list with platforms
│   ├── electronics/
│   │   └── devices.md           # Serial numbers, warranties
│   ├── collectibles/
│   │   └── magic-cards/
│   │       └── collection.md
│   └── templates/
│
├── health/                       # Health records
│   ├── overview.md              # Current health status
│   ├── medical-records/
│   ├── medications.md
│   ├── appointments.md
│   └── fitness/
│       └── goals.md
│
├── career/                       # Professional life
│   ├── resume.md
│   ├── skills.md
│   ├── certifications.md
│   └── goals.md
│
├── learning/                     # Knowledge acquisition
│   ├── books/
│   │   └── reading-list.md
│   ├── courses/
│   └── notes/
│
├── projects/                     # Personal projects
│   ├── active/
│   ├── completed/
│   └── someday/
│
├── travel/                       # Trip planning and memories
│   ├── trips/
│   │   └── 2025-destination/
│   ├── packing-lists/
│   └── loyalty-programs.md
│
├── home/                         # Home management
│   ├── maintenance-schedule.md
│   ├── projects/
│   └── warranties/
│
├── legal/                        # Important documents
│   ├── documents.md             # List of important docs and locations
│   └── contracts/
│
├── subscriptions/                # Services and recurring costs
│   └── subscriptions.md
│
├── goals/                        # Goal tracking
│   ├── 2025.md                  # Annual goals
│   ├── life-goals.md            # Long-term vision
│   └── reviews/
│       └── 2025-q1.md           # Quarterly reviews
│
├── ideas/                        # Capture bucket
│   └── ideas.md
│
├── events/                       # Shared events/memories
│   ├── 2025/
│   │   └── 2025-12-25-christmas.md
│   └── templates/
│       └── event.md
│
├── memories/                     # Special memories to preserve
│   └── 2025/
│
├── biography/                    # Historical life context (pre-system)
│   ├── overview.md              # Life timeline, quick facts
│   ├── eras/                    # Era-based life chapters
│   │   ├── 00-childhood.md
│   │   ├── 01-teenage.md
│   │   ├── 02-college.md
│   │   ├── 03-early-career.md
│   │   ├── 04-establishing.md
│   │   ├── 05-current.md
│   │   └── 06-parenting.md      # Overlapping era - fatherhood journey
│   ├── family-tree/
│   │   └── tree.md              # Family tree with links to contacts
│   ├── themes/                  # Cross-era thematic views
│   │   ├── education.md
│   │   ├── career.md
│   │   ├── relationships.md
│   │   └── travel.md
│   └── stories/                 # Individual memorable stories
│
├── changelog/                    # Daily change summaries
│   └── 2025-12-12.md
│
├── agents/                       # Agent system (like home-server)
│   ├── personas/
│   │   └── jobin.md             # Life assistant persona
│   ├── skills/
│   │   ├── daily-journal/
│   │   ├── update-contact/
│   │   ├── log-event/
│   │   ├── morning-briefing/
│   │   ├── evening-review/
│   │   └── ...
│   └── reference/
│
└── scripts/                      # Automation scripts
    ├── generate-changelog.py
    ├── weekly-summary.py
    └── google-calendar-sync.py
```

---

## Domain Specifications

### Journal (`journal/`)

Daily entries are the heartbeat of the system. Each day captures:

```markdown
---
date: 2025-12-12
mood: good
energy: 7/10
weather: sunny, 65F
---

# Thursday, December 12, 2025

## Morning Intentions
- [ ] Review Q4 goals
- [ ] Call Mom

## Events
- 9:00 AM - Team standup
- 12:00 PM - Lunch with [John Smith](../people/professional/john-smith.md)
- 6:00 PM - Soccer practice with [Kids](../people/family/)

## Interactions
### [John Smith](../people/professional/john-smith.md)
- Discussed project timeline
- He mentioned job hunting - follow up next week

### [Child Name](../people/family/child-name.md)
- Great practice today, scored 2 goals
- Asked about getting a dog again

## Accomplishments
- Completed quarterly report
- Fixed bug in trading bot

## Reflections
Good productive day. Need to carve out more 1:1 time with kids.

## Tomorrow
- [ ] Follow up with John about job search
- [ ] Research dog breeds
```

### People (`people/`)

Contact sheets with relationship context:

```markdown
---
name: John Smith
relationship: colleague
company: Acme Corp
role: Senior Engineer
met: 2023-06-15
birthday: 1985-03-22
contact:
  email: john@example.com
  phone: 555-123-4567
  linkedin: linkedin.com/in/johnsmith
tags: [work, engineering, mentor]
last_contact: 2025-12-12
---

# John Smith

## About
Senior engineer at Acme Corp. Met at the 2023 tech conference. Great resource for distributed systems questions.

## Gift Ideas
- Likes craft beer (IPAs)
- Into woodworking

## Key Notes
- Has 2 kids (Emma, 8 and Jack, 5)
- Wife is Sarah, works in marketing
- Considering job change (as of Dec 2025)

## Interaction History
- [2025-12-12](../journal/2025/12/2025-12-12.md) - Lunch, discussed job hunting
- [2025-11-15](../journal/2025/11/2025-11-15.md) - Project kickoff meeting
```

### Fatherhood (`fatherhood/`)

Dedicated space for intentional parenting:

**goals.md:**
```markdown
# Fatherhood Goals

## Core Values to Model
- [ ] Patience in difficult moments
- [ ] Curiosity and love of learning
- [ ] Kindness to strangers
- [ ] Financial responsibility

## Annual Goals (2025)
- [ ] Weekly 1:1 time with each child
- [ ] Teach basic cooking (5 recipes each)
- [ ] One camping trip
- [ ] Read together 3x/week

## Long-term Milestones
### Age-Based Goals
- **Age 8**: Teach to ride bike, basic swimming
- **Age 10**: First solo overnight with friend
- **Age 12**: Intro to personal finance
- **Age 16**: Driving lessons
```

### Finance (`finance/`)

High-level tracking with drill-down capability:

**overview.md:**
```markdown
---
updated: 2025-12-12
---

# Financial Overview

## Net Worth Summary
| Category | Amount | Notes |
|----------|--------|-------|
| Cash | $XX,XXX | [Accounts](accounts/) |
| Investments | $XXX,XXX | [Details](accounts/investment-brokerage.md) |
| Real Estate Equity | $XXX,XXX | [Properties](properties/) |
| Vehicles | $XX,XXX | [Assets](../assets/vehicles/) |
| **Total Assets** | $X,XXX,XXX | |
| Liabilities | -$XXX,XXX | Mortgages, loans |
| **Net Worth** | $X,XXX,XXX | |

## Monthly Cash Flow
- Income: $XX,XXX
- Expenses: $X,XXX
- Savings Rate: XX%

## Properties
- [123 Main St](properties/123-main-st/) - Rental, $X,XXX/mo income
- [456 Oak Ave](properties/456-oak-ave/) - Primary residence
```

---

## Linking Strategy

### Standard Markdown Links
All cross-references use relative markdown links:
```markdown
[John Smith](../people/professional/john-smith.md)
[Christmas 2025](../events/2025/2025-12-25-christmas.md)
```

### Backlink Convention
Files that reference other files should be discoverable. Use a grep-able pattern:
```markdown
## Related
<!-- backlinks auto-generated -->
- Referenced by: [2025-12-12](../journal/2025/12/2025-12-12.md)
```

### Tag System
YAML frontmatter tags enable filtering:
```yaml
tags: [family, birthday, 2025]
```

---

## Jobin - Life Assistant Persona

### Personality
- Name: Jobin
- Style: Conversational, friendly, proactive
- Tone: Warm but efficient, like a trusted executive assistant

### Capabilities
1. **Morning Briefing** - Calendar, birthdays, reminders, goals check-in
2. **Evening Review** - Process daily input, update contacts, log events
3. **Contact Updates** - Add interactions, notes, update last_contact
4. **Event Logging** - Create event files, link to participants
5. **Goal Tracking** - Check progress, suggest adjustments
6. **Weekly Summary** - Auto-generate weekly rollup
7. **Historical Capture** - Guided recall for biography/era population
8. **Catchup Mode** - Handle missed days with retrospective entries
9. **Memory Preservation** - Capture stories and memories as they surface

### Interaction Modes

**Manual (Phase 1)**:
```
User: Hey Jobin, I had lunch with John Smith today. We talked about
his job search - he's looking at startups. Also, picked up the kids
from soccer, great practice.

Jobin: Got it! I've updated:
- John Smith's contact: Added note about startup job search,
  set follow-up reminder for next week
- Today's journal: Added lunch with John, soccer pickup
- Child's contact: Noted great soccer practice

Anything else from today?
```

**Automated (Phase 2 - n8n)**:
- Pull Google Calendar events
- Aggregate screen time data
- Process text message summaries
- Generate daily changelog

---

## Implementation Phases

### Phase 1: Foundation (Manual, This Week)
See: [phase-1-foundation.md](phase-1-foundation.md)

- [ ] Create repository structure
- [ ] Build core templates (journal, contact, event)
- [ ] Create Jobin persona
- [ ] Build basic skills (daily-journal, update-contact)
- [ ] Manual workflow: dump notes → Jobin processes

### Phase 2: Expansion (Next 2-4 Weeks)
See: [phase-2-expansion.md](phase-2-expansion.md)

- [ ] Add all domain templates (finance, assets, fatherhood, etc.)
- [ ] Build changelog generator
- [ ] Weekly summary automation
- [ ] Google Calendar integration skill
- [ ] More sophisticated Jobin interactions

### Phase 3: Automation (n8n Integration)
See: [phase-3-automation.md](phase-3-automation.md)

- [ ] n8n workflows for data aggregation
- [ ] Telegram bot interface for Jobin
- [ ] Automated daily briefings
- [ ] Data source integrations (screen time, gaming, git activity)

### Phase 4: Visualization (Dashboard)
See: [phase-4-dashboard.md](phase-4-dashboard.md)

- [ ] Design dashboard UI
- [ ] Build markdown parser/aggregator
- [ ] Deploy as Docker service
- [ ] Integration with home-server homepage

---

## Open Questions

1. **Repo name**: `life-os`, `second-brain`, `personal-kb`, `vault`, other?
2. **Sensitive data**: Should financial details be in a separate private repo?
3. **Photo/media storage**: Link to external storage or include in repo?
4. **Backup strategy**: Beyond git, any additional backup needs?

---

## Related Documents

- [phase-1-foundation.md](phase-1-foundation.md) - Getting started
- [phase-2-expansion.md](phase-2-expansion.md) - Full domain buildout
- [phase-3-automation.md](phase-3-automation.md) - n8n integration
- [phase-4-dashboard.md](phase-4-dashboard.md) - Visualization layer
- [biography-system.md](biography-system.md) - Historical memory & life context
- [domains.md](domains.md) - Complete domain reference

---

## Decisions Made

1. **Repo name**: `life-os`
2. **Storage**: All in one private repo, local git (Gitea) for privacy
3. **Link style**: Standard markdown links (not wiki-style)

---

## Changelog

- **2025-12-12**: Initial plan created
- **2025-12-12**: Added biography system for historical context
