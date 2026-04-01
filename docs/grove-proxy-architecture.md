# Grove Proxy — Bootstrap-Safe LLM Fallback

`grove-proxy` is a minimal Anthropic Messages API proxy that runs as a host systemd
service on the server. It provides a fallback inference path for grove agents when
`llm-router` is unavailable.

## Why It Exists

Grove agents speak Anthropic Messages API format. All inference routes through
`llm-router` via `ANTHROPIC_BASE_URL`. When llm-router goes down, agents lose the
ability to think — including Elm, the agent responsible for restarting containers.
That's a circular dependency.

`grove-proxy` breaks the loop by running **outside Docker**, below the layer that can fail.

## Architecture

```
[Grove agent]
      │
      ├─ primary ──► llm-router (Docker) ──► gaming PC 3090 / Z.ai
      │                    ↑ may be down
      │
      └─ fallback ─► grove-proxy (host systemd)
                           │
                           ▼ OpenAI-compatible
                       Ollama (host systemd)
                           │
                           ▼
                     3070 GPU (server)
                     qwen2.5:7b-instruct-q4_K_M
```

## Deployment

Both `grove-proxy` and Ollama run as systemd services on the server host — not in
Docker. This is intentional: they must survive Docker daemon restarts, compose
failures, and CI-triggered stack restarts.

| Service | Type | Port | GPU |
|---|---|---|---|
| `ollama` | host systemd | 11434 | 3070 |
| `grove-proxy` | host systemd | 9117 | — |

## Grove Config

Each grove agent on the server adds:

```toml
[serve]
base_url = "https://local-ai-api.server.unarmedpuppy.com/v1"
fallback_base_url = "http://localhost:9117/v1"
fallback_threshold = 3
```

Or via `.env`:

```
ANTHROPIC_BASE_URL=https://local-ai-api.server.unarmedpuppy.com/v1
ANTHROPIC_FALLBACK_BASE_URL=http://localhost:9117/v1
```

## Translation Layer

`grove-proxy` uses the same `bridge/` module as `llm-router` for Anthropic↔OpenAI
translation. The module is copied into the `grove-proxy` repo (not imported as a
package dependency) to keep grove-proxy fully self-contained.

See `llm-router/bridge/` for the source. If the modules diverge significantly,
extracting `bridge/` as a shared pip package is the next step.

## Model

**Initial model:** `qwen2.5:7b-instruct-q4_K_M`
- VRAM: ~4.5GB (3070 has 8GB total)
- Quantization: Q4_K_M
- Tool calling: supported
- Use case: Elm sysadmin tasks — docker ops, log inspection, shell commands

This is not a general-purpose high-quality model. It's a bootstrap model: capable
enough for Elm to diagnose and restart the primary stack, not a replacement for 32B.

## Repo

Source: `homelab/grove-proxy` on Gitea
Install: `install.sh` on the server (creates venv, installs deps, enables systemd unit)
Update: `update.sh` (git pull + restart)

See the repo README for full installation instructions.

## ADR

`home-server/docs/adrs/2026-03-31-grove-bootstrap-safe-llm-fallback.md`
