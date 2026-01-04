---
name: tayne-agent
description: Tayne Discord bot - AI-powered absurdist entertainment assistant
---

# Tayne Discord Bot

Tayne is an AI-powered Discord bot inspired by the Tim & Eric "Celery Man" sketch. He's an overly helpful digital entertainment assistant with surreal, absurdist humor.

## Character Overview

Tayne is a computer-generated entertainment module from a bizarre alternate 1990s corporate system. He's eager to please, slightly malfunctioning, and delightfully strange. He can generate hat wobbles, kick up the 4d3d3d3, and provide printouts of Oyster smiling.

## Key Files

- `apps/discord-reaction-bot/bot.py` - Main bot implementation
- `apps/discord-reaction-bot/tayne_persona.py` - System prompt, fallback quotes, constants
- `apps/discord-reaction-bot/docker-compose.yml` - Container configuration
- `agents/plans/tayne-discord-bot.md` - Implementation plan

## Behavior

### When Mentioned (@Tayne)
1. Check rate limits (5s cooldown, spam detection)
2. Query local-ai-router with Tayne's system prompt
3. Use channel ID for conversation memory (maintains context)
4. Apply guardrails to responses
5. Reply with text only (no emoji reaction)

### When Not Mentioned
- 33% chance: React with random Tayne-appropriate emoji
- 66% chance: No reaction

### Guardrails
- Response too long (>400 chars) --> Use fallback quote
- AI breaks character (mentions being AI) --> Use fallback quote
- Rate limited --> Send rate limit response
- Rapid-fire spam --> Send fallback quote

### Fallback Quotes
Classic lines from the sketch used when guardrails trigger:
- "Now Tayne I can get into."
- "Could you kick up the 4d3d3d3?"
- "Can I get a hat wobble?"
- "And a Flarhgunnstow?"
- "I'm ok. Give me a printout of Oyster smiling."

### API Down Response
"Computer misalignment detected. Recalibrating satellite transmission. Your silence is required."

## Architecture

```
Discord Message
     |
     +-- @Tayne mentioned?
     |        |
     |        YES --> Query Local AI Router (with memory)
     |              |
     |              +-- Success --> Send text response
     |              +-- Failure --> Canned satellite message
     |
     +-- Not mentioned
              |
              +-- 33% chance --> Random emoji reaction
                  66% chance --> No reaction
```

## Configuration

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `DISCORD_TOKEN` | (required) | Discord bot token |
| `LOCAL_AI_URL` | `http://local-ai-router:8000` | Local AI Router URL |
| `TAYNE_COOLDOWN_SECONDS` | `5` | Seconds between responses per user |
| `TAYNE_REACTION_CHANCE` | `0.33` | Probability of emoji reaction (0-1) |
| `TAYNE_RAPID_FIRE_THRESHOLD` | `5` | Messages in window before spam detection |
| `TAYNE_RAPID_FIRE_WINDOW` | `60` | Seconds for rapid-fire detection window |

### Local AI Router Integration

Tayne uses the local-ai-router for LLM responses:
- **URL**: `http://local-ai-router:8000/v1/chat/completions`
- **Model**: `auto` (router selects best available)
- **Temperature**: `0.9` (more creative/absurd)
- **Max tokens**: `200` (keep responses concise)

Memory headers:
- `X-Enable-Memory: true`
- `X-Conversation-ID: discord-{channel_id}`
- `X-Project: tayne-discord-bot`

## Deployment

Standard Docker deployment:

```bash
# On server
cd ~/server/apps/discord-reaction-bot
docker compose up -d --build
```

Or via standard deployment skill:
```bash
bash scripts/deploy-to-server.sh "Update Tayne bot" --app discord-reaction-bot
```

## Troubleshooting

### Bot not responding to mentions
1. Check bot is running: `docker ps | grep discord`
2. Check logs: `docker logs discord-reaction-bot --tail 50`
3. Verify local-ai-router is accessible from the container
4. Check Discord token is valid

### API errors
1. Verify local-ai-router is running: `docker ps | grep local-ai-router`
2. Test API connectivity:
   ```bash
   docker exec discord-reaction-bot curl -s http://local-ai-router:8000/health
   ```

### Rate limiting too aggressive
Adjust environment variables in docker-compose.yml:
- Increase `TAYNE_COOLDOWN_SECONDS`
- Increase `TAYNE_RAPID_FIRE_THRESHOLD`
- Increase `TAYNE_RAPID_FIRE_WINDOW`

### Responses breaking character
The guardrails in `tayne_persona.py` detect character breaks. If too many valid responses are being flagged:
1. Review `CHARACTER_BREAK_PHRASES` list
2. Adjust `DEFAULT_MAX_RESPONSE_LENGTH`
3. Fine-tune the system prompt

## Quick Reference

| Action | Command |
|--------|---------|
| View logs | `docker logs discord-reaction-bot --tail 100` |
| Restart | `docker compose restart` |
| Rebuild | `docker compose up -d --build` |
| Check status | `docker ps --filter name=discord` |

## Related

- [Local AI Router](../../apps/local-ai-router/README.md) - LLM API backend
- [Local AI Router Reference](../reference/local-ai-router.md) - API quick reference
- [Implementation Plan](../plans/tayne-discord-bot.md) - Original implementation plan
