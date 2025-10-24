# Local AI Setup

This directory contains the setup for running local LLMs on your Windows machine with Docker Desktop.

## Architecture

- **Windows Machine**: Runs the actual LLM models using vLLM in Docker containers
- **Remote Server**: Runs a proxy service (`local-ai-app`) that forwards requests to Windows
- **Manager Service**: Automatically starts/stops model containers based on demand

## Quick Start

### 1. Windows Setup

```bash
cd local-ai
chmod +x setup.sh
./setup.sh
```

### 2. Server Setup

```bash
cd apps/local-ai-app
# Update WINDOWS_AI_HOST in docker-compose.yml with your Windows IP
docker compose up -d
```

## Models Available

- **llama3-8b**: Llama 3.1 8B Instruct (best general quality)
- **qwen2.5-14b-awq**: Qwen 2.5 14B Instruct AWQ (stronger reasoning)  
- **deepseek-coder**: DeepSeek Coder V2 Lite (coding-focused)
- **qwen-image-edit**: Qwen Image Edit 2509 (multimodal image editing)

## Features

- **On-demand loading**: Models start only when requested
- **Auto-shutdown**: Models stop after 10 minutes of inactivity
- **OpenAI compatibility**: Works with any OpenAI-compatible client
- **GPU acceleration**: Uses NVIDIA GPU for fast inference
- **Memory efficient**: Only loads models when needed

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
