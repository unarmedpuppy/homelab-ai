# Local AI Troubleshooting Guide

## Model Container Fails to Start

### Issue: Llama Model - Gated Repository Error

**Symptoms:**
- Model container exits immediately with error code 1
- Error message: `GatedRepoError: 403 Client Error. Cannot access gated repo`
- Error: `Access to model meta-llama/Llama-3.1-8B-Instruct is restricted`

**Cause:**
The Llama model is a gated model on HuggingFace and requires you to accept the model's terms of use.

**Solution:**

1. **Visit the model page on HuggingFace:**
   - Go to: https://huggingface.co/meta-llama/Llama-3.1-8B-Instruct
   - Sign in with your HuggingFace account (or create one if needed)

2. **Accept the model's terms:**
   - Click "Agree and access repository"
   - Accept the terms of use

3. **Verify your token has access:**
   - Your HF_TOKEN in `setup.sh` should be valid
   - The token should be associated with the account that accepted the terms

4. **Restart the model container:**
   ```powershell
   # Remove the failed container
   docker rm vllm-llama3-8b
   
   # Recreate it (will use the same setup.sh)
   cd local-ai
   bash setup.sh
   
   # Or manually recreate just the Llama container
   docker create --name vllm-llama3-8b --gpus all -p 8001:8000 \
     -v $(pwd)/models:/models -v $(pwd)/cache:/root/.cache/hf \
     -e HF_TOKEN=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 \
     vllm/vllm-openai:v0.6.3 \
     --model meta-llama/Llama-3.1-8B-Instruct \
     --served-model-name llama3-8b \
     --download-dir /models --dtype auto \
     --max-model-len 8192 --gpu-memory-utilization 0.90
   ```

5. **Test the model:**
   ```powershell
   # The manager will start it automatically on first request
   # Or manually start it to test
   docker start vllm-llama3-8b
   docker logs vllm-llama3-8b --follow
   ```

### Alternative: Use Non-Gated Models

If you don't want to deal with gated models, you can use the Qwen model instead:

1. **Switch to Qwen model in the web interface:**
   - Use command: `/model qwen2.5-14b-awq`

2. **Or use Qwen via API:**
   ```bash
   curl -X POST http://local-ai.server.unarmedpuppy.com/v1/chat/completions \
     -H "Content-Type: application/json" \
     -d '{
       "model": "qwen2.5-14b-awq",
       "messages": [{"role": "user", "content": "Hello!"}],
       "max_tokens": 100
     }'
   ```

## Model Takes Too Long to Start

**Symptoms:**
- Error: "backend not ready" or "503 Service Unavailable"
- Model container is starting but not ready yet

**Cause:**
- First-time model download (can take 10-30 minutes depending on model size)
- Model loading into GPU memory (can take 1-5 minutes)

**Solution:**
- Wait 30-60 seconds and try again
- Check container logs: `docker logs vllm-llama3-8b --follow`
- Monitor GPU usage to see when model is loaded

## Manager Not Starting Models

**Symptoms:**
- Requests return 503 but no container starts
- Manager logs show errors

**Troubleshooting:**

1. **Check manager logs:**
   ```powershell
   docker logs vllm-manager --tail 50
   ```

2. **Verify model configuration:**
   ```powershell
   # Check models.json exists and is valid
   cat local-ai/models.json
   ```

3. **Check Docker network:**
   ```powershell
   docker network ls | findstr my-network
   # If missing, create it:
   docker network create my-network
   ```

4. **Restart manager:**
   ```powershell
   docker compose restart manager
   ```

## Connection Issues

### Server Can't Reach Windows Manager

**Symptoms:**
- Proxy returns "Cannot connect to Windows AI service"
- Health check fails

**Troubleshooting:**

1. **Check Windows firewall:**
   ```powershell
   Get-NetFirewallRule -DisplayName "*LLM*"
   ```

2. **Verify Windows IP:**
   ```powershell
   ipconfig | findstr IPv4
   # Should match WINDOWS_AI_HOST in apps/local-ai-app/docker-compose.yml
   ```

3. **Test connection from server:**
   ```bash
   ssh -p 4242 unarmedpuppy@192.168.86.47 "curl -v http://192.168.86.63:8000/healthz"
   ```

4. **Check manager is running:**
   ```powershell
   docker ps --filter name=vllm-manager
   ```

## General Debugging Commands

```powershell
# Check all containers
docker ps -a --filter name=vllm

# Check manager health
Invoke-WebRequest -Uri "http://localhost:8000/healthz" -UseBasicParsing

# View manager logs
docker logs vllm-manager --tail 50 --follow

# View model container logs
docker logs vllm-llama3-8b --tail 50

# Check GPU usage
nvidia-smi

# Verify setup
.\verify-setup.ps1
```

