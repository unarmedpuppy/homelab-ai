# Model Garden: Multi-Provider Model Catalog and Management UI

- **Date:** 2026-03-08
- **Status:** Accepted
- **Repos/Services affected:** homelab-ai (llm-router/router.py, llm-manager/manager.py, dashboard/src/components/models/*, dashboard/src/App.tsx, dashboard/src/api/client.ts, dashboard/src/types/models.ts)

## Context

Models are defined statically in `models.json` (llm-manager) and `providers.yaml` (llm-router). When first requested, vLLM downloads weights from HuggingFace into a shared Docker volume. There is no UI to:
- Browse available models across all providers (3090, 3070, Z.ai, Claude harness)
- See which models are cached locally vs need downloading
- See which models are currently running
- Start/stop/prefetch models on demand
- Register custom models (created via weight merging tools like Obliteration)

The user wants to build toward a local model garden where open-source models are cached in Harbor for offline availability, and custom models can be created and hosted alongside standard ones.

## Decision

Build a **Model Garden** feature with:
1. **Aggregated API in llm-router** (`/v1/model-garden/*`) that merges model data from all providers
2. **Cache detection and prefetch endpoints in llm-manager** for local model management
3. **Dashboard UI** at `/models` with card-based browsing, filtering, and management controls
4. **Custom model registry** for registering metadata of user-created models

### Why llm-router for the API (not llm-manager)

The router is the single aggregation point that already knows about all providers (local and cloud). It can call each llm-manager instance to enrich model cards with live cache/status data. Putting the API in llm-manager would only show one machine's models.

### Why custom model registration is metadata-only

The model weight push workflow uses `oras push` to Harbor, which is a CLI operation involving large files (10-50GB). The UI form only registers metadata (name, quantization, VRAM, etc.) so the model appears in the catalog. The actual model loading still goes through llm-manager's existing `models.json` mechanism.

## Changes Made

### Backend: llm-manager (cache detection + prefetch)

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/v1/models/cache` | GET | Scans HuggingFace cache volume, returns cached models with sizes |
| `/v1/models/cards` | GET | Full model card listing with live status and cache info |
| `/v1/models/{id}/prefetch` | POST | Background download via `huggingface-cli download` |
| `/v1/models/{id}/prefetch` | GET | Check prefetch status (idle/downloading/completed/failed) |

Cache detection walks `{HF_CACHE_PATH}/hub/models--{org}--{name}/` directories and sums snapshot file sizes. Prefetch runs in a background thread to avoid blocking the API.

### Backend: llm-router (aggregated model garden)

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/v1/model-garden` | GET | Aggregated model cards from providers.yaml + custom registry, enriched with cache/status from llm-managers |
| `/v1/model-garden/{id}/start` | POST | Proxies to correct llm-manager |
| `/v1/model-garden/{id}/stop` | POST | Proxies to correct llm-manager |
| `/v1/model-garden/{id}/prefetch` | POST | Proxies to correct llm-manager |
| `/v1/model-garden/{id}/prefetch` | GET | Proxies prefetch status |
| `/v1/model-garden/custom` | POST | Register custom model metadata |
| `/v1/model-garden/custom/{id}` | DELETE | Unregister custom model |

The router maps provider IDs to manager URLs:
- `gaming-pc-3090` → `GAMING_PC_URL` env var
- `server-3070` → `LOCAL_3070_URL` env var

Cloud providers (Z.ai, Claude harness) don't have managers — their models appear with `status: "unavailable"` for management, `cached: null` for cache status.

Custom models are stored in `config/custom_models.json` and merged into the `GET /v1/model-garden` response with `source: "custom"`.

### Frontend: Dashboard

| Component | Description |
|-----------|-------------|
| `ModelGardenDashboard.tsx` | Main container with stats, filters, card grid, polling (30s via `useVisibilityPolling`) |
| `ModelCard.tsx` | Individual card showing name, status badge, type, provider, VRAM, context, quantization, action buttons |
| `ModelDetailPanel.tsx` | Full detail view with specs, capabilities, tags, source references, management controls |
| `ModelFilterBar.tsx` | Search + type/status/provider filter dropdowns |
| `RegisterModelModal.tsx` | Form modal for custom model metadata registration |
| `types/models.ts` | TypeScript interfaces for ModelCard, ModelGardenResponse, PrefetchStatus, etc. |

Route added at `/models` in `App.tsx` with lazy loading and `🌿 Models` nav item.

## Custom Model CLI Workflow

1. **Create model** — merge/modify weights using Obliteration or similar tool
2. **Push to Harbor** — `oras push harbor.server.unarmedpuppy.com/models/my-model:v1 ./model-weights/.`
3. **Register in UI** — use "Register Custom Model" form (sets metadata, `harbor_ref`)
4. **Add to models.json** — manually add entry so llm-manager can load it
5. **Start from UI** — click "Start" in Model Garden to load via llm-manager

## Consequences

### Positive
- Single UI to browse all models across all providers and machines
- Visibility into cache status prevents surprise cold starts
- Prefetch capability enables pre-downloading models before they're needed
- Custom model registry enables tracking Obliteration-created models
- No new nginx proxy configuration needed — existing `/api/` location routes to llm-router

### Negative / Tradeoffs
- Model Garden API adds N+1 calls (router → each llm-manager) on every poll
- Custom models require manual `models.json` entry to be loadable (registry is metadata-only)
- No upload UI — Harbor push remains a CLI workflow

### Risks
- **llm-manager unreachable:** If a manager is down, its models show as "unavailable". The API handles this gracefully with try/catch on manager calls.
- **Stale cache data:** Cache detection scans the filesystem on each call. For very large caches, this could be slow. Mitigated by 30s polling interval.

## Follow-up

- [ ] Harbor auto-push after first HuggingFace download
- [ ] Harbor pull as alternative source for model downloads
- [ ] `HF_HUB_OFFLINE=1` mode for air-gapped operation
- [ ] Model benchmarking/performance tracking (tok/s history)
- [ ] Sync custom model registry with llm-manager's models.json
- [ ] Prefetch progress indicator in UI (polling prefetch status endpoint)
