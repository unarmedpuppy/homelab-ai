# OpenAI API Compatibility as Primary Interface

- **Date:** 2025-12-29
- **Status:** Accepted
- **Authors:** Joshua Jenquist
- **Impacted Repos/Services:** homelab-ai (LLM router), agent-harness, agent-gateway, n8n, all AI consumers

## Context

Multiple services need LLM inference: agent harness, chat gateway, n8n automations, dashboards. Each could use a different API contract, but this multiplies integration work. The industry has converged on the OpenAI chat completions API as a de facto standard. Most SDKs, tools, and frameworks support it natively.

## Decision

Implement OpenAI-compatible REST API (`/v1/chat/completions`, `/v1/models`, `/v1/audio/speech`) as the primary interface for all LLM routing. Any OpenAI SDK (Python, JS) can connect without modification. The router transparently routes between local vLLM, Z.ai, Claude Harness, and Anthropic backends.

Standard SSE streaming format. Enhanced streaming mode available via `X-Enhanced-Streaming: true` header for dashboard status events.

## Options Considered

### Option A: Custom API per backend
Maximum flexibility. Every client needs custom code per backend. N clients * M backends = N*M integrations.

### Option B: OpenAI-compatible (selected)
One integration per client. All backends behind single API. SDKs work out of the box. Adding a new backend doesn't require client changes.

## Consequences

### Positive
- Any OpenAI SDK connects immediately
- Agent harness treats all backends identically
- New backends added without client changes
- Community tooling (LangChain, etc.) works natively

### Negative
- OpenAI spec doesn't expose backend-specific features
- Streaming format locked to SSE (no WebSocket option in standard)
- Must track and implement OpenAI spec changes
