# Model Garden — Abliteration & Quantization Pipeline

**Created:** 2026-03-12
**Updated:** 2026-03-14
**Status:** 🟡 In Progress — Option 1, Attempt 5 (vLLM + transformers v5 + BNB)

The goal is to build a garden of high-quality, abliterated (and/or distilled) models served by
vLLM nightly on the gaming PC (2x RTX 3090, 48GB VRAM, 64GB RAM / 54GB WSL).

---

## Model Options

| # | Model | Status | Priority |
|---|-------|--------|----------|
| 1 | Qwen3.5-27B Abliterated → vLLM (BNB or AWQ) | 🟡 In Progress | First |
| 2 | Qwopus-27B Abliterated → AWQ | ⬜ Pending | Second |
| 3 | Qwen3-32B Abliterated → AWQ | ⬜ Pending | Third |
| 4 | Qwen3-72B AWQ (no abliteration) | ⬜ Pending | Anytime |

---

## Option 1 — Qwen3.5-27B Abliterated

### What we have (as of 2026-03-14)

- **BF16 abliterated model**: `/mnt/c/models/abliterated/qwen3.5-27b-abliterated-bf16/`
  - 51GB, 28 safetensors shards, `model_type: qwen3_5_text`
  - Abliterated via obliteratus `--method basic --dtype bfloat16`
  - 186/851 tensors used original weights (meta device VRAM overflow workaround)
  - Produced by patched obliteratus image (`obliteratus:meta-patch`)

### Attempt History

#### Attempt 1 — BNB 4-bit load in vLLM (original abliterated weights) ❌
- **What:** Previous BNB 4-bit abliterated model (`/models/qwen3.5-27b-abliterated`) via `--load-format bitsandbytes`
- **Failure:** `qwen3_5_text` not in transformers 4.57.6 (pinned by vLLM nightly). Architecture not recognized.

#### Attempt 2 — AWQ quantization via llmcompressor ❌
- **What:** `llmcompressor` to quantize BF16 → AWQ
- **Failure:** llmcompressor pins transformers ≤ 4.57.6, killing qwen3_5_text support immediately.

#### Attempt 3 — AWQ quantization via AutoAWQ 0.2.9 (direct) ❌
- **What:** Rewrote `autoawq/quantize.py` to use `AutoAWQForCausalLM` directly with `qwen3_5_text → qwen3` registry patch
- **Failure 3a:** `TypeError: qwen3_5_text isn't supported yet` — registry not patched at load time
- **Failure 3b (Catcher crash):** `AttributeError: 'Catcher' object has no attribute 'layer_type'`
  - AutoAWQ wraps layer 0 in a Catcher hook; Qwen3.5's hybrid forward reads `layer_type` from it
  - Fixed by patching `awq/quantize/quantizer.py` at build time to add `__getattr__` to Catcher
  - The `__getattr__` fix itself had a bug: defining `__getattr__` on `nn.Module` overrides PyTorch's
    own `__getattr__` which resolves `_modules`. Fixed by calling `super().__getattr__()` first,
    then falling back to `self.__dict__['_modules']['module']` to avoid recursion.
- **Failure 3c (get_layers_for_scaling):** `AttributeError: 'Qwen3_5DecoderLayer' has no attribute 'self_attn'`
  - Qwen3.5 is a **hybrid architecture** — some decoder layers use linear attention (GLA-style)
    with different attribute names than standard self-attention
  - AutoAWQ's `qwen3.py` hardcodes `module.self_attn.q_proj` etc. for all layers
  - **Root cause:** `qwen3_5_text → qwen3` registry mapping gets past the type check but the
    layer structure is fundamentally different. AWQ quantization of Qwen3.5 requires a dedicated
    AWQ model implementation, not a Qwen3 alias.
  - **Status: Abandoned.** AWQ of Qwen3.5 hybrid architecture is not viable without significant
    AutoAWQ modifications.

#### Attempt 4 (Current) — vLLM + transformers v5 + BNB 4-bit ⬜
- **What:** Build custom vLLM image that upgrades transformers to v5 after install.
  vLLM nightly pins transformers 4.x, but pip doesn't enforce this at runtime.
  With transformers v5, `qwen3_5_text` is natively supported.
  Load the 51GB BF16 model using `--load-format bitsandbytes --quantization bitsandbytes`
  (vLLM quantizes on-the-fly to ~13GB, fits in 48GB VRAM).
- **Reference:** https://github.com/vllm-project/vllm/issues/35395
- **Files:** `homelab-ai/vllm/Dockerfile`
- **Status:** 🟡 Testing

### Current Attempt — Attempt 4

#### Step 1 — Build custom vLLM image ✅

```dockerfile
# homelab-ai/vllm/Dockerfile
FROM vllm/vllm-openai:nightly
RUN pip install --no-cache-dir --upgrade transformers
```

```bash
cd /mnt/c/Users/micro/repos/homelab-ai/vllm
docker build -t vllm-tf5:local .
```

#### Step 2 — Test direct load ⬜

```bash
docker run --rm --gpus all \
  -v /mnt/c/models/abliterated/qwen3.5-27b-abliterated-bf16:/model:ro \
  -v huggingface-cache:/root/.cache/huggingface \
  vllm-tf5:local \
  --model /model \
  --load-format bitsandbytes \
  --quantization bitsandbytes \
  --tensor-parallel-size 2 \
  --max-model-len 65536 \
  --gpu-memory-utilization 0.90 \
  --disable-custom-all-reduce \
  --reasoning-parser qwen3 \
  --port 8000
```

Expected: vLLM loads, quantizes to ~13GB across both GPUs, serves on port 8000.

#### Step 3 — If successful: update compose and deploy ⬜

In `docker-compose.gaming.yml`:
```yaml
- VLLM_IMAGE=vllm-tf5:local
```

Or push to Harbor and reference the tagged image.

Update `llm-manager/models.json` abliterated entry:
```json
{
  "id": "qwen3.5-27b-abliterated",
  "hf_model": "/model-bf16",
  "quantization": "bitsandbytes",
  "extra_args": [
    "--load-format", "bitsandbytes",
    "--tensor-parallel-size", "2",
    "--max-model-len", "65536",
    "--disable-custom-all-reduce",
    "--reasoning-parser", "qwen3"
  ]
}
```

Add volume mount for BF16 model path to llm-manager + spawned vLLM containers.

#### Step 4 — If transformers v5 breaks vLLM internals ⬜

Fall back to Option 1b: Qwen3-32B Abliterated (standard architecture, proven AWQ pipeline).
`model_type: qwen3`, supported by AutoAWQ 0.2.9 without any patching.

---

### Blocker: vLLM + Qwen3.5 native support

**PR to watch:** https://github.com/vllm-project/vllm/pull/30566
Once merged into vLLM nightly, `qwen3_5_text` is natively supported and this Dockerfile
hack is no longer needed. Check every session.

**Status 2026-03-13:** Open, 0 approvals, active rebasing. Not imminent.

---

## Option 2 — Qwopus-27B Abliterated + AWQ

**Model:** `Jackrong/Qwen3.5-27B-Claude-4.6-Opus-Reasoning-Distilled`
Same hybrid Qwen3.5 architecture as Option 1. AWQ quantization has the same blockers.
**Depends on:** Option 1 toolchain resolution.

---

## Option 3 — Qwen3-32B Abliterated + AWQ

**Model:** `Qwen/Qwen3-32B`
Fully proven pipeline. `model_type: qwen3` — natively supported by AutoAWQ 0.2.9, no patching.
More parameters than 27B but older architecture (no hybrid attention).
**Fallback plan if Option 1 continues to fail.**

FP16 = ~64GB. With 48GB VRAM + 54GB WSL RAM = fits via `device_map=auto` for abliteration.
AWQ quantized output: ~20GB, runs on dual-GPU TP=2.

---

## Option 4 — Qwen3-72B AWQ (No Abliteration)

**Model:** `Qwen/Qwen3-72B-AWQ` (pre-quantized from HuggingFace)
Largest model that fits in 48GB VRAM at AWQ 4-bit (~36GB). No abliteration possible.

---

## Hardware Reference

- **GPUs:** 2x RTX 3090 (48GB VRAM total, PCIe x8/x8, no NVLink)
- **RAM:** 64GB physical, 54GB WSL
- **Total addressable:** ~102GB (abliteration on CPU+GPU), 48GB (inference)
- **vLLM image:** `vllm/vllm-openai:nightly` (transformers 4.57.6, supports qwen3 + qwen3_5 AWQ path only)
- **Custom vLLM image:** `vllm-tf5:local` (nightly + transformers v5, supports qwen3_5_text natively)
- **autoawq image:** `harbor.server.unarmedpuppy.com/library/autoawq:latest` (autoawq 0.2.9)

## Tag Sequence

- v1.10.55–v1.10.58 — various llm-manager and config fixes (deployed)
- v1.10.59 — pending: models.json update after Option 1 resolution
- v1.10.60+ — subsequent model additions
