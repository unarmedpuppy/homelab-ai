# Biography System - Historical Memory & Life Context

**Purpose**: Capture your life story, historical memories, and era-based context that doesn't fit into daily journaling.

---

## Overview

At 38, you have decades of experiences, relationships, and memories that predate the Life OS system. This biography section provides:

1. **Era-based organization** - Life chapters, not specific dates
2. **Historical memory capture** - Things you remember, stories worth preserving
3. **Context for Jobin** - Background that informs daily interactions
4. **Living document** - Updated as you remember things or complete new chapters

---

## Directory Structure

```
life-os/
├── biography/
│   ├── overview.md              # Life timeline, key facts, quick reference
│   ├── eras/
│   │   ├── 00-childhood.md      # Birth - ~12 (1986-1998)
│   │   ├── 01-teenage.md        # ~13-17 (1999-2004)
│   │   ├── 02-college.md        # ~18-22 (2005-2009)
│   │   ├── 03-early-career.md   # ~23-27 (2010-2014)
│   │   ├── 04-establishing.md   # ~28-32 (2015-2019)
│   │   ├── 05-current.md        # ~33-present (2020-now)
│   │   ├── 06-parenting.md      # Overlapping era - fatherhood journey
│   │   └── _template.md
│   ├── themes/
│   │   ├── education.md         # Schools, degrees, learning journey
│   │   ├── career.md            # Job history, career evolution
│   │   ├── relationships.md     # Key relationships, how you met spouse, etc.
│   │   ├── travel.md            # Major trips and adventures
│   │   ├── homes.md             # Places you've lived
│   │   ├── hobbies.md           # Interests over time
│   │   └── milestones.md        # Major life events
│   ├── family-tree/
│   │   ├── tree.md              # Family tree overview with links
│   │   └── generations/         # Ancestry notes if desired
│   ├── stories/
│   │   ├── _index.md            # Index of stories
│   │   └── {story-slug}.md      # Individual memorable stories
│   └── people/
│       └── historical/          # People from the past (links to people/ when relevant)
```

---

## File Specifications

### Overview (`biography/overview.md`)

Quick reference for Jobin and future recall:

```markdown
---
name: Joshua Jenquist
born: YYYY-MM-DD
birthplace: City, State
current_age: 38
updated: 2025-12-12
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
| Childhood | 1986-1998 | [City], elementary/middle school |
| Teenage | 1999-2004 | High school, [key events] |
| College | 2005-2009 | [University], [major] |
| Early Career | 2010-2014 | First jobs, [city moves] |
| Establishing | 2015-2019 | [Marriage], [kids], [career growth] |
| Current | 2020-now | [Current chapter summary] |

## Life Themes
- [Key interests, values, recurring patterns]

## For Jobin
Key context for daily interactions:
- [Important background that affects daily life]
- [Relationships to remember]
- [Sensitivities or important notes]
```

### Era Template (`biography/eras/_template.md`)

```markdown
---
era: [Era Name]
years: YYYY-YYYY
age_range: X-Y
locations: [City, State]
updated: YYYY-MM-DD
---

# [Era Name] (YYYY-YYYY)

## Overview
[2-3 paragraph summary of this life chapter]

## Where I Lived
- [Address/City] (YYYY-YYYY) - [Notes]

## Key People
- [Name] - [Relationship, how met, significance]
- Links to: [../people/family/person.md] when applicable

## Education
- [School] (YYYY-YYYY) - [Degree/notes]

## Work
- [Job/Company] (YYYY-YYYY) - [Role, key experiences]

## Major Events
| Date/Year | Event | Significance |
|-----------|-------|--------------|
| YYYY | [Event] | [Why it matters] |

## Memorable Experiences
### [Experience Title]
[Story/memory]

### [Another Experience]
[Story/memory]

## What I Learned
- [Life lessons from this era]

## Artifacts
- Photos: [links or location references]
- Documents: [diplomas, letters, etc.]

## Connections to Present
- [How this era shaped who you are today]
- [People from this era still in your life]
```

### Theme Files

Thematic views that span multiple eras:

**`biography/themes/education.md`**
```markdown
---
updated: YYYY-MM-DD
---

# Education Journey

## Formal Education

| Years | School | Level | Notes |
|-------|--------|-------|-------|
| YYYY-YYYY | [Elementary] | K-5 | |
| YYYY-YYYY | [Middle] | 6-8 | |
| YYYY-YYYY | [High School] | 9-12 | |
| YYYY-YYYY | [University] | Undergrad | [Major] |

## Certifications & Training
- [Cert] (YYYY) - [Notes]

## Self-Learning
- [Topics, courses, books that shaped you]

## Teaching/Mentoring
- [Times you've taught others]
```

**`biography/themes/travel.md`**
```markdown
---
updated: YYYY-MM-DD
---

# Travel History

## Major Trips

| Year | Destination | Duration | Highlights |
|------|-------------|----------|------------|
| YYYY | [Place] | X days | [Key memories] |

## Places Lived
| Years | Location | Era | Notes |
|-------|----------|-----|-------|
| YYYY-YYYY | [City, State] | Childhood | |

## Countries Visited
- [Country] (YYYY) - [Context]

## Bucket List
- [ ] [Place to visit]
```

### Stories (`biography/stories/`)

Individual memorable stories worth preserving:

```markdown
---
title: [Story Title]
era: college
year: ~2007
people: [person1, person2]
location: [Place]
tags: [adventure, friendship, funny]
---

# [Story Title]

[The full story, written narratively]

## Why This Matters
[Why you want to remember this]

## People Involved
- [Name] - [Current status/link if in contacts]

## Photos
- [Links if available]
```

---

## Workflows

### Initial Population (Backfill)

When first setting up, Jobin can help with guided recall:

```
Jobin: Let's capture some history! I'll ask about different life periods.
Starting with college - what years were you there and where?

User: 2005-2009 at State University, majored in Computer Science

Jobin: Got it! What are 2-3 standout memories from college?

User: Road trip to [place] junior year, met [spouse] senior year,
that one professor who changed how I think about [topic]

Jobin: These are great. I've created:
- biography/eras/02-college.md with basic info
- Added the road trip and meeting [spouse] to Major Events
- Added a story stub for the professor impact

Want to expand on any of these, or move to another era?
```

### Ongoing Capture

When something triggers a memory during daily journaling:

```
User: Today reminded me of that summer in 2012 when we...

Jobin: That sounds like a memory worth preserving! Should I:
1. Add it to the Early Career era file
2. Create a standalone story in biography/stories/
3. Just note it in today's journal

User: Make it a story

Jobin: Created biography/stories/summer-2012-adventure.md
I've added a stub - want to flesh it out now or later?
```

### Missed Daily Entries

When you miss logging for a while:

```
Jobin: I notice we haven't logged anything for the past week.
Want to do a quick catchup? I can help you reconstruct:

- Dec 5-11, 2025 (7 days)

Just give me bullet points of what you remember and I'll
organize it into daily entries or a weekly summary.

User: Dec 5 was that work dinner, Dec 7 kids had soccer tournament,
rest was pretty routine

Jobin: Created:
- journal/2025/12/2025-12-05.md (work dinner noted)
- journal/2025/12/2025-12-07.md (soccer tournament)
- journal/2025/12/2025-W49-catchup.md (weekly summary for routine days)

The other days are marked as "routine - no specific events" so we
don't lose track of time.
```

### Era Transitions / Annual Biography Update

Yearly ritual to update the current era and reflect:

```
Jobin: It's January - time for the annual biography update!

Let's review 2025:
- 52 weeks logged
- 147 contacts interacted with
- 23 notable events

I'll draft additions to biography/eras/05-current.md.
Want to review what should be added to your life story?

Key candidates:
- [Major event from the year]
- [Relationship milestone]
- [Career change]
- [Travel highlight]
```

---

## Integration with Other Systems

### Links to Contacts

Historical people can link to active contacts:

```markdown
## Key People
- [John Smith](../../people/professional/john-smith.md) - College roommate,
  still close friends. Met freshman year in dorms.
```

### Links to Events/Memories

Era files can reference detailed event files:

```markdown
## Major Events
- [Wedding](../../events/2015/2015-06-15-wedding.md) - Married [spouse]
```

### Context for Jobin

Biography provides background for daily interactions:

```markdown
# For Jobin (in biography/overview.md)

## Important Context
- Dad passed in 2018 - Father's Day can be difficult
- Met spouse at [University] - they know [shared friends]
- Lived in [City] 2010-2015 - still have friends there
- Career pivot from [X] to [Y] in 2017 - formative experience
```

### Family Tree

The family tree links to contact files and provides genealogical context:

```markdown
# biography/family-tree/tree.md
---
updated: 2025-12-12
---

# Family Tree

## Immediate Family
- **Spouse**: [Name](../../people/family/spouse.md) - Married YYYY
- **Children**:
  - [Child 1](../../people/family/child1.md) - Born YYYY
  - [Child 2](../../people/family/child2.md) - Born YYYY

## Parents
- **Father**: [Name](../../people/family/dad.md) - (YYYY-YYYY)
- **Mother**: [Name](../../people/family/mom.md)

## Siblings
- [Sibling](../../people/family/sibling.md)

## Extended Family
### Paternal
- Grandparents: [Names]
- Aunts/Uncles: [Names]

### Maternal
- Grandparents: [Names]
- Aunts/Uncles: [Names]

## Family Notes
- [Important family history, traditions, stories]
```

### Photo Integration (Immich)

Photos are stored in Immich at `/jenquist-cloud` on the home server. Reference photos by:

1. **Album reference** in frontmatter:
```yaml
photos:
  album: "College Years"
  immich_album_id: "abc123"  # Optional: direct Immich album ID
```

2. **Specific photo references** in content:
```markdown
## Photos
- [Graduation Day](immich://album/graduation-2009)
- See Immich album: "2009 College Graduation"
```

3. **Future integration** (Phase 4 dashboard):
- Dashboard could pull thumbnails from Immich API
- Link directly to Immich web UI for full albums
- Consider: `https://immich.server.unarmedpuppy.com/albums/{id}`

**Note**: Photo files stay in Immich - Life OS only stores references/links, not actual images.

---

## Checklist for Implementation

### Phase 1 Addition
- [ ] Add `biography/` to directory structure
- [ ] Create overview.md template
- [ ] Create era template
- [ ] Add to Jobin's capabilities (guided recall, memory capture)

### Initial Population
- [ ] Create blank era files for each life chapter
- [ ] Populate overview.md with quick facts
- [ ] Add 2-3 key events per era (minimum viable history)

### Ongoing
- [ ] Jobin prompts for historical context when relevant
- [ ] Annual biography review ritual
- [ ] Story capture when memories surface

---

## Decisions Made

1. **Era boundaries** - Added `06-parenting` as an overlapping era dedicated to the fatherhood journey (runs parallel to establishing/current eras)

2. **Privacy levels** - All in one private repo, will use local Gitea instance (not GitHub) for privacy

3. **Family history** - Yes, includes family tree section (`biography/family-tree/`) that links to contact files in `people/family/`

4. **Photo integration** - Photos stay in Immich at `/jenquist-cloud` on home server. Life OS stores references/links only, not actual images. Future dashboard integration can pull from Immich API.
