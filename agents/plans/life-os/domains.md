# Life OS - Complete Domain Reference

All life domains to track, organized by priority and complexity.

---

## Tier 1: Core (Phase 1)

Essential for daily operation.

### Biography
**Purpose**: Historical life context, era-based memories, stories worth preserving

| File Type | Location |
|-----------|----------|
| Overview | `biography/overview.md` |
| Era | `biography/eras/XX-era-name.md` |
| Theme | `biography/themes/{theme}.md` |
| Story | `biography/stories/{story-slug}.md` |

**Era Structure**:
- 00-childhood (birth - ~12)
- 01-teenage (~13-17)
- 02-college (~18-22)
- 03-early-career (~23-27)
- 04-establishing (~28-32)
- 05-current (~33-present)
- 06-parenting (overlapping - dedicated fatherhood journey)

**Family Tree**: `biography/family-tree/tree.md` - Links to contacts in `people/family/`

**Photo Integration**: References to Immich albums at `/jenquist-cloud` (links only, no actual images)

**Key Fields (Era)**:
- era, years, age_range, locations
- Where I lived, Key people, Education, Work
- Major events, Memorable experiences
- What I learned, Connections to present

**Themes**: Education, Career, Relationships, Travel, Homes, Hobbies, Milestones

See [biography-system.md](biography-system.md) for full specification.

### Journal
**Purpose**: Daily log of activities, interactions, and reflections

| File Type | Location | Template |
|-----------|----------|----------|
| Daily entry | `journal/YYYY/MM/YYYY-MM-DD.md` | `journal/templates/daily.md` |
| Weekly summary | `journal/YYYY/weekly/YYYY-WXX.md` | `journal/templates/weekly.md` |

**Key Fields**:
- date, mood, energy, weather (frontmatter)
- Morning intentions
- Schedule/events
- Interactions (linked to contacts)
- Accomplishments
- Reflections
- Tomorrow's priorities

### People
**Purpose**: Contact sheets with relationship context

| Category | Location |
|----------|----------|
| Family | `people/family/` |
| Friends | `people/friends/` |
| Professional | `people/professional/` |
| Acquaintances | `people/acquaintances/` |

**Key Fields**:
- name, relationship, category
- met (date), birthday
- contact info (email, phone, address)
- tags, last_contact
- About section
- Gift ideas
- Key notes
- Interaction history (links to journal)

### Events
**Purpose**: Shared experiences linked to multiple contacts

| File Type | Location |
|-----------|----------|
| Event | `events/YYYY/YYYY-MM-DD-event-name.md` |

**Key Fields**:
- date, type, participants, location, tags
- Summary
- Participant links
- Photos (external links)
- Memories

### Changelog
**Purpose**: Daily summary of all changes to the repository

| File Type | Location |
|-----------|----------|
| Daily log | `changelog/YYYY-MM-DD.md` |

**Format**:
```markdown
# Changelog: 2025-12-12

## Files Modified
- journal/2025/12/2025-12-12.md (created)
- people/professional/john-smith.md (updated last_contact)

## Summary
- Logged lunch with John Smith
- Added note about his job search
```

---

## Tier 2: Life Management (Phase 2)

Important domains for comprehensive life tracking.

### Fatherhood
**Purpose**: Intentional parenting tracking

| File Type | Location |
|-----------|----------|
| Goals | `fatherhood/goals.md` |
| Child milestones | `fatherhood/milestones/{child}/YYYY.md` |
| Activity log | `fatherhood/activities/activity-log.md` |
| Lessons | `fatherhood/lessons/lessons-to-teach.md` |

**Goals Structure**:
- Core values to model
- Annual goals
- Long-term milestones (age-based)

**Milestones Structure**:
- Academic
- Sports/Activities
- Personal growth
- Memorable moments

### Finance
**Purpose**: Financial tracking and net worth

| File Type | Location |
|-----------|----------|
| Overview | `finance/overview.md` |
| Account | `finance/accounts/{account}.md` |
| Property | `finance/properties/{address}/` |
| Budget | `finance/budgets/YYYY.md` |

**Overview Structure**:
- Net worth summary table
- Monthly cash flow
- Property list with links

**Account Fields**:
- name, type, institution
- account_number_last4
- Balance history table

**Property Structure** (subdirectory):
- overview.md - Property details, value
- tenants.md - Current/past tenants
- maintenance.md - Maintenance history
- financials.md - Income/expenses

### Assets
**Purpose**: Big-ticket item tracking

| Category | Location |
|----------|----------|
| Vehicles | `assets/vehicles/{vehicle}/` |
| Real Estate | Links to `finance/properties/` |
| Electronics | `assets/electronics/` |

**Vehicle Structure**:
- overview.md - VIN, registration, insurance
- maintenance.md - Service history

**Vehicle Fields**:
- year, make, model, trim, vin
- purchased, purchase_price, current_value
- Registration, insurance details
- Maintenance table

### Inventory
**Purpose**: Collections and smaller valuable items

| Category | Location |
|----------|----------|
| Video games | `inventory/video-games/` |
| Electronics | `inventory/electronics/` |
| Collectibles | `inventory/collectibles/` |

**Collection Fields**:
- category, total_items, estimated_value
- storage_location, last_updated
- Item tables with serial numbers

### Goals
**Purpose**: Goal setting and tracking

| File Type | Location |
|-----------|----------|
| Annual | `goals/YYYY.md` |
| Life goals | `goals/life-goals.md` |
| Reviews | `goals/reviews/YYYY-QX.md` |

**Annual Goals Structure**:
- Categories (health, career, relationships, etc.)
- Specific, measurable goals
- Progress tracking

**Review Structure**:
- What went well
- What didn't
- Adjustments for next quarter

---

## Tier 3: Extended Domains (Phase 2+)

Additional life areas for comprehensive coverage.

### Health
**Purpose**: Medical records and wellness tracking

| File Type | Location |
|-----------|----------|
| Overview | `health/overview.md` |
| Medications | `health/medications.md` |
| Appointments | `health/appointments.md` |
| Medical records | `health/medical-records/` |
| Fitness | `health/fitness/` |

**Overview Fields**:
- Primary doctor, specialists
- Allergies
- Current conditions
- Health goals

**Medications Fields**:
- Current medications table (name, dose, frequency, purpose)
- Supplements
- Pharmacy info

### Career
**Purpose**: Professional life tracking

| File Type | Location |
|-----------|----------|
| Resume | `career/resume.md` |
| Skills | `career/skills.md` |
| Certifications | `career/certifications.md` |
| Goals | `career/goals.md` |

**Skills Fields**:
- Skill categories
- Proficiency levels
- Last used

### Learning
**Purpose**: Knowledge acquisition tracking

| File Type | Location |
|-----------|----------|
| Reading list | `learning/books/reading-list.md` |
| Book notes | `learning/books/{title}.md` |
| Courses | `learning/courses/` |
| Notes | `learning/notes/` |

**Book Fields**:
- title, author, genre
- status (reading, completed, abandoned)
- started, finished
- rating
- Key takeaways

### Projects
**Purpose**: Personal project tracking

| Status | Location |
|--------|----------|
| Active | `projects/active/` |
| Completed | `projects/completed/` |
| Someday | `projects/someday/` |

**Project Fields**:
- name, status, started
- Description
- Goals
- Progress log

### Travel
**Purpose**: Trip planning and memories

| File Type | Location |
|-----------|----------|
| Trips | `travel/trips/YYYY-destination/` |
| Packing lists | `travel/packing-lists/` |
| Loyalty programs | `travel/loyalty-programs.md` |

**Trip Structure**:
- overview.md - Itinerary, bookings
- memories.md - Highlights, photos
- expenses.md - Budget tracking

### Home
**Purpose**: Home management

| File Type | Location |
|-----------|----------|
| Maintenance | `home/maintenance-schedule.md` |
| Projects | `home/projects/` |
| Warranties | `home/warranties/` |

**Maintenance Schedule**:
- Monthly, quarterly, annual tasks
- Due dates
- Last completed

### Legal
**Purpose**: Important document tracking

| File Type | Location |
|-----------|----------|
| Document registry | `legal/documents.md` |
| Contracts | `legal/contracts/` |

**Document Registry Fields**:
- Document name
- Location (physical and digital)
- Expiration (if applicable)
- Notes

### Subscriptions
**Purpose**: Recurring service tracking

| File Type | Location |
|-----------|----------|
| Subscriptions | `subscriptions/subscriptions.md` |

**Fields**:
- Service name
- Cost (monthly/annual)
- Renewal date
- Payment method
- Cancel instructions

### Ideas
**Purpose**: Capture bucket for random thoughts

| File Type | Location |
|-----------|----------|
| Ideas | `ideas/ideas.md` |

**Structure**:
- Date captured
- Idea description
- Category/tags
- Status (new, exploring, acted on, discarded)

### Memories
**Purpose**: Special moments to preserve

| File Type | Location |
|-----------|----------|
| Memory | `memories/YYYY/title.md` |

**Fields**:
- date, participants, location
- Description
- Photos
- Why it matters

---

## Domain Interconnections

```
                    ┌─────────┐
                    │ Journal │
                    └────┬────┘
                         │ daily entries link to
         ┌───────────────┼───────────────┐
         │               │               │
    ┌────▼────┐    ┌─────▼─────┐   ┌─────▼─────┐
    │ People  │    │  Events   │   │   Goals   │
    └────┬────┘    └─────┬─────┘   └───────────┘
         │               │
         │ family links  │ events link to
         │               │
    ┌────▼────┐    ┌─────▼─────┐
    │Fatherhood│   │ Memories  │
    └─────────┘    └───────────┘

    ┌─────────┐    ┌─────────┐    ┌─────────┐
    │ Finance │───▶│ Assets  │───▶│Inventory│
    └─────────┘    └─────────┘    └─────────┘
         │
         │ properties
         ▼
    ┌─────────┐
    │  Home   │
    └─────────┘
```

---

## Linking Conventions

### Contact Links
```markdown
[John Smith](../people/professional/john-smith.md)
[Mom](../people/family/mom.md)
```

### Event Links
```markdown
[Christmas 2025](../events/2025/2025-12-25-christmas.md)
```

### Journal Links
```markdown
[December 12](../journal/2025/12/2025-12-12.md)
```

### Property Links (from finance overview)
```markdown
[123 Main St](properties/123-main-st/)
```

### Backlinks
Each file should have a "Related" or "References" section showing what links TO it:
```markdown
## References
- [2025-12-12](../journal/2025/12/2025-12-12.md) - Mentioned in daily journal
- [Christmas 2025](../events/2025/2025-12-25-christmas.md) - Participated
```

---

## Frontmatter Standards

All files use YAML frontmatter. Common fields:

```yaml
---
# Identity
name: Required for contacts, assets
title: Required for events, projects

# Timestamps
created: YYYY-MM-DD
updated: YYYY-MM-DD (auto-updated by Jobin)
date: YYYY-MM-DD (for dated content)

# Classification
type: Category within domain
status: Current state (active, completed, etc.)
tags: [tag1, tag2]

# Relationships
related: [path/to/file.md]
---
```

---

## Maintenance

### Daily
- Journal entry updated
- Contacts' last_contact updated
- Changelog generated

### Weekly
- Weekly summary generated
- Goal progress reviewed

### Monthly
- Financial overview updated
- Subscription renewal check

### Quarterly
- Goal review
- Net worth update
- Contact "haven't talked to" review

### Annual
- Annual goals set
- Year in review
- Archive old changelogs
