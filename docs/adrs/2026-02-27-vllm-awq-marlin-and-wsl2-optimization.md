# vLLM AWQ-Marlin Quantization and WSL2 Optimization

- **Date:** 2026-02-27
- **Status:** Accepted
- **Authors:** Joshua Jenquist
- **Impacted Repos/Services:** homelab-ai (llm-manager/models.json, llm-manager/manager.py, docker-compose.gaming.yml, image-server/requirements.txt)
- **Supersedes:** Partially updates [2026-02-22 Qwen3-32B as Primary 3090 Model](2026-02-22-qwen3-32b-as-primary-3090-model.md)

## Context

After deploying Qwen3-32B-AWQ on the RTX 3090 gaming PC (WSL2), three issues surfaced:

1. **Bootlooping containers** (`image-server`, `gaming-dashboard`) after dependency updates
2. **vLLM failing to start** with `--cpu-offload-gb` on WSL2 (V1 engine requires UVA/pinned memory, which WSL2 does not support)
3. **Extremely slow inference** (~1.6 tok/s) when CPU offloading was working via V0 engine — the 4GB PCIe round-trip per forward pass dominated latency

The original deployment used `quantization=awq` with `--enforce-eager` (disabling CUDA graphs), `--cpu-offload-gb 4` (to fit 16K context KV cache), and the V0 engine (required for CPU offloading on WSL2). All three compounded to produce unusable generation speeds.

## Decision

Switch to **`awq_marlin`** quantization, **eliminate CPU offloading**, and reduce default context to **8192 tokens** to fit entirely in VRAM. This enables the V1 engine, CUDA graphs, and Marlin's optimized GEMM kernels.

## Options Considered

### Option A: Keep AWQ with CPU offloading (status quo)

- `quantization=awq`, `--enforce-eager`, `--cpu-offload-gb 4`, V0 engine
- ~1.6 tok/s — unusable for interactive chat
- Rejected: performance too poor despite providing 16K context

### Option B: AWQ-Marlin with CPU offloading

- Switch to `awq_marlin` (faster kernels, no `--enforce-eager` needed)
- Keep `--cpu-offload-gb 4` for 16K context, stay on V0 engine
- Estimated ~5-8 tok/s improvement from Marlin kernels alone
- Rejected: CPU offloading over PCIe remains the dominant bottleneck

### Option C: AWQ-Marlin without CPU offloading, reduced context (selected)

- `quantization=awq_marlin`, no `--enforce-eager`, no CPU offloading
- Reduce `default_context` from 16384 to 8192 to halve KV cache requirement
- V1 engine enabled (no offloading = no WSL2 UVA conflict)
- CUDA graphs enabled (no `--enforce-eager`)
- **Result: ~19 tok/s** (12x improvement)

### Option D: Upgrade to PyTorch 2.4+ base image for UVA support

- Would allow V1 engine with CPU offloading on WSL2
- Rejected: requires rebuilding the PyTorch base image in Harbor, and CPU offloading still bottlenecks on PCIe bandwidth regardless of engine version

## Root Cause Analysis

### Container bootloops

| Container | Root Cause | Fix |
|-----------|-----------|-----|
| `image-server` | `diffusers>=0.30.0` references `torch.xpu` (Intel XPU), absent in PyTorch 2.2.0 base image. `transformers>=5.0.0` also incompatible. | Pin `diffusers>=0.27.0,<0.30.0` and `transformers>=4.51.3,<5.0.0` |
| `gaming-dashboard` | Old Docker image had hardcoded `llm-router` upstream in nginx config. Registry image was stale; `docker compose build` was a no-op because compose file had no `build:` directive. | Rebuild directly via `docker build` from the Dockerfile containing the corrected `nginx.conf.template` with variable-based `proxy_pass` |

### vLLM CPU offloading failure on WSL2

vLLM v0.8.5's V1 engine requires UVA (Unified Virtual Addressing) for `--cpu-offload-gb`. WSL2 does not support pinned memory (`pin_memory=False` is forced). The V1 engine crashes with:

```
AssertionError: V1 CPU offloading requires uva (pin memory) support
```

Fix: Set `VLLM_USE_V1=0` environment variable when `CPU_OFFLOAD_GB > 0` to force V0 engine. This is handled in `manager.py` when spawning vLLM containers.

### Performance analysis

| Configuration | Engine | Quantization | CUDA Graphs | CPU Offload | tok/s |
|---------------|--------|-------------|-------------|-------------|-------|
| Original | V0 | awq | Disabled | 4GB | ~1.6 |
| Final | V1 | awq_marlin | Enabled | None | ~19 |

The 12x speedup comes from three stacked improvements:
- **awq_marlin** Marlin GEMM kernels vs generic AWQ (~2-3x)
- **CUDA graphs** enabled via no `--enforce-eager` (~1.5-2x)
- **No CPU offloading** eliminates PCIe bandwidth bottleneck (~3-4x)

## Changes Made

| File | Change |
|------|--------|
| `llm-manager/models.json` | `qwen3-32b-awq` quantization `awq` -> `awq_marlin`, `default_context` 16384 -> 8192 |
| `llm-manager/manager.py` | Pass `VLLM_USE_V1=0` env var to vLLM containers when `CPU_OFFLOAD_GB > 0` |
| `docker-compose.gaming.yml` | `CPU_OFFLOAD_GB=0` (was 4), added to env vars |
| `image-server/requirements.txt` | Pin `diffusers>=0.27.0,<0.30.0`, `transformers>=4.51.3,<5.0.0` |
| `dashboard/` | Rebuilt from Dockerfile to pick up corrected nginx.conf.template |

## Consequences

### Positive

- 12x inference speedup (~19 tok/s vs ~1.6 tok/s) makes interactive chat usable
- V1 engine brings chunked prefill, prefix caching, and async output processing
- Marlin kernels are purpose-built for AWQ inference on NVIDIA GPUs
- Simpler deployment: no CPU offloading means no WSL2 UVA workarounds needed

### Negative / Tradeoffs

- Context window reduced from 16K to 8K tokens — limits long-conversation and document-analysis use cases
- `image-server` pinned to `diffusers<0.30.0` which blocks Qwen Image Edit 2509 support (requires `diffusers>=0.30.0`). Needs PyTorch 2.4+ base image to unblock.

### Risks

- **8K context may be too short** for agentic/coding workflows. Monitor usage and consider 10K-12K if VRAM budget allows.
- **Marlin kernel compatibility**: `awq_marlin` requires specific GPU compute capability. RTX 3090 (sm_86) is supported. Verify before deploying to other GPUs.

## Lessons Learned

1. **`docker compose build` requires a `build:` directive** — without it, the command is a no-op even if it exits 0. Always verify image tags/timestamps after builds.
2. **WSL2 disables `pin_memory`** — any CUDA feature depending on UVA/pinned memory will fail silently or crash. Test GPU-intensive features on WSL2 explicitly.
3. **CPU offloading is a last resort** — PCIe 3.0/4.0 bandwidth (~12-25 GB/s) is 10-40x slower than VRAM bandwidth (~936 GB/s on 3090). Even small offloads create significant bottlenecks.
4. **Version pins matter for ML stacks** — `diffusers`, `transformers`, and `torch` move fast. Pin upper bounds on all three to prevent cross-package breakage.

## Follow-up

- [ ] Rebuild `image-server` with PyTorch 2.4+ base image to unblock `diffusers>=0.30.0` and Qwen Image Edit 2509
- [ ] Test 10K-12K `max-model-len` with `awq_marlin` to recover some context window without OOM
- [ ] Add `build:` directives to `docker-compose.gaming.yml` services for local development builds
- [ ] Consider `--enable-reasoning --reasoning-parser deepseek_r1` for proper Qwen3 thinking token handling
