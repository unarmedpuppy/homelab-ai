# Docker Compose Overlay Pattern for Multi-Environment

- **Date:** 2025-12-01
- **Status:** Accepted
- **Authors:** Joshua Jenquist
- **Impacted Repos/Services:** homelab-ai, server deployment, gaming PC deployment

## Context

The homelab-ai stack deploys to two environments with different hardware and behavior:
- **Server** (RTX 3070): Always-on LLM Router, Dashboard, Server LLM Manager
- **Gaming PC** (RTX 3090): On-demand LLM Manager, Image Server, TTS Server, must yield GPU for gaming

Same codebase, different services, different GPU allocations, different lifecycle modes. Need one repo to deploy to both.

## Decision

Use base `docker-compose.yml` with environment-specific overlays:
- `docker-compose.yml` — shared networks and volumes
- `docker-compose.server.yml` — server services (always-on mode)
- `docker-compose.gaming.yml` — gaming PC services (on-demand mode)

Deployment: `docker compose -f docker-compose.yml -f docker-compose.{env}.yml up -d`

## Options Considered

### Option A: Separate repos per environment
Maximizes isolation. Duplicates shared config. Changes need to be made in two places.

### Option B: Single compose with environment variables
One file. Conditional logic is limited in Compose. Gets messy with 10+ services that differ per environment.

### Option C: Compose overlay pattern (selected)
Base file defines shared infrastructure. Overlays define environment-specific services. Clean separation. Standard Docker Compose feature.

## Consequences

### Positive
- Single codebase for both environments
- Shared config stays DRY in base file
- Environment differences are explicit and auditable
- Standard Docker Compose feature (no custom tooling)

### Negative
- Must remember to specify both files in commands
- Overriding a base service requires understanding merge semantics
