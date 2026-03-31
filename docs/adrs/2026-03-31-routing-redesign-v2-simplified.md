# Routing Redesign v2 — Simplified Auto-Routing, X-Provider Headers, Willow Proxy

- **Date:** 2026-03-31
- **Status:** Accepted
- **Authors:** Joshua Jenquist
- **Repos/Services affected:** `homelab-ai/llm-router` (router.py, complexity.py, compaction.py, routers/willow.py, providers/models.py, models.json, config/providers.yaml)
- **Supersedes:**
  - [2026-02-18-complexity-based-auto-routing.md](2026-02-18-complexity-based-auto-routing.md) (Complexity-Based Auto Routing)
  - `llm-router/docs/adr/001-auto-routing-redesign.md` (original in-repo ADR)
- **Related:**
  - [2026-02-22-qwen3-32b-as-primary-3090-model.md](2026-02-22-qwen3-32b-as-primary-3090-model.md)
  - [2026-03-22-claude-oauth-proxy.md](2026-03-22-claude-oauth-proxy.md)

## Context

The routing stack had accumulated significant dead weight. Three specific problems motivated this redesign:

**1. Complexity classification was pure overhead.** The three-tier system (ROUTINE/MODERATE/COMPLEX) introduced in the February ADR used heuristic scoring across multiple signal dimensions — keyword matching, tool counting, multi-turn depth, token estimation, temperature. All three tiers mapped to the same model (`qwen3-32b-awq` on the 3090) because the 3070 was removed from auto-routing and no cloud tier was wired up for COMPLEX. The classifier ran on every request, computed a score, emitted Prometheus metrics, and then routed to the same place regardless. The entire `TIER_MODEL_MAP`, `ClassificationResult`, scoring functions, and weight tuning infrastructure existed to produce a routing decision that was always identical.

**2. Claude Sonnet in the fallback chain was fiction.** The previous routing design included `claude-sonnet` as the final fallback (3090 -> GLM-5 -> Claude Sonnet), with context-based escalation sending requests over 100K tokens to Claude. In practice, `claude-proxy`/`claude-harness` never worked reliably as an llm-router provider. The Claude OAuth Proxy ADR (2026-03-22) formally separated Claude access from llm-router, but the dead references — `ClaudeAgentRequest`, `ClaudeAgentResponse`, `OPENCODE_URL`, claude-* model aliases, and the Claude Sonnet fallback entry — remained in router.py.

**3. No client control over provider selection.** Clients could use model aliases (`model=3090`, `model=fast`) to hint at routing, but there was no explicit mechanism to say "route this to Z.ai" or "use this specific model on this specific provider." Clients also had no way to discover what providers and models were available, and no way to verify which provider actually served a given response.

## Decision

Nine changes, grouped by concern.

### 1. Simplified auto-routing

`model=auto` routes to the gaming-pc-3090 default model (`qwen3-32b-awq`) with a single fallback to Z.ai (`glm-5`) if the 3090 is unavailable. No complexity classification, no heuristic scoring, no context-based escalation.

| Gaming mode | Routing                                      |
|-------------|----------------------------------------------|
| OFF         | 3090 (`qwen3-32b-awq`) -> Z.ai (`glm-5`) fallback |
| ON          | Z.ai (`glm-5`) only                         |

There are no token thresholds. Context that would have previously escalated to a cloud provider is now handled by rolling conversation compaction (see decision 7).

### 2. X-Provider / X-Model request headers

Clients can explicitly select a provider and model via request headers:

```
X-Provider: zai
X-Model: glm-5
```

Header-based routing takes highest precedence — above `model=auto`, above model aliases, above gaming mode. This enables routing to `explicit_only` providers (like Willow) that are excluded from auto-routing.

### 3. X-Provider / X-Model response headers

Every response includes headers identifying which provider and model actually served the request:

```
X-Provider: gaming-pc-3090
X-Model: qwen3-32b-awq
```

This replaces the previous `X-Complexity-Tier` response header, which only communicated the classification tier, not the actual routing outcome.

### 4. X-Enable-Tracing request header

```
X-Enable-Tracing: false
```

Per-request toggle to bypass all logging, Prometheus metrics, and conversation storage. Default is `true` (tracing on). Useful for high-frequency automated requests where observability overhead or storage is unwanted.

### 5. Willow provider

New provider replacing `claude-harness` in the router's provider registry.

| Property         | Value                                |
|------------------|--------------------------------------|
| Provider type    | `job` (new `ProviderType.JOB`)       |
| `explicit_only`  | `true` — excluded from auto-routing  |
| Backend          | Containerized Claude Code subscription |
| Base URL         | `http://willow:8013`                 |

Proxy endpoints exposed by the router:

| Method | Endpoint              | Description              |
|--------|-----------------------|--------------------------|
| POST   | `/v1/willow/jobs`     | Submit a new job         |
| GET    | `/v1/willow/jobs`     | List jobs                |
| GET    | `/v1/willow/jobs/{id}`| Get job status/result    |
| GET    | `/v1/willow/health`   | Willow health check      |

Willow is job-based (async), not request-response like the chat completion providers. The `routers/willow.py` module handles the proxy layer.

### 6. Discovery endpoint

```
GET /v1/routing/config
```

Returns all valid providers, models, model aliases, supported headers, and context capping configuration. Enables clients to discover the routing surface without hardcoding assumptions.

### 7. Rolling conversation compaction

New `compaction.py` module for context window management. When a conversation approaches 85% of the model's context limit, older messages are summarized into a compact representation, preserving the most recent messages in full.

This replaces context-based escalation to cloud providers. Instead of routing long conversations to a larger-context model, the router compacts the conversation to fit within the local model's window.

### 8. Dynamic context capping

Agent requests (priority 0, API keys matching `agent-*`) are capped at 16K `max_tokens` on local providers. Interactive users get the full 65K context window.

| Request source | Identification          | max_tokens cap (local) |
|----------------|-------------------------|------------------------|
| Agent          | Priority 0, `agent-*` keys | 16,384                |
| Interactive    | All other API keys       | 65,536                |

Source classification uses the new `is_agent_request()` function in `complexity.py` — the only thing that module does now.

### 9. Default context raised

`qwen3-32b-awq` `default_context` raised from 32,768 to 65,536 in `models.json`, reflecting the model's actual supported context window.

## What Was Removed

| Module/File     | Removed                                                                                          |
|-----------------|--------------------------------------------------------------------------------------------------|
| `complexity.py` | `ComplexityTier` enum, `TIER_MODEL_MAP`, `ClassificationResult`, all heuristic scoring functions (keyword matching, tool counting, multi-turn depth scoring, token estimate scoring, temperature check) |
| `router.py`     | `BACKENDS` dict, `check_backend_health()`, `has_force_big_signal()`, `ClaudeAgentRequest`/`ClaudeAgentResponse`, `SMALL_TOKEN_THRESHOLD`/`MEDIUM_TOKEN_THRESHOLD`/`LARGE_TOKEN_THRESHOLD`, `OPENCODE_URL`, Claude Sonnet entries in fallback chains, `MODEL_ALIASES` for `claude-*` model names |
| Global          | All `claude-sonnet`/`claude-proxy` references from routing logic                                  |

## What Was Added

| Module/File              | Added                                                        |
|--------------------------|--------------------------------------------------------------|
| `complexity.py`          | `is_agent_request()` — minimal source classification for context capping |
| `compaction.py`          | Rolling conversation compaction module                        |
| `routers/willow.py`      | Willow job proxy router                                       |
| `router.py`              | `/v1/routing/config` endpoint                                 |
| `providers/models.py`    | `ProviderType.JOB`, `Provider.explicit_only` field            |
| `router.py`              | `call_llm_for_agent()` rewritten to use `ProviderManager`    |
| Request/response pipeline | `X-Provider`, `X-Model`, `X-Enable-Tracing` header handling  |

## Consequences

### Positive

- **Dramatically simpler routing logic.** The hot path for `model=auto` is: check gaming mode, pick 3090 or Z.ai, done. No scoring, no tier mapping, no threshold comparisons.
- **Explicit client control.** `X-Provider`/`X-Model` headers give callers deterministic routing without relying on model alias conventions or auto-routing heuristics.
- **No dead code paths.** Claude Sonnet fallback, complexity classification, and token thresholds are removed entirely rather than commented out or left as unreachable branches.
- **Transparent responses.** Every response tells the client exactly which provider and model served it, making debugging and auditing straightforward.
- **Willow replaces claude-harness.** Job-based Claude Code access through a purpose-built proxy instead of the unreliable harness.
- **Per-request tracing control.** Automated/batch callers can opt out of logging overhead.

### Negative

- **No automatic context-based escalation to cloud.** By design — this is handled by compaction instead. If compaction proves insufficient for certain workloads, escalation could be reintroduced, but the v1 implementation showed it was never triggered in practice because all tiers routed locally.
- **Willow is explicit-only.** There is no auto-routing path to Willow; callers must know to use the `X-Provider` header or the `/v1/willow/*` endpoints directly.

### Neutral

- **API key priority still determines agent vs interactive.** The complexity classifier is gone, but the distinction between agent and interactive requests persists through API key metadata for context capping purposes.
- **Z.ai is the only cloud fallback.** The fallback chain is shorter (3090 -> Z.ai -> 503) which means if both are down, the router returns 503 rather than attempting Claude. This is acceptable given Claude access is handled separately via `claude-proxy`.

## Migration Notes

- Clients using `model=auto` require no changes — they get the same model (qwen3-32b-awq on 3090) with the same fallback (Z.ai).
- Clients relying on `model=claude-sonnet` or `model=claude-*` aliases will receive a 400 error. These aliases no longer exist. Use `claude-proxy` directly for Claude access.
- The `X-Complexity` and `X-Force-Big` request headers are no longer recognized. They are silently ignored (no error), but have no effect on routing.
- The `X-Complexity-Tier` response header is replaced by `X-Provider` and `X-Model`.
