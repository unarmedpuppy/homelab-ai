---
name: http-api-requests
description: Make HTTP requests to APIs using curl
when_to_use: Need to call APIs, check endpoints, send webhooks, test services
---

# HTTP API Requests

Make HTTP requests using curl.

## When to Use

- Test API endpoints
- Check service health
- Send webhooks
- Interact with REST APIs
- Debug HTTP issues

## Basic Requests

### GET Request

```bash
# Simple GET
curl https://api.example.com/endpoint

# With headers
curl -H "Authorization: Bearer TOKEN" https://api.example.com/endpoint

# Pretty print JSON
curl -s https://api.example.com/endpoint | jq .

# With verbose output
curl -v https://api.example.com/endpoint
```

### POST Request

```bash
# JSON body
curl -X POST https://api.example.com/endpoint \
  -H "Content-Type: application/json" \
  -d '{"key": "value"}'

# Form data
curl -X POST https://api.example.com/endpoint \
  -d "key=value&other=data"

# From file
curl -X POST https://api.example.com/endpoint \
  -H "Content-Type: application/json" \
  -d @data.json
```

### Other Methods

```bash
# PUT
curl -X PUT https://api.example.com/endpoint \
  -H "Content-Type: application/json" \
  -d '{"key": "updated"}'

# DELETE
curl -X DELETE https://api.example.com/endpoint

# PATCH
curl -X PATCH https://api.example.com/endpoint \
  -H "Content-Type: application/json" \
  -d '{"field": "patched"}'
```

## Common Options

| Option | Description |
|--------|-------------|
| `-s` | Silent mode (no progress) |
| `-S` | Show errors in silent mode |
| `-f` | Fail silently on HTTP errors |
| `-o file` | Output to file |
| `-O` | Save with remote filename |
| `-L` | Follow redirects |
| `-k` | Ignore SSL errors (insecure) |
| `-v` | Verbose output |
| `-i` | Include response headers |
| `-I` | HEAD request (headers only) |

## Authentication

### Bearer Token

```bash
curl -H "Authorization: Bearer YOUR_TOKEN" https://api.example.com
```

### Basic Auth

```bash
curl -u username:password https://api.example.com
```

### API Key Header

```bash
curl -H "X-API-Key: YOUR_KEY" https://api.example.com
```

## Response Handling

### Check Status Code

```bash
# Get HTTP status code
curl -s -o /dev/null -w "%{http_code}" https://api.example.com

# Get response with status
curl -s -w "\nHTTP Status: %{http_code}\n" https://api.example.com
```

### Parse JSON Response

```bash
# Pretty print
curl -s https://api.example.com | jq .

# Extract specific field
curl -s https://api.example.com | jq '.data.id'

# Filter array
curl -s https://api.example.com | jq '.items[] | select(.status == "active")'
```

### Save Response

```bash
# To file
curl -o response.json https://api.example.com

# With timestamp
curl -o "response-$(date +%Y%m%d-%H%M%S).json" https://api.example.com
```

## Debugging

### Verbose Output

```bash
curl -v https://api.example.com
```

### Show Request/Response Headers

```bash
# Response headers only
curl -I https://api.example.com

# Both request and response
curl -v https://api.example.com 2>&1 | grep -E "^[<>]"
```

### Timing Information

```bash
curl -w "Time: %{time_total}s\n" -o /dev/null -s https://api.example.com

# Detailed timing
curl -w "DNS: %{time_namelookup}s\nConnect: %{time_connect}s\nTTFB: %{time_starttransfer}s\nTotal: %{time_total}s\n" -o /dev/null -s https://api.example.com
```

## Common Use Cases

### Health Check

```bash
# Simple health check
curl -sf https://service.example.com/health && echo "OK" || echo "FAILED"

# With timeout
curl -sf --max-time 5 https://service.example.com/health
```

### Webhook

```bash
# Send webhook notification
curl -X POST https://webhook.example.com/notify \
  -H "Content-Type: application/json" \
  -d '{"event": "deploy", "status": "success"}'
```

### File Upload

```bash
# Upload file
curl -X POST https://api.example.com/upload \
  -F "file=@/path/to/file.txt"

# With metadata
curl -X POST https://api.example.com/upload \
  -F "file=@/path/to/file.txt" \
  -F "description=My file"
```

### API Pagination

```bash
# Loop through pages
for page in 1 2 3 4 5; do
  curl -s "https://api.example.com/items?page=$page" | jq '.items[]'
done
```

## Server API Examples

### Local AI Router

```bash
# Health check
curl https://local-ai-api.server.unarmedpuppy.com/health

# Chat completion
curl -X POST https://local-ai-api.server.unarmedpuppy.com/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{"model": "auto", "messages": [{"role": "user", "content": "Hello"}]}'

# List models
curl https://local-ai-api.server.unarmedpuppy.com/v1/models
```

### Homepage

```bash
# Check homepage
curl -I https://server.unarmedpuppy.com
```

## Troubleshooting

### SSL/TLS Issues

```bash
# Ignore SSL errors (dev only!)
curl -k https://self-signed.example.com

# Specify CA cert
curl --cacert /path/to/ca.crt https://api.example.com
```

### Connection Issues

```bash
# Set timeout
curl --connect-timeout 10 --max-time 30 https://api.example.com

# Retry on failure
curl --retry 3 --retry-delay 2 https://api.example.com
```

### DNS Issues

```bash
# Use specific DNS
curl --resolve api.example.com:443:192.168.1.100 https://api.example.com

# Check DNS
nslookup api.example.com
```

## Related Skills

- `connect-server` - Run curl on server
- `check-service-health` - Health monitoring
- `post-to-mattermost` - Webhook notifications
