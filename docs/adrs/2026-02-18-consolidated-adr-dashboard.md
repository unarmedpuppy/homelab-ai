# Consolidated ADR Dashboard via LLM Router

- **Date:** 2026-02-18
- **Status:** Accepted
- **Authors:** Joshua Jenquist
- **Impacted Repos/Services:** homelab-ai (LLM router, dashboard), all repos with docs/adrs/

## Context

We have 31 ADRs spread across 8 repos (home-server, agent-harness, homelab-ai, polyjuiced, trading-bot, agent-gateway, bird, n8n-automations), each stored in `docs/adrs/` and hosted on Gitea. There's no single place to browse them. Searching for prior decisions requires knowing which repo they live in and manually navigating Gitea.

## Decision

Add a Docs page to the homelab-ai dashboard that aggregates ADRs from all repos. The LLM Router acts as the Gitea proxy/aggregation layer rather than introducing a separate service or build-time script.

**Architecture:**
- LLM Router gets a new `/docs` sub-router with two endpoints:
  - `GET /docs/repos` — lists all org repos and their ADR files, parsing frontmatter (title, date, status) from each
  - `GET /docs/content/{repo}/{path}` — returns decoded markdown for a single ADR
- In-memory TTL caching (5 min for index, 1 min for content) to avoid hammering Gitea
- Dashboard gets a new lazy-loaded DocsPage with two-panel layout (repo/ADR tree + markdown viewer)
- Deep-linkable URLs: `/docs/:repo/:slug`

## Options Considered

### Option A: Build-time aggregation script
Cron or CI job that clones all repos and builds a static index. Stale until next run. Extra infra to maintain.

### Option B: Gitea API proxy through LLM Router (selected)
Router already exists, has httpx, serves the dashboard. Adding two endpoints is minimal. TTL caching keeps Gitea load low. Always up-to-date within cache window.

### Option C: Dedicated docs microservice
Overkill for read-only aggregation of ~30 markdown files. Another container to deploy and monitor.

## Consequences

### Positive
- Single place to browse all architecture decisions
- Deep-linkable — can share URLs to specific ADRs
- No new services or build steps — just two endpoints on the existing router
- Automatically picks up new repos/ADRs within 5 minutes

### Negative
- First request after cache expiry is slow (sequential Gitea API calls per repo)
- Router now depends on Gitea API availability (but failure is graceful — cached data still served)
- GITEA_TOKEN must be provisioned as a new secret
