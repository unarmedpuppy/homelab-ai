# Local AI Dashboard

A modern React dashboard for visualizing Local AI Router metrics, conversations, and RAG search capabilities.

## Features

- **Dashboard View**: Real-time metrics with activity heatmap, model usage charts, and performance stats
- **Conversation Explorer**: Browse and search through conversation history with full message details
- **RAG Playground**: Interactive semantic search to find similar conversations and retrieve context
- **Chat Interface**: Send messages with streaming responses and provider selection
- **TTS Toggle**: Auto-play text-to-speech for assistant responses (when enabled)
- **Image Upload**: Multimodal chat with image attachments

## Tech Stack

- React + TypeScript
- Vite
- Tailwind CSS
- Recharts (data visualization)
- React Query (data fetching & caching)
- Axios (API client)

## Development

```bash
# Install dependencies
npm install

# Run dev server
npm run dev

# Build for production
npm run build
```

## Docker Deployment

```bash
# Build and run with Docker Compose
docker compose up -d

# The dashboard will be available at:
# https://local-ai-dashboard.server.unarmedpuppy.com
```

## Configuration

The dashboard connects to the Local AI Router API. Configure the API URL:

```env
VITE_API_URL=http://localhost:8012
```

For Docker deployment, the API is accessed via the internal network at `http://local-ai-router:8000`.

### TTS Configuration

TTS is now proxied through the Local AI Router for unified access. The router handles routing to the Gaming PC's local-ai manager.

No additional configuration needed - TTS uses the same API key and endpoint as the main chat functionality.

**How TTS works:**
1. Enable TTS via the 🔊 toggle button in the chat header
2. After each assistant response, TTS request goes through Local AI Router
3. Router proxies to Gaming PC for Chatterbox Turbo generation
4. Audio auto-plays in the browser
5. Memory is freed after playback (Blob URL revoked)

**TTS availability:** The toggle appears if the Local AI Router is healthy and reachable.

## API Integration

The dashboard consumes the following API endpoints from the Local AI Router:

- `/memory/*` - Conversation history and search
- `/metrics/*` - Usage statistics and analytics
- `/rag/*` - Semantic search and RAG context retrieval

See [API Documentation](../local-ai-router/README.md) for complete endpoint details.
