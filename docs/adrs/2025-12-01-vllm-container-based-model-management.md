# vLLM Container-Based Model Management

- **Date:** 2025-12-01
- **Status:** Accepted
- **Authors:** Joshua Jenquist
- **Impacted Repos/Services:** homelab-ai (LLM manager), Docker infrastructure, GPU allocation

## Context

The homelab runs multiple LLM models across two GPUs (RTX 3090 24GB, RTX 3070 8GB). Models need to be loaded/unloaded based on demand and VRAM availability. The gaming PC must suspend AI services during gaming. A model serving solution needs dynamic lifecycle management, not just static deployment.

## Decision

Use vLLM for model serving with one Docker container per model instance, orchestrated by a centralized LLM Manager that auto-detects GPU VRAM and filters available models.

**Two deployment modes:**
- **Gaming PC**: `on-demand` — load on request, unload after 600s idle timeout
- **Server**: `always-on` — default model preloaded, stays resident

Shared HuggingFace cache volume across all containers. Docker Compose overlay pattern for environment-specific config (`docker-compose.server.yml`, `docker-compose.gaming.yml`).

## Options Considered

### Option A: Ollama
Simple CLI. Limited model support. No fine-grained VRAM management. No dynamic loading/unloading API.

### Option B: Text Generation Inference (TGI)
Good performance. Less flexible model support than vLLM. Smaller community.

### Option C: vLLM with container-per-model (selected)
Best model compatibility. Dynamic container lifecycle management. Container isolation prevents VRAM leaks between models. Compose overlays enable different modes per hardware.

## Consequences

### Positive
- Container isolation prevents VRAM leaks between models
- Gaming mode suspends AI containers cleanly
- Shared HuggingFace cache avoids duplicate model downloads
- Same codebase deploys to different hardware via compose overlays

### Negative
- Container startup adds latency for on-demand models (~10-30s for model load)
- Docker overhead per model vs. multi-model server
- VRAM fragmentation possible with multiple small models
