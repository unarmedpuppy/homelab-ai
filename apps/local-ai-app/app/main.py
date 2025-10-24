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

@app.post("/v1/chat/completions")
async def chat_completions(request: Request):
    """Proxy chat completions to Windows AI service"""
    try:
        body = await request.json()
        logger.info(f"Proxying chat request for model: {body.get('model', 'unknown')}")
        
        async with httpx.AsyncClient(timeout=TIMEOUT) as client:
            response = await client.post(
                f"{WINDOWS_AI_BASE_URL}/v1/chat/completions",
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

@app.post("/v1/images/generations")
async def image_generations(request: Request):
    """Proxy image generation requests to Windows AI service"""
    try:
        body = await request.json()
        logger.info(f"Proxying image generation request for model: {body.get('model', 'unknown')}")
        
        async with httpx.AsyncClient(timeout=TIMEOUT) as client:
            response = await client.post(
                f"{WINDOWS_AI_BASE_URL}/v1/images/generations",
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
