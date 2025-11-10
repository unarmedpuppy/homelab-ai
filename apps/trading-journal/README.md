# Trading Journal Application

A self-hosted trading journal application inspired by Tradezella, designed for personal use. Track trades, visualize performance, and analyze your trading activity through a comprehensive web interface.

## 📚 Documentation

Before starting work on this project, read these documents in order:

1. **`STARTUP_GUIDE.md`** - Essential formulas, API keys, setup details
2. **`IMPLEMENTATION_PLAN.md`** - Complete feature specification and architecture
3. **`TRADING_JOURNAL_AGENTS_PROMPT.md`** - Guidelines for agents implementing features
4. **`TRADING_JOURNAL_AGENT_REVIEWER_PROMPT.md`** - Standards for code reviewers
5. **`TASKS.md`** - Task tracking and status

## 🚀 Quick Start (For Agents)

1. **Read the documentation** (see above)
2. **Check `TASKS.md`** for available tasks
3. **Claim a task** by updating status in `TASKS.md`
4. **Follow the task details** in `TRADING_JOURNAL_AGENTS_PROMPT.md`
5. **Complete Pre-Submission Checklist** before marking as `[REVIEW]`
6. **Wait for review** and address feedback

## 🎯 Current Status

**Project Status**: Foundation Setup In Progress

**Next Steps**:
- [x] T1.1: Project Structure Setup (COMPLETED)
- [x] T1.2: Docker Compose Configuration (COMPLETED)
- [x] T1.3: PostgreSQL Database Setup (COMPLETED)
- [x] T1.4: FastAPI Backend Foundation (COMPLETED)
- [x] T1.5: SQLAlchemy Models (COMPLETED)
- [x] T1.6: Pydantic Schemas (COMPLETED)
- [x] T1.7: Trade CRUD API Endpoints (COMPLETED)
- [x] T1.8: React Frontend Foundation (COMPLETED)
- [x] T1.9: Basic Trade Entry Form (COMPLETED)
- [ ] ... (see `TASKS.md` for full list)

## 📋 Features (MVP)

- ⏳ Trade entry and management (all trade types)
- ⏳ Dashboard with KPIs and charts
- ⏳ Calendar view with daily P&L
- ⏳ Daily journal with trade details
- ⏳ Price charts with trade overlays
- ⏳ Comprehensive REST API
- ⏳ Responsive mobile design

## 🛠️ Technology Stack

- **Backend**: FastAPI (Python), PostgreSQL, SQLAlchemy
- **Frontend**: React, TypeScript, Vite, Material-UI
- **Charts**: TradingView Lightweight Charts, Recharts
- **Infrastructure**: Docker Compose

## 📝 Project Structure

```
apps/trading-journal/
├── STARTUP_GUIDE.md              # Essential startup information
├── IMPLEMENTATION_PLAN.md         # Complete implementation plan
├── TRADING_JOURNAL_AGENTS_PROMPT.md      # Agent guidelines
├── TRADING_JOURNAL_AGENT_REVIEWER_PROMPT.md  # Reviewer standards
├── TASKS.md                       # Task tracking
├── README.md                      # This file
├── docker-compose.yml             # Docker configuration
├── env.template                   # Environment variables template
├── backend/                       # FastAPI backend
└── frontend/                      # React frontend
```

## 🔑 Required Setup

1. **API Keys** (see `STARTUP_GUIDE.md` for details):
   - Alpha Vantage API key (free tier available)
   - CoinGecko API key (optional, free tier available)
   - Polygon.io API key (optional, for options data)

2. **Environment Variables**:
   - Copy `env.template` to `.env`
   - Generate API key: `openssl rand -hex 32`
   - Generate database password: `openssl rand -hex 32`
   - Add your API keys

3. **Docker Setup**:
   - Ensure Docker and Docker Compose are installed
   - Network `my-network` must exist (created by other apps)

## 🧪 Testing

After setup, test the application:

```bash
# Start services
docker compose up -d --build

# Check status
docker compose ps

# View logs
docker compose logs -f backend
docker compose logs -f frontend

# Test API
curl http://localhost:8100/api/health
```

## 📖 For More Information

- **Setup Details**: See `STARTUP_GUIDE.md`
- **Architecture**: See `IMPLEMENTATION_PLAN.md`
- **Development Guidelines**: See `TRADING_JOURNAL_AGENTS_PROMPT.md`
- **Code Review Standards**: See `TRADING_JOURNAL_AGENT_REVIEWER_PROMPT.md`

---

**Status**: Ready for implementation
**Last Updated**: Based on planning phase completion

