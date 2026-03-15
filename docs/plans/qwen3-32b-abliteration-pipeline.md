# Qwen3-32B Abliteration Pipeline

**Status:** Pending — waiting on 64GB RAM upgrade
**Created:** 2026-03-12

## Goal

Abliterate Qwen3-32B (remove refusal direction from weights), quantize to AWQ, and serve as the primary model on the gaming PC using both RTX 3090s.

## Why Qwen3-32B

- `model_type: qwen3` — fully supported by vLLM nightly's transformers 4.57.6, no custom image needed
- At AWQ 4-bit (~20GB), leaves ~28GB free across both GPUs for KV cache
- 65K context is comfortable at this weight/cache ratio
- More capable than Qwen3.5-27B-AWQ (current default), and avoids the `qwen3_5_text` architecture blocker

## Why Not Qwen3.5-27B (current abliterated model)

The abliterated Qwen3.5-27B weights are in `/models/qwen3.5-27b-abliterated` and are good, but:
- `model_type: qwen3_5_text` — not recognized by transformers 4.57.6 (vLLM nightly)
- BNB load path requires transformers to recognize the architecture; AWQ path does not
- AutoAWQ also blocked on `qwen3_5_text` support
- Fix would require a custom vLLM image with transformers>=5.0 — risky, breaks other models

## Hardware

- 2x RTX 3090 (24GB each = 48GB VRAM)
- 64GB RAM (upgraded 2026-03-12), WSL capped at 56GB via `.wslconfig`
- Total addressable during abliteration: 48GB VRAM + 56GB RAM = 104GB

Qwen3-32B FP16 = ~64GB — fits easily with most weights in VRAM.

## Steps

### 1. After RAM upgrade: update .wslconfig

```
# C:\Users\micro\.wslconfig
[wsl2]
memory=56GB
swap=8GB
```

Then restart WSL from PowerShell:
```powershell
wsl --shutdown
```

### 2. Run obliteratus

From Git Bash on Windows, in the homelab-ai repo:

```bash
./abliteration/run.sh Qwen/Qwen3-32B advanced qwen3-32b-abliterated
```

This will:
- Pull the obliteratus container from Harbor
- Download Qwen3-32B FP16 from HuggingFace (into huggingface-cache volume)
- Abliterate using the `advanced` method
- Write modified weights to `C:/models/abliterated/qwen3-32b-abliterated`

Expected duration: several hours (activation collection + SVD on a 32B model).

### 3. Quantize to AWQ

Once abliteration is complete, run AutoAWQ on the output:

```bash
# TODO: document autoawq run command once qwen3_5 blocker is confirmed not an issue for qwen3
# Qwen3-32B uses model_type: qwen3 — should work with current AutoAWQ
docker run --rm --gpus all \
  -v C:/models/abliterated/qwen3-32b-abliterated:/input \
  -v C:/models/quantized/qwen3-32b-abliterated-awq:/output \
  -v huggingface-cache:/root/.cache/huggingface \
  harbor.server.unarmedpuppy.com/library/autoawq:latest \
  quantize /input --output /output --bits 4 --group-size 128
```

Verify the output config.json still has `model_type: qwen3` (not `qwen3_5_text`).

### 4. Add to local-models volume

```bash
# Copy quantized output into the local-models Docker volume
docker run --rm \
  -v C:/models/quantized/qwen3-32b-abliterated-awq:/src \
  -v local-models:/models \
  alpine cp -r /src /models/qwen3-32b-abliterated-awq
```

### 5. Add model to models.json

Add entry to `/mnt/c/Users/micro/repos/homelab-ai/llm-manager/models.json`:

```json
{
  "id": "qwen3-32b-abliterated",
  "name": "Qwen3 32B Abliterated AWQ",
  "hf_model": "/models/qwen3-32b-abliterated-awq",
  "quantization": "awq_marlin",
  "type": "text",
  "vram_gb": 20,
  "gpu_count": 2,
  "max_context": 65536,
  "default_context": 65536,
  "extra_args": ["--enable-auto-tool-choice", "--tool-call-parser", "hermes", "--reasoning-parser", "qwen3", "--disable-custom-all-reduce"],
  "description": "Qwen3-32B abliterated (refusal direction removed), AWQ 4-bit. Dual-GPU TP=2, 65K context.",
  "architecture": "Qwen3",
  "license": "Apache-2.0",
  "tags": ["reasoning", "thinking", "abliterated", "uncensored", "tool-calling", "primary"]
}
```

### 6. Update DEFAULT_MODEL and deploy

In `docker-compose.gaming.yml`:
```yaml
- DEFAULT_MODEL=qwen3-32b-abliterated
```

Tag a new release to trigger CI build and deploy:
```bash
cd /mnt/c/Users/micro/repos/homelab-ai
git add llm-manager/models.json docker-compose.gaming.yml
git commit -m "feat: add Qwen3-32B abliterated AWQ as primary model"
GIT_SSH_COMMAND="ssh -i ~/.ssh/id_ed25519_claude -p 2223" git tag v1.10.58
GIT_SSH_COMMAND="ssh -i ~/.ssh/id_ed25519_claude -p 2223" git push origin v1.10.58
```

Then trigger deploy-webhook:
```bash
curl -X POST http://localhost:8007/deploy \
  -H "Authorization: Bearer V2d06TKJCtsAnv6lYZjrv6OaW6_5brqVMlGWx2skvHU" \
  -H "Content-Type: application/json" \
  -d '{"service": "llm-manager"}'
```

## Open Questions

- Confirm AutoAWQ run command syntax (check autoawq container entrypoint)
- Verify quantized model config.json retains `model_type: qwen3` after AWQ pass
- Decide whether to keep `qwen3.5-27b-abliterated` in the volume or clean it up
