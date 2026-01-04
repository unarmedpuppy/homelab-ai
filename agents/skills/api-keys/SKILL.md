---
name: api-keys
description: Manage API keys for homelab-ai LLM Router and configure dashboard authentication
when_to_use: When setting up or troubleshooting homelab-ai API authentication, creating new API keys, or fixing 401 errors from the dashboard
---

# Homelab-AI API Key Management

## Overview

The homelab-ai LLM Router uses API key authentication for protected endpoints (`/v1/chat/completions`, `/v1/audio/speech`, `/v1/images/*`). Keys are stored as SHA-256 hashes in SQLite.

## Key Locations

- **Router DB**: `/data/local-ai-router.db` (inside llm-router container)
- **Auth module**: `llm-router/auth.py`
- **Dashboard nginx**: `dashboard/nginx.conf.template`

## Creating API Keys

### 1. Ensure Database Table Exists

```bash
ssh -p 4242 unarmedpuppy@192.168.86.47 "docker exec llm-router python3 -c '
import sqlite3
conn = sqlite3.connect(\"/data/local-ai-router.db\")
cursor = conn.cursor()
cursor.execute(\"\"\"
    CREATE TABLE IF NOT EXISTS client_api_keys (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        key_hash TEXT NOT NULL UNIQUE,
        key_prefix TEXT NOT NULL,
        name TEXT NOT NULL,
        created_at DATETIME NOT NULL,
        last_used_at DATETIME,
        expires_at DATETIME,
        enabled BOOLEAN NOT NULL DEFAULT 1,
        scopes TEXT,
        metadata TEXT
    )
\"\"\")
conn.commit()
print(\"Table ready\")
'"
```

### 2. Create API Key

```bash
ssh -p 4242 unarmedpuppy@192.168.86.47 'docker exec llm-router python3 -c "
from auth import create_api_key
key, id = create_api_key(name=\"CLIENT_NAME\", scopes=[\"chat\", \"memory\", \"metrics\"])
print(f\"API Key: {key}\")
print(f\"Key ID: {id}\")
"'
```

**Scopes**: `chat`, `memory`, `metrics`, `agent`

### 3. List Existing Keys

```bash
ssh -p 4242 unarmedpuppy@192.168.86.47 'docker exec llm-router python3 -c "
from auth import list_api_keys
for k in list_api_keys():
    print(k)
"'
```

## Configuring Dashboard

The dashboard uses nginx to inject the API key server-side (key never exposed to browser).

### 1. Update docker-compose.server.yml

Add `LOCAL_AI_API_KEY` to dashboard service:

```yaml
dashboard:
  environment:
    - VITE_API_URL=http://llm-router:8000
    - LOCAL_AI_API_KEY=lai_xxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

### 2. Restart Dashboard

```bash
ssh -p 4242 unarmedpuppy@192.168.86.47 "cd ~/server/apps/homelab-ai && docker compose pull dashboard && docker compose up -d dashboard"
```

## Verifying Authentication

### Test Key Works

```bash
ssh -p 4242 unarmedpuppy@192.168.86.47 "curl -s -H 'Authorization: Bearer lai_xxxxx' http://localhost:8012/health | jq ."
```

### Check Dashboard Proxy

```bash
curl -s https://homelab-ai.server.unarmedpuppy.com/api/health
```

## Troubleshooting

### "Empty API key" Error
- Dashboard nginx not injecting key
- Check `LOCAL_AI_API_KEY` env var is set in dashboard container
- Verify nginx config has `proxy_set_header Authorization "Bearer ${LOCAL_AI_API_KEY}";`

### "no such table: client_api_keys"
- Fresh database, run table creation SQL above
- Bug in `init_database()` - runs migrations before creating tables

### Key Not Working
- Verify key exists: `list_api_keys()`
- Check key enabled status
- Ensure correct scopes for endpoint

## Current Keys

| Name | Prefix | Scopes |
|------|--------|--------|
| dashboard | lai_7f40 | chat, memory, metrics |
| opencode | lai_5ce9 | chat, memory, metrics, agent |
| n8n | lai_1117 | chat |

**Full keys stored in secrets manager / .env files - never in git**
