# Qwopus: Claude Opus 4.6 Reasoning-Distilled Model Integration

- **Date:** 2026-03-08
- **Status:** Accepted
- **Repos/Services affected:** homelab-ai (llm-manager/models.json, llm-manager/manager.py, llm-router/config/providers.yaml, llm-router/router.py)

## Context

Community model `Jackrong/Qwen3.5-27B-Claude-4.6-Opus-Reasoning-Distilled` ("Qwopus") distills Claude Opus 4.6 reasoning capabilities into Qwen3.5-27B architecture via LoRA fine-tuning on ~8K reasoning traces. This offers a local, offline-capable model with strong reasoning and coding agent performance. The model is available only in BF16 and GGUF formats — no AWQ quantization exists yet.

The existing model serving infrastructure uses vLLM with AWQ-Marlin quantization for all local models. BF16 at 27B params (~54GB) does not fit on a 24GB RTX 3090. A quantization strategy is needed.

## Decision

Add Qwopus as an **additional selectable model** (not replacing the default `qwen3.5-27b-awq`) using **BitsAndBytes 4-bit quantization** via vLLM, with a new per-model `env_overrides` mechanism to handle compatibility requirements.

## Options Considered

### Option A: Wait for community AWQ quantization
No work required, but indefinite wait. Rejected — user wants the model available now.

### Option B: Create AWQ quantization ourselves
Run AutoAWQ on BF16 weights to produce AWQ-Marlin checkpoint. Best long-term solution but requires significant compute time and testing. Tracked as future enhancement.

### Option C: BitsAndBytes 4-bit via vLLM (selected)
- vLLM supports `--quantization bitsandbytes --load-format bitsandbytes` for on-the-fly 4-bit quantization
- ~16.5GB VRAM footprint (fits on 24GB 3090 with room for KV cache)
- Requires `VLLM_USE_V1=0` (BNB not yet compatible with vLLM V1 engine)
- Slower than AWQ-Marlin but functional immediately

### Option D: GGUF via llama.cpp
Model has GGUF variants. Would require a separate inference engine. Rejected — would fragment the serving infrastructure.

## Changes Made

| File | Change |
|------|--------|
| `llm-manager/models.json` | Added `qwopus-27b` entry with `quantization: "bitsandbytes"`, `extra_args: ["--reasoning-parser", "qwen3", "--load-format", "bitsandbytes"]`, and `env_overrides: {"VLLM_USE_V1": "0"}` |
| `llm-manager/manager.py` | Added per-model `env_overrides` support in container creation. Merges model-level env vars into the container environment dict. |
| `llm-router/config/providers.yaml` | Added `qwopus-27b` model config under `gaming-pc-3090` provider with capabilities and tags |
| `llm-router/router.py` | Added `"qwopus": "qwopus-27b"` to `MODEL_ALIASES` dict and model listing endpoint |

### Per-Model env_overrides Pattern

The `env_overrides` field in `models.json` allows individual models to set container environment variables that differ from global defaults. This was needed because BitsAndBytes requires `VLLM_USE_V1=0` while all other models use V1 engine.

```python
# In manager.py container creation
**{k: str(v) for k, v in card.get("env_overrides", {}).items()},
```

This pattern is generic and can be reused for any future model that needs non-default environment configuration.

## Consequences

### Positive
- Claude Opus reasoning quality available locally, offline, at zero marginal cost
- Accessible via `model="qwopus"` alias through the router
- Per-model env_overrides pattern enables future models with different requirements
- Native thinking mode via `--reasoning-parser qwen3`

### Negative / Tradeoffs
- BitsAndBytes is slower than AWQ-Marlin (~30-50% lower throughput)
- Forces `VLLM_USE_V1=0` for this model (loses V1 engine optimizations)
- LoRA fine-tuning on ~8K sequences means reasoning quality may degrade beyond 8K context

### Risks
- **Context window uncertainty:** Model architecture supports 262K but was trained on ~8K. Set `default_context: 8192` conservatively, `max_context: 32768` optimistically. Needs empirical testing.
- **BNB quantization quality:** 4-bit BNB may have more quality loss than AWQ for reasoning tasks. Mitigated by creating AWQ quant as follow-up.

## Follow-up

- [ ] Create AWQ quantization using AutoAWQ (tracked in model-garden-enhancements.md #1)
- [ ] Test effective context window limits at 8K, 16K, 32K (tracked in model-garden-enhancements.md #2)
- [ ] Evaluate as reasoning-tier default in complexity router (tracked in model-garden-enhancements.md #3)
- [ ] Benchmark tok/s vs qwen3.5-27b-awq to quantify BNB performance gap
