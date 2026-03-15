# ADR: Lightweight Model Garden Additions and Server vLLM Upgrade

- **Date:** 2026-03-15
- **Status:** Accepted
- **Repos/Services affected:** homelab-ai (`llm-manager/models.json`, `docker-compose.server.yml`)
- **Tasks:** homelab-ai-024, homelab-ai-025
- **Related:**
  - [2026-03-08-model-garden-architecture.md](2026-03-08-model-garden-architecture.md)
  - [2026-03-15-glm-model-garden-additions.md](2026-03-15-glm-model-garden-additions.md)

## Context

Two independent goals addressed together:

### 1. RTX 3070 Model Coverage

The server's RTX 3070 (8GB VRAM) was underserved — only `qwen2.5-7b-awq` (5GB) was
realistically available. A range of sub-4GB models fills this gap with models suited for
always-on workloads, fast tool calling, and low-latency responses.

### 2. Mobile / Edge / Godot Catalog

The SmolLM2 series and Gemma3 small models serve a dual purpose:
- Runnable by vLLM on the server (catalog + prefetch into `huggingface-cache` volume)
- Primary deployment path: **GGUF export for Godot** via GDLlama GDExtension, and
  **mobile bundling** via MLC-LLM (iOS Metal, Android Vulkan) or ONNX Runtime

Registering them in `models.json` makes them visible in the model garden UI and
prefetchable to Harbor-backed persistent storage even if they aren't actively served by vLLM.

### 3. vLLM Server Upgrade: v0.6.6.post1 → v0.17.1

Server was pinned at initial deployment. v0.17.1 (released 2026-03-11) adds:
- Phi-4-mini tool calling (PR #14880)
- Qwen3 series support (v0.8.5+)
- Improved Gemma3 support
- V1 engine (faster small model throughput)
- Numerous quantization and stability fixes

## Decisions

### Models Added (10 total)

#### RTX 3070 Served Models (vram_gb ≤ 8)

| Model ID | HF Model | Quant | VRAM | Tool Calling |
|----------|----------|-------|------|--------------|
| `qwen2.5-0.5b` | `Qwen/Qwen2.5-0.5B-Instruct` | native | 1GB | hermes |
| `qwen2.5-1.5b-awq` | `Qwen/Qwen2.5-1.5B-Instruct-AWQ` | awq_marlin | 2GB | hermes |
| `qwen2.5-3b-awq` | `Qwen/Qwen2.5-3B-Instruct-AWQ` | awq_marlin | 3GB | hermes |
| `phi-4-mini` | `microsoft/Phi-4-mini-instruct` | bitsandbytes | 3GB | verify on v0.17.1 |
| `gemma3-2b` | `google/gemma-3-2b-it` | native | 4GB | auto (prompt) |
| `gemma3-1b` | `google/gemma-3-1b-it` | native | 2GB | auto (prompt) |

#### Mobile / Edge / Godot Catalog (also vLLM-servable on 3070)

| Model ID | HF Model | Size (native) | Primary Use |
|----------|----------|---------------|-------------|
| `smollm2-1.7b` | `HuggingFaceTB/SmolLM2-1.7B-Instruct` | ~3.2GB | Fine-tune + GGUF/ONNX/MLC |
| `smollm2-360m` | `HuggingFaceTB/SmolLM2-360M-Instruct` | ~680MB | GGUF for Godot (GDLlama) |
| `smollm2-135m` | `HuggingFaceTB/SmolLM2-135M-Instruct` | ~260MB | Mobile bundle |
| `gemma3-270m` | `google/gemma-3-270m-it` | ~520MB | FunctionGemma tool calling at edge |

### vLLM Upgrade

```yaml
# docker-compose.server.yml
- VLLM_IMAGE=${HARBOR_REGISTRY}/docker-hub/vllm/vllm-openai:v0.17.1
```

Harbor proxies Docker Hub — pulls `vllm/vllm-openai:v0.17.1` on first use.

## VRAM Routing

llm-manager detects GPU VRAM and filters models automatically:

- **RTX 3070 (8GB, server):** loads `vram_gb ≤ 8` → 12 models available
- **RTX 3090 (24GB, gaming PC):** loads all `vram_gb ≤ 24`; `gpu_count: 2` models use TP

The mobile/edge models (smollm2, gemma3-270m) technically fit the 3070 and will be loaded
by vLLM if requested. This is fine — they serve as a download cache even if rarely used for
inference directly.

## Mobile / Godot Deployment Notes

### Godot (GDLlama GDExtension)

```gdscript
var llama = GDLlama.new()
llama.model_path = "res://models/smollm2-360m-q6.gguf"
var response = await llama.generate("NPC: " + player_input)
```

Best models: `smollm2-360m` (Q6_K, ~450MB) or `gemma3-270m` (Q4, ~320MB for tool calls).
Fine-tune on game dialogue with QLoRA first for character consistency.

### Mobile (MLC-LLM)

Compiles to platform binaries. Supported models include SmolLM2, Gemma3, Qwen2.5.
`gemma3-1b` QAT INT4 GGUF: ~500MB, runs on mid-range Android/iOS.

### Fine-Tuning on the 3070

The RTX 3070 (8GB) can QLoRA fine-tune up to ~3B models:

```bash
# Example: fine-tune SmolLM2-360M on game dialogue
unsloth-cli finetune --model HuggingFaceTB/SmolLM2-360M-Instruct \
  --dataset game_dialogue.jsonl --lora-rank 16 --output ./finetuned
# Export to GGUF for Godot
python -m llama_cpp.convert --model ./finetuned --outfile model-q6.gguf --outtype q6_k
```

## Verification Checklist

- [ ] `phi-4-mini`: confirm `--tool-call-parser` name on vLLM v0.17.1 (likely `hermes` or `phi3`)
- [ ] `gemma3-270m`: verify HF ID — FunctionGemma may be at `google/functiongemma-270m`
- [ ] `Qwen/Qwen2.5-3B-Instruct-AWQ`: verify this exact HF repo exists
- [ ] vLLM v0.17.1: confirm `awq_marlin` still works (should — long-stable feature)
- [ ] Server redeploy: verify llm-manager starts and loads at least one model successfully
- [ ] `CPU_OFFLOAD_GB=1` in server compose: may need removing for v0.17.1 V1 engine

## Consequences

- 3070 server gains 10 new models including always-on candidates (qwen2.5-0.5b/1.5b, gemma3-1b)
- Mobile/edge models are prefetchable to `huggingface-cache` via model garden UI
- GGUF export for Godot/mobile is a manual workflow for now (not automated)
- vLLM v0.17.1 is a large jump from v0.6.6 — monitor server llm-manager logs after deploy
- Phi-4-mini tool-call-parser needs one test cycle to confirm correct parser name

## Follow-up

- Automate GGUF export pipeline (HF weights → quantized GGUF → Harbor OCI artifact)
- Investigate MLC-LLM compilation workflow for mobile bundle
- Fine-tune `smollm2-360m` on domain-specific dialogue for Godot
- Add Phi-4-mini AWQ once community quant available (faster load than BNB)
