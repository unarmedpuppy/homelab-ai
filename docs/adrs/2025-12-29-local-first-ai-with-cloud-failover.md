# Local-First AI Architecture with Cloud Failover

- **Date:** 2025-12-29
- **Status:** Accepted
- **Authors:** Joshua Jenquist
- **Impacted Repos/Services:** homelab-ai (LLM router, LLM manager), agent-harness, all AI consumers

## Context

The homelab needs LLM inference for agents, chat, and automation. Cloud APIs (Anthropic, OpenAI) provide high quality but cost per token. Local GPUs (RTX 3090 on gaming PC, RTX 3070 on server) provide free inference but limited concurrency (one request per GPU). The goal is to serve >80% of requests locally and fail over to cloud only when necessary.

## Decision

Build a hybrid AI infrastructure that prioritizes local GPU inference with intelligent cloud failover. An LLM Router acts as an OpenAI-compatible proxy that routes requests based on token count, task complexity, backend availability, and gaming mode state.

**Routing logic:**
1. Explicit model request → route to requested backend
2. Token estimate <2K → 3070 (fast path)
3. Gaming mode ON → 3070 only (unless force-big header)
4. Token 2K-16K + 3090 available → 3090
5. Complex/long context → Z.ai or Claude Harness (cloud)
6. Fallback chain: 3070 → 3090 → cloud

Agent requests prioritized over user requests. Single-request constraint per GPU.

## Options Considered

### Option A: Cloud-only
Simple. Expensive at scale ($100+/month for heavy agent usage). Requires internet.

### Option B: Local-only
Free inference. No fallback when GPUs are busy or gaming. Queue depth grows unbounded.

### Option C: Hybrid with intelligent routing (selected)
Best of both. Local GPUs handle the majority. Cloud absorbs spikes. Gaming mode awareness prevents inference during gaming. Cost stays near-zero for typical usage.

## Consequences

### Positive
- Near-zero inference cost for typical workloads
- Graceful degradation when GPUs busy or gaming
- OpenAI-compatible API means all clients work unchanged

### Negative
- Routing logic adds complexity and latency (~5ms)
- GPU concurrency limit (1 request/GPU) creates bottlenecks under load
- Cloud failover has variable latency and occasional cost
