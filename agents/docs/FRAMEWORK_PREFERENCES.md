# Framework Preferences for Agent Development

## Overview

This document defines the preferred technology stack and frameworks for all agent-developed applications and services in the home server project.

## Preferred Technology Stack

### Frontend
- **Framework**: Next.js (React-based)
- **Language**: TypeScript
- **Styling**: Tailwind CSS (preferred) or CSS Modules
- **State Management**: React Context API or Zustand (for complex state)
- **Data Fetching**: Next.js built-in fetch or React Query (TanStack Query)
- **UI Components**: shadcn/ui (preferred) or Headless UI

### Backend
- **Runtime**: Node.js
- **Language**: TypeScript
- **Framework**: Express.js (for REST APIs) or Next.js API Routes
- **Database**: 
  - SQLite (for simple apps, like agent monitoring)
  - PostgreSQL (for complex apps with relationships)
- **ORM**: Prisma (preferred) or Drizzle ORM
- **Validation**: Zod

### Infrastructure
- **Containerization**: Docker + Docker Compose
- **Reverse Proxy**: Traefik (already configured)
- **Monitoring**: Grafana + InfluxDB (for time-series data)
- **Service Discovery**: Homepage integration

## When to Use This Stack

**Use Next.js/TypeScript + Node.js for:**
- New web applications
- Dashboards and monitoring tools
- Agent activity dashboards
- Any new frontend/backend services

**Exceptions (Use Existing Stack):**
- Python services that integrate with existing Python codebases
- Services that require specific Python libraries
- MCP servers (Python-based, already established)

## Project Structure Template

```
project-name/
├── docker-compose.yml
├── .env.example
├── README.md
│
├── backend/                    # Node.js backend (if separate)
│   ├── package.json
│   ├── tsconfig.json
│   ├── src/
│   │   ├── index.ts            # Express app entry
│   │   ├── routes/             # API routes
│   │   ├── services/           # Business logic
│   │   ├── models/             # Data models
│   │   └── utils/              # Utilities
│   └── Dockerfile
│
├── frontend/                    # Next.js frontend
│   ├── package.json
│   ├── tsconfig.json
│   ├── next.config.js
│   ├── tailwind.config.js
│   ├── src/
│   │   ├── app/                # Next.js App Router
│   │   │   ├── layout.tsx
│   │   │   ├── page.tsx
│   │   │   └── api/            # API routes (if using Next.js API)
│   │   ├── components/          # React components
│   │   ├── lib/                 # Utilities, API clients
│   │   ├── types/               # TypeScript types
│   │   └── hooks/               # Custom React hooks
│   └── Dockerfile
│
└── docker-compose.yml           # Orchestration
```

## Example: Next.js + Node.js Setup

### Backend (Express + TypeScript)

```typescript
// backend/src/index.ts
import express from 'express';
import cors from 'cors';

const app = express();
app.use(cors());
app.use(express.json());

app.get('/api/health', (req, res) => {
  res.json({ status: 'ok' });
});

const PORT = process.env.PORT || 3001;
app.listen(PORT, () => {
  console.log(`Server running on port ${PORT}`);
});
```

### Frontend (Next.js + TypeScript)

```typescript
// frontend/src/app/page.tsx
export default function HomePage() {
  return (
    <div className="container mx-auto p-4">
      <h1 className="text-2xl font-bold">Dashboard</h1>
    </div>
  );
}
```

## Integration with Existing Infrastructure

### Grafana Integration
- Export metrics to InfluxDB
- Create Grafana dashboards for visualization
- Use InfluxDB line protocol for time-series data

### Homepage Integration
- Add service link to Homepage config
- Use Traefik labels for routing
- Follow existing service patterns

### Docker Compose Pattern

```yaml
version: "3.8"
services:
  backend:
    build: ./backend
    environment:
      - DATABASE_URL=${DATABASE_URL}
    ports:
      - "3001:3001"
    networks:
      - my-network

  frontend:
    build: ./frontend
    environment:
      - NEXT_PUBLIC_API_URL=http://backend:3001
    ports:
      - "3002:3000"
    depends_on:
      - backend
    networks:
      - my-network

networks:
  my-network:
    external: true
```

## Development Guidelines

1. **TypeScript First**: Always use TypeScript, avoid `any` types
2. **Type Safety**: Define types for all API responses and data structures
3. **Error Handling**: Use proper error boundaries and try-catch blocks
4. **Code Organization**: Follow Next.js App Router conventions
5. **API Design**: RESTful APIs with clear endpoints
6. **Documentation**: Document API endpoints and component props
7. **Testing**: Write unit tests for critical logic (Jest + React Testing Library)

## References

- **Next.js Docs**: https://nextjs.org/docs
- **TypeScript Docs**: https://www.typescriptlang.org/docs/
- **Prisma Docs**: https://www.prisma.io/docs
- **Tailwind CSS**: https://tailwindcss.com/docs
- **shadcn/ui**: https://ui.shadcn.com/

---

**Status**: Active
**Last Updated**: 2025-01-13
**Applies To**: All new agent-developed applications

