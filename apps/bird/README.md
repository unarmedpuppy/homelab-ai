# Bird - X/Twitter Bookmark Processor

Automated bookmark processor that fetches your X/Twitter bookmarks, categorizes them with AI, and maintains a living document of technologies and resources to learn.

## Overview

This service:
1. Fetches your X bookmarks and likes using the [Bird CLI](https://github.com/steipete/bird)
2. Sends them to your local AI router for intelligent categorization
3. Updates a markdown document (`docs/learning-list.md`) with organized content
4. Commits changes to git automatically

## Prerequisites

You need your X/Twitter authentication cookies. Get them from your browser:

1. Open https://x.com and log in
2. Open DevTools (F12) → Application → Cookies → x.com
3. Copy values for:
   - `auth_token`
   - `ct0`

## Setup

1. **Create environment file:**
   ```bash
   cp env.template .env
   ```

2. **Add your Twitter cookies to `.env`:**
   ```bash
   AUTH_TOKEN=your_auth_token_here
   CT0=your_ct0_token_here
   ```

3. **Build the container:**
   ```bash
   docker compose build
   ```

## Usage

### Manual Run (One-shot)

```bash
docker compose up
```

This will:
- Fetch your recent bookmarks and likes
- Process new items through AI categorization
- Update `docs/learning-list.md`
- Commit and push changes

### Scheduled Run (Cron)

Add to your crontab on the server:

```bash
# Run bookmark processor every 6 hours
0 */6 * * * cd ~/server/apps/bird && docker compose up --build 2>&1 >> ~/server/logs/bird.log
```

### Daemon Mode (Continuous)

Set in `.env`:
```bash
RUN_MODE=daemon
SLEEP_INTERVAL=21600  # 6 hours in seconds
```

Then:
```bash
docker compose up -d
```

## Configuration

| Variable | Default | Description |
|----------|---------|-------------|
| `AUTH_TOKEN` | - | X.com auth_token cookie (required) |
| `CT0` | - | X.com ct0 cookie (required) |
| `AI_ROUTER_URL` | `http://local-ai-router:8000` | Local AI router endpoint |
| `BOOKMARK_LIMIT` | `50` | Max bookmarks to fetch per run |
| `RUN_MODE` | `cron` | `cron` (one-shot) or `daemon` (continuous) |
| `SLEEP_INTERVAL` | `21600` | Seconds between runs in daemon mode (6 hours) |

## Output

The processor creates/updates `docs/learning-list.md` with sections:

- **Technologies to Explore** - Tools, frameworks, libraries
- **Concepts to Learn** - Ideas, patterns, methodologies  
- **Resources to Read** - Tutorials, articles, repos
- **Project Ideas** - Inspirations from bookmarks
- **Other Bookmarks** - Uncategorized items

Items are prioritized (1-5 scale) and tagged with relevant topics.

## Architecture

```
┌─────────────┐     ┌──────────────────┐     ┌─────────────────┐
│ Bird CLI    │────▶│ process_bookmarks│────▶│ local-ai-router │
│ (fetch X)   │     │ .py              │     │ (categorize)    │
└─────────────┘     └──────────────────┘     └─────────────────┘
                            │
                            ▼
                    ┌──────────────────┐
                    │ docs/learning-   │
                    │ list.md + git    │
                    └──────────────────┘
```

## Data Files

| File | Purpose |
|------|---------|
| `data/processed.json` | Track processed tweet IDs (avoid duplicates) |
| `data/bookmarks.json` | Cache of raw bookmark data |

## Troubleshooting

### "Failed to fetch bookmarks"

Your Twitter cookies may have expired. Get fresh ones from your browser.

### "AI request failed"

Check that local-ai-router is running:
```bash
curl http://localhost:8012/health
```

### "Git error"

Ensure the repo mount is writable:
```bash
docker compose run --rm bird ls -la /repo
```

## References

- [Bird CLI](https://github.com/steipete/bird) - Twitter CLI tool
- [Local AI Router](../local-ai-router/README.md) - AI inference router
