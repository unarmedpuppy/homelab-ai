# Two-GPU Local AI Architecture Plan

**Status**: Planned
**Created**: 2025-12-20
**Epic**: `home-server-bme` (Two-GPU Local AI Architecture)
**Upgrades**: `apps/local-ai-app/` (current proxy-only architecture)

## Related Beads

| Bead ID | Task | Status |
|---------|------|--------|
| `home-server-bme` | Epic: Two-GPU Local AI Architecture | Open |
| `home-server-k33` | Install RTX 3070 in rack mount | Blocked by `ngo` |
| `home-server-6yo` | Install NVIDIA drivers + CUDA on Debian | Blocked by `k33` |
| `home-server-und` | Create Windows networking stability layer | Ready |
| `home-server-pp6` | Create Windows gaming mode endpoint | Ready |
| `home-server-49l` | Deploy Qwen3-Coder-14B on Windows/WSL2 | Blocked by `und` |
| `home-server-jz4` | Create router service with intelligent routing | Blocked by `6yo`, `und`, `pp6`, `49l` |
| `home-server-e0h` | Upgrade local-ai-app to use router | Blocked by `jz4` |
| `home-server-avw` | Configure OpenCode to use local vLLM | Blocked by `jz4` |
| `home-server-yol` | Document operational procedures | Blocked by `e0h` |

## Overview

Upgrade from single Windows-only inference to a dual-GPU architecture with explicit routing and gaming-aware gating.

### Current State
- `apps/local-ai-app/` proxies requests to Windows machine
- Windows runs all models (Llama 3.1 8B, Qwen 2.5 14B, DeepSeek Coder)
- No routing logic, no gaming awareness
- Single point of failure

### Target State
- **RTX 3070 (Debian Server)**: Always-on control plane + small models
- **RTX 3090 (Windows Gaming PC)**: Warm burst compute + big models, gaming-gated

## Core Constraints (First Principles)

1. **Gaming and LLM inference are incompatible workloads** when sharing a GPU indiscriminately
2. **Stability and determinism beat hardware utilization** at this scale
3. **Routing must be explicit and auditable**, not heuristic guesswork

Therefore:
- Gaming PC must never unpredictably receive inference load
- Heavy inference must still be *available* when explicitly requested

## System Roles

### RTX 3070 — Debian Server (Always-On Service Node)

| Attribute | Value |
|-----------|-------|
| Role | Control Plane |
| OS | Debian Linux (headless) |
| Availability | Always running |
| Stack | CUDA + Docker |
| API | Single OpenAI-compatible endpoint |

**Responsibilities**:
- Primary entrypoint for all LLM requests
- Request routing (small vs big)
- Tool calling, planning, coding, orchestration
- Runs small/medium models (7B-8B class)

### RTX 3090 — Windows 11 Gaming PC (Burst Compute Node)

| Attribute | Value |
|-----------|-------|
| Role | Pure Compute |
| OS | Windows 11 + WSL2 + Docker Desktop |
| Availability | Warm by default, gated during gaming |
| Stack | vLLM inside WSL2 |
| API | Exposed via `netsh portproxy` |

**Responsibilities**:
- Heavy inference (32B-class models)
- Long context, deep reasoning, large refactors
- No routing logic, no agent state

## Networking Strategy

### WSL2 IP Stability via `netsh portproxy`

WSL2 IPs are ephemeral. Solution:

```
Windows LAN IP:8000 → portproxy → WSL2 IP:8000
```

**Components**:
1. vLLM runs inside WSL2 (Ubuntu) on port 8000
2. Windows `portproxy` forwards LAN traffic to current WSL IP
3. Self-healing PowerShell script refreshes mapping at login/startup

**Debian router only needs**:
```
http://<WINDOWS_LAN_IP>:8000
```

Never needs to know about WSL internals.

## Gaming-Aware Gating

### Mode System (Deterministic)

Windows exposes lightweight HTTP endpoint on port `18000`:

```json
{ "mode": "NORMAL" | "GAMING" }
```

**Backed by**:
- `C:\llm\mode.txt` (persistent state)
- PowerShell HTTP listener on port `18000`

### Mode Semantics

| Mode | Big Model | Router Behavior |
|------|-----------|-----------------|
| `NORMAL` | Warm, available | Prefers big for heavy requests |
| `GAMING` | Available but gated | **Will not** send traffic unless explicitly forced |

## Force-Big Override Signals

Any of these **explicit signals** override GAMING mode:

| Signal Type | Example |
|-------------|---------|
| HTTP Header | `X-Force-Big: true` |
| Model Selection | `model = "big"` |
| Prompt Tag | `#force_big` (regex-based) |

If none present and mode == GAMING → request routes to 3070 only.

## Routing Policy (Authoritative)

Evaluation order inside router:

```
1. Explicit force-big signals → route to 3090 if healthy
2. Query Windows mode endpoint
   - If GAMING → route to 3070
3. If NORMAL:
   - Token estimate ≥ threshold → 3090
   - Force-big regex match → 3090
4. If big node unhealthy → fail-soft to 3070
```

**No implicit GPU usage. No guessing.**

## Model Allocation

### Primary Model: Qwen3-Coder-14B (RTX 3090)

**Target workload**: Coding, refactors, agent-style usage (OpenCode integration)

| Attribute | Value |
|-----------|-------|
| Model | Qwen3-Coder-14B |
| Parameters | ~14B |
| VRAM Required | 24 GB (fits 3090 exactly) |
| Context Length | 32,768 tokens |
| Quantization | None (full precision bfloat16) |
| Expected Speed | ~25-50 tokens/sec (single user) |

**vLLM Launch Configuration**:
```bash
vllm serve Qwen/Qwen3-Coder-14B \
  --dtype bfloat16 \
  --max-model-len 32768 \
  --gpu-memory-utilization 0.90
```

**Why 14B over 32B**:
- 32B requires multi-GPU (doesn't fit in 24GB)
- 14B is the best quality/VRAM tradeoff for single 3090
- Sufficient for coding tasks and agent workflows

### Secondary Model: Qwen3-Coder-7B or Llama 3.1 8B (RTX 3070)

**Target workload**: Quick responses, routing, tool calling, planning

| Attribute | Value |
|-----------|-------|
| Model | Qwen3-Coder-7B or Llama 3.1 8B |
| Parameters | ~7-8B |
| VRAM Required | ~8 GB (fits 3070's 8GB) |
| Context Length | 8,192-16,384 tokens |
| Quantization | Optional AWQ for headroom |
| Expected Speed | ~40-80 tokens/sec |

**Use cases**:
- Fast autocomplete suggestions
- Quick tool-call decisions
- Planning and orchestration
- Fallback when 3090 unavailable

### Model Decision Matrix

| Model | Params | GPU | Fit | Use Case |
|-------|--------|-----|-----|----------|
| Qwen3-Coder-7B | ~7B | 3070 | ✅ Easy | Fast routing, autocomplete |
| Qwen3-Coder-14B | ~14B | 3090 | ✅ Target | Coding, refactors, agents |
| Qwen3-Coder-32B | ~32B | 3090 | ❌ No | Requires multi-GPU |
| Qwen3-Coder-72B | ~72B | — | ❌ No | Data-center only |

### System Requirements (Windows Gaming PC)

| Component | Minimum | Recommended |
|-----------|---------|-------------|
| GPU | RTX 3090 (24GB) | RTX 4090 (24GB, 1.5x faster) |
| RAM | 32 GB | 64 GB |
| CPU | 8 cores | 16-32 cores |
| Storage | NVMe SSD | NVMe SSD |
| Driver | NVIDIA ≥535 | Latest |
| CUDA | 12.x | 12.x |

**Note**: CPU affects concurrency. Undersized CPUs bottleneck multi-agent workflows.

### Operational Caveats

1. **KV Cache Dominates VRAM**
   - Long context + agents consume multiple GB
   - Concurrency increases VRAM pressure non-linearly

2. **Concurrency Risk**
   - 24GB handles 1 request comfortably
   - 2+ concurrent agent calls can OOM without tuning

3. **Quantization Trade-offs**
   - AWQ/GPTQ can fit 14B into ~16GB
   - Downsides: reduced tool-call reliability, less precise edits
   - **Acceptable only for autocomplete, not refactors**

### RTX 3090 vs 4090 Consideration

| Attribute | RTX 3090 | RTX 4090 |
|-----------|----------|----------|
| VRAM | 24 GB | 24 GB |
| Speed | Baseline | ~1.5-1.7× faster |
| Price | ~$800-1000 used | ~$1800-2000 |
| Recommendation | Current choice | Future upgrade |

3090 is viable; 4090 benefits latency-sensitive workloads significantly.

## Operational Muscle Memory

### Default (Not Gaming)
```powershell
# Mode = NORMAL (automatic)
# Big vLLM container running
# Router auto-routes heavy requests to 3090
```

### Before Gaming
```powershell
set-mode.ps1 GAMING
# Optional: stop big vLLM container for zero GPU use
```

### While Gaming
- Only heavy inference when explicitly forced
- All other requests go to 3070

### After Gaming
```powershell
set-mode.ps1 NORMAL
# Optional: restart big vLLM container
```

## Implementation Phases

### Phase 1: Debian GPU Setup (RTX 3070)
- [ ] Install NVIDIA drivers + CUDA on Debian server
- [ ] Configure Docker with GPU support
- [ ] Deploy vLLM with small model (Llama 3.1 8B)
- [ ] Test GPU inference locally

### Phase 2: Router Service
- [ ] Create router service (Python/FastAPI)
- [ ] Implement OpenAI-compatible API endpoint
- [ ] Add routing logic (small vs big)
- [ ] Add mode endpoint querying
- [ ] Add force-big signal detection

### Phase 3: Windows Stability Layer
- [ ] Create `netsh portproxy` setup script
- [ ] Create self-healing IP refresh script (runs at login)
- [ ] Create mode endpoint (PowerShell HTTP listener)
- [ ] Create `set-mode.ps1` script
- [ ] Test LAN accessibility from Debian

### Phase 4: Windows vLLM Upgrade
- [ ] Deploy vLLM with 32B model in WSL2
- [ ] Configure for LAN access via portproxy
- [ ] Test heavy inference from Debian

### Phase 5: Router Integration
- [ ] Connect router to both backends
- [ ] Implement health checks
- [ ] Implement fail-soft logic
- [ ] Test routing decisions

### Phase 6: Upgrade local-ai-app
- [ ] Update `apps/local-ai-app/` to use router
- [ ] Update documentation
- [ ] Test web interface with new architecture

### Phase 7: Documentation & Testing
- [ ] Document operational procedures
- [ ] Create gaming mode scripts on Windows
- [ ] Test gaming + inference scenarios
- [ ] Update local-ai-app README

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────┐
│                         Clients (API/Web)                           │
└─────────────────────────────────┬───────────────────────────────────┘
                                  │
                                  ▼
┌─────────────────────────────────────────────────────────────────────┐
│                    Debian Server (RTX 3070)                         │
│  ┌───────────────────────────────────────────────────────────────┐  │
│  │                     Router Service                            │  │
│  │  - OpenAI-compatible API                                      │  │
│  │  - Routing logic (small/big)                                  │  │
│  │  - Mode endpoint querying                                     │  │
│  │  - Force-big signal detection                                 │  │
│  └───────────────────────────────┬───────────────────────────────┘  │
│                                  │                                   │
│  ┌───────────────────────────────▼───────────────────────────────┐  │
│  │              vLLM (Small Models - 7B-8B)                      │  │
│  │  - Llama 3.1 8B                                               │  │
│  │  - Always available                                           │  │
│  └───────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────┬───────────────────────────────────┘
                                  │
                    (Conditional routing)
                                  │
                                  ▼
┌─────────────────────────────────────────────────────────────────────┐
│                  Windows Gaming PC (RTX 3090)                       │
│  ┌───────────────────────────────────────────────────────────────┐  │
│  │                   Mode Endpoint (:18000)                      │  │
│  │  - Returns NORMAL or GAMING                                   │  │
│  │  - Controlled by set-mode.ps1                                 │  │
│  └───────────────────────────────────────────────────────────────┘  │
│                                                                      │
│  ┌───────────────────────────────────────────────────────────────┐  │
│  │                   netsh portproxy                             │  │
│  │  - LAN:8000 → WSL2:8000                                       │  │
│  │  - Self-healing IP refresh                                    │  │
│  └───────────────────────────────┬───────────────────────────────┘  │
│                                  │                                   │
│  ┌───────────────────────────────▼───────────────────────────────┐  │
│  │              WSL2 + vLLM (Big Models - 32B)                   │  │
│  │  - Qwen 2.5 32B or similar                                    │  │
│  │  - Warm by default                                            │  │
│  │  - Gated during GAMING mode                                   │  │
│  └───────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────┘
```

## Comparison: Current vs Target

| Aspect | Current | Target |
|--------|---------|--------|
| GPU utilization | Windows only | Both GPUs |
| Routing | None (direct proxy) | Intelligent router |
| Gaming awareness | None | Explicit mode system |
| Availability | Windows-dependent | Always-on (3070 fallback) |
| Model size | Up to 14B | Up to 32B |
| Control plane | None | Debian server |
| Fail-soft | None | 3070 fallback |

## Explicit Non-Goals

- No dual-GPU gaming PC
- No automatic GPU utilization heuristics
- No LLM-only routing decisions
- No third "pet PC" mindset
- No consolidation attempts

**This is infrastructure, not experimentation.**

## Final Decision Summary

- **Separation of concerns wins** over consolidation
- 3070 = always-on control plane
- 3090 = warm burst compute, explicitly gated
- portproxy chosen for stability
- Gaming impact eliminated by design, not hope

This architecture is intentionally boring, predictable, and scalable.

## References

- [apps/local-ai-app/](../../apps/local-ai-app/) - Current proxy service (to be upgraded)
- [infrastructure-agent.md](../personas/infrastructure-agent.md) - Network infrastructure
