# Local AI Dashboard UI

**Status**: Complete - Testing Deployment
**Created**: 2025-12-28
**Implemented**: 2025-12-28
**Related**: [Memory & Metrics System](memory-metrics-system.md)

## Vision

A beautiful, responsive web dashboard for visualizing Local AI Router usage metrics and exploring conversation history. OpenCode Wrapped style with GitHub activity charts, model usage breakdowns, and conversation search.

## Goals

- **Metrics Visualization** - Activity heatmaps, model distribution, token usage trends
- **Conversation Explorer** - Search, browse, and view full conversation history
- **RAG Testing** - Interactive semantic search playground
- **Real-time Updates** - Live metrics as requests flow through the router
- **Minimal Dependencies** - Lightweight, fast-loading, works on mobile

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     Dashboard UI (React)                     │
│  • Activity Chart (GitHub-style heatmap)                    │
│  • Model Usage Pie Chart                                    │
│  • Conversation Explorer                                    │
│  • RAG Search Playground                                    │
│  • Real-time Stats Widget                                   │
└────────────────────────┬────────────────────────────────────┘
                         │
                         │ HTTP/JSON API
                         ▼
┌─────────────────────────────────────────────────────────────┐
│              Local AI Router API                             │
│  • /metrics/dashboard - Dashboard stats                     │
│  • /metrics/activity - Activity chart data                  │
│  • /memory/conversations - Conversation list                │
│  • /rag/search - Semantic search                            │
└─────────────────────────────────────────────────────────────┘
```

## Tech Stack

### Option 1: React + Vite (Recommended)
- **Framework**: React with TypeScript
- **Build**: Vite (fast, modern)
- **Charts**: Recharts or Chart.js
- **Styling**: Tailwind CSS
- **State**: React Query for API calls
- **Deployment**: Static build served by Traefik

**Pros**:
- Modern, fast development
- Great component ecosystem
- Easy to deploy as static files
- TypeScript for type safety

**Cons**:
- Requires Node.js build step
- Larger bundle size

### Option 2: Vanilla JS + Alpine.js (Lightweight)
- **Framework**: Alpine.js (minimal, Vue-like)
- **Charts**: Lightweight chart library
- **Styling**: Tailwind CSS (CDN)
- **No Build**: Direct HTML/JS/CSS

**Pros**:
- Extremely lightweight
- No build step required
- Faster initial load
- Easier to modify

**Cons**:
- Less structured for large apps
- Fewer pre-built components

### Recommendation: **React + Vite**
Better developer experience, TypeScript safety, and rich ecosystem outweigh the slightly larger bundle size.

## Implementation Phases

### Phase 1: Project Setup ✅
- [x] Create `apps/local-ai-dashboard/` directory
- [x] Initialize Vite + React + TypeScript project
- [x] Set up Tailwind CSS (v4 with @tailwindcss/postcss)
- [x] Configure API client (axios with React Query)
- [x] Set up Docker Compose service
- [x] Add Traefik labels for routing

**Tech Decisions**:
- Vite for fast HMR and optimized builds
- TypeScript for API contract safety
- Recharts for declarative charts
- React Query for caching and real-time updates

### Phase 2: Dashboard Stats Page ✅
- [x] Fetch `/metrics/dashboard` data
- [x] Display key metrics cards:
  - Total Requests
  - Total Tokens
  - Success Rate
  - Average Duration
- [x] Activity heatmap (GitHub-style)
  - 90-day grid with week columns
  - Color intensity by request count
  - Hover tooltips with date + count
- [x] Model usage pie chart
  - Breakdown by model with Recharts
  - Legend with labels
  - Interactive tooltips
- [x] Backend distribution pie chart
- [x] Daily request and token usage bar charts

**Design Inspiration**: GitHub profile, OpenCode Wrapped, Vercel analytics

### Phase 3: Conversation Explorer ✅
- [x] List view of conversations
  - Pagination (100 limit)
  - Shows message count and created date
  - Click to view details
- [x] Conversation detail view
  - Full message history
  - Message roles (user/assistant/system) with color coding
  - Token counts per message
  - Timestamps
  - Model and backend metadata
- [x] Search conversations
  - Full-text search input
  - Live search with React Query
  - Debounced search (triggers at 3+ chars)

### Phase 4: RAG Playground ✅
- [x] Interactive semantic search
  - Query textarea input
  - Similarity threshold slider (0.0 - 1.0, default 0.3)
  - Max results slider (1-20, default 5)
- [x] Display search results
  - Conversation snippets with sample messages
  - Similarity scores (percentage display)
  - Conversation metadata (created date, message count)
- [x] Context preview
  - Separate "Get Context" button
  - Shows formatted context string for LLM injection
  - Displayed in monospace pre block

### Phase 5: Real-time Updates ✅ (Polling)
- [x] React Query polling every 60s for dashboard
- [x] Stale time 30s for all queries
- [x] Auto-refresh on window focus
- [ ] WebSocket connection (future enhancement)
- [ ] Live stats widget (using polling currently)

### Phase 6: Deployment & Polish ✅
- [x] Docker multi-stage build (Node builder + Nginx)
- [x] Add loading states (React Query isLoading)
- [x] Error handling (error boundaries and displays)
- [x] Mobile responsive design (Tailwind responsive classes)
- [x] Dark mode support (Tailwind dark: classes)
- [x] Docker build configuration (Dockerfile + nginx.conf)
- [x] Traefik routing configuration (HTTPS + redirect)
- [x] Production build optimized
- [ ] Bundle size optimization (future: code splitting)
- [ ] Dark mode toggle UI (uses system preference currently)

## File Structure

```
apps/local-ai-dashboard/
├── Dockerfile
├── docker-compose.yml
├── package.json
├── tsconfig.json
├── vite.config.ts
├── tailwind.config.js
├── index.html
└── src/
    ├── main.tsx
    ├── App.tsx
    ├── api/
    │   └── client.ts          # API wrapper
    ├── components/
    │   ├── DashboardStats.tsx  # Main dashboard
    │   ├── ActivityChart.tsx   # Heatmap
    │   ├── ModelUsageChart.tsx # Pie chart
    │   ├── ConversationList.tsx
    │   ├── ConversationDetail.tsx
    │   └── RAGPlayground.tsx
    ├── hooks/
    │   └── useMetrics.ts       # React Query hooks
    ├── types/
    │   └── api.ts              # TypeScript types
    └── utils/
        └── formatting.ts       # Date/number formatting
```

## API Contracts (TypeScript)

```typescript
// Dashboard Stats
interface DashboardStats {
  started_date: string;
  days_active: number;
  most_active_day: string;
  most_active_day_count: number;
  activity_chart: ActivityDay[];
  top_models: ModelUsage[];
  providers_used: Record<string, number>;
  total_sessions: number;
  total_messages: number;
  total_tokens: number;
  unique_projects: number;
  longest_streak: number;
  cost_savings: number | null;
}

interface ActivityDay {
  date: string;
  count: number;
  level: number; // 0-4 for color intensity
}

interface ModelUsage {
  model: string;
  count: number;
  percentage: number;
  total_tokens: number;
}

// Conversations
interface Conversation {
  id: string;
  created_at: string;
  updated_at: string;
  session_id?: string;
  user_id?: string;
  project?: string;
  title?: string;
  metadata?: any;
  message_count: number;
  total_tokens: number;
}

interface Message {
  id: number;
  conversation_id: string;
  timestamp: string;
  role: "user" | "assistant" | "system" | "tool";
  content: string;
  model_used?: string;
  backend?: string;
  tokens_prompt?: number;
  tokens_completion?: number;
}

// RAG
interface RAGSearchResult {
  query: string;
  results: Array<{
    conversation_id: string;
    similarity_score: number;
  }>;
}

interface RAGContext {
  query: string;
  context: Array<{
    conversation_id: string;
    similarity_score: number;
    text: string;
    message_count: number;
  }>;
}
```

## Docker Configuration

### docker-compose.yml
```yaml
x-enabled: true

services:
  local-ai-dashboard:
    build: .
    image: harbor.server.unarmedpuppy.com/library/local-ai-dashboard:latest
    container_name: local-ai-dashboard
    restart: unless-stopped
    environment:
      - TZ=America/Chicago
      - VITE_API_URL=https://local-ai-api.server.unarmedpuppy.com
    networks:
      - my-network
    labels:
      - "traefik.enable=true"
      # HTTPS redirect
      - "traefik.http.middlewares.dashboard-redirect.redirectscheme.scheme=https"
      - "traefik.http.routers.dashboard-redirect.middlewares=dashboard-redirect"
      - "traefik.http.routers.dashboard-redirect.rule=Host(`ai-dashboard.server.unarmedpuppy.com`)"
      - "traefik.http.routers.dashboard-redirect.entrypoints=web"
      # Main router
      - "traefik.http.routers.dashboard.rule=Host(`ai-dashboard.server.unarmedpuppy.com`)"
      - "traefik.http.routers.dashboard.entrypoints=websecure"
      - "traefik.http.routers.dashboard.tls.certresolver=myresolver"
      - "traefik.http.services.dashboard.loadbalancer.server.port=80"
      # Homepage labels
      - "homepage.group=AI"
      - "homepage.name=AI Dashboard"
      - "homepage.icon=mdi-chart-box"
      - "homepage.href=https://ai-dashboard.server.unarmedpuppy.com"
      - "homepage.description=Local AI usage metrics and conversation explorer"

networks:
  my-network:
    external: true
```

### Dockerfile
```dockerfile
FROM node:20-alpine AS builder

WORKDIR /app

COPY package*.json ./
RUN npm ci

COPY . .
RUN npm run build

FROM nginx:alpine

COPY --from=builder /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
```

### nginx.conf
```nginx
server {
    listen 80;
    server_name _;

    root /usr/share/nginx/html;
    index index.html;

    location / {
        try_files $uri $uri/ /index.html;
    }

    # API proxy (if needed)
    location /api/ {
        proxy_pass https://local-ai-api.server.unarmedpuppy.com/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    # Caching for static assets
    location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg|woff|woff2|ttf|eot)$ {
        expires 1y;
        add_header Cache-Control "public, immutable";
    }
}
```

## Design Mockup

```
┌─────────────────────────────────────────────────────────────────┐
│  🤖 Local AI Dashboard                          [Dark Mode 🌙]  │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌────────────┐│
│  │ Days Active │ │   Messages  │ │   Tokens    │ │   Streak   ││
│  │     12      │ │    1,234    │ │  567.8K     │ │     7d     ││
│  └─────────────┘ └─────────────┘ └─────────────┘ └────────────┘│
│                                                                  │
│  ┌─────────────────────────────────────────────────────────────┐│
│  │            Activity Chart (Last 365 Days)                   ││
│  │  [GitHub-style heatmap grid showing daily activity]        ││
│  │  Jan  Feb  Mar  Apr  May  Jun  Jul  Aug  Sep  Oct  Nov  Dec││
│  │  ████ ████ ████ ████ ████ ████ ████ ████ ████ ████ ████ █████
│  │  Legend: □ None  ■ 1-5  ■ 6-15  ■ 16-30  ■ 31+              ││
│  └─────────────────────────────────────────────────────────────┘│
│                                                                  │
│  ┌────────────────────────┐ ┌──────────────────────────────────┐│
│  │   Model Usage          │ │  Provider Distribution           ││
│  │   [Pie chart showing   │ │  Local: 72%  ██████████████░░░░  ││
│  │    model percentages]  │ │  OpenCode: 28%  █████░░░░░░░░░░  ││
│  └────────────────────────┘ └──────────────────────────────────┘│
│                                                                  │
│  [Conversations] [RAG Playground]                               │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

## Key Features

### 1. Activity Heatmap
- 365-day grid (52 weeks × 7 days)
- Color intensity: 0 (gray) → 4 (dark green)
- Hover tooltip: "Dec 28, 2025: 15 requests"
- Click to filter metrics by date

### 2. Model Usage Breakdown
- Pie chart with percentages
- Top 5 models shown
- "Other" category for remaining
- Click to view detailed stats

### 3. Conversation Explorer
- Table view with columns:
  - ID (truncated)
  - Created
  - Messages
  - Tokens
  - User/Project (if set)
- Click row to open detail modal
- Full message history with syntax highlighting

### 4. RAG Playground
- Query input with examples
- Adjustable similarity threshold
- Real-time search results
- Preview of context injection

## Performance Considerations

- **Code Splitting**: Lazy load conversation detail views
- **Pagination**: Limit API results (50 per page)
- **Caching**: React Query with 5-minute stale time
- **Optimistic Updates**: Instant UI feedback
- **Debouncing**: Search input (300ms delay)

## Security

- **CORS**: Configure Local AI Router to allow dashboard origin
- **Authentication**: Future phase (basic auth or OAuth)
- **Rate Limiting**: Protect API endpoints from abuse

## Future Enhancements

- **Export**: Download metrics as CSV/JSON
- **Alerts**: Email notifications for errors or high usage
- **Comparisons**: Week-over-week, month-over-month trends
- **Custom Dashboards**: Save user preferences
- **Conversation Editing**: Manually add/edit conversations
- **Embedding Visualization**: t-SNE plot of conversation clusters

## Success Criteria

- ✅ Dashboard loads in < 2 seconds
- ✅ Activity chart renders 365 days smoothly
- ✅ Conversations searchable in < 1 second
- ✅ Mobile responsive (works on phone)
- ✅ Works offline (after initial load)
- ✅ Zero data loss (all metrics preserved)

## References

- [Recharts Documentation](https://recharts.org/)
- [React Query](https://tanstack.com/query/latest)
- [Tailwind CSS](https://tailwindcss.com/)
- [Vite Guide](https://vitejs.dev/guide/)
- [GitHub Activity Heatmap](https://github.com/grubersjoe/react-github-calendar)

---

**Next Steps**: Start with Phase 1 (project setup) once approved.
