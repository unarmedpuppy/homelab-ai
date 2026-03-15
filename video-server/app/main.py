"""
FastAPI server for video generation using HuggingFace Diffusers.

Supports:
  - tencent/HunyuanVideo-1.5  (15GB FP16, single 3090, 720p-1080p)
  - tencent/HunyuanVideo       (40GB FP8, dual 3090 with xDiT, 540p)
  - Wan-AI/Wan2.1-T2V-14B      (24GB BF16, dual 3090 with FSDP+xDiT)

API:
  GET  /health
  GET  /v1/models
  POST /v1/videos/generations
  GET  /

Env vars:
  MODEL_ID  - HuggingFace model ID (default: tencent/HunyuanVideo-1.5)
  GPU_COUNT - Number of GPUs (default: 1)
  LOG_LEVEL - Logging level (default: INFO)
"""

import os
import time
import base64
import tempfile
import logging
from typing import Optional, List

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
import torch

LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()
logging.basicConfig(
    level=getattr(logging, LOG_LEVEL, logging.INFO),
    format="%(asctime)s %(levelname)s %(name)s — %(message)s",
)
logger = logging.getLogger(__name__)

try:
    import diffusers
    DIFFUSERS_AVAILABLE = True
    logger.info(f"diffusers {diffusers.__version__} available")
except ImportError:
    DIFFUSERS_AVAILABLE = False
    logger.warning("diffusers not available — video generation disabled")

try:
    import imageio
    import imageio_ffmpeg  # noqa: F401 — validates ffmpeg plugin is present
    IMAGEIO_AVAILABLE = True
except ImportError:
    IMAGEIO_AVAILABLE = False
    logger.warning("imageio/imageio-ffmpeg not available — MP4 export disabled")

app = FastAPI(title="Video Inference Server", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------------------------------
# Global state
# ---------------------------------------------------------------------------

model_pipeline = None
MODEL_ID = os.getenv("MODEL_ID", "tencent/HunyuanVideo-1.5")
GPU_COUNT = int(os.getenv("GPU_COUNT", "1"))
device = "cuda" if torch.cuda.is_available() else "cpu"


def _detect_model_type(model_id: str) -> str:
    m = model_id.lower()
    if "hunyuanvideo" in m:
        return "hunyuanvideo"
    if "wan" in m and ("t2v" in m or "i2v" in m or "wan2" in m):
        return "wan"
    return "generic"


MODEL_TYPE = _detect_model_type(MODEL_ID)
logger.info(f"Model: {MODEL_ID}  type={MODEL_TYPE}  gpus={GPU_COUNT}  device={device}")


# ---------------------------------------------------------------------------
# Model loading
# ---------------------------------------------------------------------------

def load_model():
    global model_pipeline

    if model_pipeline is not None:
        return model_pipeline

    if not DIFFUSERS_AVAILABLE:
        raise RuntimeError("diffusers library not installed")

    logger.info(f"Loading {MODEL_ID} ({MODEL_TYPE}) ...")
    t0 = time.time()

    if MODEL_TYPE == "hunyuanvideo":
        from diffusers import HunyuanVideoPipeline, HunyuanVideoTransformer3DModel

        transformer = HunyuanVideoTransformer3DModel.from_pretrained(
            MODEL_ID, subfolder="transformer", torch_dtype=torch.bfloat16
        )
        model_pipeline = HunyuanVideoPipeline.from_pretrained(
            MODEL_ID,
            transformer=transformer,
            torch_dtype=torch.float16,
        )
        # CPU offload handles VRAM — essential for fitting within 15-40GB
        model_pipeline.enable_model_cpu_offload()
        model_pipeline.vae.enable_tiling()

    elif MODEL_TYPE == "wan":
        from diffusers import WanPipeline

        model_pipeline = WanPipeline.from_pretrained(
            MODEL_ID,
            torch_dtype=torch.bfloat16,
        )
        model_pipeline.enable_model_cpu_offload()

    else:
        from diffusers import DiffusionPipeline

        model_pipeline = DiffusionPipeline.from_pretrained(
            MODEL_ID,
            torch_dtype=torch.float16 if device == "cuda" else torch.float32,
        )
        if device == "cuda":
            model_pipeline = model_pipeline.to(device)

    logger.info(f"Model ready in {time.time() - t0:.0f}s")
    return model_pipeline


# ---------------------------------------------------------------------------
# Pydantic models
# ---------------------------------------------------------------------------

class VideoGenerationRequest(BaseModel):
    prompt: str
    model: Optional[str] = None
    negative_prompt: Optional[str] = None
    num_frames: Optional[int] = Field(
        default=None,
        description="Frame count. Defaults: hunyuanvideo=61, wan=81, generic=16",
    )
    height: Optional[int] = Field(
        default=None,
        description="Output height in pixels. Defaults: hunyuanvideo=544, wan=480",
    )
    width: Optional[int] = Field(
        default=None,
        description="Output width in pixels. Defaults: hunyuanvideo=960, wan=832",
    )
    num_inference_steps: Optional[int] = Field(default=30)
    fps: Optional[int] = Field(default=15, description="Frames per second for output MP4")


class VideoGenerationResponse(BaseModel):
    created: int
    data: List[dict]


# ---------------------------------------------------------------------------
# Startup
# ---------------------------------------------------------------------------

@app.on_event("startup")
async def startup_event():
    import asyncio

    async def _load():
        try:
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(None, load_model)
        except Exception as e:
            logger.warning(f"Startup load failed — will retry on first request: {e}")

    asyncio.create_task(_load())


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@app.get("/health")
async def health():
    gpu_info = {}
    if torch.cuda.is_available():
        for i in range(torch.cuda.device_count()):
            props = torch.cuda.get_device_properties(i)
            free, total = torch.cuda.mem_get_info(i)
            gpu_info[f"gpu{i}"] = {
                "name": props.name,
                "vram_total_gb": round(total / 1e9, 1),
                "vram_free_gb": round(free / 1e9, 1),
            }
    return {
        "status": "healthy",
        "model_loaded": model_pipeline is not None,
        "model_id": MODEL_ID,
        "model_type": MODEL_TYPE,
        "device": device,
        "gpu_count": GPU_COUNT,
        "gpus": gpu_info,
    }


@app.get("/v1/models")
async def list_models():
    model_slug = MODEL_ID.split("/")[-1].lower()
    return {
        "object": "list",
        "data": [
            {
                "id": model_slug,
                "object": "model",
                "created": int(time.time()),
                "owned_by": "local-ai",
                "type": "video",
            }
        ],
    }


@app.post("/v1/videos/generations", response_model=VideoGenerationResponse)
async def generate_video(request: VideoGenerationRequest):
    try:
        pipeline = load_model()
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Model not available: {e}")

    # Per-model defaults
    if MODEL_TYPE == "hunyuanvideo":
        height = request.height or 544
        width = request.width or 960
        num_frames = request.num_frames or 61
    elif MODEL_TYPE == "wan":
        height = request.height or 480
        width = request.width or 832
        num_frames = request.num_frames or 81
    else:
        height = request.height or 480
        width = request.width or 832
        num_frames = request.num_frames or 16

    fps = request.fps or 15
    steps = request.num_inference_steps or 30

    logger.info(
        f"Generating: '{request.prompt[:60]}' {width}x{height} "
        f"{num_frames}f {steps}steps @{fps}fps"
    )
    t0 = time.time()

    try:
        kwargs = dict(
            prompt=request.prompt,
            height=height,
            width=width,
            num_frames=num_frames,
            num_inference_steps=steps,
        )
        if request.negative_prompt:
            kwargs["negative_prompt"] = request.negative_prompt

        with torch.no_grad():
            result = pipeline(**kwargs)

        # Diffusers video pipelines return result.frames[0] as list of PIL Images
        if hasattr(result, "frames"):
            frames = result.frames[0]
        else:
            frames = result[0]

        if not IMAGEIO_AVAILABLE:
            raise RuntimeError("imageio-ffmpeg not installed — cannot encode video")

        with tempfile.NamedTemporaryFile(suffix=".mp4", delete=False) as f:
            tmp_path = f.name

        imageio.mimwrite(tmp_path, frames, fps=fps, quality=8)

        with open(tmp_path, "rb") as f:
            video_bytes = f.read()
        os.unlink(tmp_path)

        elapsed = time.time() - t0
        logger.info(f"Done in {elapsed:.1f}s — {len(video_bytes) // 1024}KB")

        return VideoGenerationResponse(
            created=int(time.time()),
            data=[
                {
                    "b64_mp4": base64.b64encode(video_bytes).decode(),
                    "revised_prompt": request.prompt,
                    "width": width,
                    "height": height,
                    "num_frames": num_frames,
                    "fps": fps,
                    "generation_time_s": round(elapsed, 1),
                }
            ],
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Generation failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Video generation failed: {e}")


@app.get("/")
async def root():
    return {
        "service": "Video Inference Server",
        "model": MODEL_ID,
        "model_type": MODEL_TYPE,
        "status": "running",
        "model_loaded": model_pipeline is not None,
    }
