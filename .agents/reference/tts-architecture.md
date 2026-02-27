# TTS Architecture - Local AI Integration

Reference document for the Text-to-Speech architecture decision and implementation.

## Decision Summary

| Aspect | Decision |
|--------|----------|
| **Model** | Chatterbox Turbo (350M params) |
| **Primary GPU** | RTX 3090 on Gaming PC |
| **Fallback** | None initially (CPU fallback in Phase 2) |
| **API** | OpenAI-compatible `/v1/audio/speech` |
| **Integration** | Docker container managed by `local-ai/manager` |
| **Location** | `local-ai/tts-inference-server/` |
| **Keep-Warm** | Auto-starts on boot, stays loaded until gaming mode |
| **Dashboard** | TTS toggle for auto-play responses |

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                        TTS ARCHITECTURE (Integrated)                             │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                  │
│   ┌─────────────┐                                                               │
│   │   Client    │                                                               │
│   └──────┬──────┘                                                               │
│          │                                                                       │
│          │  POST /v1/audio/speech                                               │
│          ▼                                                                       │
│   ┌─────────────────────────────────────────────────────────────────────────┐   │
│   │                      GAMING PC - LOCAL AI MANAGER                        │   │
│   │                         192.168.86.63:8000                               │   │
│   ├─────────────────────────────────────────────────────────────────────────┤   │
│   │                                                                          │   │
│   │   models.json:                                                           │   │
│   │   ┌──────────────────────────────────────────────────────────────────┐  │   │
│   │   │  "chatterbox-turbo": {                                            │  │   │
│   │   │      "container": "chatterbox-tts",                               │  │   │
│   │   │      "port": 8006,                                                │  │   │
│   │   │      "type": "tts",                                               │  │   │
│   │   │      "keep_warm": true                                            │  │   │
│   │   │  }                                                                 │  │   │
│   │   └──────────────────────────────────────────────────────────────────┘  │   │
│   │                                                                          │   │
│   │   Manager behavior:                                                      │   │
│   │   1. On boot: Auto-starts keep-warm models (TTS + qwen2.5)              │   │
│   │   2. Receives request → proxies to container                            │   │
│   │   3. No idle timeout (stays warm until gaming mode)                     │   │
│   │   4. Gaming mode ON → stops all models                                   │   │
│   │   5. Gaming mode OFF → restarts keep-warm models                        │   │
│   │                                                                          │   │
│   └──────────────────────────────┬──────────────────────────────────────────┘   │
│                                  │                                               │
│                                  ▼                                               │
│   ┌─────────────────────────────────────────────────────────────────────────┐   │
│   │                     CHATTERBOX-TTS CONTAINER                             │   │
│   │                      (started on-demand by manager)                      │   │
│   ├─────────────────────────────────────────────────────────────────────────┤   │
│   │                                                                          │   │
│   │   Model: Chatterbox Turbo (350M params)                                 │   │
│   │   VRAM: ~1.5GB                                                           │   │
│   │   Latency: ~0.3s for 10s audio                                          │   │
│   │   API: /v1/audio/speech, /health, /v1/models                            │   │
│   │                                                                          │   │
│   └─────────────────────────────────────────────────────────────────────────┘   │
│                                                                                  │
│   Other containers (also managed):                                               │
│   - vllm-qwen14b-awq (text, 8002)                                               │
│   - vllm-llama3-8b (text, 8001)                                                 │
│   - qwen-image-server (image, 8005)                                             │
│                                                                                  │
└─────────────────────────────────────────────────────────────────────────────────┘
```

**Key benefit**: TTS is managed the same way as text and image models - on-demand loading, auto-shutdown, gaming mode awareness.

## Why Chatterbox Turbo?

| Criteria | Chatterbox Turbo | Alternatives |
|----------|------------------|--------------|
| **Model Size** | 350M (distilled) | Coqui TTS: 100M-500M, Bark: 1B+ |
| **VRAM** | ~1.5GB | Bark: 4-8GB, Tortoise: 8GB+ |
| **Quality** | State-of-the-art | Comparable to commercial |
| **Speed** | 0.03-0.05x RTF | Bark: 0.5-2x, Tortoise: 10x+ |
| **Voice Cloning** | Yes (10s ref) | Some support it |
| **License** | MIT | Varies |

**Key advantage**: 1-step decoder (distilled from 10 steps) makes it extremely fast while maintaining quality.

## Why Gaming PC (3090) as Primary?

| Consideration | Gaming PC (3090) | Server (3070) |
|---------------|------------------|---------------|
| **VRAM Total** | 24GB | 8GB |
| **VRAM Free** | ~14-16GB (after vLLM) | ~1.5GB |
| **Can coexist with LLM** | Yes | Tight |
| **Always on** | Yes (typically) | Yes |
| **Network hop** | Same LAN (~1ms) | Local |

**Decision**: Run TTS on Gaming PC because:
1. Plenty of VRAM headroom (24GB - 8GB vLLM = 16GB free)
2. No contention with server's vLLM
3. Faster GPU (3090 > 3070)
4. Gaming PC is typically always on

## Fallback Strategy

**Phase 1 (Current)**: No fallback - return 503 if Gaming PC unavailable

**Phase 2 (Future)**: CPU fallback on server
- Run Chatterbox on CPU when Gaming PC is down
- Much slower (~5-10s for 10s audio) but functional
- No VRAM contention since it uses CPU

```python
# Future router logic
async def route_tts(request):
    if await health_check("gaming-pc:8080"):
        return await proxy_to("gaming-pc:8080", request)
    elif ENABLE_TTS_CPU_FALLBACK:
        return await proxy_to("localhost:8081", request)  # CPU mode
    else:
        raise HTTPException(503, "TTS service unavailable")
```

## API Compatibility

The Chatterbox TTS Server exposes an OpenAI-compatible API:

### Request (OpenAI Format)
```json
{
  "model": "tts-1",
  "input": "Hello, world!",
  "voice": "alloy",
  "response_format": "wav",
  "speed": 1.0
}
```

### Mapping to Chatterbox
| OpenAI Param | Chatterbox Mapping |
|--------------|-------------------|
| `model` | Ignored (always Chatterbox Turbo) |
| `input` | Text to synthesize |
| `voice` | Voice reference clip filename |
| `response_format` | Output format (wav only for now) |
| `speed` | Not yet implemented |

### Response
- Binary audio file (WAV)
- Headers: `X-Audio-Duration`, `X-Generation-Time`, `X-Real-Time-Factor`

## VRAM Budget

### Gaming PC (RTX 3090, 24GB)

| Component | VRAM | Notes |
|-----------|------|-------|
| vLLM (qwen3-32b-awq) | ~22GB | Primary LLM (awq_marlin, 8K context) |
| Chatterbox Turbo | ~1.5GB | TTS (runs on port 8006) |
| System/overhead | ~1GB | CUDA, drivers |
| **Total Used (LLM active)** | **~22-23GB** | qwen3-32b fills most VRAM |
| **Available** | **~1-2GB** | TTS coexists only when LLM is stopped |

> **Note (2026-02-27):** Qwen3-32B-AWQ with `awq_marlin` and 8K context uses ~22GB.
> TTS and LLM cannot coexist on GPU simultaneously. Gaming mode stops the LLM;
> TTS runs as a standalone container managed by `docker-compose.gaming.yml`.

### Server (RTX 3070, 8GB)

| Component | VRAM | Notes |
|-----------|------|-------|
| vLLM (qwen2.5-7b-awq) | ~6.5GB | Primary LLM |
| System/overhead | ~0.5GB | CUDA, drivers |
| **Total Used** | **~7GB** | |
| **Available** | **~1GB** | Not enough for Chatterbox GPU |

**Conclusion**: Server 3070 cannot run both vLLM and Chatterbox on GPU simultaneously. Either:
1. Unload vLLM when TTS needed (high latency)
2. Run TTS on CPU (slow but works)
3. Don't use server for TTS (current approach)

## Performance Expectations

### Chatterbox Turbo on RTX 3090

| Input | Audio Duration | Generation Time | RTF |
|-------|----------------|-----------------|-----|
| Short (50 chars) | ~3s | ~0.15s | 0.05x |
| Medium (200 chars) | ~10s | ~0.35s | 0.035x |
| Long (500 chars) | ~25s | ~0.8s | 0.032x |
| Very Long (1000 chars) | ~50s | ~1.5s | 0.03x |

**Note**: RTF < 1.0 means faster than real-time. Generation is ~30x faster than playback.

### Total Latency (Client Perspective)

```
Total = Network (router) + TTS Generation + Network (response) + Download

Example for 200 chars → 10s audio:
- Network to router: ~1ms
- Router processing: ~5ms
- Network to Gaming PC: ~1ms
- TTS Generation: ~350ms
- Network response: ~1ms
- Audio download: ~50ms (10s WAV @ 16kHz ≈ 320KB)

Total: ~410ms time-to-first-byte, ~460ms to complete download
```

## Streaming vs Batch

### Current: Batch Mode
- Generate full audio, return when complete
- Simpler implementation
- Time-to-first-byte = full generation time

### Future: Streaming Mode
- Stream audio chunks as generated
- Lower perceived latency
- Requires:
  1. Chunked generation (Chatterbox doesn't support natively)
  2. OR sentence-by-sentence generation
  3. Audio chunk streaming protocol

**Recommendation**: Start with batch mode. Add streaming later if latency becomes an issue.

## Integration Points

### 1. Direct API Access
```bash
curl -X POST http://192.168.86.63:8080/v1/audio/speech \
  -H "Content-Type: application/json" \
  -d '{"input": "Hello world"}' \
  --output speech.wav
```

### 2. Via Local AI Router (Future)
```bash
curl -X POST https://local-ai-api.server.unarmedpuppy.com/v1/audio/speech \
  -H "Content-Type: application/json" \
  -d '{"input": "Hello world"}' \
  --output speech.wav
```

### 3. Python SDK
```python
from openai import OpenAI

client = OpenAI(
    base_url="http://192.168.86.63:8080/v1",
    api_key="not-needed"
)

response = client.audio.speech.create(
    model="tts-1",
    input="Hello, this is a test.",
    voice="default"
)

response.stream_to_file("speech.wav")
```

## Future Enhancements

1. **Router Integration**: Add `/v1/audio/speech` endpoint to Local AI Router
2. **CPU Fallback**: Run Chatterbox on server CPU when Gaming PC unavailable
3. **Streaming**: Implement sentence-by-sentence streaming
4. **Voice Management**: Web UI for uploading/managing voice clips
5. **Caching**: Cache common phrases (greetings, etc.)
6. **Metrics**: Track TTS usage in router metrics

## Dashboard Integration

The Local AI Dashboard has a TTS toggle for auto-playing assistant responses:

```
Dashboard (browser) → nginx /tts/ proxy → Gaming PC:8000 → Chatterbox TTS → WAV bytes → browser playback
```

**Configuration** (`apps/local-ai-dashboard/.env`):
```env
TTS_API_URL=http://<GAMING_PC_IP>:8000
```

**How it works:**
1. User enables 🔊 TTS toggle in chat header
2. After each assistant response, dashboard calls `/tts/v1/audio/speech`
3. Nginx proxies to Gaming PC manager
4. WAV bytes returned, Blob URL created
5. Audio auto-plays in browser
6. Blob URL revoked after playback (memory freed)

**No files on disk** - audio is streamed in memory only.

## Related Documentation

- [TTS Inference Server](../../local-ai/tts-inference-server/README.md)
- [Local AI Manager](../../local-ai/README.md)
- [Local AI Dashboard](../../apps/local-ai-dashboard/README.md)
- [Local AI Router](../../apps/local-ai-router/README.md)
- [Chatterbox Turbo on HuggingFace](https://huggingface.co/ResembleAI/chatterbox-turbo)
