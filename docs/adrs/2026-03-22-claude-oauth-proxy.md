# ADR: Claude OAuth Proxy — Single Auth Point for Multi-Machine Claude Code

- **Date:** 2026-03-22
- **Status:** Accepted
- **Repos/Services affected:** `claude-proxy` (new), `homelab-ai/llm-router/config/providers.yaml`
- **Related:**
  - [2026-03-15-claude-code-local-routing-optimization.md](2026-03-15-claude-code-local-routing-optimization.md)

## Context

Claude Code sessions on multiple machines (Mac Mini, home server via Gilfoyle, gaming PC via Hal)
each require their own `claude auth login` OAuth session. The OAuth token expires daily. The
existing workaround (`claude-token-refresh.sh`) handles this on the Mac Mini, but Gilfoyle and
Hal still require manual re-auth.

The previous architecture routed Claude Code through llm-router as an `ANTHROPIC_BASE_URL`
target, with `claude-harness` (Claude Code CLI in Docker) as the final fallback provider. This
caused unnecessary translation:

```
Claude Code (Anthropic format)
  → llm-router (OpenAI format internally)
  → claude-harness (OpenAI in → claude CLI subprocess → JSONL → OpenAI out)
  → Anthropic API
```

Three format conversions to end up back at Anthropic. Additionally, claude-harness required its
own Claude auth on the server host, which also expired.

## Decision

**Separate the two routing concerns:**

1. **Local model routing** → llm-router (gaming PC vLLM, server 3070, Z.ai). Unchanged.
2. **Claude API access** → `claude-proxy`: a thin passthrough service on Mac Mini that injects
   the live OAuth token and forwards native Anthropic API requests directly.

**claude-proxy** (`~/workspace/claude-proxy/`, port 8099):
- Reads `accessToken` from `~/.claude/.credentials.json` on every request (auto-picks up
  token refreshes from the existing `claude-token-refresh.sh` LaunchAgent)
- Accepts any `/v1/*` Anthropic API request
- Strips inbound auth, injects the real OAuth token, forwards to `api.anthropic.com`
- Passes SSE streaming through without buffering
- Auth: `CLAUDE_PROXY_TOKEN` env var (shared internal secret for cross-machine use)
- Deployed as LaunchAgent `ai.innie.claude-proxy` on Mac Mini

**llm-router** removes `claude-harness` as a provider. The fallback chain becomes:
`gaming-pc-3090 → zai → 503` (no silent Claude fallback).

**Remote machine usage** is intentional and per-session, not a default:
```bash
# ~/.zshrc on Gilfoyle / Hal
use-claude() {
  export ANTHROPIC_BASE_URL=http://averys-mac-mini:8099
  export ANTHROPIC_API_KEY=<CLAUDE_PROXY_TOKEN>
  echo "Claude proxy active (averys-mac-mini:8099)"
}
```

The default `ANTHROPIC_BASE_URL` on remote machines continues to point at llm-router. `use-claude`
is run explicitly when a session should talk to Claude directly.

## Consequences

**Positive:**
- Single OAuth token to maintain across the entire fleet
- No format translation — native Anthropic API end-to-end
- Gilfoyle and Hal never need `claude auth login` again
- llm-router is local-models-only, which is what it's for
- claude-harness exits the routing stack (Docker container may remain for Ralph)

**Negative:**
- claude-proxy is a new service to run and monitor on Mac Mini
- If Mac Mini is unreachable, remote machines lose Claude access (acceptable — they have llm-router)
- Claude model entries removed from llm-router mean they're no longer in the dashboard's model list

**Deployment:**
```bash
# Install plist (once)
cp ~/workspace/claude-proxy/ai.innie.claude-proxy.plist ~/Library/LaunchAgents/
# Edit REPLACE_WITH_TOKEN in the plist first, then:
launchctl load ~/Library/LaunchAgents/ai.innie.claude-proxy.plist

# Verify
curl http://localhost:8099/health
```
