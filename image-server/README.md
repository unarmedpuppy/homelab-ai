# Image Inference Server

FastAPI server for image generation/editing models using HuggingFace Diffusers.

## Overview

This server provides OpenAI-compatible API endpoints for image generation models. It's designed to work alongside the vLLM text generation containers, managed by the same manager service.

## Architecture

- **Base**: NVIDIA CUDA runtime (for GPU support)
- **Framework**: FastAPI + HuggingFace Diffusers
- **API**: OpenAI-compatible endpoints
- **Port**: 8005+ (separate from vLLM ports 8001-8004)

## Setup

### Build Docker Image

```bash
cd local-ai/image-inference-server
docker build -t image-inference-server:latest .
```

### Run Container

```bash
docker run -d \
  --name qwen-image-server \
  --gpus all \
  -p 8005:8000 \
  -v $(pwd)/models:/models \
  -v $(pwd)/cache:/root/.cache/hf \
  -e MODEL_NAME=Qwen/Qwen-Image-Edit-2509 \
  -e HF_TOKEN=your_token_here \
  image-inference-server:latest
```

## API Endpoints

### Health Check
```
GET /health
```

### List Models (OpenAI-compatible)
```
GET /v1/models
```

### Generate Images (OpenAI-compatible)
```
POST /v1/images/generations
{
  "prompt": "a duck jumping over a puddle",
  "model": "qwen_image_edit",
  "n": 1,
  "size": "1024x1024",
  "response_format": "url"
}
```

## Status

**⚠️ Proof of Concept**: This is an initial implementation. Full OpenAI compatibility and all features are not yet implemented.

## Next Steps

1. Test with Qwen Image Edit model
2. Verify GPU compatibility
3. Implement full OpenAI API compatibility
4. Add image editing endpoints
5. Optimize performance

