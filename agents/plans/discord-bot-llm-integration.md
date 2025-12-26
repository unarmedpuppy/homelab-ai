# Discord Bot LLM Integration Plan

**Goal:** Make Tayne respond with AI-generated messages when mentioned or DMed.

## Phase 1: Basic Ollama Integration
- [ ] Add `aiohttp` dependency for async HTTP requests
- [ ] Detect when Tayne is mentioned (`@Tayne`) or receives a DM
- [ ] Extract the user's message (strip the mention)
- [ ] Call Ollama API at `http://ollama:11434/api/generate`
- [ ] Reply with the generated response

## Phase 2: Personality & Context
- [ ] Add a system prompt defining Tayne's personality
- [ ] Optionally store conversation history per channel/user
- [ ] Add typing indicator while generating

## Phase 3: Configuration
- [ ] Make model configurable via env var (`OLLAMA_MODEL=llama3`)
- [ ] Add max response length limits
- [ ] Add rate limiting to prevent abuse

## Technical Notes
- Bot container needs to be on same Docker network as Ollama
- Ollama is already running at `ollama:11434` internally
- Response streaming possible but adds complexity

## Files to Modify
- `apps/discord-reaction-bot/bot.py` - Main bot logic
- `apps/discord-reaction-bot/Dockerfile` - Add aiohttp dependency
- `apps/discord-reaction-bot/docker-compose.yml` - Add env vars for model config
