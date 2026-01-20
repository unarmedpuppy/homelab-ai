# Local AI Dashboard

A retro/pixel-art "command center" React dashboard for AI infrastructure management, task tracking, and conversation exploration.

## Features

### Chat Interface (`/`, `/chat/:conversationId`)
- Streaming chat with provider selection
- TTS toggle for auto-play text-to-speech
- Image upload for multimodal conversations
- Conversation history sidebar

### Ralph Loop Management (`/ralph`)
- View current Ralph-Wiggum loop status and progress
- Start new loops with label filter and priority options
- Stop running loops
- Execution log viewer with auto-refresh

### Provider Monitoring (`/providers`)
- Real-time provider health status
- Utilization metrics and progress bars
- Provider configuration details

### Stats Dashboard (`/stats`)
- Activity heatmap visualization
- Model usage charts
- Performance statistics

### Agent Runs (`/agents`)
- Agent execution history
- Run logs and status tracking

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

# Type checking
npm run typecheck

# Linting
npm run lint
```

### Mobile Testing

For testing mobile layouts during development:

1. Open browser DevTools (F12)
2. Toggle device toolbar (Ctrl+Shift+M)
3. Select a mobile device preset or enter custom dimensions

Breakpoints:
- Mobile: < 640px (single column, bottom nav, hamburger menu)
- Tablet: 640px - 1023px (collapsible sidebar)
- Desktop: >= 1024px (persistent sidebar)

## Docker Deployment

```bash
# Build and run with Docker Compose
docker compose up -d

# The dashboard will be available at:
# https://local-ai-dashboard.server.unarmedpuppy.com
```

## Configuration

### Environment Variables

```env
# Local AI Router API URL
VITE_API_URL=http://localhost:8012

# Claude Harness API URL (for Ralph endpoints)
VITE_CLAUDE_HARNESS_URL=http://localhost:8013
```

For Docker deployment:
- API is accessed via internal network at `http://local-ai-router:8000`
- Claude Harness at `http://claude-harness:8000`

### TTS Configuration

TTS is proxied through the Local AI Router. No additional configuration needed.

**How TTS works:**
1. Enable TTS via the toggle button in the chat header
2. After each assistant response, TTS request goes through Local AI Router
3. Router proxies to Gaming PC for Chatterbox Turbo generation
4. Audio auto-plays in the browser

## API Integration

The dashboard consumes the following API endpoints:

### From Local AI Router
- `/memory/*` - Conversation history and search
- `/metrics/*` - Usage statistics and analytics
- `/rag/*` - Semantic search and RAG context retrieval

### From Claude Harness
- `/v1/ralph/status` - Ralph loop status
- `/v1/ralph/start` - Start new Ralph loop
- `/v1/ralph/stop` - Stop running loop
- `/v1/ralph/logs` - Execution logs

See [LLM Router Documentation](../llm-router/README.md) for complete endpoint details.

## Component Library

The dashboard uses a custom "Retro Design System" with pixel-art styling. Components are located in `src/components/ui/`.

See [Component Documentation](./src/components/ui/README.md) for usage details.

## Project Structure

```
src/
├── components/
│   ├── ui/              # Retro design system components
│   ├── ralph/           # Ralph management components
│   └── ...              # Feature components
├── hooks/               # Custom React hooks
├── api/                 # API client and types
├── styles/
│   └── retro-theme.css  # CSS custom properties
├── types/               # TypeScript type definitions
└── App.tsx              # Main application with routing
```
