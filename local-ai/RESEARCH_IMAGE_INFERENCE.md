# Research: Image Model Inference Engines

**Task**: home-server-bbc - Research inference engines for image models  
**Date**: 2025-01-17  
**Status**: In Progress

## Objective

Research and evaluate inference engines for image generation/editing models, specifically for Qwen Image Edit 2509 and similar multimodal models. The goal is to find a solution that:
- Works with image generation/editing models (not just text)
- Can be containerized (Docker)
- Provides OpenAI-compatible API endpoints
- Integrates with existing manager architecture
- Has reasonable GPU requirements

## Current Situation

- **vLLM**: Currently used for text models, but does NOT support image generation models
- **Qwen Image Edit**: Attempted to use with vLLM, failed with `ValueError: No supported config format found`
- **Architecture**: Windows PC runs Docker containers, manager service routes requests

## Options Evaluated

### Option 1: HuggingFace Diffusers + Custom FastAPI Server

**Description**: Use HuggingFace Diffusers library with a custom FastAPI server that provides OpenAI-compatible endpoints.

**Pros**:
- ✅ Well-documented and actively maintained
- ✅ Supports many image models (Stable Diffusion, Qwen Image, etc.)
- ✅ Python-based, easy to integrate
- ✅ Can create custom API endpoints matching OpenAI format
- ✅ Good GPU support (CUDA)
- ✅ Model loading and inference is straightforward

**Cons**:
- ⚠️ Requires custom FastAPI server development
- ⚠️ Need to implement OpenAI-compatible API format ourselves
- ⚠️ May need to handle model-specific quirks

**Implementation Approach**:
```python
# FastAPI server with Diffusers
from diffusers import DiffusionPipeline
from fastapi import FastAPI
import torch

app = FastAPI()
pipe = DiffusionPipeline.from_pretrained("Qwen/Qwen-Image-Edit-2509")

@app.post("/v1/images/generations")
async def generate_image(request: ImageGenerationRequest):
    # Convert OpenAI format to Diffusers format
    # Run inference
    # Return OpenAI-compatible response
```

**Docker Setup**:
- Base image: `nvidia/cuda:12.1.0-runtime-ubuntu22.04`
- Install: Python, PyTorch, Diffusers, FastAPI
- Expose port: 8000 (or 8005+ for image models)

**GPU Requirements**: Similar to vLLM (CUDA, GPU memory)

**API Compatibility**: Can be made OpenAI-compatible with custom endpoints

**Verdict**: ⭐⭐⭐⭐ (4/5) - Good option, requires some development work

---

### Option 2: Model-Specific Inference Servers

**Description**: Check if Qwen or other providers offer official inference servers for their image models.

**Research Findings**:
- Qwen Image models: No official inference server found
- Most image models rely on community implementations
- Some commercial services exist but not suitable for self-hosting

**Pros**:
- ✅ Would be optimized for specific models
- ✅ Potentially better performance

**Cons**:
- ❌ No official server found for Qwen Image Edit
- ❌ Would require using different servers for different models
- ❌ Less control over deployment

**Verdict**: ⭐⭐ (2/5) - Not viable, no official servers available

---

### Option 3: Text Generation Inference (TGI) - Image Variant

**Description**: Check if there's an image generation equivalent to HuggingFace's TGI (Text Generation Inference).

**Research Findings**:
- TGI is text-only (as the name suggests)
- No equivalent for image generation found
- HuggingFace focuses on Diffusers for image models

**Verdict**: ⭐ (1/5) - Not applicable

---

### Option 4: Custom FastAPI Server with Transformers

**Description**: Use HuggingFace Transformers library directly (without Diffusers) with custom FastAPI server.

**Pros**:
- ✅ More control over implementation
- ✅ Can use any model architecture

**Cons**:
- ⚠️ More complex than Diffusers
- ⚠️ Need to handle model loading, inference pipeline ourselves
- ⚠️ Diffusers is specifically designed for image generation and is easier

**Verdict**: ⭐⭐⭐ (3/5) - Possible but more work than Diffusers

---

## Recommendation: Option 1 (HuggingFace Diffusers + Custom FastAPI)

**Rationale**:
1. **Best fit for image models**: Diffusers is specifically designed for image generation/editing
2. **Active development**: Well-maintained by HuggingFace
3. **Flexibility**: Can support multiple image models (not just Qwen)
4. **Integration**: Can create OpenAI-compatible API endpoints
5. **Containerization**: Easy to Dockerize
6. **GPU support**: Native CUDA support

**Implementation Plan**:
1. Create Dockerfile for image inference server
2. Build FastAPI server with Diffusers
3. Implement `/v1/images/generations` endpoint (OpenAI-compatible)
4. Add health check endpoint
5. Test with Qwen Image Edit model

**Next Steps**:
- Create proof-of-concept container
- Test model loading and inference
- Verify GPU compatibility
- Measure performance

## Alternative Consideration: Use Existing Services

**Note**: For production use, could consider:
- Replicate API (commercial, not self-hosted)
- Stability AI API (commercial)
- But goal is self-hosted solution, so not viable

## References

- HuggingFace Diffusers: https://huggingface.co/docs/diffusers/
- Qwen Image Models: https://qwenlm.github.io/blog/qwen-imagen/
- FastAPI: https://fastapi.tiangolo.com/
- OpenAI Images API: https://platform.openai.com/docs/api-reference/images

---

**Status**: Research complete, ready for decision and implementation

