# Bird Bookmark Processor - Testing & Integration Plan

**Status**: In Progress  
**Created**: 2025-01-01  
**Goal**: Test Bird bookmark fetching, AI categorization, and design the data/agent integration

## Overview

Before setting up cron automation, we need to:
1. Validate the full pipeline works end-to-end
2. Design where data lives and how it's accessed
3. Plan agent integration for querying and triggering

## Phase 1: Authentication & Fetching

### 1.1 Configure Twitter Cookies
- [ ] Get `auth_token` and `ct0` from user's browser
- [ ] Add to server `.env` file
- [ ] Verify Bird CLI can authenticate

### 1.2 Test Bookmark Fetching
- [ ] Run Bird CLI standalone to fetch bookmarks
- [ ] Verify JSON output format
- [ ] Test with `BOOKMARK_LIMIT=5` for quick iteration

## Phase 2: AI Categorization

### 2.1 Verify Local AI Router
- [ ] Confirm router is running on server
- [ ] Test `/v1/chat/completions` endpoint
- [ ] Verify model routing works

### 2.2 Test Categorization
- [ ] Run processor with fetched bookmarks
- [ ] Validate AI response format (categories, priority, tags)
- [ ] Check error handling for malformed responses

## Phase 3: Data Storage Design

### 3.1 Current Design
```
apps/bird/data/
├── processed.json     # Set of processed tweet IDs (avoid duplicates)
└── bookmarks.json     # Cache of raw bookmark data (optional)

docs/
└── learning-list.md   # Living document of categorized resources
```

### 3.2 Questions to Resolve
- **Where does `learning-list.md` live?**
  - Option A: `docs/learning-list.md` (current) - in main repo, git-tracked
  - Option B: Separate repo for "second brain" content
  - Option C: Wiki.js page (queryable, web UI)

- **How are duplicates handled?**
  - Current: `processed.json` stores tweet IDs
  - On each run, skip already-processed IDs

- **Git commit workflow?**
  - Current: Container commits to `/repo` mount (~/server)
  - Commits with "Bird Bot" as author
  - Auto-push after each run

### 3.3 Data Persistence
- `data/` directory persists between runs (Docker volume)
- `processed.json` survives container rebuilds
- Learning list is in git, so always recoverable

## Phase 4: Agent Integration

### 4.1 Trigger Capabilities
How can the agent run Bird?

```bash
# Option 1: Docker compose (current)
docker compose -f ~/server/apps/bird/docker-compose.yml up

# Option 2: Direct script call
# Could add a wrapper script for agent use

# Option 3: Agent endpoint task
# POST /agent/run with task "Process my Twitter bookmarks"
```

### 4.2 Query Capabilities
How can the agent search/query bookmarks?

- **Option A**: Read `docs/learning-list.md` directly
- **Option B**: SQLite database for structured queries
- **Option C**: Memory system integration (store in Local AI Router memory)

### 4.3 Surfacing Results
- Learning list is markdown - easy to read/summarize
- Agent can grep for specific topics/tags
- Could add a "what's new" summary endpoint

## Phase 5: End-to-End Test

### 5.1 Full Pipeline Test
1. Fetch 5 bookmarks
2. Categorize with AI
3. Generate/update learning-list.md
4. Commit to git
5. Verify on GitHub

### 5.2 Validation Checklist
- [ ] Bookmarks fetched successfully
- [ ] AI categorization returns valid JSON
- [ ] Learning list has correct format
- [ ] Git commit appears in history
- [ ] No duplicate entries on re-run

## Success Criteria

1. **Fetching works**: Can retrieve bookmarks from X
2. **AI works**: Categorization produces useful output
3. **Persistence works**: Data survives restarts, no duplicates
4. **Git works**: Changes committed and pushed
5. **Agent-ready**: Clear path for agent to trigger/query

## Next Steps After Testing

- Set up cron job (every 6 hours)
- Add to homepage dashboard
- Create agent skill for querying learning list
- Consider expanding to likes, threads, etc.
