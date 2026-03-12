# Model Garden — Abliteration & Quantization Pipeline

**Created:** 2026-03-12
**Status:** 🟡 In Progress — Option 1 active

The goal is to build a garden of high-quality, abliterated (and/or distilled) models served by
vLLM nightly on the gaming PC (2x RTX 3090, 48GB VRAM, 64GB RAM / 54GB WSL).

---

## Model Options

| # | Model | Status | Priority |
|---|-------|--------|----------|
| 1 | Qwen3.5-27B Abliterated → AWQ | 🟡 In Progress | First |
| 2 | Qwopus-27B Abliterated → AWQ | ⬜ Pending | Second |
| 3 | Qwen3-32B Abliterated → AWQ | ⬜ Pending | Third |
| 4 | Qwen3-72B AWQ (no abliteration) | ⬜ Pending | Anytime |

---

## Option 1 — Qwen3.5-27B Abliterated + AWQ

**Why first:** Abliterated FP16 weights already exist in the local-models volume.
Only the quantization step is needed. Could be done today.

**Why it works:** vLLM nightly's AWQ path supports `qwen3_5_text` (proven by
QuantTrio/Qwen3.5-27B-AWQ running successfully). The autoawq container already has
`autoawq 0.2.9` and `transformers 5.3.0` — just the quantize.py script needs to be
rewritten to use AutoAWQ directly instead of llmcompressor (which isn't installed).

### Step 1 — Fix quantize.py ✅ / ⬜

Rewrite `/homelab-ai/autoawq/quantize.py` to use `AutoAWQForCausalLM` instead of
`llmcompressor`. The container already has everything needed.

**Risk:** autoawq 0.2.9 has `qwen3` and `qwen3_moe` in its registry but not `qwen3_5`.
May fall back to generic implementation — test and verify output is valid.

### Step 2 — Build & push new autoawq image ⬜

```bash
# Tag new release to trigger CI build
cd /mnt/c/Users/micro/repos/homelab-ai
GIT_SSH_COMMAND="ssh -i ~/.ssh/id_ed25519_claude -p 2223" git tag v1.10.58
GIT_SSH_COMMAND="ssh -i ~/.ssh/id_ed25519_claude -p 2223" git push origin v1.10.58
```

### Step 3 — Run quantization ⬜

```bash
# From Git Bash on Windows
mkdir -p C:/models/quantized/qwen3.5-27b-abliterated-awq

docker run --rm --gpus all \
  -v C:/models/abliterated/qwen3.5-27b-abliterated:/input \
  -v C:/models/quantized/qwen3.5-27b-abliterated-awq:/output \
  harbor.server.unarmedpuppy.com/library/autoawq:latest \
  --model-path /input --output-path /output --group-size 128
```

Expected duration: 1-3 hours (GPU-accelerated AWQ calibration).

### Step 4 — Verify output ⬜

```bash
# Confirm model_type is still qwen3_5_text (vLLM AWQ path handles it)
docker run --rm \
  -v C:/models/quantized/qwen3.5-27b-abliterated-awq:/output \
  --entrypoint="" harbor.server.unarmedpuppy.com/library/autoawq:latest \
  python3 -c "import json; cfg=json.load(open('/output/config.json')); print(cfg['model_type'], cfg['quantization_config'])"
```

### Step 5 — Add to local-models volume ⬜

```bash
docker run --rm \
  -v C:/models/quantized/qwen3.5-27b-abliterated-awq:/src \
  -v local-models:/models \
  alpine sh -c "cp -r /src /models/qwen3.5-27b-abliterated-awq"
```

### Step 6 — Add to models.json and deploy ⬜

Add to `llm-manager/models.json`:
```json
{
  "id": "qwen3.5-27b-abliterated",
  "name": "Qwen3.5 27B Abliterated AWQ",
  "hf_model": "/models/qwen3.5-27b-abliterated-awq",
  "quantization": "awq_marlin",
  "type": "text",
  "vram_gb": 14,
  "gpu_count": 2,
  "max_context": 65536,
  "default_context": 65536,
  "extra_args": ["--disable-custom-all-reduce", "--reasoning-parser", "qwen3"],
  "description": "Qwen3.5-27B abliterated (refusal direction removed). AWQ 4-bit, dual-GPU TP=2, 65K context.",
  "architecture": "Qwen3.5",
  "license": "Apache-2.0",
  "tags": ["reasoning", "thinking", "abliterated", "uncensored", "primary", "dual-gpu"]
}
```

Update `docker-compose.gaming.yml`:
```yaml
- DEFAULT_MODEL=qwen3.5-27b-abliterated
```

Deploy:
```bash
cd /mnt/c/Users/micro/repos/homelab-ai
git add llm-manager/models.json docker-compose.gaming.yml
git commit -m "feat: add Qwen3.5-27B abliterated AWQ as primary model"
GIT_SSH_COMMAND="ssh -i ~/.ssh/id_ed25519_claude -p 2223" git tag v1.10.59
GIT_SSH_COMMAND="ssh -i ~/.ssh/id_ed25519_claude -p 2223" git push origin v1.10.59
```

Then trigger deploy-webhook on gaming PC:
```bash
curl -X POST http://localhost:8007/deploy \
  -H "Authorization: Bearer V2d06TKJCtsAnv6lYZjrv6OaW6_5brqVMlGWx2skvHU" \
  -H "Content-Type: application/json" \
  -d '{"service": "llm-manager"}'
```

---

## Option 2 — Qwopus-27B Abliterated + AWQ

**Model:** `Jackrong/Qwen3.5-27B-Claude-4.6-Opus-Reasoning-Distilled`
Claude Opus 4.6 reasoning distilled into Qwen3.5-27B. Same architecture as Option 1.
Potentially the most capable 27B model we can run — Opus reasoning patterns baked into weights, then refusal removed.

**Depends on:** Option 1 toolchain working (same architecture, same AWQ path).

### Step 1 — Run obliteratus ⬜

```bash
# From Git Bash on Windows, in homelab-ai repo
./abliteration/run.sh \
  Jackrong/Qwen3.5-27B-Claude-4.6-Opus-Reasoning-Distilled \
  advanced \
  qwopus-27b-abliterated
```

Output: `C:/models/abliterated/qwopus-27b-abliterated`
Expected duration: several hours.

### Step 2 — Run quantization ⬜

```bash
mkdir -p C:/models/quantized/qwopus-27b-abliterated-awq

docker run --rm --gpus all \
  -v C:/models/abliterated/qwopus-27b-abliterated:/input \
  -v C:/models/quantized/qwopus-27b-abliterated-awq:/output \
  harbor.server.unarmedpuppy.com/library/autoawq:latest \
  --model-path /input --output-path /output --group-size 128
```

### Steps 3-5 — Volume, models.json, deploy ⬜

Same pattern as Option 1. Model ID: `qwopus-27b-abliterated`, vram_gb: 14, gpu_count: 2.

---

## Option 3 — Qwen3-32B Abliterated + AWQ

**Model:** `Qwen/Qwen3-32B`
Fully proven pipeline. `model_type: qwen3` — supported by autoawq, vLLM, transformers 4.57.6+.
More parameters than Options 1/2 but older architecture.

**Hardware during abliteration:** Qwen3-32B FP16 = ~64GB.
With 48GB VRAM + 54GB WSL RAM = 102GB total — fits comfortably via `device_map=auto`.

### Step 1 — Run obliteratus ⬜

```bash
# From Git Bash on Windows, in homelab-ai repo
./abliteration/run.sh Qwen/Qwen3-32B advanced qwen3-32b-abliterated
```

Output: `C:/models/abliterated/qwen3-32b-abliterated`
Expected duration: several hours (larger model than 27B).

### Step 2 — Run quantization ⬜

```bash
mkdir -p C:/models/quantized/qwen3-32b-abliterated-awq

docker run --rm --gpus all \
  -v C:/models/abliterated/qwen3-32b-abliterated:/input \
  -v C:/models/quantized/qwen3-32b-abliterated-awq:/output \
  harbor.server.unarmedpuppy.com/library/autoawq:latest \
  --model-path /input --output-path /output --group-size 128
```

### Steps 3-5 — Volume, models.json, deploy ⬜

Model ID: `qwen3-32b-abliterated`, vram_gb: 20, gpu_count: 2, max_context: 65536.

Extra args: `["--enable-auto-tool-choice", "--tool-call-parser", "hermes", "--reasoning-parser", "qwen3", "--disable-custom-all-reduce"]`

---

## Option 4 — Qwen3-72B AWQ (No Abliteration)

**Model:** `Qwen/Qwen3-72B` (pre-quantized AWQ from HuggingFace)
Largest model that fits in 48GB VRAM at AWQ 4-bit (~36GB weights, ~12GB KV cache).
No abliteration possible on this hardware (FP16 = 144GB >> 102GB total).
Refusal behavior intact — but raw capability is far ahead of any 27-32B model.

### Step 1 — Pull model to local-models volume ⬜

```bash
# Pull into huggingface cache then copy to volume, or use vLLM to pre-download
docker run --rm --gpus all \
  -v huggingface-cache:/root/.cache/huggingface \
  -v local-models:/models \
  vllm/vllm-openai:nightly \
  python3 -c "
from huggingface_hub import snapshot_download
import shutil
path = snapshot_download('Qwen/Qwen3-72B-AWQ')
shutil.copytree(path, '/models/qwen3-72b-awq')
print('Done:', path)
"
```

### Step 2 — Add to models.json ⬜

```json
{
  "id": "qwen3-72b-awq",
  "name": "Qwen3 72B AWQ",
  "hf_model": "/models/qwen3-72b-awq",
  "quantization": "awq_marlin",
  "type": "text",
  "vram_gb": 36,
  "gpu_count": 2,
  "max_context": 32768,
  "default_context": 16384,
  "extra_args": ["--enable-auto-tool-choice", "--tool-call-parser", "hermes", "--reasoning-parser", "qwen3", "--disable-custom-all-reduce"],
  "description": "Qwen3-72B AWQ 4-bit. Largest model on hardware. Dual-GPU TP=2. No abliteration.",
  "architecture": "Qwen3",
  "license": "Apache-2.0",
  "tags": ["reasoning", "thinking", "tool-calling", "large", "dual-gpu"]
}
```

---

## Hardware Reference

- **GPUs:** 2x RTX 3090 (48GB VRAM total, PCIe x8/x8, no NVLink)
- **RAM:** 64GB physical, 54GB WSL
- **Total addressable:** 102GB (abliteration), 48GB (inference)
- **vLLM image:** `vllm/vllm-openai:nightly` (transformers 4.57.6, supports qwen3 + qwen3_5 AWQ)
- **autoawq image:** `harbor.server.unarmedpuppy.com/library/autoawq:latest` (autoawq 0.2.9, transformers 5.3.0)
- **Deploy secret:** in `.env` and `deploy-webhook` container env

## Next Tag Sequence

- v1.10.57 — llm-manager with abliterated model configs (deployed)
- v1.10.58 — autoawq script fix (Option 1 toolchain)
- v1.10.59 — models.json + DEFAULT_MODEL after Option 1 quantization
- v1.10.60+ — subsequent model additions
