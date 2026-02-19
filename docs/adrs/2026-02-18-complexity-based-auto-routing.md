# Complexity-Based Auto-Routing for LLM Router

- **Date:** 2026-02-18
- **Status:** Accepted
- **Authors:** Joshua Jenquist
- **Impacted Repos/Services:** homelab-ai (LLM router)
- **Supersedes:** Routing logic section of [Local-First AI with Cloud Failover](2025-12-29-local-first-ai-with-cloud-failover.md)

## Context

The router's `model=auto` mode used a binary heuristic: estimate tokens (chars/4), check for a `X-Force-Big` header or `#force_big` tag, and pick 3070 or 3090. This meant a 50-token "debug this distributed systems race condition" routed identically to "what's 2+2" — both went to the 3070. The only escape hatch was callers manually setting force-big, which none of them did consistently.

Real-world requests vary along multiple dimensions: tool count, system prompt intent, conversation depth, requested output length, and keyword complexity. The router should use these signals to make better default decisions without requiring callers to change anything.

## Decision

Replace the token-count + force-big heuristic with a **rule-based complexity classifier** (`complexity.py`). Classification is a pure function — no I/O, no LLM inference call, no added latency beyond microseconds.

### Tier System

| Tier | Model | Provider | When |
|------|-------|----------|------|
| ROUTINE | qwen2.5-7b-awq | server-3070 | Simple Q&A, short chat, lookups |
| MODERATE | qwen2.5-14b-awq | gaming-pc-3090 | Coding, multi-turn, tools, analysis |
| COMPLEX | qwen2.5-14b-awq | gaming-pc-3090 | Heavy reasoning, long context, architecture |

MODERATE and COMPLEX route to the same model today but are tracked separately in Prometheus for future differentiation (e.g., when a cloud tier becomes available for COMPLEX).

### Two Signal Sources

**Option A — Heuristic scoring (additive, capped at 1.0):**
- Tools present (+0.1/tool, max 0.4)
- Coding keywords in system prompt (+0.2)
- Reasoning keywords in system prompt (+0.15)
- Multi-turn depth past 3 user messages (+0.05/turn, max 0.2)
- Token estimate >2K (scaled +0.0–0.3)
- max_tokens >1024 (scaled +0.0–0.15)
- Complexity keywords in last user message (+0.1–0.2)
- Low temperature <=0.3 (+0.05)

Score thresholds: <0.25 = ROUTINE, 0.25–0.6 = MODERATE, >0.6 = COMPLEX.

**Option B — Caller-declared signals (priority order):**
1. `X-Complexity: routine|moderate|complex` header
2. `X-Force-Big: true` → COMPLEX (backward compat)
3. `#force_big` in message → COMPLEX (backward compat)
4. API key `metadata.complexity` field
5. `X-Source: n8n|agent|agent-harness` → MODERATE floor

**Conflict resolution:** `final_tier = max(caller_tier, heuristic_tier)`. Heuristics can only escalate, never downgrade a caller's declaration. This prevents a caller from accidentally sending a 10-tool request to the 3070's limited context.

### Observability

- `X-Complexity-Tier` response header on every routed request
- `local_ai_complexity_classifications_total` Prometheus counter with `tier` and `primary_signal` labels
- Structured log line with tier, score, and signal list

## Options Considered

### Option 1: LLM-based classification
Route every request through a small classifier model first ("is this simple or complex?"). Accurate but adds 200–500ms latency and creates a circular dependency (need an LLM to route to an LLM). Could revisit if heuristics prove insufficient, but the latency cost is hard to justify when the heuristics are free.

### Option 2: Caller-only classification (headers/metadata only)
Let callers declare complexity and don't analyze content at all. Zero false positives from heuristics, but requires every caller to be updated and correctly declare complexity. Most callers (chat UI, n8n workflows) have no concept of task complexity. Would leave the majority of requests unclassified, defaulting to ROUTINE.

### Option 3: Rule-based heuristics + caller overrides (selected)
Heuristics provide good defaults for all callers with zero integration work. Caller signals give power users and agents explicit control when they need it. The max() conflict resolution means heuristics can only help, never hurt. Simple to debug (score + signal list in every log line), simple to tune (adjust weights or thresholds), and simple to extend (add new signals without changing the interface).

### Option 4: ML classifier trained on historical routing data
Train a small model on past requests labeled by which backend produced better results. Would be the most accurate long-term, but requires labeled training data we don't have yet. The Prometheus metrics from Option 3 will generate exactly this dataset — so this becomes a natural evolution path once we have enough data.

## Consequences

### Positive
- "Debug this race condition" now routes to 3090 automatically, no caller changes needed
- Agent calls are data-driven instead of hardcoded — if an agent call somehow has no tools, it can route to 3070
- All backward-compat signals (X-Force-Big, #force_big, model aliases) still work
- Prometheus metrics give visibility into classification distribution for future tuning
- Pure-function classifier is trivially unit-testable (45 tests)

### Negative
- Keyword-based heuristics will have false positives (e.g., "I'm coding" in casual chat → MODERATE)
- Score weights are hand-tuned, not data-driven — may need adjustment after observing production traffic
- MODERATE and COMPLEX both route to 3090 today, so the distinction is theoretical until a cloud tier is wired up

### Migration Path
- Monitor `local_ai_complexity_classifications_total` for tier distribution
- If ROUTINE requests fail on 3070 (context overflow), the signal weights need tuning upward
- If 3090 is overloaded with MODERATE requests that could have been ROUTINE, tune weights downward
- When ready for cloud fallback on COMPLEX, add the provider to TIER_MODEL_MAP — no other changes needed
