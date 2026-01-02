"""
FastAPI server for image model inference using HuggingFace Diffusers.
Provides OpenAI-compatible API endpoints for image generation.
"""

import os
import time
import base64
from io import BytesIO
from typing import Optional, List
from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from PIL import Image
import torch

# Try to import diffusers, but handle gracefully if not available
try:
    from diffusers import DiffusionPipeline
    # Try to import Qwen-specific pipeline if available (newer diffusers versions)
    try:
        from diffusers import QwenImageEditPlusPipeline
        QWEN_PIPELINE_AVAILABLE = True
    except ImportError:
        QWEN_PIPELINE_AVAILABLE = False
    DIFFUSERS_AVAILABLE = True
except ImportError:
    DIFFUSERS_AVAILABLE = False
    QWEN_PIPELINE_AVAILABLE = False
    print("WARNING: diffusers not available. Image generation will not work.")

app = FastAPI(title="Image Inference Server", version="0.1.0")

# Global model state
model_pipeline = None
model_name = os.getenv("MODEL_NAME", "Qwen/Qwen-Image-Edit-2509")
device = "cuda" if torch.cuda.is_available() else "cpu"

class ImageGenerationRequest(BaseModel):
    """OpenAI-compatible image generation request"""
    prompt: str
    model: Optional[str] = None
    n: Optional[int] = 1  # Number of images to generate
    size: Optional[str] = "1024x1024"  # Image size
    response_format: Optional[str] = "url"  # "url" or "b64_json"
    user: Optional[str] = None
    image: Optional[str] = None  # Base64 image data for editing

class ImageResponse(BaseModel):
    """OpenAI-compatible image response"""
    created: int
    data: List[dict]

def load_model():
    """Load the image generation model"""
    global model_pipeline
    
    if not DIFFUSERS_AVAILABLE:
        raise RuntimeError("diffusers library not available")
    
    if model_pipeline is not None:
        return model_pipeline
    
    print(f"Loading model: {model_name} on device: {device}")
    try:
        # For Qwen models, try QwenImageEditPlusPipeline first if available
        if "qwen" in model_name.lower() and "image" in model_name.lower() and QWEN_PIPELINE_AVAILABLE:
            print("Using QwenImageEditPlusPipeline for Qwen Image Edit model")
            model_pipeline = QwenImageEditPlusPipeline.from_pretrained(
                model_name,
                torch_dtype=torch.float16 if device == "cuda" else torch.float32,
                device_map="cuda" if device == "cuda" else None,
                trust_remote_code=True,
            )
        else:
            # Use auto-detection for other models or if Qwen pipeline not available
            print("Using DiffusionPipeline auto-detection")
            model_pipeline = DiffusionPipeline.from_pretrained(
                model_name,
                torch_dtype=torch.float16 if device == "cuda" else torch.float32,
                device_map="cuda" if device == "cuda" else None,
                trust_remote_code=True,
            )
        
        # Move to device if not already on it (device_map should handle this, but ensure it)
        if device == "cuda" and hasattr(model_pipeline, 'to'):
            try:
                model_pipeline = model_pipeline.to(device)
            except Exception as e:
                print(f"Note: Could not move pipeline to device (may already be there): {e}")
        print(f"Model loaded successfully")
        return model_pipeline
    except Exception as e:
        print(f"Error loading model: {e}")
        import traceback
        traceback.print_exc()
        raise

@app.on_event("startup")
async def startup_event():
    """Load model on startup (non-blocking)"""
    import asyncio
    async def load_model_async():
        try:
            # Run model loading in executor to avoid blocking
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(None, load_model)
            print("Model loaded successfully on startup")
        except Exception as e:
            print(f"Warning: Could not load model on startup: {e}")
            print("Model will be loaded on first request")
    
    # Start loading model in background, don't wait for it
    asyncio.create_task(load_model_async())

@app.get("/health")
async def health():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "model_loaded": model_pipeline is not None,
        "device": device,
        "cuda_available": torch.cuda.is_available()
    }

@app.get("/v1/models")
async def list_models():
    """List available models (OpenAI-compatible)"""
    return {
        "object": "list",
        "data": [
            {
                "id": model_name.split("/")[-1].lower().replace("-", "_"),
                "object": "model",
                "created": int(time.time()),
                "owned_by": "local-ai"
            }
        ]
    }

@app.post("/v1/images/generations")
async def generate_image(request: ImageGenerationRequest):
    """
    Generate images (OpenAI-compatible endpoint)
    
    Note: This is a simplified implementation. Full OpenAI compatibility
    would require more features like image editing, variations, etc.
    """
    # Ensure model is loaded
    try:
        pipeline = load_model()
    except Exception as e:
        raise HTTPException(
            status_code=503,
            detail=f"Model not available: {str(e)}"
        )
    
    # Generate or edit image
    try:
        if request.image:
            print(f"Editing image with prompt: {request.prompt[:50]}...")
            # Decode base64 image
            try:
                if request.image.startswith('data:'):
                    # Remove data URL prefix
                    image_data = request.image.split(',')[1]
                else:
                    image_data = request.image
                
                image_bytes = base64.b64decode(image_data)
                input_image = Image.open(BytesIO(image_bytes))
                
                # Run image editing
                with torch.no_grad():
                    result = pipeline(
                        prompt=request.prompt,
                        image=input_image,  # Pass input image for editing
                        num_images_per_prompt=request.n or 1,
                    )
            except Exception as e:
                raise HTTPException(
                    status_code=400,
                    detail=f"Invalid image data: {str(e)}"
                )
        else:
            print(f"Generating image with prompt: {request.prompt[:50]}...")
            # Run inference for generation
            with torch.no_grad():
                result = pipeline(
                    prompt=request.prompt,
                    num_images_per_prompt=request.n or 1,
                    # Note: size parameter would need to be parsed and passed appropriately
                )
        
        # Handle result (Diffusers returns different formats depending on pipeline)
        images = []
        if isinstance(result, list):
            images = result
        elif hasattr(result, 'images'):
            images = result.images
        else:
            # Fallback: try to get first image
            images = [result[0]] if result else []
        
        # Convert to response format
        response_data = []
        for img in images:
            if request.response_format == "b64_json":
                # Convert PIL Image to base64
                buffered = BytesIO()
                img.save(buffered, format="PNG")
                img_str = base64.b64encode(buffered.getvalue()).decode()
                response_data.append({
                    "b64_json": img_str,
                    "revised_prompt": request.prompt  # Simplified
                })
            else:
                # Return as URL (in real implementation, would save and return URL)
                # For now, return base64 in URL format
                buffered = BytesIO()
                img.save(buffered, format="PNG")
                img_str = base64.b64encode(buffered.getvalue()).decode()
                response_data.append({
                    "url": f"data:image/png;base64,{img_str}",
                    "revised_prompt": request.prompt
                })
        
        return ImageResponse(
            created=int(time.time()),
            data=response_data
        )
        
    except Exception as e:
        print(f"Error generating image: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Image generation failed: {str(e)}"
        )

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "service": "Image Inference Server",
        "model": model_name,
        "status": "running",
        "model_loaded": model_pipeline is not None
    }

