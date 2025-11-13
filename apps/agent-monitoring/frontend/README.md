# Agent Monitoring Frontend

Next.js 14+ dashboard for monitoring AI agent activity.

## Features

- Real-time agent status overview
- Agent detail pages with stats and history
- Activity feed with auto-refresh
- System statistics dashboard
- Modern UI with Tailwind CSS

## Development

### Setup

```bash
# Install dependencies
npm install

# Copy environment file
cp .env.local.example .env.local

# Edit .env.local with your backend URL
```

### Run

```bash
# Development server
npm run dev

# Build for production
npm run build
npm start
```

### Environment Variables

- `NEXT_PUBLIC_API_URL` - Backend API URL (default: http://localhost:3001)

## Project Structure

```
src/
├── app/                    # Next.js App Router
│   ├── page.tsx            # Main dashboard
│   ├── agents/[id]/        # Agent detail pages
│   └── layout.tsx          # Root layout
├── components/             # React components
│   ├── AgentCard.tsx       # Agent card component
│   ├── ActivityFeed.tsx    # Activity feed component
│   └── StatsCards.tsx      # Statistics cards
├── lib/                    # Utilities
│   └── api.ts              # API client
└── types/                  # TypeScript types
    └── index.ts            # Type definitions
```

## Pages

- `/` - Main dashboard with agent overview and activity feed
- `/agents/[id]` - Individual agent detail page

## Features

- **Server-Side Rendering**: Fast initial load with Next.js SSR
- **Auto-Refresh**: Activity feed refreshes every 5 seconds
- **Responsive Design**: Works on mobile, tablet, and desktop
- **Type Safety**: Full TypeScript support

---

**Status**: Phase 3 Implementation
