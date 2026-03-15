# ADR: Video Generation Server

- **Date:** 2026-03-15
- **Status:** Accepted
- **Repos/Services affected:** homelab-ai (`video-server/`, `docker-compose.gaming.yml`, `.gitea/workflows/build.yml`)
- **Tasks:** homelab-ai-026
- **Related:**
  - [2026-03-15-48gb-video-image-model-garden.md](2026-03-15-48gb-video-image-model-garden.md)

## Context

The model garden contains video generation models (LTX-Video, CogVideoX, HunyuanVideo, Wan 2.2) but no serving infrastructure — the existing image-server only handles image pipelines. Video generation requires:

- Diffusers-based serving (not vLLM — these are not text models)
- Frame sequence encoding to MP4 via ffmpeg
- Multi-turn inference support for tool-chain compatibility
- A new `POST /v1/videos/generations` endpoint following the image-server API style

## Decision

Add a `video-server` service to the gaming PC stack, mirroring the `image-server` pattern exactly:
- `pytorch-base:2.2.0-cuda12.1` base image (same as image-server)
- FastAPI + uvicorn, internal port 8000, external port **8008**
- `MODEL_ID` env var selects which model to load at startup
- `GPU_COUNT` env var for future multi-GPU support
- Model type auto-detected from MODEL_ID (hunyuanvideo / wan / generic)

## Model Support

The server supports three model families via Diffusers:

| Model Type | Detection | Loading | Default Resolution |
|---|---|---|---|
| `hunyuanvideo` | ID contains "hunyuanvideo" | `HunyuanVideoPipeline` + transformer | 960×544, 61 frames |
| `wan` | ID contains "wan" + t2v/i2v | `WanPipeline` | 832×480, 81 frames |
| `generic` | fallback | `DiffusionPipeline.from_pretrained` | 832×480, 16 frames |

All models use `enable_model_cpu_offload()` — critical for staying within VRAM limits when model sizes approach the 15-40GB range.

## API Design

`POST /v1/videos/generations` — response returns base64-encoded MP4:

```json
{
  "prompt": "A cat walks on grass",
  "height": 544, "width": 960,
  "num_frames": 61, "fps": 15,
  "num_inference_steps": 30
}
→ {"created": 1710000000, "data": [{"b64_mp4": "...", "width": 960, "height": 544, "generation_time_s": 42.1}]}
```

## Default Deployment

Default model: `tencent/HunyuanVideo-1.5` (15GB FP16, single 3090, 720p).
This is the safest choice — fits comfortably within one 3090's 24GB, leaving the second GPU free for LLM inference.

To switch to dual-GPU HunyuanVideo (40GB FP8), change `MODEL_ID` and `count: 2` in docker-compose.gaming.yml.

## Consequences

- All video models tagged `needs-video-server` in models.json are now servable
- HunyuanVideo 540p (dual 3090, 40GB FP8) requires `GPU_COUNT=2` and xDiT integration — not yet implemented, v2 work
- Wan 2.2 FSDP+xDiT dual-GPU is also a v2 item
- First recommended test: `HunyuanVideo-1.5` single GPU — widest support, best documented

## Follow-up

- Integrate xDiT for `HunyuanVideo` dual-GPU (540p FP8)
- Add `image-to-video` support (`init_image` parameter)
- Consider returning video as streaming response for large files
