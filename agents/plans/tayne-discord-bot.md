# Tayne Discord Bot Implementation Plan

**Status**: In Progress  
**Created**: 2025-12-29  
**Goal**: Transform discord-reaction-bot into "Tayne" - an AI-powered Discord bot with absurdist/surreal humor

## Overview

Tayne is inspired by the Tim & Eric "Celery Man" sketch - an overly helpful digital entertainment assistant with surreal, absurdist humor. The bot responds when mentioned, maintains channel conversation context, and has appropriate guardrails.

## Architecture

```
Discord Message
     |
     +-- @Tayne mentioned?
     |        |
     |        YES --> Query Local AI Router (with memory)
     |              |
     |              +-- Success --> Send text response (check guardrails)
     |              |
     |              +-- Failure --> Canned "satellite" message
     |
     +-- Not mentioned
              |
              +-- 33% chance --> Random emoji reaction
                  66% chance --> No reaction
```

## Behavior Specifications

### When Mentioned
- Query local-ai-router with Tayne's system prompt
- Use channel ID for conversation memory (maintains context)
- Reply with text only (no emoji reaction)
- Check rate limits before querying
- Apply guardrails to responses

### When Not Mentioned
- 33% chance: React with random Tayne-appropriate emoji
- 66% chance: No reaction at all

### Rate Limiting
- Per-user cooldown: 5 seconds between responses
- Rapid-fire detection: 5+ mentions in 60 seconds triggers canned responses
- Prevents API abuse while allowing reasonable conversation

### Guardrails
- Response too long (>400 chars) --> Use fallback quote
- AI "breaks character" (mentions being AI/language model) --> Use fallback quote
- Off-rails conversation --> Deflect with Tayne quotes

### Fallback Responses
When guardrails trigger or conversation goes weird, respond with quotes from the sketch:
- "Now Tayne I can get into."
- "Could you kick up the 4d3d3d3?"
- "Can I get a hat wobble?"
- "And a Flarhgunnstow?"
- etc.

### API Down Response
"Computer misalignment detected. Recalibrating satellite transmission. Your silence is required."

## Technical Details

### Local AI Router Integration
- URL: `http://local-ai-router:8000/v1/chat/completions`
- Headers:
  - `X-Enable-Memory: true`
  - `X-Conversation-ID: discord-{channel_id}`
  - `X-Project: tayne-discord-bot`
- Model: `auto`
- Temperature: 0.9 (more creative/absurd)
- Max tokens: 200 (keep responses concise)

### Emoji Set (Tayne-Appropriate + Original)
Original: `['eggplant', 'salute', 'shrimp', 'poop', 'clown', 'rocket', 'ok_hand', 'pinched_fingers']`

New Tayne additions:
- `'man_dancing'` - Very Tayne
- `'floppy_disk'` - Retro digital
- `'chart_increasing'` - Corporate
- `'desktop_computer'` - Computer theme
- `'top_hat'` - Hat wobble reference
- `'sparkles'` - Razzle dazzle
- `'crystal_ball'` - Mystical digital
- `'dizzy'` - Surreal spiral
- `'robot'` - Digital assistant
- `'cd'` - Retro media
- `'satellite'` - "Satellite transmission"
- `'oyster'` - "Printout of Oyster smiling"

## File Changes

| File | Action | Description |
|------|--------|-------------|
| `apps/discord-reaction-bot/tayne_persona.py` | CREATE | System prompt, fallback quotes, constants |
| `apps/discord-reaction-bot/requirements.txt` | CREATE | Add aiohttp dependency |
| `apps/discord-reaction-bot/bot.py` | REWRITE | Full implementation with LLM integration |
| `apps/discord-reaction-bot/Dockerfile` | MODIFY | Install requirements.txt |
| `apps/discord-reaction-bot/docker-compose.yml` | MODIFY | Add env vars if needed |
| `agents/personas/tayne-agent.md` | CREATE | Agent persona documentation |

## Environment Variables

```bash
# Required (existing)
DISCORD_TOKEN=your_bot_token_here

# Optional (have sensible defaults)
LOCAL_AI_URL=http://local-ai-router:8000
TAYNE_COOLDOWN_SECONDS=5
TAYNE_REACTION_CHANCE=0.33
TAYNE_RAPID_FIRE_THRESHOLD=5
TAYNE_RAPID_FIRE_WINDOW=60
```

## Testing Checklist

- [ ] Bot connects to Discord successfully
- [ ] Bot can reach local-ai-router from Docker network
- [ ] Mention triggers LLM response
- [ ] Non-mention has ~33% emoji reaction rate
- [ ] Rate limiting kicks in on spam
- [ ] Guardrails trigger fallback quotes when needed
- [ ] API down triggers satellite message
- [ ] Memory persists within channel conversations

## Deployment

Standard deployment workflow:
1. Commit changes to git
2. Push to remote
3. SSH to server and git pull
4. `docker compose up -d --build` in apps/discord-reaction-bot/

## Related Files

- `agents/reference/local-ai-router.md` - API documentation
- `agents/personas/tayne-agent.md` - Tayne persona reference
