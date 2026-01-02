---
name: test-tts
description: Test Text-to-Speech generation via Chatterbox Turbo
when_to_use: When testing TTS functionality, debugging audio generation, or verifying TTS setup
---

# Test TTS (Text-to-Speech)

> **⚠️ MIGRATION NOTICE (January 2025)**
> 
> TTS Server source code migrated to [homelab-ai](https://github.com/unarmedpuppy/homelab-ai) repo.
> Gaming PC now deploys from homelab-ai. This skill's test commands remain valid.

Test Chatterbox Turbo TTS generation via the Gaming PC manager.

## Quick Test

```bash
# Generate speech (replace with your Gaming PC IP)
curl -X POST http://<GAMING_PC_IP>:8000/v1/audio/speech \
  -H "Content-Type: application/json" \
  -d '{"model": "chatterbox-turbo", "input": "Hello, this is a test."}' \
  --output test.wav

# Play the audio
ffplay test.wav
# Or on Windows: start test.wav
# Or on Mac: afplay test.wav
```

## API Reference

### Generate Speech

**Endpoint:** `POST /v1/audio/speech`

**Request:**
```json
{
  "model": "chatterbox-turbo",
  "input": "Text to synthesize (max 4096 chars)",
  "voice": "default",
  "response_format": "wav"
}
```

**Response:** Binary WAV audio file

**Headers in response:**
- `X-Audio-Duration` - Duration of generated audio in seconds
- `X-Generation-Time` - Time taken to generate
- `X-Real-Time-Factor` - Generation speed (< 1.0 means faster than real-time)

### Voice Options

| Voice | Description |
|-------|-------------|
| `default` | Built-in default voice |
| `<name>` | Custom voice from `voices/<name>.wav` |

### Voice Cloning

To use a custom voice:

1. Add a WAV file to `local-ai/voices/` (10-15 seconds of clear speech)
2. Reference by filename (without .wav):

```bash
curl -X POST http://<GAMING_PC_IP>:8000/v1/audio/speech \
  -H "Content-Type: application/json" \
  -d '{"model": "chatterbox-turbo", "input": "Hello!", "voice": "my-custom-voice"}' \
  --output output.wav
```

### List Available Voices

```bash
curl http://<GAMING_PC_IP>:8000/v1/voices | jq
```

## Test Scenarios

### 1. Basic Generation

```bash
curl -X POST http://<GAMING_PC_IP>:8000/v1/audio/speech \
  -H "Content-Type: application/json" \
  -d '{"model": "chatterbox-turbo", "input": "Testing one two three."}' \
  --output basic.wav
```

### 2. Long Text

```bash
curl -X POST http://<GAMING_PC_IP>:8000/v1/audio/speech \
  -H "Content-Type: application/json" \
  -d '{
    "model": "chatterbox-turbo",
    "input": "This is a longer piece of text to test how the TTS system handles extended content. It should produce natural sounding speech with appropriate pauses and intonation throughout the entire passage."
  }' \
  --output long.wav
```

### 3. Via Manager (On-Demand Start)

The manager handles starting the TTS container if not running:

```bash
# First request may take ~30-60s for model to load
curl -X POST http://<GAMING_PC_IP>:8000/v1/audio/speech \
  -H "Content-Type: application/json" \
  -d '{"model": "chatterbox-turbo", "input": "Hello from manager!"}' \
  --output manager.wav
```

### 4. Check Container Health

```bash
# Check TTS container directly (if running)
curl http://<GAMING_PC_IP>:8006/health | jq

# Check via manager
curl http://<GAMING_PC_IP>:8000/status | jq '.running_models[] | select(.name == "chatterbox-turbo")'
```

## Performance Expectations

| Input | Audio Duration | Generation Time | RTF |
|-------|----------------|-----------------|-----|
| 50 chars | ~3s | ~0.15s | 0.05x |
| 200 chars | ~10s | ~0.35s | 0.035x |
| 500 chars | ~25s | ~0.8s | 0.032x |

RTF (Real-Time Factor) < 1.0 means faster than real-time.

## Dashboard TTS

The Local AI Dashboard has a TTS toggle for auto-playing responses:

1. Open: https://local-ai-dashboard.server.unarmedpuppy.com
2. Click the 🔊 TTS button to enable
3. Send a chat message
4. Audio auto-plays after response completes

**Configuration:** Dashboard needs `TTS_API_URL` configured in `.env`.

## Troubleshooting

### TTS Container Not Starting

```bash
# Check container exists
docker ps -a | grep chatterbox

# Check logs
docker logs chatterbox-tts --tail 50

# Manual start
docker start chatterbox-tts
```

### Slow First Request

First request loads the model (~30-60s). Subsequent requests are fast.

With keep-warm enabled, the model auto-starts on boot and stays loaded.

### VRAM Error

```bash
# Check VRAM usage
nvidia-smi

# TTS uses ~1.5GB VRAM
# If VRAM is full, stop other models first
curl -X POST http://<GAMING_PC_IP>:8000/stop-all
```

### Audio Quality Issues

- Keep input text under 500 chars for best quality
- Use punctuation for natural pauses
- Avoid special characters

### No Audio Output

```bash
# Verify file was created
ls -la test.wav

# Check file has content
file test.wav

# If empty, check manager logs
docker logs local-ai-manager --tail 20
```

## Python Example

```python
import requests

response = requests.post(
    "http://<GAMING_PC_IP>:8000/v1/audio/speech",
    json={
        "model": "chatterbox-turbo",
        "input": "Hello from Python!",
        "voice": "default"
    }
)

with open("output.wav", "wb") as f:
    f.write(response.content)

print(f"Audio duration: {response.headers.get('X-Audio-Duration')}s")
print(f"Generation time: {response.headers.get('X-Generation-Time')}s")
```

## OpenAI SDK Example

```python
from openai import OpenAI

client = OpenAI(
    base_url="http://<GAMING_PC_IP>:8000/v1",
    api_key="not-needed"
)

response = client.audio.speech.create(
    model="tts-1",  # Mapped to chatterbox-turbo
    input="Hello, this is a test.",
    voice="default"
)

response.stream_to_file("speech.wav")
```

## Related

- [Gaming PC Manager](../gaming-pc-manager/SKILL.md)
- [TTS Architecture](../../reference/tts-architecture.md)
- [TTS Inference Server](../../../local-ai/tts-inference-server/README.md)
- [Local AI Dashboard](../../../apps/local-ai-dashboard/README.md)
