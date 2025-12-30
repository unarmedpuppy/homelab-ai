import os
import httpx
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Local AI Proxy",
    description="Proxy service to call local AI models running on Windows machine",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Configuration
WINDOWS_AI_HOST = os.getenv("WINDOWS_AI_HOST", "192.168.86.100")
WINDOWS_AI_PORT = os.getenv("WINDOWS_AI_PORT", "8000")
TIMEOUT = int(os.getenv("TIMEOUT", "300"))

WINDOWS_AI_BASE_URL = f"http://{WINDOWS_AI_HOST}:{WINDOWS_AI_PORT}"

@app.get("/")
async def root():
    """Serve the chat interface"""
    return FileResponse("static/index.html")

@app.get("/api/info")
async def api_info():
    """API information endpoint"""
    return {
        "message": "Local AI Proxy Service",
        "windows_host": WINDOWS_AI_HOST,
        "windows_port": WINDOWS_AI_PORT,
        "base_url": WINDOWS_AI_BASE_URL
    }

@app.get("/health")
async def health():
    """Check if the Windows AI service is accessible"""
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(f"{WINDOWS_AI_BASE_URL}/healthz")
            if response.status_code == 200:
                return {
                    "status": "healthy",
                    "windows_ai": response.json(),
                    "proxy": "running"
                }
            else:
                return {
                    "status": "unhealthy",
                    "windows_ai": f"HTTP {response.status_code}",
                    "proxy": "running"
                }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return {
            "status": "unhealthy",
            "windows_ai": f"Connection failed: {str(e)}",
            "proxy": "running"
        }

@app.get("/v1/models")
async def get_models():
    """Get available models from Windows AI service"""
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(f"{WINDOWS_AI_BASE_URL}/v1/models")
            if response.status_code == 200:
                return response.json()
            else:
                raise HTTPException(
                    status_code=response.status_code,
                    detail=f"Windows AI service returned {response.status_code}"
                )
    except httpx.TimeoutException:
        raise HTTPException(status_code=504, detail="Windows AI service timeout")
    except httpx.ConnectError:
        raise HTTPException(status_code=503, detail="Cannot connect to Windows AI service")
    except Exception as e:
        logger.error(f"Error getting models: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/models/info")
async def models_info():
    """Get detailed information about available models"""
    models_info = {
        "llama3-8b": {
            "name": "Llama 3.1 8B Instruct",
            "description": "Best general quality model, good for most tasks",
            "size": "8B parameters",
            "context_length": 8192,
            "use_cases": ["general chat", "reasoning", "writing", "analysis"]
        },
        "qwen2.5-14b-awq": {
            "name": "Qwen 2.5 14B Instruct AWQ",
            "description": "Stronger reasoning capabilities, quantized for efficiency",
            "size": "14B parameters (4-bit quantized)",
            "context_length": 6144,
            "use_cases": ["complex reasoning", "analysis", "research", "technical tasks"]
        },
        "deepseek-coder": {
            "name": "DeepSeek Coder V2 Lite",
            "description": "Specialized for coding tasks and programming assistance",
            "size": "7B parameters",
            "context_length": 8192,
            "use_cases": ["code generation", "debugging", "code review", "programming help"]
        },
        "qwen-image-edit": {
            "name": "Qwen Image Edit 2509",
            "description": "Multimodal model for image editing and generation",
            "size": "Large multimodal model",
            "context_length": 4096,
            "use_cases": ["image editing", "image generation", "visual tasks", "multimodal chat"]
        }
    }
    return {"models": models_info}

@app.get("/usage/stats")
async def usage_stats():
    """Get usage statistics and model status"""
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(f"{WINDOWS_AI_BASE_URL}/healthz")
            if response.status_code == 200:
                health_data = response.json()
                running_models = health_data.get("running", [])
                return {
                    "proxy_status": "running",
                    "windows_ai_status": "connected",
                    "running_models": running_models,
                    "total_models": len(running_models),
                    "last_check": "now",
                    "model_status": {
                        model_id: {
                            "loaded": model_id in running_models,
                            "status": "ready" if model_id in running_models else "not_loaded",
                            "container_name": f"vllm-{model_id.replace('-', '')}" if model_id in running_models else None
                        }
                        for model_id in ["llama3-8b", "qwen2.5-14b-awq", "deepseek-coder", "qwen-image-edit"]
                    }
                }
            else:
                return {
                    "proxy_status": "running",
                    "windows_ai_status": "disconnected",
                    "running_models": [],
                    "total_models": 0,
                    "last_check": "now",
                    "model_status": {
                        model_id: {
                            "loaded": False,
                            "status": "disconnected",
                            "container_name": None
                        }
                        for model_id in ["llama3-8b", "qwen2.5-14b-awq", "deepseek-coder", "qwen-image-edit"]
                    }
                }
    except Exception as e:
        return {
            "proxy_status": "running",
            "windows_ai_status": "error",
            "error": str(e),
            "running_models": [],
            "total_models": 0,
            "last_check": "now",
            "model_status": {
                model_id: {
                    "loaded": False,
                    "status": "error",
                    "container_name": None
                }
                for model_id in ["llama3-8b", "qwen2.5-14b-awq", "deepseek-coder", "qwen-image-edit"]
            }
        }

@app.get("/model-status")
async def model_status():
    """Get current model loading status"""
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(f"{WINDOWS_AI_BASE_URL}/healthz")
            if response.status_code == 200:
                health_data = response.json()
                running_models = health_data.get("running", [])
                return {
                    "status": "connected",
                    "running_models": running_models,
                    "model_status": {
                        model_id: {
                            "loaded": model_id in running_models,
                            "status": "ready" if model_id in running_models else "not_loaded"
                        }
                        for model_id in ["llama3-8b", "qwen2.5-14b-awq", "deepseek-coder", "qwen-image-edit"]
                    }
                }
            else:
                return {
                    "status": "disconnected",
                    "running_models": [],
                    "model_status": {
                        model_id: {
                            "loaded": False,
                            "status": "disconnected"
                        }
                        for model_id in ["llama3-8b", "qwen2.5-14b-awq", "deepseek-coder", "qwen-image-edit"]
                    }
                }
    except Exception as e:
        return {
            "status": "error",
            "error": str(e),
            "running_models": [],
            "model_status": {
                model_id: {
                    "loaded": False,
                    "status": "error"
                }
                for model_id in ["llama3-8b", "qwen2.5-14b-awq", "deepseek-coder", "qwen-image-edit"]
            }
        }

@app.get("/model-loading-progress/{model_name}")
async def model_loading_progress(model_name: str):
    """Get model loading progress from Windows manager"""
    import re
    
    # Map model names to container names
    container_map = {
        "llama3-8b": "vllm-llama3-8b",
        "qwen2.5-14b-awq": "vllm-qwen14b-awq",
        "deepseek-coder": "vllm-coder7b",
        "qwen-image-edit": "vllm-qwen-image"
    }
    
    container_name = container_map.get(model_name)
    if not container_name:
        return {"error": "Unknown model", "progress": 0, "status": "unknown"}
    
    try:
        # Check if model is ready
        async with httpx.AsyncClient(timeout=5.0) as client:
            health_response = await client.get(f"{WINDOWS_AI_BASE_URL}/healthz")
            if health_response.status_code == 200:
                health_data = health_response.json()
                running_models = health_data.get("running", [])
                
                if model_name in running_models:
                    return {
                        "progress": 100,
                        "status": "ready",
                        "message": "Model is ready"
                    }
        
        # If not ready, try to get progress from logs via Windows manager
        # We'll use a simple heuristic: if container is running but not ready, it's loading
        async with httpx.AsyncClient(timeout=2.0) as client:
            try:
                # Try to connect to the model directly - if it fails, it's loading
                test_response = await client.get(f"{WINDOWS_AI_BASE_URL}/v1/models")
                # If we get here and model isn't in running_models, it's loading
                return {
                    "progress": 50,  # Estimated - we can't get exact progress from API
                    "status": "loading",
                    "message": "Model is loading, please wait..."
                }
            except:
                # Can't connect - model is starting up
                return {
                    "progress": 25,
                    "status": "starting",
                    "message": "Model container is starting..."
                }
    except Exception as e:
        return {
            "progress": 0,
            "status": "error",
            "message": f"Error checking progress: {str(e)}"
        }

@app.post("/v1/chat/completions")
async def chat_completions(request: Request):
    """Proxy chat completions to Windows AI service"""
    try:
        body = await request.json()
        model_name = body.get("model", "unknown")
        logger.info(f"Proxying chat request for model: {model_name}")
        
        # Quick heuristic check (non-blocking) - if model name contains "image", reject immediately
        # Full validation happens at Windows manager level
        if "image" in model_name.lower():
            logger.warning(f"Chat completion requested for image model: {model_name}")
            raise HTTPException(
                status_code=400,
                detail=f"Model '{model_name}' is an image model and does not support text chat. Use /v1/images/generations for image models."
            )
        
        async with httpx.AsyncClient(timeout=TIMEOUT) as client:
            response = await client.post(
                f"{WINDOWS_AI_BASE_URL}/v1/chat/completions",
                json=body,
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                error_text = response.text
                logger.error(f"Windows AI service error: {response.status_code} - {error_text}")
                
                # Provide more helpful error messages
                if response.status_code == 503:
                    if "backend not ready" in error_text.lower():
                        detail = "Model is starting up. This may take a few minutes on first use as the model downloads. Please wait 30-60 seconds and try again."
                    else:
                        detail = f"Model backend is not ready: {error_text}. The model may be starting up or there may be an issue with the model container."
                else:
                    detail = f"Windows AI service error: {error_text}"
                
                raise HTTPException(
                    status_code=response.status_code,
                    detail=detail
                )
                
    except httpx.TimeoutException:
        logger.error("Request timeout to Windows AI service")
        raise HTTPException(status_code=504, detail="Request timeout - the model may be taking too long to respond")
    except httpx.ConnectError:
        logger.error("Cannot connect to Windows AI service")
        raise HTTPException(status_code=503, detail="Cannot connect to Windows AI service. Ensure the Windows AI manager is running.")
    except HTTPException:
        raise  # Re-raise HTTP exceptions
    except Exception as e:
        logger.error(f"Error in chat completions: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/v1/completions")
async def completions(request: Request):
    """Proxy completions to Windows AI service"""
    try:
        body = await request.json()
        logger.info(f"Proxying completion request for model: {body.get('model', 'unknown')}")
        
        async with httpx.AsyncClient(timeout=TIMEOUT) as client:
            response = await client.post(
                f"{WINDOWS_AI_BASE_URL}/v1/completions",
                json=body,
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                logger.error(f"Windows AI service error: {response.status_code} - {response.text}")
                raise HTTPException(
                    status_code=response.status_code,
                    detail=f"Windows AI service error: {response.text}"
                )
                
    except httpx.TimeoutException:
        logger.error("Request timeout to Windows AI service")
        raise HTTPException(status_code=504, detail="Request timeout")
    except httpx.ConnectError:
        logger.error("Cannot connect to Windows AI service")
        raise HTTPException(status_code=503, detail="Cannot connect to Windows AI service")
    except Exception as e:
        logger.error(f"Error in completions: {e}")
        raise HTTPException(status_code=500, detail=str(e))

async def get_model_type(model_name: str) -> str:
    """Get model type (text or image) from Windows AI service"""
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            # Get models list to check if model exists
            response = await client.get(f"{WINDOWS_AI_BASE_URL}/v1/models")
            if response.status_code == 200:
                models_data = response.json()
                # Check if model exists in the list
                model_ids = [m.get("id") for m in models_data.get("data", [])]
                if model_name not in model_ids:
                    return "unknown"
                
                # For now, we'll use a simple heuristic:
                # Image models typically have "image" in the name
                # In the future, the manager could expose model type via API
                if "image" in model_name.lower():
                    return "image"
                return "text"
    except:
        pass
    return "unknown"

@app.post("/v1/images/generations")
async def image_generations(request: Request):
    """Proxy image generation requests to Windows AI service"""
    try:
        body = await request.json()
        model_name = body.get("model", "unknown")
        logger.info(f"Proxying image generation request for model: {model_name}")
        
        # Quick heuristic check (non-blocking) - if model name doesn't contain "image", reject immediately
        # Full validation happens at Windows manager level
        if "image" not in model_name.lower():
            logger.warning(f"Image generation requested for text model: {model_name}")
            raise HTTPException(
                status_code=400,
                detail=f"Model '{model_name}' is a text model and does not support image generation. Use /v1/chat/completions for text models."
            )
        
        async with httpx.AsyncClient(timeout=TIMEOUT) as client:
            response = await client.post(
                f"{WINDOWS_AI_BASE_URL}/v1/images/generations",
                json=body,
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                error_text = response.text
                logger.error(f"Windows AI service error: {response.status_code} - {error_text}")
                
                # Provide more helpful error messages
                if response.status_code == 503:
                    if "backend not ready" in error_text.lower() or "not ready" in error_text.lower():
                        detail = "Image model is starting up. This may take a few minutes on first use. Please wait 30-60 seconds and try again."
                    else:
                        detail = f"Image model backend is not ready: {error_text}. The model may be starting up or there may be an issue with the model container."
                elif response.status_code == 400:
                    detail = f"Invalid image generation request: {error_text}"
                else:
                    detail = f"Windows AI service error: {error_text}"
                
                raise HTTPException(
                    status_code=response.status_code,
                    detail=detail
                )
                
    except httpx.TimeoutException:
        logger.error("Request timeout to Windows AI service")
        raise HTTPException(status_code=504, detail="Request timeout - image generation may take longer than expected")
    except httpx.ConnectError:
        logger.error("Cannot connect to Windows AI service")
        raise HTTPException(status_code=503, detail="Cannot connect to Windows AI service. Ensure the Windows AI manager is running.")
    except HTTPException:
        raise  # Re-raise HTTP exceptions
    except Exception as e:
        logger.error(f"Error in image generation: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/docs")
async def get_docs():
    """Get API documentation"""
    return {
        "title": "Local AI Proxy API",
        "description": "Proxy service for local AI models running on Windows machine",
        "version": "1.0.0",
        "endpoints": {
            "GET /": "Service information",
            "GET /health": "Health check",
            "GET /v1/models": "List available models",
            "GET /models/info": "Detailed model information",
            "GET /usage/stats": "Usage statistics",
            "POST /v1/chat/completions": "Chat completions",
            "POST /v1/completions": "Text completions",
            "POST /v1/images/generations": "Image generation"
        },
        "models": ["llama3-8b", "qwen2.5-14b-awq", "deepseek-coder", "qwen-image-edit"],
        "windows_host": WINDOWS_AI_HOST,
        "windows_port": WINDOWS_AI_PORT
    }

@app.get("/status")
async def status():
    """Get comprehensive status information"""
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            health_response = await client.get(f"{WINDOWS_AI_BASE_URL}/healthz")
            models_response = await client.get(f"{WINDOWS_AI_BASE_URL}/v1/models")
            
            return {
                "proxy": {
                    "status": "running",
                    "uptime": "active",
                    "version": "1.0.0"
                },
                "windows_ai": {
                    "status": "connected" if health_response.status_code == 200 else "disconnected",
                    "health": health_response.json() if health_response.status_code == 200 else None,
                    "models_available": models_response.json() if models_response.status_code == 200 else None
                },
                "timestamp": "now"
            }
    except Exception as e:
        return {
            "proxy": {
                "status": "running",
                "uptime": "active",
                "version": "1.0.0"
            },
            "windows_ai": {
                "status": "error",
                "error": str(e)
            },
            "timestamp": "now"
        }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
