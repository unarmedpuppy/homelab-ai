# Local AI App

This service acts as a proxy to call local AI models running on your Windows machine from your remote server. It provides a ChatGPT-like web interface and OpenAI-compatible API endpoints.

## Homepage Integration

The service is configured with homepage labels for easy access:
- **Group**: AI & ML
- **Name**: Local AI Chat  
- **Icon**: OpenAI icon
- **Description**: ChatGPT-like interface for local LLM models

## Setup

### 1. Windows Machine Setup

First, set up the local AI service on your Windows machine:

1. Navigate to the `local-ai` directory in this repository
2. Run the setup script:
   ```bash
   cd local-ai
   chmod +x setup.sh
   ./setup.sh
   ```

This will:
- Create Docker containers for the AI models (Llama 3.1 8B, Qwen 2.5 14B AWQ, DeepSeek Coder)
- Start the manager service on port 8000
- Set up automatic model loading/unloading

### 2. Configure Windows Firewall

Allow port 8000 from your server's IP:
```powershell
New-NetFirewallRule -DisplayName "LLM Manager 8000" -Direction Inbound -Protocol TCP -LocalPort 8000 -RemoteAddress <SERVER_IP> -Action Allow
```

### 3. Deploy Proxy Service

Deploy this proxy service to your remote server:

1. Set environment variables in `docker-compose.yml`:
   ```yaml
   environment:
     - WINDOWS_AI_HOST=192.168.86.100  # Your Windows machine IP
     - WINDOWS_AI_PORT=8000            # Manager port on Windows
     - TIMEOUT=300                     # Request timeout
   ```

2. Start the service:
   ```bash
   docker compose up -d
   ```

The service will be available on:
- **External port**: 8067 (mapped to internal port 8000)
- **HTTPS**: `https://local-ai.server.unarmedpuppy.com` (with basic auth)
- **Local**: `http://local-ai.local.unarmedpuppy.com` (no auth required)

### Authentication

The service is protected with basic authentication when accessed via HTTPS:
- **Username**: `unarmedpuppy`
- **Password**: Same as your other services
- **Realm**: `Local AI Chat`

Local access via `local-ai.local.unarmedpuppy.com` bypasses authentication for convenience.

## Usage

### Web Chat Interface

Access the ChatGPT-like interface at: `https://local-ai.server.unarmedpuppy.com`

**Note**: You'll need to authenticate with your username and password when accessing via HTTPS.

Features:
- Modern, responsive chat interface
- Dynamic model selection from API
- Real-time connection status
- Typing indicators
- Message history
- **Image upload support for multimodal prompting**
- **Conversation saving and loading**
- Clear chat functionality
- Mobile-friendly design

### API Endpoints

- `GET /`: Web chat interface
- `GET /api/info`: Service information
- `GET /health`: Check service health
- `GET /v1/models`: List available models
- `GET /models/info`: Detailed model information
- `GET /usage/stats`: Usage statistics and model status
- `GET /model-status`: Lightweight model loading status
- `GET /docs`: API documentation
- `GET /status`: Comprehensive status information
- `POST /v1/chat/completions`: Chat completions
- `POST /v1/completions`: Text completions
- `POST /v1/images/generations`: Image generation

### Available Models

- `llama3-8b`: Llama 3.1 8B Instruct (best general quality)
- `qwen2.5-14b-awq`: Qwen 2.5 14B Instruct AWQ (stronger reasoning)
- `deepseek-coder`: DeepSeek Coder V2 Lite (coding-focused)
- `qwen-image-edit`: Qwen Image Edit 2509 (multimodal image editing)

### Example Usage

**Web Interface:**
Simply visit `https://local-ai.server.unarmedpuppy.com` in your browser to use the chat interface. You'll be prompted for authentication.

**New Features:**
- **Image Upload**: Click the 📷 button to upload images for multimodal prompting (works with Qwen Image Edit model)
- **Save Conversations**: Click the 💾 button to save your current conversation with a custom name
- **Load Conversations**: Click the 📁 button to view and load previously saved conversations
- **Dynamic Models**: Models are loaded automatically from the API endpoint
- **Model Status Indicator**: Real-time status showing if models are loaded and ready on the Windows GPU

**API Usage:**
```bash
# Check health
curl http://local-ai.server.unarmedpuppy.com/health

# List models
curl http://local-ai.server.unarmedpuppy.com/v1/models

# Get detailed model info
curl http://local-ai.server.unarmedpuppy.com/models/info

# Check usage stats
curl http://local-ai.server.unarmedpuppy.com/usage/stats

# Get API documentation
curl http://local-ai.server.unarmedpuppy.com/docs

# Check model loading status
curl http://local-ai.server.unarmedpuppy.com/model-status

# Chat completion
curl -X POST http://local-ai.server.unarmedpuppy.com/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "llama3-8b",
    "messages": [{"role": "user", "content": "Hello, how are you?"}],
    "max_tokens": 100
  }'
```

## Features

- **On-demand loading**: Models start only when requested
- **Auto-shutdown**: Models stop after idle timeout (10 minutes)
- **OpenAI compatibility**: Works with any OpenAI-compatible client
- **Health monitoring**: Built-in health checks
- **Error handling**: Proper error propagation and logging
- **CORS support**: Cross-origin requests enabled

## Troubleshooting

1. **Connection issues**: Check Windows firewall and IP address
2. **Model loading slow**: First request downloads the model (can take time)
3. **Timeout errors**: Increase TIMEOUT environment variable
4. **GPU issues**: Ensure Docker Desktop has GPU support enabled

## Security Notes

- The Windows AI service should only be accessible from your server
- Consider using VPN or secure network for production use
- Monitor logs for unusual activity
