# Local AI Setup

This directory contains the setup for running local LLMs on your Windows machine with Docker Desktop.

## Architecture

- **Windows Machine (3090)**: Runs LLM models using vLLM in Docker containers
- **Home Server (3070)**: Runs local models for fast routing (pending GPU setup)
- **Local AI Router** (`apps/local-ai-router/`): Intelligent API router with OpenAI-compatible endpoints
- **Local AI Dashboard** (`apps/local-ai-dashboard/`): React dashboard for chat, metrics, and conversation history
- **Manager Service**: Automatically starts/stops model containers based on demand

> **Note**: The legacy `local-ai-app` proxy has been sunset. Use the router and dashboard instead.

## Quick Start

> **Note:** Auto-startup is configured. See [STARTUP_STATUS.md](STARTUP_STATUS.md) for details and removal instructions.

### 1. Windows Setup

**First time setup:**
```bash
cd local-ai
chmod +x setup.sh
./setup.sh
```

**Or if you're on Windows PowerShell:**
```powershell
cd local-ai
# Build image inference server first
.\build-image-server.ps1
# Then run setup
bash setup.sh
```

**Note**: The setup script will automatically build the image inference server if the Dockerfile exists. You can also build it manually first.

**Verify setup:**
```powershell
.\verify-setup.ps1
```

**Start services (manager + web dashboard):**
```powershell
docker compose up -d
```

This starts both the manager service and the web dashboard automatically.

### 2. Configure Windows Firewall

Allow port 8000 from your server's IP (optional but recommended for security):
```powershell
# Replace <SERVER_IP> with your server's IP address
New-NetFirewallRule -DisplayName "LLM Manager 8000" -Direction Inbound -Protocol TCP -LocalPort 8000 -RemoteAddress <SERVER_IP> -Action Allow
```

Or allow from your local network (less secure but easier):
```powershell
New-NetFirewallRule -DisplayName "LLM Manager 8000" -Direction Inbound -Protocol TCP -LocalPort 8000 -RemoteAddress 192.168.86.0/24 -Action Allow
```

### 3. Server Setup

```bash
# Start the Local AI Router
cd apps/local-ai-router
docker compose up -d

# Start the Local AI Dashboard (optional - for web UI)
cd apps/local-ai-dashboard
docker compose up -d
```

**Access Points:**
- **API**: `https://local-ai-api.server.unarmedpuppy.com` (OpenAI-compatible)
- **Dashboard**: `https://local-ai-dashboard.server.unarmedpuppy.com`

## Models Available

### Text Generation Models (vLLM)
- **llama3-8b**: Llama 3.1 8B Instruct (best general quality)
- **qwen2.5-14b-awq**: Qwen 2.5 14B Instruct AWQ (stronger reasoning)  
- **deepseek-coder**: DeepSeek Coder V2 Lite (coding-focused)

### Image Generation Models (Diffusers)
- **qwen-image-edit**: Qwen Image Edit 2509 (image generation and editing)

### Text-to-Speech Models (Chatterbox)
- **chatterbox-turbo**: Chatterbox Turbo 350M (fast TTS with voice cloning)

**Note**: Each model type uses a different inference engine:
- Text models: vLLM
- Image models: HuggingFace Diffusers (`image-inference-server/`)
- TTS models: Chatterbox (`tts-inference-server/`)

## Features

- **On-demand loading**: Models start only when requested
- **Auto-shutdown**: Models stop after 10 minutes of inactivity
- **Gaming Mode**: Prevent new models from starting while gaming or doing GPU-intensive work
- **Resource Management**: Check status, force-stop models, and ensure GPU is free
- **OpenAI compatibility**: Works with any OpenAI-compatible client
- **GPU acceleration**: Uses NVIDIA GPU for fast inference
- **Memory efficient**: Only loads models when needed
- **Multimodal support**: Text, image, and TTS models
- **Unified management**: Single manager service handles all model types

## Usage

**Web Dashboard:**
Visit `https://local-ai-dashboard.server.unarmedpuppy.com` for the chat interface with:
- Streaming responses with status updates
- Conversation history and search
- Provider/model selection
- Image upload for multimodal chat

**API Usage:**
```bash
# Chat completion via router (auto-routes to best backend)
curl -X POST https://local-ai-api.server.unarmedpuppy.com/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "auto",
    "messages": [{"role": "user", "content": "Hello!"}],
    "max_tokens": 100
  }'

# Force routing to 3090
curl -X POST https://local-ai-api.server.unarmedpuppy.com/v1/chat/completions \
  -H "Content-Type: application/json" \
  -H "X-Force-Big: true" \
  -d '{
    "model": "big",
    "messages": [{"role": "user", "content": "Complex task..."}]
  }'
```

**TTS Usage (Text-to-Speech):**
```bash
# Generate speech via manager (starts container on-demand)
curl -X POST http://localhost:8000/v1/audio/speech \
  -H "Content-Type: application/json" \
  -d '{
    "model": "chatterbox-turbo",
    "input": "Hello, this is Chatterbox Turbo!",
    "voice": "default"
  }' \
  --output speech.wav

# Play the audio
ffplay speech.wav
```

See [Local AI Router README](../apps/local-ai-router/README.md) for full API documentation.
See [TTS Inference Server README](./tts-inference-server/README.md) for TTS-specific documentation.

## Requirements

- Windows 11 with Docker Desktop
- NVIDIA GPU with CUDA support
- WSL2 enabled
- Docker Desktop GPU acceleration enabled
- At least 24GB VRAM recommended for all models

## Resource Management & Gaming Mode

**Web Dashboard (Auto-starts with Docker):**
The web dashboard is now a Docker container that starts automatically with `docker compose up`.

```powershell
# Just start docker compose (dashboard starts automatically)
docker compose up -d

# Then open in your browser:
# http://localhost:8080
```

The web dashboard provides:
- Real-time status monitoring (auto-refreshes every 2 seconds)
- One-click gaming mode toggle
- Stop all models button
- Visual indicators for safe-to-game status
- Accessible from any device on your network

**Desktop GUI (Alternative):**
```powershell
# Launch the lightweight desktop GUI
.\gaming-mode-gui.ps1
```

**Command Line:**

**Before gaming or GPU-intensive work:**

```powershell
# Check if safe to game
.\control-gaming-mode.ps1 safe

# Stop all models and enable gaming mode
.\control-gaming-mode.ps1 stop-all
.\control-gaming-mode.ps1 enable
```

**After gaming:**

```powershell
.\control-gaming-mode.ps1 disable
```

For complete documentation, see [GAMING_MODE.md](GAMING_MODE.md).

## Deployment

For detailed deployment instructions, see [DEPLOYMENT.md](DEPLOYMENT.md).

For testing, see [TESTING.md](TESTING.md).

For troubleshooting, see [TROUBLESHOOTING.md](TROUBLESHOOTING.md).

For gaming mode and resource management, see [GAMING_MODE.md](GAMING_MODE.md).
