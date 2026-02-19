# Separate Metrics and Memory Databases

- **Date:** 2025-12-29
- **Status:** Accepted
- **Authors:** Joshua Jenquist
- **Impacted Repos/Services:** homelab-ai (LLM router), dashboard

## Context

The LLM router handles two fundamentally different data types: operational metrics (every API request) and conversation memory (opt-in history with RAG). Combining them in one store creates privacy concerns (not all API calls should be permanently stored) and performance issues (metrics writes shouldn't block memory queries).

## Decision

Maintain two independent SQLite databases within the LLM Router:

| Database | Purpose | Write Pattern | Privacy |
|----------|---------|---------------|---------|
| Metrics DB | Logs all API requests | Always on, every request | Operational only |
| Memory DB | Conversation history + RAG | Opt-in via `X-Enable-Memory: true` header | Requires `X-User-ID` |

Memory storage is explicitly opt-in. Clients must include both headers to save conversations. Metrics are always collected.

## Options Considered

### Option A: Single database for everything
Simpler schema. Privacy concern — all conversations logged by default. No way to opt out.

### Option B: Two databases with explicit opt-in (selected)
Clear privacy boundary. Metrics always collected for observability. Conversations only stored when requested. Databases can be backed up independently.

## Consequences

### Positive
- Privacy by default — conversations not stored unless explicitly requested
- Metrics always available for monitoring without privacy concerns
- Independent backup and retention policies per database

### Negative
- Two databases to manage and migrate
- Dashboard needs separate queries for metrics vs. conversations
