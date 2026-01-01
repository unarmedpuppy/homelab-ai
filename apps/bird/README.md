# Bird - X/Twitter Bookmark Storage

Automated bookmark fetcher that stores your X/Twitter bookmarks and likes in a SQLite database for viewing and querying.

## Overview

This service:
1. Fetches your X bookmarks and likes using the [Bird CLI](https://github.com/steipete/bird)
2. Stores them in a local SQLite database (`data/bird.db`)
3. Provides a data source for the Bird Viewer UI and external agents

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
- Store new tweets in the SQLite database
- Skip duplicates automatically

### Scheduled Run (n8n)

Import the n8n workflow for automated processing:

1. Open n8n: https://n8n.server.unarmedpuppy.com
2. Import workflow from: `apps/n8n/workflows/bird-bookmark-processor.json`
3. Activate the workflow

The workflow runs every 6 hours, parses output, and can notify on failures.

**Alternative (cron)**: If you prefer cron, use `scripts/bird-cron.sh`:
```bash
0 */6 * * * ~/server/scripts/bird-cron.sh
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
| `BOOKMARK_LIMIT` | `50` | Max bookmarks to fetch per run |
| `RUN_MODE` | `cron` | `cron` (one-shot) or `daemon` (continuous) |
| `SLEEP_INTERVAL` | `21600` | Seconds between runs in daemon mode (6 hours) |

## Architecture

```
┌─────────────┐     ┌──────────────────┐     ┌─────────────────┐
│ Bird CLI    │────▶│ process_bookmarks│────▶│ SQLite Database │
│ (fetch X)   │     │ .py              │     │ (data/bird.db)  │
└─────────────┘     └──────────────────┘     └─────────────────┘
                                                     │
                                                     ▼
                                          ┌─────────────────────┐
                                          │ Bird Viewer UI /    │
                                          │ External Agents     │
                                          └─────────────────────┘
```

## Database Schema

| Table | Purpose |
|-------|---------|
| `runs` | Processing runs (timestamp, source, status, post_count) |
| `posts` | Stored tweets (tweet_id, author, content, url, media_urls) |
| `categorizations` | AI categorization (for future use) |
| `approvals` | Approval workflow (for future use) |

## Troubleshooting

### "Failed to fetch bookmarks"

Your Twitter cookies may have expired. Get fresh ones from your browser.

### Database issues

Check the database file exists and has correct permissions:
```bash
docker compose run --rm bird ls -la /app/data/
```

## Web Interface

- **API**: https://bird-api.server.unarmedpuppy.com
- **Viewer**: https://bird-viewer.server.unarmedpuppy.com

## References

- [Bird CLI](https://github.com/steipete/bird) - Twitter CLI tool
- [Bird Viewer](../bird-viewer/) - React UI for viewing stored bookmarks
