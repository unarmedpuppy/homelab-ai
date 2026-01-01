---
name: query-bird-posts
description: Query stored X/Twitter bookmarks and likes via Bird API
when_to_use: When you need to search, list, or analyze saved tweets from bookmarks/likes
---

# Query Bird Posts

Access stored X/Twitter bookmarks and likes through the Bird API.

## Quick Reference

```bash
# Stats
curl -s "https://bird-api.server.unarmedpuppy.com/agent/stats" | jq .

# Get bookmarks
curl -s "https://bird-api.server.unarmedpuppy.com/agent/bookmarks?limit=20" | jq .

# Get likes
curl -s "https://bird-api.server.unarmedpuppy.com/agent/likes?limit=20" | jq .

# Search all posts
curl -s "https://bird-api.server.unarmedpuppy.com/agent/posts?search=AI&limit=20" | jq .

# Get single post by internal ID
curl -s "https://bird-api.server.unarmedpuppy.com/posts/{id}" | jq .
```

## Agent Endpoints

### Get Stats
```bash
curl -s "https://bird-api.server.unarmedpuppy.com/agent/stats" | jq .
# Returns: { bookmarks, likes, both, unique_total }
```

### Get Bookmarks
```bash
curl -s "https://bird-api.server.unarmedpuppy.com/agent/bookmarks?limit=50" | jq .
# Optional: ?search=keyword
```

### Get Likes
```bash
curl -s "https://bird-api.server.unarmedpuppy.com/agent/likes?limit=50" | jq .
# Optional: ?search=keyword
```

### Get All Posts (with filters)
```bash
# All posts
curl -s "https://bird-api.server.unarmedpuppy.com/agent/posts?limit=50" | jq .

# Filter by source
curl -s "https://bird-api.server.unarmedpuppy.com/agent/posts?source=bookmarks&limit=50" | jq .

# Search content
curl -s "https://bird-api.server.unarmedpuppy.com/agent/posts?search=machine+learning&limit=20" | jq .
```

## Response Format

Agent endpoints return simplified JSON:

```json
{
  "count": 20,
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

## Common Tasks

### Find posts about a topic
```bash
curl -s "https://bird-api.server.unarmedpuppy.com/agent/posts?search=typescript&limit=30" | jq '.posts[] | {author, content}'
```

### Get recent bookmarks with URLs
```bash
curl -s "https://bird-api.server.unarmedpuppy.com/agent/bookmarks?limit=10" | jq '.posts[] | {url, content}'
```

### Count posts by source
```bash
curl -s "https://bird-api.server.unarmedpuppy.com/agent/stats" | jq .
```

### Extract all t.co media links from bookmarks
```bash
curl -s "https://bird-api.server.unarmedpuppy.com/agent/bookmarks?limit=100" | jq -r '.posts[].content' | grep -oE 'https://t\.co/[a-zA-Z0-9]+'
```

## Notes

- **Media**: Images/videos are NOT stored locally. The `content` field contains `t.co` links that redirect to media on X.
- **Limits**: Max 200 posts per request for agent endpoints.
- **Sources**: `bookmark`, `like`, `both` (post was both bookmarked and liked), `manual`.
- **UI**: https://bird-viewer.server.unarmedpuppy.com

## Full Reference

See `agents/reference/bird-api.md` for complete API documentation.
