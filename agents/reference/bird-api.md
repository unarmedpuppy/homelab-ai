# Bird API Reference

API for querying stored X/Twitter bookmarks and likes.

**Base URL**: `https://bird-api.server.unarmedpuppy.com`

## Agent Endpoints (Simplified JSON)

Optimized for MCP tools and external agents - minimal fields, no pagination metadata.

### GET /agent/stats
Quick counts for bookmarks, likes, and overlap.

```bash
curl -s https://bird-api.server.unarmedpuppy.com/agent/stats | jq .
```

**Response:**
```json
{
  "bookmarks": 33,
  "likes": 100,
  "both": 0,
  "unique_total": 133
}
```

### GET /agent/bookmarks
Get bookmarked posts (includes posts marked as "both").

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `limit` | int | 50 | Max posts (1-200) |
| `search` | string | - | Filter by content |

```bash
curl -s "https://bird-api.server.unarmedpuppy.com/agent/bookmarks?limit=10" | jq .
```

**Response:**
```json
{
  "count": 10,
  "posts": [
    {
      "tweet_id": "2006757558435066130",
      "author": "nikshepsvn",
      "content": "thought i killed v5... https://t.co/OmnC6Ihf9S",
      "url": "https://x.com/nikshepsvn/status/2006757558435066130",
      "posted_at": "2026-01-01T16:01:00"
    }
  ]
}
```

### GET /agent/likes
Get liked posts (includes posts marked as "both").

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `limit` | int | 50 | Max posts (1-200) |
| `search` | string | - | Filter by content |

```bash
curl -s "https://bird-api.server.unarmedpuppy.com/agent/likes?limit=10" | jq .
```

### GET /agent/posts
Get all posts with optional filtering.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `source` | string | - | Filter: `bookmark`, `like`, `both`, `bookmarks`, `likes` |
| `limit` | int | 50 | Max posts (1-200) |
| `search` | string | - | Filter by content |

```bash
# All posts
curl -s "https://bird-api.server.unarmedpuppy.com/agent/posts?limit=20" | jq .

# Only bookmarks
curl -s "https://bird-api.server.unarmedpuppy.com/agent/posts?source=bookmarks&limit=20" | jq .

# Search
curl -s "https://bird-api.server.unarmedpuppy.com/agent/posts?search=AI&limit=10" | jq .
```

## UI Endpoints (Full Schema)

Used by the Bird Viewer UI - includes pagination and all fields.

### GET /posts
List all posts with pagination.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `page` | int | 1 | Page number |
| `page_size` | int | 20 | Posts per page (1-100) |
| `source` | string | - | Filter: `bookmark`, `like`, `both`, `manual` |
| `author` | string | - | Filter by author username |
| `search` | string | - | Filter by content |
| `run_id` | string | - | Filter by processing run |

```bash
curl -s "https://bird-api.server.unarmedpuppy.com/posts?page=1&page_size=5" | jq .
```

### GET /posts/bookmarks
List bookmarked posts (includes "both" source).

### GET /posts/likes
List liked posts (includes "both" source).

### GET /posts/{post_id}
Get single post by internal ID.

```bash
curl -s "https://bird-api.server.unarmedpuppy.com/posts/07acb8516653" | jq .
```

### GET /stats
Full statistics with latest run info.

```bash
curl -s "https://bird-api.server.unarmedpuppy.com/stats" | jq .
```

**Response:**
```json
{
  "total_posts": 133,
  "total_runs": 1,
  "latest_run": {
    "id": "76b32d83d5bf",
    "source": "mixed",
    "status": "success",
    "timestamp": "2026-01-01T23:26:58.186437",
    "post_count": 133
  },
  "posts_by_source": {
    "bookmark": 33,
    "like": 100
  }
}
```

### GET /runs
List processing runs.

### GET /runs/{run_id}
Get single run details.

## Post Schema

| Field | Type | Description |
|-------|------|-------------|
| `id` | string | Internal ID (12 chars) |
| `tweet_id` | string | Twitter/X tweet ID |
| `source` | string | `bookmark`, `like`, `both`, or `manual` |
| `author_username` | string | @handle |
| `author_display_name` | string | Display name |
| `content` | string | Tweet text (includes t.co links) |
| `url` | string | Full tweet URL |
| `media_urls` | string | JSON array of media URLs (usually null) |
| `tweet_created_at` | datetime | When tweet was posted |
| `fetched_at` | datetime | When we fetched it |
| `run_id` | string | Processing run ID |

## Media

- **Images/videos are NOT stored locally**
- Tweet `content` contains `t.co` shortened links pointing to media
- Agents can follow these links or use the `url` field to view on X
- The `media_urls` field exists but is typically null (Bird CLI limitation)

## Related

- **UI**: https://bird-viewer.server.unarmedpuppy.com
- **Skill**: `agents/skills/query-bird-posts/`
- **App**: `apps/bird/`
