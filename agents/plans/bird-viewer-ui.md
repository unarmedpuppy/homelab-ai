# Bird Viewer UI - Implementation Plan

## Overview

Interactive web UI for viewing and managing Bird bookmark processing pipeline. Shows what posts were fetched, AI categorization decisions, and allows manual intervention before writing to learning-list.md.

## Requirements

### Functional
1. **Run History** - View all processing runs with timestamp, status, post count
2. **Post Feed** - See each fetched post with content, author, original link
3. **AI Decisions** - View categorization, tags, confidence for each post
4. **Changes Log** - See what would be/was written to learning-list.md
5. **Interactive Actions**:
   - Re-run a failed fetch
   - Re-categorize a post (override AI)
   - Delete/ignore a post
   - Manually add a post (paste URL)
   - Edit entry before save
   - Approve/reject before writing

### Non-Functional
- Persistent storage (SQLite) - searchable archive forever
- Standalone app at `bird-viewer.server.unarmedpuppy.com`
- Traefik auth (bypassed on LAN)
- Match local-ai-dashboard tech stack

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        Bird Viewer                               │
├─────────────────────────────────────────────────────────────────┤
│  React Frontend (Vite + TanStack Query + Tailwind)              │
│  - Run history view                                              │
│  - Post detail view                                              │
│  - Approval queue                                                │
│  - Manual entry form                                             │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                     Bird Viewer API                              │
│                  (FastAPI - Python)                              │
├─────────────────────────────────────────────────────────────────┤
│  GET  /api/runs              - List all runs                     │
│  GET  /api/runs/:id          - Run details with posts            │
│  GET  /api/posts             - List posts (filterable)           │
│  GET  /api/posts/:id         - Post detail                       │
│  POST /api/posts/:id/recategorize  - Re-run AI categorization   │
│  POST /api/posts/:id/approve       - Approve for learning-list  │
│  POST /api/posts/:id/reject        - Reject/ignore post         │
│  PUT  /api/posts/:id         - Edit post/categorization          │
│  DELETE /api/posts/:id       - Delete post                       │
│  POST /api/posts/manual      - Add post manually (URL)           │
│  POST /api/runs/trigger      - Trigger new fetch run             │
│  GET  /api/pending           - Posts awaiting approval           │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                      SQLite Database                             │
├─────────────────────────────────────────────────────────────────┤
│  runs: id, timestamp, status, source, post_count, error         │
│  posts: id, run_id, tweet_id, author, content, url, created_at  │
│  categorizations: id, post_id, category, tags, confidence,      │
│                   reasoning, is_override, created_at             │
│  approvals: id, post_id, status, learning_list_entry,           │
│             written_at, edited_by                                │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Bird Processor                                │
│               (Existing - Modified)                              │
├─────────────────────────────────────────────────────────────────┤
│  - Write to DB instead of directly to learning-list.md          │
│  - Posts go to "pending" status by default                       │
│  - Only approved posts written to learning-list.md               │
│  - OR: Auto-approve mode for hands-off operation                 │
└─────────────────────────────────────────────────────────────────┘
```

## Tech Stack

### Frontend (apps/bird-viewer/)
- React 19 + TypeScript
- Vite
- Tailwind CSS 4
- TanStack Query (react-query)
- Axios
- React Router

### Backend (apps/bird-viewer/api/ or apps/bird/api/)
- FastAPI (Python) - co-located with Bird processor
- SQLite with SQLAlchemy
- Shared database with Bird processor

## Database Schema

```sql
-- Processing runs
CREATE TABLE runs (
    id TEXT PRIMARY KEY,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    source TEXT NOT NULL,  -- 'bookmarks', 'likes', 'manual'
    status TEXT NOT NULL,  -- 'running', 'success', 'error'
    post_count INTEGER DEFAULT 0,
    error_message TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Fetched posts/tweets
CREATE TABLE posts (
    id TEXT PRIMARY KEY,
    run_id TEXT REFERENCES runs(id),
    tweet_id TEXT UNIQUE,
    author_username TEXT,
    author_display_name TEXT,
    content TEXT,
    url TEXT,
    media_urls TEXT,  -- JSON array
    tweet_created_at DATETIME,
    fetched_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- AI categorizations (multiple per post for history)
CREATE TABLE categorizations (
    id TEXT PRIMARY KEY,
    post_id TEXT REFERENCES posts(id),
    category TEXT,
    tags TEXT,  -- JSON array
    confidence REAL,
    reasoning TEXT,
    model_used TEXT,
    is_override BOOLEAN DEFAULT FALSE,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Approval workflow
CREATE TABLE approvals (
    id TEXT PRIMARY KEY,
    post_id TEXT REFERENCES posts(id) UNIQUE,
    status TEXT NOT NULL,  -- 'pending', 'approved', 'rejected'
    learning_list_entry TEXT,  -- Generated markdown
    edited_entry TEXT,  -- User-edited version
    written_at DATETIME,  -- When written to learning-list.md
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Indexes
CREATE INDEX idx_posts_run ON posts(run_id);
CREATE INDEX idx_categorizations_post ON categorizations(post_id);
CREATE INDEX idx_approvals_status ON approvals(status);
CREATE INDEX idx_runs_timestamp ON runs(timestamp DESC);
```

## UI Components

### 1. Dashboard / Run History
```
┌─────────────────────────────────────────────────────────────────┐
│  Bird Viewer                                    [Trigger Run ▼] │
├─────────────────────────────────────────────────────────────────┤
│  Pending Approval: 12        │  Total Posts: 847               │
│  Today's Runs: 4             │  Last Run: 2 hours ago ✓        │
├─────────────────────────────────────────────────────────────────┤
│  Recent Runs                                                     │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │ ✓ 2025-01-01 17:00  │ bookmarks │ 5 posts  │ [View]       │ │
│  │ ✓ 2025-01-01 11:00  │ bookmarks │ 3 posts  │ [View]       │ │
│  │ ✗ 2025-01-01 05:00  │ bookmarks │ 0 posts  │ [Retry]      │ │
│  │ ✓ 2024-12-31 23:00  │ likes     │ 8 posts  │ [View]       │ │
│  └────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
```

### 2. Approval Queue
```
┌─────────────────────────────────────────────────────────────────┐
│  Pending Approval (12)                      [Approve All] [━━━] │
├─────────────────────────────────────────────────────────────────┤
│  ┌────────────────────────────────────────────────────────────┐ │
│  │ @elikimd                                    2h ago         │ │
│  │ ─────────────────────────────────────────────────────────  │ │
│  │ "The best way to learn distributed systems is to build     │ │
│  │  one. Here's my journey building a Raft implementation..." │ │
│  │                                                             │ │
│  │ Category: Tech/Distributed Systems    Confidence: 0.92     │ │
│  │ Tags: [raft] [distributed] [learning]                      │ │
│  │                                                             │ │
│  │ Learning List Entry:                                        │ │
│  │ ┌──────────────────────────────────────────────────────┐   │ │
│  │ │ ## Distributed Systems - Raft Implementation         │   │ │
│  │ │ [@elikimd](https://x.com/...) shares journey...     │   │ │
│  │ └──────────────────────────────────────────────────────┘   │ │
│  │                                                             │ │
│  │ [✓ Approve] [✗ Reject] [✎ Edit] [↻ Re-categorize]         │ │
│  └────────────────────────────────────────────────────────────┘ │
│                                                                  │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │ @nextjs                                     5h ago         │ │
│  │ ...                                                        │ │
│  └────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
```

### 3. Post Detail / Edit View
```
┌─────────────────────────────────────────────────────────────────┐
│  ← Back to Queue                                                 │
├─────────────────────────────────────────────────────────────────┤
│  Original Post                                                   │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │ @elikimd · Dec 31, 2024                    [Open on X ↗]  │ │
│  │                                                             │ │
│  │ The best way to learn distributed systems is to build      │ │
│  │ one. Here's my journey building a Raft implementation...   │ │
│  │                                                             │ │
│  │ 🔗 github.com/elikimd/raft-go                              │ │
│  └────────────────────────────────────────────────────────────┘ │
│                                                                  │
│  AI Categorization                            [↻ Re-run AI]     │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │ Category: [Tech/Distributed Systems    ▼]                  │ │
│  │ Tags:     [raft] [distributed] [learning] [+]              │ │
│  │ Confidence: 0.92                                            │ │
│  │ Reasoning: "Post discusses building distributed systems..." │ │
│  └────────────────────────────────────────────────────────────┘ │
│                                                                  │
│  Learning List Entry                                             │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │ ## Distributed Systems - Raft Implementation               │ │
│  │                                                             │ │
│  │ [@elikimd](https://x.com/elikimd/status/123) shares their  │ │
│  │ journey building a Raft consensus implementation in Go.    │ │
│  │                                                             │ │
│  │ Key takeaways:                                              │ │
│  │ - Start with leader election                                │ │
│  │ - Log replication is the hard part                          │ │
│  │                                                             │ │
│  │ 🔗 [Source](https://x.com/...) | [GitHub](https://...)     │ │
│  └────────────────────────────────────────────────────────────┘ │
│                                                                  │
│  [✓ Approve & Write] [✗ Reject] [Save Draft]                   │
└─────────────────────────────────────────────────────────────────┘
```

### 4. Manual Add
```
┌─────────────────────────────────────────────────────────────────┐
│  Add Post Manually                                               │
├─────────────────────────────────────────────────────────────────┤
│  Tweet URL:                                                      │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │ https://x.com/username/status/123456789                    │ │
│  └────────────────────────────────────────────────────────────┘ │
│                                                                  │
│  [Fetch & Categorize]                                           │
└─────────────────────────────────────────────────────────────────┘
```

## Implementation Phases

### Phase 1: Database & API Foundation
1. Create SQLite schema
2. Modify Bird processor to write to DB instead of file
3. Add "auto-approve" mode toggle for backwards compatibility
4. Create FastAPI backend with basic CRUD endpoints
5. Dockerize API

### Phase 2: Frontend Shell
1. Scaffold Vite + React + Tailwind project
2. Set up TanStack Query
3. Create routing (Dashboard, Queue, Post Detail)
4. Build basic layouts and navigation

### Phase 3: Core Views
1. Dashboard with run history
2. Approval queue list
3. Post detail view
4. Read-only first, verify data flow

### Phase 4: Interactive Features
1. Approve/reject functionality
2. Edit entry before save
3. Re-categorize (call AI again)
4. Manual post addition
5. Trigger new run

### Phase 5: Polish & Deploy
1. Traefik labels (auth + LAN bypass)
2. Error handling and loading states
3. Search and filtering
4. Mobile responsiveness
5. Documentation

## File Structure

```
apps/bird-viewer/
├── api/                      # FastAPI backend
│   ├── __init__.py
│   ├── main.py               # FastAPI app
│   ├── database.py           # SQLAlchemy setup
│   ├── models.py             # ORM models
│   ├── schemas.py            # Pydantic schemas
│   └── routes/
│       ├── runs.py
│       ├── posts.py
│       └── approvals.py
├── src/                      # React frontend
│   ├── api/
│   │   └── client.ts
│   ├── components/
│   │   ├── Dashboard.tsx
│   │   ├── ApprovalQueue.tsx
│   │   ├── PostDetail.tsx
│   │   ├── PostCard.tsx
│   │   ├── RunHistory.tsx
│   │   └── ManualAdd.tsx
│   ├── types/
│   │   └── api.ts
│   ├── App.tsx
│   └── main.tsx
├── docker-compose.yml
├── Dockerfile
├── package.json
├── vite.config.ts
├── tailwind.config.js
└── README.md
```

## Docker Compose

```yaml
services:
  bird-viewer:
    build: .
    container_name: bird-viewer
    restart: unless-stopped
    environment:
      - DATABASE_URL=sqlite:///data/bird.db
      - AI_ROUTER_URL=http://local-ai-router:8000
    volumes:
      - ./data:/app/data
      - ../bird/docs:/app/docs  # For writing learning-list.md
    networks:
      - my-network
    labels:
      - "traefik.enable=true"
      # LAN access (no auth)
      - "traefik.http.routers.bird-viewer-lan.rule=Host(`bird-viewer.server.unarmedpuppy.com`) && ClientIP(`192.168.86.0/24`)"
      - "traefik.http.routers.bird-viewer-lan.entrypoints=websecure"
      - "traefik.http.routers.bird-viewer-lan.tls.certresolver=myresolver"
      - "traefik.http.routers.bird-viewer-lan.priority=100"
      # External access (with auth)
      - "traefik.http.routers.bird-viewer.rule=Host(`bird-viewer.server.unarmedpuppy.com`)"
      - "traefik.http.routers.bird-viewer.entrypoints=websecure"
      - "traefik.http.routers.bird-viewer.tls.certresolver=myresolver"
      - "traefik.http.routers.bird-viewer.middlewares=homepage-auth@docker"
      - "traefik.http.routers.bird-viewer.priority=50"
      - "traefik.http.services.bird-viewer.loadbalancer.server.port=3000"
      # Homepage integration
      - "homepage.group=AI & Automation"
      - "homepage.name=Bird Viewer"
      - "homepage.icon=twitter"
      - "homepage.href=https://bird-viewer.server.unarmedpuppy.com"
      - "homepage.description=Twitter bookmark processor"

networks:
  my-network:
    external: true
```

## Migration Path

### Existing Bird Processor Changes

1. **Add database writer** alongside file writer
2. **Config flag**: `APPROVAL_MODE=auto|manual`
   - `auto`: Write to DB + immediately to learning-list.md (current behavior)
   - `manual`: Write to DB only, require approval via UI
3. **Shared SQLite database** between Bird processor and Bird Viewer

### Data Migration

For existing learning-list.md entries, optionally parse and import to DB for unified history.

## Open Questions

1. **Shared DB or API calls?** 
   - Bird processor writes directly to SQLite (simpler)
   - OR Bird processor calls Bird Viewer API (more decoupled)
   - Recommendation: Shared SQLite for simplicity

2. **Real-time updates?**
   - Polling (simple, TanStack Query handles this)
   - WebSockets (more complex, better UX)
   - Recommendation: Start with polling, add WS later if needed

3. **Batch operations?**
   - Approve all pending
   - Bulk categorization
   - Recommendation: Add in Phase 4

## Effort Estimate

| Phase | Effort |
|-------|--------|
| Phase 1: Database & API | 4-6 hours |
| Phase 2: Frontend Shell | 2-3 hours |
| Phase 3: Core Views | 4-6 hours |
| Phase 4: Interactive Features | 6-8 hours |
| Phase 5: Polish & Deploy | 3-4 hours |
| **Total** | **19-27 hours** |

## Next Steps

1. Review and approve this plan
2. Create Beads task for tracking
3. Begin Phase 1 implementation
