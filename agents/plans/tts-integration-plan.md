# TTS Integration Plan - Chatterbox Turbo

Implementation plan for adding Text-to-Speech capability using Chatterbox Turbo, integrated with the existing `local-ai` manager system.

## Overview

| Item | Details |
|------|---------|
| **Goal** | Always-available TTS via Local AI Manager |
| **Model** | Chatterbox Turbo (350M params) |
| **Primary GPU** | RTX 3090 (Gaming PC) |
| **Fallback** | None initially; CPU fallback in Phase 2 |
| **API** | OpenAI-compatible `/v1/audio/speech` |
| **Location** | `local-ai/tts-inference-server/` |

## Phase 1: Integrated TTS Server (Current)

**Status**: Code written, ready for deployment

### Deliverables
- [x] TTS Inference Server (`local-ai/tts-inference-server/`)
- [x] Dockerfile for containerized deployment
- [x] OpenAI-compatible `/v1/audio/speech` endpoint
- [x] Health check endpoint (`/health`, `/v1/models`)
- [x] Voice cloning support (reference clips)
- [x] Manager integration (`models.json` updated)
- [x] Build scripts (`build-tts-server.ps1`, `build-tts-server.sh`)
- [x] Reference documentation (`agents/reference/tts-architecture.md`)

### Deployment Steps

1. **Build Docker image on Gaming PC**
   ```powershell
   cd local-ai
   .\build-tts-server.ps1
   ```

2. **Create container (manager starts it on-demand)**
   ```powershell
   docker create `
     --name chatterbox-tts `
     --gpus all `
     -v ${PWD}/voices:/app/voices `
     -v ${PWD}/cache:/root/.cache/huggingface `
     --network my-network `
     tts-inference-server:latest
   ```

3. **Test manually**
   ```powershell
   # Start container
   docker start chatterbox-tts
   
   # Wait for model to load (~30-60s first time)
   curl http://localhost:8006/health
   
   # Generate speech
   curl -X POST http://localhost:8006/v1/audio/speech `
     -H "Content-Type: application/json" `
     -d '{"model": "chatterbox-turbo", "input": "Hello, this is a test."}' `
     --output test.wav
   
   # Stop container (manager will do this automatically)
   docker stop chatterbox-tts
   ```

4. **Test via manager (on-demand loading)**
   ```powershell
   # Manager starts container automatically when needed
   curl -X POST http://localhost:8000/v1/audio/speech `
     -H "Content-Type: application/json" `
     -d '{"model": "chatterbox-turbo", "input": "Hello via manager!"}' `
     --output test.wav
   ```

### Success Criteria
- [ ] Docker image builds successfully
- [ ] Container starts and model loads
- [ ] Health endpoint returns `{"status": "healthy"}`
- [ ] Can generate speech via direct container access
- [ ] Can generate speech via manager (on-demand start)
- [ ] Container auto-stops after 10min idle
- [ ] VRAM usage ~1.5GB

---

## Phase 2: Router Integration (Optional)

**Status**: Not started

The TTS is already accessible via the Gaming PC manager at `192.168.86.63:8000`. 
This phase adds routing through the server's Local AI Router for unified access.

### Goals
- Add `/v1/audio/speech` endpoint to Local AI Router on server
- Proxy requests to Gaming PC manager
- Health-aware routing

### Tasks

1. **Add TTS config to router**
   ```python
   # router.py or config/providers.yaml
   TTS_ENDPOINT = os.getenv("TTS_ENDPOINT", "http://192.168.86.63:8000")
   ```

2. **Add /v1/audio/speech endpoint**
   ```python
   @app.post("/v1/audio/speech")
   async def audio_speech(request: Request):
       body = await request.json()
       body["model"] = "chatterbox-turbo"  # Ensure correct model
       
       async with httpx.AsyncClient(timeout=120.0) as client:
           response = await client.post(
               f"{TTS_ENDPOINT}/v1/audio/speech",
               json=body,
           )
           return Response(
               content=response.content,
               media_type=response.headers.get("content-type"),
               headers={
                   "X-Audio-Duration": response.headers.get("X-Audio-Duration"),
                   "X-Generation-Time": response.headers.get("X-Generation-Time"),
               }
           )
   ```

### Success Criteria
- [ ] Router exposes `/v1/audio/speech`
- [ ] Requests proxied to Gaming PC manager
- [ ] On-demand container start works through proxy

---

## Phase 3: Fallback & Resilience

**Status**: Future

### Options

#### Option A: CPU Fallback on Server
- Run Chatterbox on server CPU when Gaming PC unavailable
- Slow (~5-10s for 10s audio) but functional
- No VRAM contention

#### Option B: GT 1030 on Gaming PC
- Add GT 1030 as dedicated TTS GPU
- Fast, dedicated, no contention
- Requires physical installation

#### Option C: Queue-based Fallback
- Queue TTS requests when Gaming PC unavailable
- Process when available
- Not real-time, but guarantees delivery

### Recommendation
Start with Option A (CPU fallback) for simplicity. Can add Option B later if CPU is too slow.

---

## Phase 4: Advanced Features

**Status**: Future

### Potential Enhancements

1. **Streaming TTS**
   - Sentence-by-sentence generation
   - Stream audio chunks to client
   - Lower perceived latency

2. **Voice Management UI**
   - Upload voice reference clips via dashboard
   - Preview voices
   - Manage voice library

3. **Caching**
   - Cache common phrases
   - Hash-based lookup
   - Reduces GPU load for repeated content

4. **Metrics & Monitoring**
   - Track TTS usage in router metrics
   - Generation time histograms
   - Voice usage statistics

5. **Multi-language**
   - Use Chatterbox Multilingual (500M)
   - 23+ languages support
   - Higher VRAM (~2GB)

---

## Resource Requirements

### Gaming PC (3090)

| Phase | Additional VRAM | Total VRAM Used |
|-------|-----------------|-----------------|
| Phase 1 | +1.5GB (Chatterbox) | ~9-11GB |
| Phase 4 (Multilingual) | +0.5GB | ~10-12GB |

**Available for gaming**: ~12-15GB (of 24GB)

### Server (3070)

| Phase | Impact |
|-------|--------|
| Phase 1-2 | None (TTS on Gaming PC) |
| Phase 3 (CPU fallback) | CPU only, no VRAM |

---

## Timeline

| Phase | Effort | Dependencies |
|-------|--------|--------------|
| Phase 1 | 1-2 hours | Gaming PC access |
| Phase 2 | 2-4 hours | Phase 1 complete |
| Phase 3 | 4-8 hours | Phase 2 complete |
| Phase 4 | Varies | As needed |

---

## Related Files

- `local-ai/tts-inference-server/` - TTS inference server (Docker)
- `local-ai/models.json` - Model configuration (includes chatterbox-turbo)
- `local-ai/manager/` - Manager service that handles on-demand loading
- `local-ai/build-tts-server.ps1` - Build script (Windows)
- `local-ai/build-tts-server.sh` - Build script (Linux/WSL)
- `agents/reference/tts-architecture.md` - Architecture decision doc
- `apps/local-ai-router/` - Server-side router (optional integration)
