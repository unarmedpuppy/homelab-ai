# Deployment Guide for Multimodal Inference Support

This guide covers deploying the complete multimodal inference system with both text and image models.

## Prerequisites

- Windows 11 with Docker Desktop
- NVIDIA GPU with CUDA support
- WSL2 enabled
- Docker Desktop GPU acceleration enabled
- At least 24GB VRAM recommended (for all models)

## Step-by-Step Deployment

### 1. Build Image Inference Server

First, build the Docker image for the image inference server:

**On Windows (PowerShell):**
```powershell
cd local-ai
.\build-image-server.ps1
```

**Or on Linux/Mac:**
```bash
cd local-ai
chmod +x build-image-server.sh
./build-image-server.sh
```

This will build the `image-inference-server:latest` Docker image.

### 2. Run Setup Script

Run the setup script to create all containers:

**On Windows (PowerShell):**
```powershell
cd local-ai
bash setup.sh
```

This will:
- Create text model containers (vLLM)
- Build and create image model container (if build succeeded)
- Start the manager service

### 3. Verify Setup

Run the verification script:

```powershell
.\verify-setup.ps1
```

Or run the multimodal test suite:

```powershell
.\test-multimodal.ps1
```

### 4. Configure Windows Firewall

Allow port 8000 from your server's IP:

```powershell
# Replace <SERVER_IP> with your server's IP address
New-NetFirewallRule -DisplayName "LLM Manager 8000" -Direction Inbound -Protocol TCP -LocalPort 8000 -RemoteAddress <SERVER_IP> -Action Allow
```

Or allow from your local network:

```powershell
New-NetFirewallRule -DisplayName "LLM Manager 8000" -Direction Inbound -Protocol TCP -LocalPort 8000 -RemoteAddress 192.168.86.0/24 -Action Allow
```

### 5. Deploy Server Proxy

On your server:

```bash
cd apps/local-ai-app
# Verify WINDOWS_AI_HOST in docker-compose.yml matches your Windows IP
docker compose up -d
```

## Verification

### Test Text Models

```bash
curl -X POST http://local-ai.server.unarmedpuppy.com/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "qwen2.5-14b-awq",
    "messages": [{"role": "user", "content": "Hello!"}],
    "max_tokens": 100
  }'
```

### Test Image Models

```bash
curl -X POST http://local-ai.server.unarmedpuppy.com/v1/images/generations \
  -H "Content-Type: application/json" \
  -d '{
    "model": "qwen-image-edit",
    "prompt": "a duck jumping over a puddle",
    "n": 1,
    "size": "1024x1024",
    "response_format": "b64_json"
  }'
```

### Test via Web UI

Visit: `https://local-ai.server.unarmedpuppy.com`

1. Select a text model: `/model qwen2.5-14b-awq`
2. Send a text prompt
3. Switch to image model: `/model qwen-image-edit`
4. Upload an image (Ctrl+U) or generate from prompt
5. Enter edit prompt for image editing

## Troubleshooting

### Image Server Build Fails

**Issue**: Docker build fails for image-inference-server

**Solution**:
1. Check Docker Desktop is running
2. Verify GPU support: `docker run --rm --gpus all nvidia/cuda:12.1.0-base-ubuntu22.04 nvidia-smi`
3. Check disk space: `docker system df`
4. Try building manually:
   ```powershell
   cd local-ai/image-inference-server
   docker build -t image-inference-server:latest .
   ```

### Image Model Container Not Created

**Issue**: Setup script doesn't create qwen-image-server container

**Solution**:
1. Build image first: `.\build-image-server.ps1`
2. Create container manually:
   ```powershell
   docker create --name qwen-image-server --gpus all -p 8005:8000 `
     -v ${PWD}/models:/models -v ${PWD}/cache:/root/.cache/hf `
     -e MODEL_NAME=Qwen/Qwen-Image-Edit-2509 `
     -e HF_TOKEN=your_token_here `
     --network my-network `
     image-inference-server:latest
   ```

### Image Model Not Loading

**Issue**: Image model container starts but model doesn't load

**Solution**:
1. Check container logs: `docker logs qwen-image-server --follow`
2. Verify GPU available: `nvidia-smi`
3. Check HuggingFace token is valid
4. Verify model name is correct: `Qwen/Qwen-Image-Edit-2509`
5. Check disk space for model download

### Manager Can't Find Image Model

**Issue**: Manager doesn't recognize image model

**Solution**:
1. Verify `models.json` has correct entry:
   ```json
   {
     "qwen-image-edit": {
       "container": "qwen-image-server",
       "port": 8005,
       "type": "image"
     }
   }
   ```
2. Restart manager: `docker compose restart manager`
3. Check manager logs: `docker logs vllm-manager --follow`

## Performance Optimization

### GPU Memory

- Text models: ~8-14GB VRAM each
- Image models: ~12-16GB VRAM
- Total recommended: 24GB+ VRAM

### Model Loading

- First load: 5-15 minutes (model download + loading)
- Subsequent loads: 1-5 minutes (from cache)
- Use on-demand loading to save memory

### Container Management

- Models auto-stop after 10 minutes idle
- Manager handles start/stop automatically
- Monitor with: `docker ps` and `docker stats`

## Next Steps

1. **Test all models** - Use test-multimodal.ps1
2. **Run full test suite** - See TESTING.md
3. **Monitor performance** - Check GPU usage, response times
4. **Optimize if needed** - Adjust GPU memory, batch sizes

## Support

- **Documentation**: See `local-ai/README.md` and `local-ai/TESTING.md`
- **Troubleshooting**: See `local-ai/TROUBLESHOOTING.md`
- **Research**: See `local-ai/RESEARCH_IMAGE_INFERENCE.md`

