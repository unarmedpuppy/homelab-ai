# Phase 2: Domain Expansion

**Status**: Planned (after Phase 1)
**Goal**: Build out all life domains with templates, expand Jobin's capabilities

---

## Deliverables

1. Complete templates for all domains
2. Google Calendar integration skill
3. Weekly/monthly summary generators
4. Enhanced Jobin interactions
5. Changelog automation

---

## Domain Templates to Create

### Finance Domain

#### Account Template (`finance/accounts/`)
```markdown
---
name:
type: # checking, savings, investment, retirement, crypto
institution:
account_number_last4:
opened:
primary_use:
---

# {{ACCOUNT_NAME}}

## Details
- Institution:
- Type:
- Opened:

## Current Balance
| Date | Balance | Notes |
|------|---------|-------|
| 2025-12-12 | $X,XXX | |

## Notes

```

#### Property Template (`finance/properties/`)
```markdown
---
address:
type: # primary, rental, vacation, commercial
purchased:
purchase_price:
current_value:
mortgage:
  lender:
  rate:
  payment:
  remaining:
---

# {{ADDRESS}}

## Property Details
- Bedrooms:
- Bathrooms:
- Sq Ft:
- Year Built:
- Lot Size:

## Financial Summary
| Metric | Value |
|--------|-------|
| Purchase Price | |
| Current Value | |
| Equity | |
| Monthly Mortgage | |
| Property Tax (annual) | |
| Insurance (annual) | |

## For Rentals
See: [tenants.md](tenants.md) | [financials.md](financials.md)

## Maintenance
See: [maintenance.md](maintenance.md)
```

### Assets Domain

#### Vehicle Template (`assets/vehicles/`)
```markdown
---
year:
make:
model:
trim:
vin:
purchased:
purchase_price:
current_value:
---

# {{YEAR}} {{MAKE}} {{MODEL}}

## Details
- VIN:
- Color:
- Mileage:

## Registration & Insurance
- Registration Expires:
- Insurance:
- Policy #:

## Maintenance History
| Date | Mileage | Service | Cost | Shop |
|------|---------|---------|------|------|
| | | | | |

## Notes

```

### Inventory Domain

#### Collection Template
```markdown
---
category:
total_items:
estimated_value:
storage_location:
last_updated:
---

# {{COLLECTION_NAME}}

## Overview
- Total Items:
- Estimated Value:
- Storage:

## Inventory

### {{SUBCATEGORY}}
| Item | Condition | Value | Serial/ID | Notes |
|------|-----------|-------|-----------|-------|
| | | | | |

## Insurance
- Covered under:
- Rider needed:

## Notes

```

### Health Domain

#### Medications Template
```markdown
---
updated:
---

# Medications

## Current Medications
| Medication | Dose | Frequency | Prescriber | Purpose | Started |
|------------|------|-----------|------------|---------|---------|
| | | | | | |

## Supplements
| Supplement | Dose | Frequency | Purpose |
|------------|------|-----------|---------|
| | | | |

## Allergies
-

## Pharmacy
- Name:
- Phone:
- Address:
```

### Fatherhood Domain

#### Child Milestones Template
```markdown
---
child:
year:
---

# {{CHILD_NAME}} - {{YEAR}} Milestones

## Academic
| Date | Milestone | Notes |
|------|-----------|-------|
| | | |

## Sports/Activities
| Date | Milestone | Notes |
|------|-----------|-------|
| | | |

## Personal Growth
| Date | Milestone | Notes |
|------|-----------|-------|
| | | |

## Memorable Moments
<!-- Special memories from this year -->

## Photos
<!-- Links to photos -->
```

---

## Skills to Build

### Google Calendar Integration

`agents/skills/google-calendar-sync/SKILL.md`

**Purpose**: Pull calendar events into daily journal

**Implementation Options**:
1. Google Calendar API with service account
2. CalDAV sync
3. Manual ICS export/import

**Output**: Populate journal Schedule section

### Weekly Summary Generator

`agents/skills/weekly-summary/SKILL.md`

**Purpose**: Auto-generate weekly rollup from daily journals

**Process**:
1. Read all daily journals for the week
2. Aggregate: interactions, accomplishments, events
3. Calculate: contacts made, goals progress
4. Generate `journal/YYYY/weekly/YYYY-WXX.md`

### Morning Briefing Generator

`agents/skills/morning-briefing/SKILL.md`

**Purpose**: Generate daily briefing for Jobin to present

**Components**:
1. Today's calendar (when integrated)
2. Birthdays in next 7 days (scan contacts)
3. Open reminders/todos
4. Goal status check
5. Relevant contact context for today's meetings

### Evening Review Processor

`agents/skills/evening-review/SKILL.md`

**Purpose**: Process unstructured daily input into structured updates

**Process**:
1. Parse natural language input
2. Identify: people, events, accomplishments, todos
3. Update: journal, contacts, events
4. Generate: changelog
5. Confirm: summary back to user

---

## Checklist

### Templates
- [ ] Finance: account, property, tenant, budget
- [ ] Assets: vehicle, electronics
- [ ] Inventory: collection, item
- [ ] Health: overview, medications, appointments
- [ ] Career: resume, skills, certifications
- [ ] Learning: book, course, notes
- [ ] Projects: project template
- [ ] Travel: trip, packing list
- [ ] Home: maintenance schedule, warranty
- [ ] Legal: document registry
- [ ] Subscriptions: subscription list
- [ ] Goals: annual, quarterly review

### Skills
- [ ] Google Calendar sync
- [ ] Weekly summary generator
- [ ] Monthly summary generator
- [ ] Morning briefing
- [ ] Evening review processor
- [ ] Birthday reminder checker
- [ ] Goal progress tracker

### Automation
- [ ] Changelog auto-generator script
- [ ] Template populator script
- [ ] Backlink updater script

---

## Success Criteria

Phase 2 complete when:
- [ ] All domain templates exist
- [ ] Can create any type of record from template
- [ ] Weekly summaries auto-generate
- [ ] Morning briefings work (even without calendar)
- [ ] Evening review processes input reliably
