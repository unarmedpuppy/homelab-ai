"""
TTS Inference Server - OpenAI-compatible TTS API using Chatterbox Turbo.

Designed to integrate with the local-ai manager system alongside
vLLM (text) and Diffusers (image) containers.
"""

import io
import os
import time
import logging
from pathlib import Path
from typing import Optional, Literal

import torch
import torchaudio as ta
from fastapi import FastAPI, HTTPException, Response
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

# Configure logging
logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO"),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Global model instance
model = None
device = None
model_loaded = False

# Configuration
VOICES_DIR = Path(os.getenv("VOICES_DIR", "/app/voices"))
DEFAULT_VOICE_PATH = os.getenv("DEFAULT_VOICE_PATH", None)


class SpeechRequest(BaseModel):
    """OpenAI-compatible speech request."""
    model: str = Field(default="chatterbox-turbo", description="Model name")
    input: str = Field(..., description="Text to synthesize", max_length=4096)
    voice: str = Field(default="default", description="Voice reference clip name")
    response_format: Literal["wav", "mp3", "opus", "aac", "flac", "pcm"] = Field(
        default="wav", 
        description="Audio format (currently only wav supported)"
    )
    speed: float = Field(default=1.0, ge=0.25, le=4.0, description="Speed (not yet implemented)")


def get_gpu_memory():
    """Get GPU memory usage in MB."""
    if torch.cuda.is_available():
        used = torch.cuda.memory_allocated() / 1024 / 1024
        total = torch.cuda.get_device_properties(0).total_memory / 1024 / 1024
        return used, total
    return None, None


def load_model():
    """Load Chatterbox Turbo model."""
    global model, device, model_loaded
    
    logger.info("Loading Chatterbox Turbo model...")
    start_time = time.time()
    
    try:
        from chatterbox.tts_turbo import ChatterboxTurboTTS
        
        # Determine device
        if torch.cuda.is_available():
            device = "cuda"
            logger.info(f"Using CUDA device: {torch.cuda.get_device_name(0)}")
        else:
            device = "cpu"
            logger.warning("CUDA not available, using CPU (will be slow!)")
        
        # Load model
        model = ChatterboxTurboTTS.from_pretrained(device=device)
        model_loaded = True
        
        elapsed = time.time() - start_time
        vram_used, vram_total = get_gpu_memory()
        logger.info(
            f"Model loaded in {elapsed:.1f}s on {device}. "
            f"VRAM: {vram_used:.0f}/{vram_total:.0f} MB" if vram_used else f"Model loaded in {elapsed:.1f}s on {device}"
        )
        
        return True
    except Exception as e:
        logger.error(f"Failed to load model: {e}")
        model_loaded = False
        return False


# Load model on import (server startup)
load_model()

app = FastAPI(
    title="TTS Inference Server",
    description="OpenAI-compatible TTS API using Chatterbox Turbo",
    version="1.0.0",
)

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root():
    """API root."""
    return {
        "name": "TTS Inference Server",
        "model": "chatterbox-turbo",
        "version": "1.0.0",
        "status": "ready" if model_loaded else "loading",
    }


@app.get("/health")
async def health():
    """Health check endpoint (used by manager)."""
    vram_used, vram_total = get_gpu_memory()
    return {
        "status": "healthy" if model_loaded else "unhealthy",
        "model_loaded": model_loaded,
        "device": device or "unknown",
        "vram_used_mb": vram_used,
        "vram_total_mb": vram_total,
    }


@app.get("/v1/models")
async def list_models():
    """List available models (OpenAI-compatible, used by manager for health check)."""
    return {
        "object": "list",
        "data": [
            {
                "id": "chatterbox-turbo",
                "object": "model",
                "created": int(time.time()),
                "owned_by": "resemble-ai",
                "type": "tts",
            }
        ]
    }


@app.get("/v1/voices")
async def list_voices():
    """List available voice reference clips."""
    voices = ["default"]
    
    # Scan voices directory
    if VOICES_DIR.exists():
        for voice_file in VOICES_DIR.glob("*.wav"):
            voices.append(voice_file.stem)
    
    return {
        "voices": voices,
        "voices_dir": str(VOICES_DIR),
    }


@app.post("/v1/audio/speech")
async def create_speech(request: SpeechRequest):
    """
    Generate speech from text (OpenAI-compatible).
    
    Voice cloning via 'voice' parameter:
    - "default": Built-in voice
    - "name": Uses voices/{name}.wav as reference
    """
    if not model_loaded or model is None:
        raise HTTPException(
            status_code=503,
            detail="Model not loaded. Server may still be starting."
        )
    
    if not request.input.strip():
        raise HTTPException(status_code=400, detail="Input text cannot be empty")
    
    # Determine voice reference path
    voice_path = None
    if request.voice and request.voice != "default":
        voice_file = VOICES_DIR / f"{request.voice}.wav"
        if voice_file.exists():
            voice_path = str(voice_file)
        elif Path(request.voice).exists():
            voice_path = request.voice
        else:
            raise HTTPException(
                status_code=400,
                detail=f"Voice '{request.voice}' not found"
            )
    elif DEFAULT_VOICE_PATH and Path(DEFAULT_VOICE_PATH).exists():
        voice_path = DEFAULT_VOICE_PATH
    
    logger.info(f"Generating speech: {len(request.input)} chars, voice={request.voice}")
    
    start_time = time.time()
    
    try:
        # Generate audio
        if voice_path:
            wav = model.generate(request.input, audio_prompt_path=voice_path)
        else:
            wav = model.generate(request.input)
        
        elapsed = time.time() - start_time
        audio_duration = wav.shape[1] / model.sr
        rtf = elapsed / audio_duration
        
        logger.info(f"Generated {audio_duration:.1f}s audio in {elapsed:.2f}s (RTF={rtf:.3f}x)")
        
        # Convert to WAV bytes
        if request.response_format == "wav":
            buffer = io.BytesIO()
            ta.save(buffer, wav, model.sr, format="wav")
            buffer.seek(0)
            media_type = "audio/wav"
        else:
            raise HTTPException(
                status_code=400,
                detail=f"Format '{request.response_format}' not yet supported. Use 'wav'."
            )
        
        return Response(
            content=buffer.read(),
            media_type=media_type,
            headers={
                "X-Audio-Duration": str(audio_duration),
                "X-Generation-Time": str(elapsed),
                "X-Real-Time-Factor": str(rtf),
            }
        )
        
    except Exception as e:
        logger.error(f"Generation failed: {e}")
        raise HTTPException(status_code=500, detail=f"Speech generation failed: {str(e)}")


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", "8000"))
    uvicorn.run(app, host="0.0.0.0", port=port)
