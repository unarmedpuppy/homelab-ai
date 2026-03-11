# Model Garden & Qwopus Enhancements

Tracking future enhancements identified during the Qwopus integration (2026-03-08).

## Immediate Follow-ups

### 1. Create AWQ Quant of Qwopus
- **Why**: BitsAndBytes 4-bit quantization works but AWQ/AWQ-Marlin is faster (matches existing model patterns)
- **How**: Use AutoAWQ to quantize `Jackrong/Qwen3.5-27B-Claude-4.6-Opus-Reasoning-Distilled` BF16 weights
- **Result**: Upload to Harbor as local artifact, update models.json to use `awq_marlin` quantization
- **Benefit**: Better throughput, consistent with qwen3-32b-awq serving pattern, enables VLLM_USE_V1=1

### 2. Test Qwopus Context Window Limits
- **Why**: Model was LoRA fine-tuned on ~8K sequences but architecture supports 262K. Effective context is unclear.
- **How**: Run increasing context length tests (8K, 16K, 32K) and evaluate quality degradation
- **Result**: Set `default_context` and `max_context` in models.json to validated values

### 3. Evaluate Qwopus as Reasoning-Tier Default
- **Why**: If testing confirms strong reasoning, could route COMPLEX tier requests to Qwopus
- **How**: Update `TIER_MODEL_MAP` in `complexity.py` to route `ComplexityTier.COMPLEX` → `qwopus-27b`
- **Depends on**: Context window testing (#2) and quality benchmarks

## Local Model Garden Infrastructure

### 4. Model Prefetch Script
- **Why**: Models download lazily on first request, causing long cold starts
- **How**: Add `scripts/prefetch-models.sh` that iterates `models.json` and runs `huggingface-cli download` for each model into the `huggingface-cache` Docker volume
- **Scope**: Parse models.json, download each `hf_model`, verify cache integrity

### 5. Harbor OCI Artifact Storage for Models
- **Why**: Models depend on HuggingFace being reachable. Harbor already hosts all container images.
- **How**: Push model weights as OCI artifacts to Harbor using `oras push`
- **Pattern**: `harbor.server.unarmedpuppy.com/models/<model-id>:<version>`
- **Integration**: llm-manager pulls from Harbor instead of HuggingFace
- **Requires**: ORAS CLI, Harbor project for model artifacts

### 6. Offline Mode (HF_HUB_OFFLINE)
- **Why**: Ensure inference works without internet access
- **How**: Set `HF_HUB_OFFLINE=1` in vLLM container environment after models are cached
- **Depends on**: Prefetch script (#4) or Harbor storage (#5) to pre-populate cache

### 7. Model Garden Dashboard
- **Why**: No visibility into which models are cached, available, or need downloading
- **How**: Extend existing dashboard to show:
  - Cached vs. uncached models from models.json
  - Download progress / trigger downloads
  - VRAM usage per model
  - Model swap controls
- **File**: `dashboard/src/` (new component)

## Model Catalog Expansion

### 8. Add More Distilled/Community Models
- Track community models worth adding to the garden
- Candidates: Qwen3.5-35B-A3B (MoE variant of Qwopus), other reasoning distillations
- Evaluate against qwen3-32b-awq on coding/reasoning tasks
