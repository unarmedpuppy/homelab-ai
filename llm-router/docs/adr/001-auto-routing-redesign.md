# ADR 004: LLM Router Auto-Routing Redesign

**Date:** 2026-02-22
**Status:** Accepted
**Context:** llm-router auto-routing

## Decision

Redesign auto-routing to use 3090 as primary when gaming mode is OFF, with GLM-5 and Claude Sonnet as escalation targets for large context requests. Remove 3070 from auto-routing (manual only).

## Context

The previous routing logic used 3070 as the default for all requests, escalating to 3090 only when context exceeded 2K tokens. This had several issues:

1. **3070 limitations**: Only 2K context window, frequently required escalation
2. **Gaming mode ignored**: Gaming mode status was tracked but not used in routing decisions
3. **No cloud escalation for context**: Large context requests (>32K) had no automatic escalation path
4. **Token estimation crude**: Used `len(content) // 4` approximation

## New Routing Logic

### Gaming Mode OFF (default)
```
tokens < 16K  → 3090 (qwen2.5-14b-awq, 32K context)
tokens 16K-100K → GLM-5 (Z.ai, 205K context)
tokens > 100K → Claude Sonnet (200K context)
```

### Gaming Mode ON
```
tokens < 100K → GLM-5 (skip local GPUs)
tokens > 100K → Claude Sonnet
```

### Fallback Chain
```
3090 → GLM-5 → Claude Sonnet
```

### Explicit Requests
Explicit model/provider requests are ALWAYS honored, even in gaming mode:
- `model=3070` or `model=qwen2.5-7b-awq` → routes to 3070
- `model=3090` or `model=gaming-pc` → routes to 3090

## Changes Made

### config/providers.yaml
- Changed priorities: 3090=1, zai=2, claude-harness=3, 3070=99
- Added GLM-5 model (205K context, $1/1M tokens)
- Updated glm-4.7 to non-default
- Updated 3070 model to non-default, manual-only description

### router.py
- Added tiktoken for accurate token estimation
- Added LARGE_TOKEN_THRESHOLD (100K)
- Rewrote route_request() with gaming mode awareness
- Updated MODEL_ALIASES (removed 3070 from small/fast aliases)
- Added fallback chain handling

### providers/manager.py
- Updated cloud fallback to use ordered fallback chain (GLM-5 → Claude Sonnet)

### requirements.txt
- Added tiktoken>=0.7.0

## Consequences

### Positive
- 3090 gets full utilization when available (not gaming)
- Large context requests automatically route to capable models
- Gaming mode actually affects routing (no local GPU usage)
- More accurate token estimation
- Clear fallback chain

### Negative
- 3070 no longer auto-routed (may sit idle)
- Requires tiktoken dependency (~50MB)
- Gaming mode check adds latency to routing (~5ms)

### Neutral
- Explicit requests unchanged (backward compatible)
- Cloud costs increase for large context (but those requests would have failed on local)

## Verification

1. `docker compose up --build` to rebuild with tiktoken
2. Test auto-routing with gaming mode OFF:
   - Small request (<16K) → should hit 3090
   - Medium request (16K-100K) → should hit GLM-5
   - Large request (>100K) → should hit Claude
3. Test gaming mode ON:
   - Auto request (any size) → should hit GLM-5 (skips local GPUs)
   - Explicit `model=3070` → should still work (explicit honored)
4. Test fallback:
   - Stop 3090 → request should fallback to GLM-5
   - Stop GLM-5 → request should fallback to Claude
