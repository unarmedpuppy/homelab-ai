# Plan: Qwopus Abliteration → AWQ Quantization → Dual-GPU Serving

## Context

The Qwopus model (`Jackrong/Qwen3.5-27B-Claude-4.6-Opus-Reasoning-Distilled`) is currently configured with BitsAndBytes 4-bit quantization on a single GPU (`qwopus-27b` in models.json). This is slow (~30-50% lower throughput than AWQ-Marlin) and requires `VLLM_USE_V1=0`.

**Goal:** Create an abliterated (uncensored), AWQ-quantized variant of Qwopus that runs across both RTX 3090 GPUs with tensor parallelism, maximizing KV cache for 128K+ context. Then make it the default model.

**Pipeline:** Qwopus BF16 → Obliteratus (remove refusal vectors) → AutoAWQ (4-bit quantization) → Serve via vLLM TP=2 → Push to Harbor

**Hardware:** 2× RTX 3090 (24GB each = 48GB total). AWQ 4-bit model ≈ 14GB total (7GB/GPU), leaving ~17GB/GPU for KV cache.

## Phase 1: Run Obliteratus on Qwopus

Run the existing `abliteration/run.sh` against the Qwopus model.

```bash
cd C:\Users\micro\repos\homelab-ai\abliteration
./run.sh "Jackrong/Qwen3.5-27B-Claude-4.6-Opus-Reasoning-Distilled" advanced qwopus-27b-abliterated
```

- Downloads BF16 weights from HuggingFace into `huggingface-cache` volume (if not already cached)
- Runs Obliteratus `advanced` method to remove refusal direction vectors
- Output: `C:/models/abliterated/qwopus-27b-abliterated/` (~54GB BF16 weights)
- Uses existing Docker image `library/obliteratus:latest`

**Time estimate:** 15-30 min (download) + 10-20 min (abliteration on GPU)

## Phase 2: Create AutoAWQ Tooling

**New directory:** `autoawq/` with Dockerfile, quantize script, and run script.

### `autoawq/Dockerfile`
- Base: `pytorch/pytorch:2.5.1-cuda12.4-cudnn9-runtime` (same as abliteration)
- Install: `autoawq`, `transformers`, `accelerate`, `sentencepiece`, `protobuf`
- Entrypoint: `python /app/quantize.py`

### `autoawq/quantize.py`
- Loads BF16 model from `/input` mount
- Runs AutoAWQ quantization with config: `w_bit=4, q_group_size=128, zero_point=True, version="gemm"`
- Saves AWQ checkpoint to `/output` mount
- Args: `--model-path`, `--output-path`, `--group-size` (default 128)

### `autoawq/run.sh`
```bash
# Usage: ./run.sh <input_path> <output_name>
# Example: ./run.sh C:/models/abliterated/qwopus-27b-abliterated qwopus-27b-awq
docker run --rm --gpus all \
  -v "${INPUT_PATH}:/input" \
  -v "${OUTPUT_DIR}:/output" \
  autoawq:latest \
  --model-path /input --output-path /output
```

### `autoawq/build.sh`
Build the image locally (not in CI — this is a dev tool):
```bash
docker build -t autoawq:latest .
```

### CI: Add `build-autoawq` job to `.gitea/workflows/build.yml`
Same pattern as `build-obliteratus` — build-only, not in deploy `needs` list.

## Phase 3: Quantize Abliterated Model

```bash
cd C:\Users\micro\repos\homelab-ai\autoawq
./run.sh C:/models/abliterated/qwopus-27b-abliterated qwopus-27b-awq
```

- Input: `C:/models/abliterated/qwopus-27b-abliterated/` (BF16, ~54GB)
- Output: `C:/models/quantized/qwopus-27b-awq/` (AWQ 4-bit, ~14GB)
- **Time estimate:** 30-60 min on RTX 3090

## Phase 4: Add Local Models Volume to Manager

**File:** `llm-manager/manager.py` (line 222)

Currently only mounts `huggingface-cache`. Add a second volume mount for custom/quantized models:

```python
volumes={
    "huggingface-cache": {"bind": "/root/.cache/huggingface", "mode": "rw"},
    "local-models": {"bind": "/models", "mode": "ro"},  # Custom/abliterated models
}
```

**File:** `docker-compose.gaming.yml`

Add `local-models` volume to llm-manager service and volumes section:
```yaml
volumes:
  - /var/run/docker.sock:/var/run/docker.sock
  - huggingface-cache:/root/.cache/huggingface
  - local-models:/models  # Custom quantized models
```

```yaml
volumes:
  huggingface-cache:
    external: true
  local-models:
    external: true
```

**Create the volume on gaming PC:**
```bash
docker volume create --driver local --opt type=none --opt o=bind --opt device=C:/models/quantized local-models
```

This binds `C:/models/quantized/` on the host to the `local-models` Docker volume, making all quantized models accessible inside vLLM containers at `/models/<model-name>/`.

**New env var:** `LOCAL_MODELS_PATH` in manager.py (default `/models`) — controls the bind target inside containers.

## Phase 5: Update models.json

**File:** `llm-manager/models.json`

Replace the existing `qwopus-27b` (BNB) entry with the new AWQ variant:

```json
{
  "id": "qwopus-27b-awq",
  "name": "Qwopus 27B AWQ (Opus Abliterated)",
  "hf_model": "/models/qwopus-27b-awq",
  "quantization": "awq_marlin",
  "type": "text",
  "vram_gb": 14,
  "gpu_count": 2,
  "max_context": 131072,
  "default_context": 32768,
  "extra_args": ["--disable-custom-all-reduce", "--reasoning-parser", "qwen3"],
  "description": "Claude Opus 4.6 reasoning distilled into Qwen3.5-27B, abliterated, AWQ-Marlin quantized. Dual-GPU TP=2 with 128K context.",
  "architecture": "Qwen3.5 (Opus distilled, abliterated)",
  "license": "Apache-2.0",
  "tags": ["reasoning", "distilled", "thinking", "coding-agent", "opus", "abliterated", "dual-gpu"]
}
```

Key differences from current `qwopus-27b`:
- `hf_model`: `/models/qwopus-27b-awq` (local path, not HuggingFace)
- `quantization`: `awq_marlin` (was `bitsandbytes`)
- `gpu_count`: 2 (was 1)
- `max_context`: 131072 (was 32768)
- No `env_overrides` needed (AWQ-Marlin works with V1 engine)
- No `--load-format bitsandbytes` in extra_args
- Adds `--disable-custom-all-reduce` (required for TP=2 on consumer GPUs)

## Phase 6: Update Router Config + DEFAULT_3090_MODEL

**File:** `llm-router/config/providers.yaml`

Update `qwopus-27b` entry to `qwopus-27b-awq` with `contextWindow: 131072`.

**File:** `llm-router/router.py`

Add `"qwopus-awq": "qwopus-27b-awq"` to `MODEL_ALIASES`.

**File:** `docker-compose.gaming.yml`

Change `DEFAULT_MODEL=qwopus-27b-awq` (was `qwen3.5-27b-awq`).

**File:** `docker-compose.server.yml`

Change `DEFAULT_3090_MODEL=${DEFAULT_3090_MODEL:-qwopus-27b-awq}` (was `qwen3-32b-awq`).

This makes Qwopus AWQ the default for all routing — Claude model aliases, complexity tier routing, and the `3090` shortcut all resolve to it.

## Phase 7: Push to Harbor

Create `scripts/harbor-push.sh`:
```bash
#!/usr/bin/env bash
# Push quantized model to Harbor for offline availability
# Usage: ./harbor-push.sh <model_dir> <tag>
MODEL_DIR="${1:?Usage: harbor-push.sh <model_dir> <tag>}"
TAG="${2:?Usage: harbor-push.sh <model_dir> <tag>}"
HARBOR="${HARBOR_REGISTRY:-harbor.server.unarmedpuppy.com}"

oras push "${HARBOR}/models/${TAG}:latest" "${MODEL_DIR}/."
```

Run:
```bash
./scripts/harbor-push.sh C:/models/quantized/qwopus-27b-awq qwopus-27b-awq
```

Requires `oras` CLI installed (`winget install oras-project.oras` or `scoop install oras`).

## Phase 8: CUDA Graph Mitigation

vLLM issue #35743 reports CUDA graph capture failures with AWQ 4-bit + TP=2 on Qwen3.5-27B (Hopper GPUs). The RTX 3090 is Ampere, which may not be affected. If it does fail:

**Mitigation 1** (likely needed): Add `--enforce-eager` to `extra_args` in models.json. Disables CUDA graphs entirely — small throughput hit but reliable.

**Mitigation 2** (if available in nightly): Use `--compilation-config '{"level": 1}'` for piecewise CUDA graphs.

We'll start without `--enforce-eager` and add it only if CUDA graph capture fails during testing.

## Files Summary

| File | Action |
|------|--------|
| `autoawq/Dockerfile` | **Create** — AutoAWQ Docker image |
| `autoawq/quantize.py` | **Create** — Quantization script |
| `autoawq/run.sh` | **Create** — Run script (mounts input/output volumes) |
| `autoawq/build.sh` | **Create** — Local image build script |
| `.gitea/workflows/build.yml` | **Modify** — Add `build-autoawq` job |
| `llm-manager/manager.py` | **Modify** — Add `local-models` volume mount (line 222) |
| `llm-manager/models.json` | **Modify** — Replace `qwopus-27b` with `qwopus-27b-awq` |
| `llm-router/config/providers.yaml` | **Modify** — Update qwopus entry |
| `llm-router/router.py` | **Modify** — Add `qwopus-awq` alias |
| `docker-compose.gaming.yml` | **Modify** — Add `local-models` volume, change DEFAULT_MODEL |
| `docker-compose.server.yml` | **Modify** — Change DEFAULT_3090_MODEL default |
| `scripts/harbor-push.sh` | **Create** — Harbor push helper |

## Execution Order

1. **Code changes first** (phases 2, 4, 5, 6) — commit and push
2. **Build AutoAWQ image** (phase 2 build.sh) on gaming PC
3. **Run Obliteratus** (phase 1) on gaming PC — ~30-50 min
4. **Run AutoAWQ** (phase 3) on gaming PC — ~30-60 min
5. **Create local-models volume** (phase 4) on gaming PC
6. **Deploy updated stack** — `docker compose pull && docker compose up -d`
7. **Test** — verify model loads, abliteration works, context window, performance
8. **Push to Harbor** (phase 7) for offline backup
9. **Apply CUDA graph fix** (phase 8) if needed

## Verification

1. `docker exec llm-manager curl localhost:8000/status` — qwopus-27b-awq shows as running
2. `nvidia-smi` — both GPUs show ~7GB model weight usage each
3. Send chat request with `model=qwopus-27b-awq` — get valid response
4. Abliteration test: ask a typically-refused question — should answer without refusal
5. Context test: send 32K+ token prompt — should process without OOM
6. Performance: measure tok/s and compare to qwen3.5-27b-awq baseline
7. Router test: default routing resolves to qwopus-27b-awq

## Rollback

If anything goes wrong:
1. Change `DEFAULT_MODEL` back to `qwen3.5-27b-awq` in docker-compose.gaming.yml
2. Change `DEFAULT_3090_MODEL` back to `qwen3-32b-awq` in docker-compose.server.yml
3. The old `qwopus-27b` (BNB) entry can be restored in models.json
4. `docker compose up -d` to redeploy
