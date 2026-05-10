# Homelab AI v2

Infrastructure for local LLM inference, routing, observability, and model post-processing across a multi-GPU homelab environment.

## Language

**AI Gateway**:
The central API entry point that routes inference requests, authenticates clients, translates between API formats, emits traces, and logs metrics.
_Avoid_: router, provider-router, llm-router

**LLM Manager**:
A service that manages GPU inference containers (vLLM, llama.cpp) on a single host. Handles model loading, swapping, gaming mode, and container lifecycle.
_Avoid_: manager, vllm-manager

**Provider**:
A backend that can serve inference requests. Either a local LLM Manager instance or a cloud API (z.ai).
_Avoid_: backend, endpoint, service (when referring to a provider)

**Model**:
A specific LLM identified by an ID, with a context window, capabilities, and an assigned provider.
_Avoid_: engine, checkpoint

**Route**:
The act of selecting a provider and model for an inference request based on availability, health, and priority.
_Avoid_: dispatch, forward

**Trace**:
A structured record of an inference request emitted by the gateway, including model used, tokens, latency, and outcome.
_Avoid_: log, event (when referring specifically to a trace)

**Gaming Mode**:
A state on the gaming PC LLM Manager that unloads all models to free GPUs for gaming. Can be toggled via API.
_Avoid_: game mode, GPU pause

**Bridge**:
The Anthropic ↔ OpenAI API translation layer. Converts request/response formats and SSE streaming between the two protocols.
_Avoid_: translator, converter, proxy (too generic)

**API Key**:
A credential used to authenticate requests to the AI Gateway. Default format is `lai-{hex}`. Anthropic-compatible keys with `sk-ant-api03-` prefix are created explicitly via the `prefix` parameter when needed for Claude Code / Anthropic SDK compatibility.
_Avoid_: token, secret, credential (too generic)

## Relationships

- An **AI Gateway** routes to one or more **Providers**
- A **Provider** serves one or more **Models**
- A **Route** selects exactly one **Provider** and one **Model**
- Every request through the **AI Gateway** produces a **Trace**
- The **Bridge** is used when clients speak Anthropic format
- The **Dashboard API** is the single source of truth for agent fleet health (no separate fleet-gateway)

## Flagged ambiguities

- "router" was used to mean both the AI Gateway service and the routing decision — resolved: "gateway" means the service, "route" means the decision.
- "manager" was used interchangeably for llm-manager and provider management logic — resolved: "LLM Manager" is the GPU orchestration service; provider selection is "routing".
- "fleet-gateway" / "innie fleet-gateway" — resolved: no longer exists. Fleet health monitoring lives in the Dashboard API.
- "dashboard-api" and "hub-api" are the same thing — the plan uses "hub-api.server.unarmedpuppy.com" as the domain but the codebase will reference it as "dashboard-api" internally. Either term is fine in context.
