# Bird Bookmark Processor Reference

Automated X/Twitter bookmark processor that categorizes bookmarks using AI and maintains a living learning document.

## Overview

Bird processor fetches your X bookmarks and likes, uses AI to categorize them, and updates a markdown document with organized learning resources.

## Architecture

```
┌─────────────┐     ┌──────────────────┐     ┌─────────────────┐     ┌──────────┐
│ Bird CLI    │────▶│ Process          │────▶│ Local AI Router │────▶│ Git Repo  │
│ (fetch X)   │     │ (Python)         │     │ (categorize)    │     │ (update) │
└─────────────┘     └──────────────────┘     └─────────────────┘     └──────────┘
```

## Components

### Bird CLI
- **What**: Twitter/X CLI tool
- **Purpose**: Fetch bookmarks and likes via undocumented GraphQL API
- **Installation**: `npm install -g @steipete/bird`
- **Commands used**:
  - `bird bookmarks -n 50 --json` - Fetch bookmarks
  - `bird likes -n 50 --json` - Fetch likes
  - `bird whoami` - Verify authentication

### Python Processor
- **File**: `apps/bird/process_bookmarks.py`
- **Purpose**: Orchestrate entire workflow
- **Functions**:
  - Fetch bookmarks/likes via Bird CLI
  - Deduplicate against processed IDs
  - Send to AI for categorization
  - Generate markdown document
  - Commit changes to git

### Local AI Router
- **Endpoint**: `http://local-ai-router:8000/v1/chat/completions`
- **Purpose**: Intelligent categorization
- **Headers**: `X-Project: bird-bookmark-processor`, `X-User-ID: bird-bot`
- **Model**: `auto` (let router choose best provider)
- **Temperature**: 0.3 (deterministic categorization)

### Git Integration
- **Repo**: `~/server/` (mounted as `/repo` in container)
- **Output**: `docs/learning-list.md`
- **Commit message**: Auto-generated (e.g., "bird: Update learning list with 12 items")

## Data Flow

### Input
1. Fetch latest 50 bookmarks and 50 likes
2. Merge and deduplicate by tweet ID
3. Filter out already-processed tweets

### Processing
4. Send tweet text to AI for categorization
5. AI responds with JSON structure:
   ```json
   {
     "items": [
       {
         "tweet_id": "123456789012345678",
         "summary": "Thread-safe Rust async patterns",
         "category": "technologies",
         "topics": ["rust", "async", "patterns"],
         "priority": 5,
         "url": "https://x.com/user/status/123456789012345678"
       }
     ]
   }
   ```

### Output
6. Generate/append to `docs/learning-list.md`:
   - Technologies to Explore
   - Concepts to Learn
   - Resources to Read
   - Project Ideas
   - Other Bookmarks

7. Commit changes with auto-generated message
8. Save processed IDs to `data/processed.json`

## Configuration

### Environment Variables
```bash
# Authentication (REQUIRED)
AUTH_TOKEN=your_auth_token_from_browser
CT0=your_ct0_cookie_from_browser

# AI Router
AI_ROUTER_URL=http://local-ai-router:8000

# Processing Options
BOOKMARK_LIMIT=50          # How many to fetch per run
RUN_MODE=cron              # "cron" (one-shot) or "daemon"
SLEEP_INTERVAL=21600       # 6 hours in seconds (daemon only)

# Git Configuration
GIT_USER_NAME=Bird Bot
GIT_USER_EMAIL=bird@server.unarmedpuppy.com
```

### Getting Twitter Cookies
1. Open https://x.com and log in
2. DevTools (F12) → Application → Cookies → x.com
3. Copy values for:
   - `auth_token`
   - `ct0`

### File Structure
```
apps/bird/
├── Dockerfile              # Node 22 + Python + Bird CLI
├── docker-compose.yml      # Service configuration
├── process_bookmarks.py  # Main processing script
├── requirements.txt        # Python dependencies
├── env.template           # Configuration template
├── .env                   # Secrets (gitignored)
├── README.md              # User documentation
└── data/
    ├── processed.json     # Track processed tweet IDs
    └── bookmarks.json    # Cache raw data
```

## Running Modes

### Manual (One-Shot)
```bash
cd apps/bird
docker compose up --build
```

### Scheduled (Cron)
On server, add to crontab:
```cron
# Run every 6 hours
0 */6 * * * cd ~/server/apps/bird && docker compose up --build >> ~/server/logs/bird.log 2>&1
```

### Daemon (Continuous)
Set in `.env`:
```bash
RUN_MODE=daemon
SLEEP_INTERVAL=21600  # 6 hours
```

Then:
```bash
docker compose up -d
```

## Output Format

### Markdown Structure
```markdown
# Learning List

_Last update: 2026-01-01 10:00_

## Technologies to Explore
- [.....] **Rust, async, patterns**: Thread-safe Rust async patterns [link](https://x.com/user/status/123456789012345678)
- [....] **Deno**: Fast JavaScript runtime [link](https://x.com/user/status/9876543210987654321)

## Concepts to Learn
- **GraphQL query batching**: Efficient API pattern [link](https://x.com/user/status/543216789012345678)
```

### Categories
| Category | Description | Examples |
|----------|-------------|-----------|
| `technologies` | Tools, frameworks, libraries | Rust, Deno, PostgreSQL |
| `concepts` | Ideas, patterns, methodologies | GraphQL batching, Rate limiting |
| `resources` | Tutorials, articles, docs | "X API docs, Blog posts |
| `projects` | Project ideas, inspirations | CLI tools, Web scrapers |
| `other` | Uncategorized items | Random tweets, memes |

### Priority Levels
| Priority | Meaning |
|----------|---------|
| 5 | Must learn immediately |
| 4 | High priority |
| 3 | Medium priority |
| 2 | Nice to know |
| 1 | Lowest priority |

## Troubleshooting

### Authentication Failed
- **Error**: Bird CLI returns auth failure
- **Cause**: Twitter cookies expired
- **Fix**: Get fresh cookies from browser and update `.env`

### AI Router Not Responding
```bash
# Check if router is running
docker ps | grep local-ai-router

# Check health endpoint
curl http://localhost:8012/health
```

### Git Commit Failed
```bash
# Check logs
docker compose logs bird

# Verify repo mount
docker compose run --rm bird ls -la /repo
```

### No New Tweets Processed
- **Cause**: All bookmarks/likes already processed
- **Check**: View `data/processed.json`
- **Manual run**: Delete `data/processed.json` and re-run

## Related
- [Bird CLI GitHub](https://github.com/steipete/bird)
- [Local AI Router](./local-ai-router.md)
- [Skill: bird-bookmark-processor](../skills/bird-bookmark-processor/SKILL.md)
- [apps/bird/README.md](../../apps/bird/README.md)

## Development Notes

### AI Categorization Prompt
The system uses a structured prompt asking AI to:
1. Analyze tweet content for technical topics
2. Extract tools, frameworks, libraries, patterns
3. Identify concepts vs resources vs projects
4. Assign priority (1-5 scale) based on importance
5. Return JSON with tweet_id, summary, category, topics, priority, url

### Deduplication
- Track processed tweet IDs in `data/processed.json`
- Prevent re-processing same tweets
- Allows incremental updates

### Error Handling
- Bird CLI failures logged but don't crash
- AI request failures logged but don't crash
- Git errors don't prevent retry on next run
- All errors logged with timestamps

## Future Enhancements
- [ ] N8n integration for manual trigger
- [ ] Web UI for viewing processed items
- [ ] Statistics on categories/priorities
- [ ] Automated cookie refresh mechanism
- [ ] Backup/export of learning list
