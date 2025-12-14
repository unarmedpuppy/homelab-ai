# Phase 4: Visualization Dashboard

**Status**: Planned (after Phase 3)
**Goal**: Build a web dashboard to visualize the markdown-based knowledge base

---

## Overview

Create a web interface that renders the Life OS markdown files into an interactive dashboard. Think of it as a personal "mission control" that aggregates and visualizes your life data.

---

## Dashboard Sections

### Home / Overview

```
┌─────────────────────────────────────────────────────────────┐
│                     Life OS Dashboard                        │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐       │
│  │   Today      │  │   Upcoming   │  │    Goals     │       │
│  │              │  │              │  │              │       │
│  │ 3 events     │  │ Mom's bday   │  │ 67% weekly   │       │
│  │ 2 contacts   │  │ in 3 days    │  │ progress     │       │
│  └──────────────┘  └──────────────┘  └──────────────┘       │
│                                                              │
│  ┌────────────────────────────────────────────────────┐     │
│  │                 Recent Activity                     │     │
│  │  • Updated John Smith contact                       │     │
│  │  • Logged lunch meeting                            │     │
│  │  • Completed quarterly review                      │     │
│  └────────────────────────────────────────────────────┘     │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

### Journal View

- Calendar view of entries
- Click to view/edit daily entry
- Weekly/monthly summaries
- Search across entries

### People View

- Contact cards with last interaction
- Family tree visualization
- Interaction timeline
- Birthday calendar
- "Haven't talked to in X days" alerts

### Finance View

- Net worth chart over time
- Account balances summary
- Property portfolio
- Monthly cash flow
- Budget vs actual

### Fatherhood View

- Goals checklist with progress
- Milestone timeline per child
- Activity log
- Memory highlights

### Assets & Inventory

- Asset list with values
- Vehicle maintenance due dates
- Collection summaries
- Serial number lookup

### Goals View

- Annual goals with progress bars
- Quarterly review summaries
- Life goals board
- Habit tracking (if implemented)

---

## Technical Architecture

### Option A: Static Site Generator

**Tech**: Astro, Next.js, or Hugo with custom templates

**Pros**:
- Simple, fast
- Can be hosted on GitHub Pages
- No backend needed

**Cons**:
- Requires rebuild on changes
- Limited interactivity

**Implementation**:
1. Build script reads all markdown files
2. Generates static HTML pages
3. Deploy to GitHub Pages or home server
4. Webhook triggers rebuild on push

### Option B: Dynamic Server

**Tech**: FastAPI (Python) or Express (Node) with React/Vue frontend

**Pros**:
- Real-time updates
- Rich interactivity
- Can include edit capabilities

**Cons**:
- More complex
- Requires running server

**Implementation**:
1. Backend reads markdown files on demand
2. API endpoints for each section
3. Frontend renders data
4. Optional: Edit capabilities with git commit

### Option C: Obsidian Publish Alternative

**Tech**: Quartz, MkDocs, or similar

**Pros**:
- Designed for markdown knowledge bases
- Good search, graph view
- Easy setup

**Cons**:
- Less customizable
- May not fit dashboard metaphor

---

## Recommended: Option B (Docker Service)

Given the home-server context, a Docker-deployed dynamic app makes sense:

```
apps/life-os-dashboard/
├── docker-compose.yml
├── backend/
│   ├── Dockerfile
│   ├── main.py           # FastAPI app
│   ├── parsers/          # Markdown parsers per domain
│   └── requirements.txt
├── frontend/
│   ├── Dockerfile
│   ├── src/
│   │   ├── App.tsx
│   │   ├── pages/
│   │   └── components/
│   └── package.json
└── README.md
```

### Backend API

```python
# Example endpoints
GET /api/journal/today
GET /api/journal/{date}
GET /api/contacts
GET /api/contacts/{id}
GET /api/finance/overview
GET /api/goals/current
GET /api/changelog/recent
GET /api/search?q={query}
```

### Frontend Components

```
src/
├── pages/
│   ├── Dashboard.tsx        # Home overview
│   ├── Journal.tsx          # Journal browser
│   ├── People.tsx           # Contact management
│   ├── Finance.tsx          # Financial overview
│   ├── Fatherhood.tsx       # Parenting dashboard
│   ├── Assets.tsx           # Asset tracking
│   └── Goals.tsx            # Goal tracking
├── components/
│   ├── ContactCard.tsx
│   ├── JournalEntry.tsx
│   ├── GoalProgress.tsx
│   ├── NetWorthChart.tsx
│   └── ActivityFeed.tsx
└── utils/
    └── api.ts
```

---

## UI/UX Considerations

### Design Principles

1. **Glanceable** - Key metrics visible immediately
2. **Drill-down** - Click to see details
3. **Searchable** - Global search across all content
4. **Mobile-friendly** - Works on phone for quick lookups
5. **Dark mode** - Easy on eyes, consistent with home-server aesthetic

### Visual Elements

- **Cards** for summary views
- **Timelines** for historical data
- **Charts** for numeric trends (net worth, goals)
- **Graph view** for relationships between entities
- **Calendar** for time-based navigation

---

## Integration with Home Server

### Traefik Labels

```yaml
labels:
  - "traefik.enable=true"
  - "traefik.http.routers.life-os.rule=Host(`life.server.unarmedpuppy.com`)"
  - "traefik.http.routers.life-os.tls=true"
  - "traefik.http.routers.life-os.middlewares=auth@file"  # Protected
```

### Homepage Integration

```yaml
- Life OS:
    icon: mdi-brain
    href: https://life.server.unarmedpuppy.com
    description: Personal knowledge base
    group: Personal
```

---

## Checklist

### Design
- [ ] Wireframe each page
- [ ] Choose color scheme / design system
- [ ] Define component library

### Backend
- [ ] Set up FastAPI project
- [ ] Markdown parsing for each domain
- [ ] API endpoints for all data
- [ ] Search implementation
- [ ] Git integration (read repo path)

### Frontend
- [ ] Set up React/Vue project
- [ ] Implement all pages
- [ ] Charts and visualizations
- [ ] Mobile responsive
- [ ] Dark mode

### Deployment
- [ ] Dockerize backend and frontend
- [ ] docker-compose.yml
- [ ] Traefik integration
- [ ] Homepage entry

### Testing
- [ ] API tests
- [ ] Frontend tests
- [ ] End-to-end flow

---

## Success Criteria

Phase 4 complete when:
- [ ] Dashboard accessible at life.server.unarmedpuppy.com
- [ ] All major sections viewable
- [ ] Can search across all content
- [ ] Mobile-friendly
- [ ] Integrated into homepage
- [ ] Updates reflect within minutes of git push

---

## Future Enhancements

- Edit capabilities from dashboard (commit back to git)
- Graph visualization of entity relationships
- AI-powered insights ("You haven't talked to X in 30 days")
- Widget view for mobile home screen
- Voice interface via Jobin
