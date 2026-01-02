# TTS Inference Server

FastAPI server for text-to-speech using Chatterbox Turbo.

## Overview

This server provides OpenAI-compatible API endpoints for TTS. It integrates with the local-ai manager system alongside vLLM (text) and Diffusers (image) containers.

## Architecture

- **Base**: NVIDIA CUDA runtime (for GPU support)
- **Model**: Chatterbox Turbo (350M params, ~1.5GB VRAM)
- **Framework**: FastAPI
- **API**: OpenAI-compatible `/v1/audio/speech`
- **Port**: 8006 (configured in models.json)

## Setup

### Build Docker Image

```bash
cd local-ai/tts-inference-server
docker build -t tts-inference-server:latest .
```

Or use the build script:
```powershell
.\build-tts-server.ps1
```

### Create Container (Manager will start it on-demand)

```bash
docker create \
  --name chatterbox-tts \
  --gpus all \
  -v $(pwd)/voices:/app/voices \
  -v $(pwd)/cache:/root/.cache/huggingface \
  --network my-network \
  tts-inference-server:latest
```

### Test Manually

```bash
# Start container
docker start chatterbox-tts

# Health check
curl http://localhost:8006/health

# Generate speech
curl -X POST http://localhost:8006/v1/audio/speech \
  -H "Content-Type: application/json" \
  -d '{"input": "Hello, this is a test of Chatterbox Turbo."}' \
  --output test.wav

# Stop container
docker stop chatterbox-tts
```

## API Endpoints

### Health Check
```
GET /health
```
Returns model status and VRAM usage.

### List Models (OpenAI-compatible)
```
GET /v1/models
```

### List Voices
```
GET /v1/voices
```

### Generate Speech (OpenAI-compatible)
```
POST /v1/audio/speech
{
  "model": "chatterbox-turbo",
  "input": "Text to synthesize",
  "voice": "default",
  "response_format": "wav"
}
```

Returns: WAV audio file

## Voice Cloning

Add `.wav` files to the `voices/` directory (10-15 seconds of clear speech).

```bash
# Add custom voice
cp my-voice-sample.wav voices/custom-voice.wav

# Use in API
curl -X POST http://localhost:8006/v1/audio/speech \
  -H "Content-Type: application/json" \
  -d '{"input": "Hello", "voice": "custom-voice"}' \
  --output output.wav
```

## Integration with Manager

The server is registered in `models.json`:

```json
{
  "chatterbox-turbo": {
    "container": "chatterbox-tts",
    "port": 8006,
    "type": "tts"
  }
}
```

The manager will:
1. Start the container on first TTS request
2. Proxy `/v1/audio/speech` requests
3. Stop the container after idle timeout

## Performance

| Input Length | Audio Duration | Generation Time | RTF |
|--------------|----------------|-----------------|-----|
| 50 chars | ~3s | ~0.15s | 0.05x |
| 200 chars | ~10s | ~0.35s | 0.035x |
| 500 chars | ~25s | ~0.8s | 0.032x |

RTF (Real-Time Factor) < 1.0 means faster than real-time.

## VRAM Usage

- Model: ~1.5GB
- Peak during generation: ~2GB
- Coexists with vLLM models (total ~9GB of 24GB on 3090)

## Related

- [Local AI README](../README.md)
- [TTS Architecture](../../agents/reference/tts-architecture.md)
- [Chatterbox Turbo](https://huggingface.co/ResembleAI/chatterbox-turbo)
