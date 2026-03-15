# ADR: 48GB Dual-GPU Video and Image Model Garden Additions

- **Date:** 2026-03-15
- **Status:** Accepted
- **Repos/Services affected:** homelab-ai (`llm-manager/models.json`)
- **Tasks:** homelab-ai-028
- **Related:**
  - [2026-03-08-model-garden-architecture.md](2026-03-08-model-garden-architecture.md)
  - [2026-03-15-lightweight-model-garden-and-vllm-upgrade.md](2026-03-15-lightweight-model-garden-and-vllm-upgrade.md)

## Context

Previous model garden additions for image/video were constrained to single-GPU VRAM limits (~16GB).
The gaming PC has two RTX 3090s (48GB VRAM total) plus 56GB system RAM — substantially more capacity
than previously catalogued. This ADR adds the top-tier open-source video and image generation models
that require or benefit from this full 48GB envelope.

### Hardware Available

- 2x RTX 3090 = 48GB VRAM total
- 56GB system RAM (usable for CPU offload)
- Multi-GPU frameworks: xDiT (diffusion), FSDP (Wan), tensor parallel (text models)

## Models Added (4)

### Video Models

#### HunyuanVideo (540p FP8)
- **HF:** `tencent/HunyuanVideo`
- **VRAM:** ~40GB (FP8), gpu_count: 2
- **Architecture:** 13B transformer
- **Notes:** Tencent's SOTA open video model. FP8 quantization via Diffusers brings 540p within the
  48GB envelope. 720p FP8 is ~50GB — too tight for reliable dual-3090 use. Multi-GPU via xDiT
  Unified Sequence Parallelism. Supports T2V and I2V.
- **License:** HunyuanVideo Community License (non-commercial use OK for personal/research)

#### HunyuanVideo 1.5
- **HF:** `tencent/HunyuanVideo-1.5`
- **VRAM:** ~15GB (FP16), gpu_count: 1
- **Notes:** Improved motion quality and consistency over v1.0. Fits single RTX 3090. 720p–1080p
  capable. Serves as the practical always-available video generation option (doesn't require both
  GPUs, won't conflict with concurrent text model use on the second GPU).

#### Wan 2.2 T2V-14B
- **HF:** `Wan-AI/Wan2.1-T2V-14B`
- **VRAM:** ~24GB (BF16), gpu_count: 2
- **Notes:** Strong competitor to HunyuanVideo at 720p. 14B parameters distributed across both
  3090s via FSDP+xDiT. Excellent T2V and I2V quality, well-maintained by Wan-AI. At 24GB BF16,
  has comfortable headroom on 48GB.

### Image Models

#### HunyuanImage 3.0 NF4
- **HF:** `EricRollei/HunyuanImage-3.0-Instruct-NF4-v2`
- **Original:** `tencent/HunyuanImage-3.0`
- **VRAM:** ~48GB (NF4), gpu_count: 2
- **Architecture:** 80B MoE
- **Notes:** Tencent's 80B MoE image model — qualitative leap over FLUX.2 for photorealism and
  Chinese/English bilingual prompts. NF4 community quant by EricRollei brings it to ~48GB.
  **Marginal fit** — tagged accordingly. May require `CPU_OFFLOAD_GB` or swap space depending on
  actual peak VRAM usage. NF4 loads via BitsAndBytes in Diffusers.
- **Caution:** Tagged `marginal` — may need `--offload-param` or `--cpu-offload-gb` tuning on
  first run. Monitor VRAM headroom carefully.

## Infrastructure Requirements

All four models require the **video-server** container (task homelab-ai-026), which does not yet
exist. The video-server will need:

- Diffusers-based serving (not vLLM — these are not text models)
- xDiT support for multi-GPU HunyuanVideo
- FSDP or model parallelism for Wan 2.2 dual-GPU
- BitsAndBytes 4-bit loading support (for HunyuanImage NF4)

The models are registered in `models.json` now for catalog visibility and prefetch capability.
The `needs-video-server` tag marks them as not yet servable.

## VRAM Summary

| Model | VRAM | GPUs | Resolution | Status |
|-------|------|------|------------|--------|
| hunyuanvideo | 40GB FP8 | 2 | 540p | Needs video-server |
| hunyuanvideo-1.5 | 15GB FP16 | 1 | 720p–1080p | Needs video-server |
| wan-2.2-t2v-14b | 24GB BF16 | 2 | 720p | Needs video-server |
| hunyuanimage-3.0-nf4 | ~48GB NF4 | 2 | up to 4K | Needs video-server, marginal |

Existing single-GPU video models (LTX-Video, CogVideoX-5B) remain in catalog — better options
when GPU availability is limited or when running alongside an active LLM session.

## Consequences

- Model garden now covers the full VRAM spectrum: 1GB (smollm2-135m) → 48GB (hunyuanimage-3.0-nf4)
- HunyuanVideo-1.5 (15GB, single GPU) is the practical default for video generation once
  video-server is deployed
- HunyuanImage-3.0 NF4 is aspirational — may be unstable at the memory limit; FLUX.2-dev remains
  the reliable production image model
- video-server container becomes the blocking dependency for all video generation capabilities

## Follow-up

- Build video-server container with Diffusers + xDiT + FSDP support (homelab-ai-026)
- First load test: HunyuanVideo-1.5 (safest — single GPU, comfortable VRAM margin)
- Verify HunyuanImage 3.0 NF4 peak VRAM on first inference — may need CPU offload tuning
- Monitor for HunyuanVideo 720p FP8 community solution that fits under 48GB
