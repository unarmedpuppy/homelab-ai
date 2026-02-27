# Qwen3-32B-AWQ as Primary RTX 3090 Model

- **Date:** 2026-02-22
- **Status:** Accepted
- **Repos/Services affected:** homelab-ai (llm-manager/models.json, llm-router/config/providers.yaml, llm-router/complexity.py, docker-compose.gaming.yml)

## Context

The RTX 3090 (24GB VRAM, 32GB system RAM) was running `qwen2.5-32b-awq` as its default model, released mid-2024. By early 2026, several stronger models fit the same VRAM envelope. The auto-routing tier map was also sending MODERATE/COMPLEX requests to `qwen2.5-14b-awq`, underutilizing the 3090.

## Decision

Replace `qwen2.5-32b-awq` / `qwen2.5-14b-awq` as the primary 3090 model with **`Qwen/Qwen3-32B-AWQ`** across all routing layers.

## Options Considered

### Option A: Stay on Qwen2.5-32B-AWQ
Stable, known-good, no work required.
Rejected — significantly outperformed by Qwen3 on reasoning, coding, and instruction following. No reason to stay.

### Option B: Qwen3-32B-AWQ (selected)
- **HF repo:** `Qwen/Qwen3-32B-AWQ` (official first-party quantization)
- **VRAM:** ~19.3GB — fits on 24GB with ~4.7GB for KV cache
- **Context:** 16K practical on 24GB (`--max-model-len 16384` passed via `default_context`)
- **Key win:** Hybrid thinking/non-thinking mode — same model handles fast chat AND deep CoT reasoning
- **vLLM:** Full support >= 0.8.5 (pinned in docker-compose.gaming.yml)
- **Benchmarks vs Qwen2.5-32B:** AIME24 ~79% vs ~50%, GPQA Diamond 69% vs 65.8%, LiveBench substantial improvement

### Option C: Qwen3-Coder-30B-A3B AWQ (MoE)
- ~15GB VRAM, 48K+ context, 50%+ SWE-bench Verified
- Stronger for coding/agentic tasks
- Rejected for now: community-maintained AWQ checkpoint (not official), MoE architecture less tested in this vLLM setup
- **Revisit** if primary use shifts heavily toward agentic coding

### Option D: GLM-4.7-Flash AWQ
- 59.2% SWE-bench (best in class), dominant tool use
- Rejected: vLLM KV cache bug (MLA not recognized for `glm4_moe_lite`) limits context to 2-8K until PR #32614 merges to stable vLLM
- **Revisit** when MLA fix ships in vLLM stable release

## Changes Made

| File | Change |
|------|--------|
| `llm-manager/models.json` | Added `qwen3-32b-awq` entry (`Qwen/Qwen3-32B-AWQ`, 20GB VRAM, 16384 default context) |
| `llm-router/config/providers.yaml` | Added `qwen3-32b-awq` as `isDefault: true` on `gaming-pc-3090`; kept `qwen2.5-14b-awq` as non-default fallback |
| `llm-router/complexity.py` | TIER_MODEL_MAP MODERATE + COMPLEX → `qwen3-32b-awq` (was `qwen2.5-14b-awq`) |
| `docker-compose.gaming.yml` | `DEFAULT_MODEL=qwen3-32b-awq`; pinned `VLLM_IMAGE` to `v0.8.5` (was `:latest`) |

## Consequences

### Positive
- Full 3090 VRAM utilized for primary model (32B vs 14B for auto-routed requests)
- Thinking mode available for MODERATE/COMPLEX requests without switching models
- vLLM version pinned — no surprise breakage from `:latest` pulling an incompatible build

### Negative / Tradeoffs
- Qwen3-32B is slower to load on first on-demand request (~60-90s cold start vs ~30s for 14B)
- 16K context limit practical on 24GB (Qwen2.5 also had 32K theoretical but similar practical limits)
- vLLM `v0.8.5` needs to be available in Harbor cache — pull on gaming PC after deploy

### Risks
- **Thinking mode token blowup:** Qwen3 thinking traces can be very long. If token budget isn't managed by callers, costs/latency increase for simple tasks. Mitigated by ROUTINE tier still routing to 7B on server, and non-thinking mode is default.
- **GLM-4.7-Flash is better for coding** once the vLLM MLA bug is fixed. This decision should be revisited when PR #32614 merges.

## Follow-up

- [x] Confirm Harbor has vLLM `v0.8.5` cached — pull gaming PC deploy and verify
- [x] **Performance optimization (2026-02-27):** Switched to `awq_marlin` quantization, eliminated CPU offloading, reduced context to 8K. See [ADR: vLLM AWQ-Marlin and WSL2 Optimization](2026-02-27-vllm-awq-marlin-and-wsl2-optimization.md). Result: ~19 tok/s (was ~1.6 tok/s).
- [ ] Monitor Qwen3 thinking mode behavior in router logs — may want to add `--enable-reasoning --reasoning-parser deepseek_r1` to manager serve args for proper thinking token handling
- [ ] Watch vLLM PR #32614 (GLM MLA fix) — swap to GLM-4.7-Flash when merged
- [ ] Consider Qwen3-Coder-30B-A3B MoE as a second model slot for heavy agentic sessions
