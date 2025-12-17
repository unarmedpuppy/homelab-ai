# Local AI Setup

This directory contains the setup for running local LLMs on your Windows machine with Docker Desktop.

## Architecture

- **Windows Machine**: Runs the actual LLM models using vLLM (text) and custom inference servers (image) in Docker containers
- **Remote Server**: Runs a proxy service (`local-ai-app`) that forwards requests to Windows
- **Manager Service**: Automatically starts/stops model containers based on demand
- **Model Types**: Supports both text generation (vLLM) and image generation (Diffusers) models

## Quick Start

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

**Start manager (if not running):**
```powershell
docker compose up -d
```

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
cd apps/local-ai-app
# Verify WINDOWS_AI_HOST in docker-compose.yml matches your Windows IP (default: 192.168.86.63)
docker compose up -d
```

## Models Available

### Text Generation Models (vLLM)
- **llama3-8b**: Llama 3.1 8B Instruct (best general quality)
- **qwen2.5-14b-awq**: Qwen 2.5 14B Instruct AWQ (stronger reasoning)  
- **deepseek-coder**: DeepSeek Coder V2 Lite (coding-focused)

### Image Generation Models (Diffusers)
- **qwen-image-edit**: Qwen Image Edit 2509 (image generation and editing)

**Note**: Image models use a separate inference engine (HuggingFace Diffusers) and run in different containers than text models. See `local-ai/image-inference-server/` for the image model server implementation.

## Features

- **On-demand loading**: Models start only when requested
- **Auto-shutdown**: Models stop after 10 minutes of inactivity
- **OpenAI compatibility**: Works with any OpenAI-compatible client
- **GPU acceleration**: Uses NVIDIA GPU for fast inference
- **Memory efficient**: Only loads models when needed
- **Multimodal support**: Supports both text generation and image generation models
- **Unified management**: Single manager service handles both text and image models

## Usage

Access via: `http://local-ai.server.unarmedpuppy.com`

**Web Chat Interface:**
Visit the URL above for a ChatGPT-like interface with model selection, real-time chat, and mobile support.

**API Usage:**
```bash
curl -X POST http://local-ai.server.unarmedpuppy.com/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "llama3-8b",
    "messages": [{"role": "user", "content": "Hello!"}],
    "max_tokens": 100
  }'

# Image editing with Qwen Image Edit
curl -X POST http://local-ai.server.unarmedpuppy.com/v1/images/generations \
  -H "Content-Type: application/json" \
  -d '{
    "model": "qwen-image-edit",
    "prompt": "Edit this image to add a sunset",
    "n": 1,
    "size": "1024x1024"
  }'
```

## Requirements

- Windows 11 with Docker Desktop
- NVIDIA GPU with CUDA support
- WSL2 enabled
- Docker Desktop GPU acceleration enabled
- At least 24GB VRAM recommended for all models

## Deployment

For detailed deployment instructions, see [DEPLOYMENT.md](DEPLOYMENT.md).

For testing, see [TESTING.md](TESTING.md).

For troubleshooting, see [TROUBLESHOOTING.md](TROUBLESHOOTING.md).
