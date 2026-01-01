---
name: bird-bookmark-processor
description: X/Twitter bookmark processor that categorizes bookmarks with AI and maintains a learning list
when_to_use: When setting up, troubleshooting, or running the Bird bookmark processor
---

# Bird Bookmark Processor

Fetches X/Twitter bookmarks, categorizes them with AI, and maintains `docs/learning-list.md`.

## Quick Start

```bash
cd apps/bird

# 1. Create .env with your Twitter cookies
cp env.template .env
# Edit .env and add AUTH_TOKEN and CT0 from your browser

# 2. Build and run
docker compose build
docker compose up
```

## Get Twitter Cookies

1. Open https://x.com and log in
2. Open DevTools (F12) → Application → Cookies → x.com
3. Copy values for `auth_token` and `ct0`

## Manual Run

```bash
cd ~/server/apps/bird
docker compose up --build
```

## Server Cron Setup

Add to crontab on server:

```bash
crontab -e
```

```cron
# Run Bird bookmark processor every 6 hours
0 */6 * * * cd ~/server/apps/bird && docker compose up --build >> ~/server/logs/bird.log 2>&1
```

Create logs directory:
```bash
mkdir -p ~/server/logs
```

## Output Location

- **Learning list**: `docs/learning-list.md`
- **Processed IDs**: `apps/bird/data/processed.json`
- **Logs**: `~/server/logs/bird.log`

## Troubleshooting

### Cookies expired
Get fresh cookies from browser and update `.env`.

### AI router not responding
```bash
curl http://localhost:8012/health
```

### Check container logs
```bash
docker compose logs bird
```

## Related

- [Bird README](../../../apps/bird/README.md)
- [Local AI Router](../../reference/local-ai-router.md)
