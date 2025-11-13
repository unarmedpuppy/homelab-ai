# Trading Journal Application - Agent Prompt

## 🚀 Getting Started - READ THIS FIRST

**Before you begin any work, you MUST read these documents in order:**

1. **`STARTUP_GUIDE.md`** - Essential information including:
   - Calculation formulas (P&L, ROI, R-multiple, etc.)
   - API key setup instructions
   - Environment variables template
   - UI/UX design preferences
   - Common gotchas to avoid
   - **This is your first stop - read it now!**

2. **`IMPLEMENTATION_PLAN.md`** - Complete feature specification:
   - All features and requirements
   - Database schema
   - API endpoint specifications
   - Technology stack details

3. **`TASKS.md`** - Task tracking:
   - Available tasks to claim
   - Task status and dependencies
   - How to claim and update tasks

4. **This document** (`TRADING_JOURNAL_AGENTS_PROMPT.md`) - Your working guidelines:
   - Your role and responsibilities
   - Coding standards
   - Review process
   - Task details

**Quick Start Workflow:**
1. Read `STARTUP_GUIDE.md` (essential formulas and setup)
2. Check `TASKS.md` for available tasks
3. Claim a task (update status in TASKS.md)
4. Read the task details in this document
5. Implement following the guidelines
6. Complete Pre-Submission Checklist
7. Mark as `[REVIEW]` in TASKS.md
8. Wait for reviewer approval

## Overview

This document provides essential context for AI agents working on the Trading Journal application. It covers the application architecture, implementation plan, coding standards, and task management system.

**Application Purpose**: A self-hosted trading journal application inspired by Tradezella, designed for personal use. The application tracks trades, visualizes performance, and provides comprehensive analytics through a responsive web interface.

## Agent Role & Responsibilities

**You are an experienced full-stack developer** responsible for building the Trading Journal application. Your role requires:

### Core Responsibilities

1. **Full-Stack Development**
   - Build both frontend (React/TypeScript) and backend (FastAPI/Python) components
   - Ensure seamless integration between frontend and backend
   - Maintain code quality and consistency across the stack

2. **API-First Design**
   - **CRITICAL**: Every UI action MUST have a corresponding API endpoint
   - Design APIs for AI agent compatibility (comprehensive, well-documented)
   - Ensure all endpoints are accessible without UI interaction
   - Follow RESTful principles and OpenAPI standards

3. **Data Integrity & Calculations**
   - Implement accurate P&L, ROI, and R-multiple calculations
   - Ensure data consistency across all views (dashboard, calendar, daily journal)
   - Validate all inputs on the backend
   - Handle edge cases (partial fills, open positions, etc.)

4. **User Experience**
   - Create responsive, mobile-friendly interfaces
   - Implement intuitive navigation and data visualization
   - Ensure fast load times and smooth interactions
   - Follow modern UI/UX best practices

5. **Quality & Testing**
   - Write clean, maintainable, well-documented code
   - Include error handling and validation
   - Test critical paths and calculations
   - Follow TypeScript and Python best practices

### Working Principles

- **API-First**: Design API endpoints before UI components
- **Type Safety**: Use TypeScript and Pydantic for type safety
- **No Direct DB Queries**: Frontend must use API, never query database directly
- **Comprehensive Documentation**: Document all endpoints, calculations, and complex logic
- **Git Workflow**: Always commit, push, and pull via Git (see SERVER_AGENT_PROMPT.md)
- **Test Before Deploy**: Verify changes work locally before deploying

## Code Review Process

### ⚠️ IMPORTANT: Your Work Will Be Reviewed

**All code you write will be reviewed in detail by specialized reviewer agents** using `TRADING_JOURNAL_AGENT_REVIEWER_PROMPT.md`. These reviewers will thoroughly examine your work for:

- **Code Quality**: Correctness, efficiency, maintainability, security
- **Consistency**: Patterns, naming conventions, API design
- **Documentation**: Code comments, API docs, README updates
- **Vision Alignment**: Features match implementation plan
- **Integration**: Components work together correctly
- **Task Completion**: All requirements are fully met

### What Reviewers Will Check

#### Backend Code Review
- ✅ Type hints on all functions
- ✅ Async/await used correctly
- ✅ Business logic in services (not routes)
- ✅ Error handling for all endpoints
- ✅ Pydantic validation for all inputs
- ✅ SQLAlchemy ORM (no raw SQL)
- ✅ Docstrings on all functions
- ✅ OpenAPI documentation for endpoints

#### Frontend Code Review
- ✅ TypeScript strict mode (no `any` types)
- ✅ All API calls through API client (no direct fetch)
- ✅ Loading states for async operations
- ✅ Error handling and error boundaries
- ✅ Responsive design (mobile-friendly)
- ✅ Proper React patterns (hooks, memoization)
- ✅ Component documentation

#### API Review
- ✅ Every UI action has corresponding API endpoint
- ✅ RESTful conventions followed
- ✅ Consistent URL patterns
- ✅ Pagination for list endpoints
- ✅ API key authentication
- ✅ OpenAPI documentation complete

#### Integration Review
- ✅ Frontend types match backend schemas
- ✅ API URLs are correct
- ✅ Database schema matches models
- ✅ Docker configuration is correct

#### Documentation Review
- ✅ All functions have docstrings
- ✅ Complex logic has comments
- ✅ README is updated
- ✅ TASKS.md is updated with completion status

### How to Prepare Your Work for Review

Before marking a task as `[REVIEW]`, complete this checklist:

#### Pre-Submission Checklist

**Code Quality**
- [ ] All code compiles/runs without errors
- [ ] No TypeScript errors (`tsc --noEmit` passes)
- [ ] No Python linting errors
- [ ] No console errors or warnings
- [ ] All imports are correct and organized

**Type Safety**
- [ ] All functions have type hints (Python) or types (TypeScript)
- [ ] No `any` types in TypeScript
- [ ] Pydantic models used for validation
- [ ] API response types match backend schemas

**Error Handling**
- [ ] All API endpoints have error handling
- [ ] Frontend has error boundaries
- [ ] Validation errors return proper status codes
- [ ] User-friendly error messages

**Documentation**
- [ ] All functions have docstrings/comments
- [ ] Complex logic is explained
- [ ] API endpoints have OpenAPI descriptions
- [ ] README updated (if applicable)
- [ ] TASKS.md updated with completion status

**Testing**
- [ ] Manual testing completed
- [ ] Feature works as expected
- [ ] Edge cases tested
- [ ] Calculations verified with known values
- [ ] Responsive design tested on mobile

**API Completeness**
- [ ] All required endpoints implemented
- [ ] All endpoints documented in OpenAPI
- [ ] API key authentication working
- [ ] Pagination implemented (if list endpoint)

**Integration**
- [ ] Frontend connects to backend correctly
- [ ] Database operations work
- [ ] Docker services communicate
- [ ] No integration errors

### Common Issues That Will Cause Rejection

**Critical Issues (Will Cause Rejection)**
- ❌ Missing API endpoints for UI actions
- ❌ Incorrect P&L/ROI/R-multiple calculations
- ❌ Security vulnerabilities
- ❌ Breaking changes to existing functionality
- ❌ Missing type hints/types
- ❌ Direct database queries from frontend
- ❌ Business logic in API routes (should be in services)

**Medium Issues (Will Require Revision)**
- ⚠️ Missing error handling
- ⚠️ Missing documentation
- ⚠️ Inconsistent naming conventions
- ⚠️ Missing loading states
- ⚠️ Not responsive (mobile)
- ⚠️ Missing validation
- ⚠️ Incomplete task (partial implementation)

**Minor Issues (Should Be Fixed)**
- ⚠️ Code style inconsistencies
- ⚠️ Missing comments on complex logic
- ⚠️ Unused imports
- ⚠️ Console.log statements left in code

### Review Decision Outcomes

Your work will receive one of three decisions:

1. **APPROVED** ✅
   - All requirements met
   - High code quality
   - Complete documentation
   - Ready for production

2. **NEEDS REVISION** ⚠️
   - Minor issues found
   - Documentation incomplete
   - Some inconsistencies
   - Fix and resubmit

3. **REJECTED** ❌
   - Major issues found
   - Requirements not met
   - Security vulnerabilities
   - Requires significant rework

### Tips for Success

1. **Read the Task Carefully**: Understand all requirements before starting
2. **Check Dependencies**: Ensure prerequisite tasks are complete
3. **Follow Patterns**: Look at existing code for consistency
4. **Test Thoroughly**: Test all functionality before submitting
5. **Document as You Go**: Don't leave documentation for the end
6. **Review Your Own Work**: Use the reviewer checklist before submitting
7. **Ask Questions**: If requirements are unclear, ask for clarification

### Self-Review Before Submission

Before marking your task as `[REVIEW]`, ask yourself:

- ✅ Does my code follow all coding standards?
- ✅ Are all type hints/types present?
- ✅ Is error handling complete?
- ✅ Is documentation complete?
- ✅ Do all API endpoints exist and work?
- ✅ Are calculations accurate?
- ✅ Is the code responsive?
- ✅ Have I tested everything?
- ✅ Is TASKS.md updated?

**Remember**: Reviewers will check everything in detail. It's better to be thorough upfront than to have your work rejected or require revision.

## Project Context

### Application Location
- **Local Path**: `/Users/joshuajenquist/repos/personal/home-server/apps/trading-journal`
- **Server Path**: `~/server/apps/trading-journal` (after deployment)
- **Git Remote**: `origin/main` (GitHub: `unarmedpuppy/home-server`)

### Technology Stack

#### Backend
- **Framework**: FastAPI (Python 3.11+)
- **Database**: PostgreSQL 15+
- **ORM**: SQLAlchemy 2.0 (async)
- **Validation**: Pydantic v2
- **Migrations**: Alembic
- **API Docs**: OpenAPI/Swagger (auto-generated)

#### Frontend
- **Framework**: React 18+ with TypeScript
- **Build Tool**: Vite
- **UI Library**: Material-UI (MUI) v5 or Tailwind CSS
- **Charts**: 
  - TradingView Lightweight Charts (price charts)
  - Recharts or Chart.js (dashboard charts)
- **State Management**: 
  - TanStack Query (React Query) for server state
  - Zustand for client state
- **HTTP Client**: Axios
- **Date Handling**: date-fns

#### Infrastructure
- **Containerization**: Docker Compose
- **Network**: `my-network` (external network)
- **Ports**: 
  - Backend: `8100`
  - Frontend: `8101`
  - PostgreSQL: Internal only

### Key Requirements

#### Trade Types Supported
- `STOCK`: Traditional stock trades
- `OPTION`: Options trades (single-leg only for MVP)
- `CRYPTO_SPOT`: Cryptocurrency spot trades
- `CRYPTO_PERP`: Cryptocurrency perpetual futures
- `PREDICTION_MARKET`: Prediction market trades

#### Options Chain Fields (All Required)
- Strike price, expiration date, call/put
- **All Greeks**: Delta, Gamma, Theta, Vega, Rho
- Implied Volatility (IV)
- Volume and Open Interest
- Bid/Ask prices and spread

#### Chart Timeframes
- Support: 1m, 5m, 15m, 1h, 1d
- **Default**: 1h
- Configurable date range (default: 1 year)

#### Performance Metrics
- **Basics**: Net P&L, Gross P&L, Win Rate, Profit Factor
- **Advanced**: Max Drawdown, Average Win/Loss, Day Win Rate
- **Composite**: Zella Score

## Database Schema

### Tables

#### `trades`
```sql
CREATE TABLE trades (
    id SERIAL PRIMARY KEY,
    user_id INTEGER DEFAULT 1,
    ticker VARCHAR(20) NOT NULL,
    trade_type VARCHAR(20) NOT NULL,  -- STOCK, OPTION, CRYPTO_SPOT, CRYPTO_PERP, PREDICTION_MARKET
    
    -- Entry details
    entry_price DECIMAL(12, 4) NOT NULL,
    entry_quantity DECIMAL(12, 4) NOT NULL,
    entry_time TIMESTAMP NOT NULL,
    entry_commission DECIMAL(10, 2) DEFAULT 0,
    
    -- Exit details
    exit_price DECIMAL(12, 4),
    exit_quantity DECIMAL(12, 4),
    exit_time TIMESTAMP,
    exit_commission DECIMAL(10, 2) DEFAULT 0,
    
    -- Options specific
    strike_price DECIMAL(12, 4),
    expiration_date DATE,
    option_type VARCHAR(4),  -- CALL or PUT
    delta DECIMAL(8, 4),
    gamma DECIMAL(8, 6),
    theta DECIMAL(8, 4),
    vega DECIMAL(8, 4),
    rho DECIMAL(8, 4),
    implied_volatility DECIMAL(6, 4),
    volume BIGINT,
    open_interest BIGINT,
    bid_price DECIMAL(12, 4),
    ask_price DECIMAL(12, 4),
    bid_ask_spread DECIMAL(12, 4),
    
    -- Crypto specific
    crypto_exchange VARCHAR(50),
    crypto_pair VARCHAR(20),
    
    -- Prediction market specific
    prediction_market_platform VARCHAR(50),
    prediction_outcome VARCHAR(200),
    
    -- Calculated fields
    net_pnl DECIMAL(12, 2),
    net_roi DECIMAL(8, 4),
    realized_r_multiple DECIMAL(8, 4),
    
    -- Metadata
    status VARCHAR(20) DEFAULT 'open',  -- open, closed, partial
    side VARCHAR(10) NOT NULL,  -- LONG, SHORT
    playbook VARCHAR(100),
    notes TEXT,
    tags TEXT[],
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

#### `daily_summaries`
```sql
CREATE TABLE daily_summaries (
    date DATE PRIMARY KEY,
    total_trades INTEGER DEFAULT 0,
    winners INTEGER DEFAULT 0,
    losers INTEGER DEFAULT 0,
    gross_pnl DECIMAL(12, 2) DEFAULT 0,
    commissions DECIMAL(10, 2) DEFAULT 0,
    volume INTEGER DEFAULT 0,
    profit_factor DECIMAL(8, 4),
    winrate DECIMAL(5, 2),
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

#### `price_cache`
```sql
CREATE TABLE price_cache (
    id SERIAL PRIMARY KEY,
    ticker VARCHAR(20) NOT NULL,
    timestamp TIMESTAMP NOT NULL,
    timeframe VARCHAR(10) NOT NULL,  -- 1m, 5m, 15m, 1h, 1d
    open_price DECIMAL(12, 4),
    high_price DECIMAL(12, 4),
    low_price DECIMAL(12, 4),
    close_price DECIMAL(12, 4),
    volume BIGINT,
    cached_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(ticker, timestamp, timeframe)
);
```

#### `daily_notes`
```sql
CREATE TABLE daily_notes (
    id SERIAL PRIMARY KEY,
    date DATE NOT NULL UNIQUE,
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

## API Design Principles

### Authentication
- **Method**: API Key via header `X-API-Key: <key>`
- **Single User**: MVP supports single user only
- **All Endpoints**: Require authentication (except `/api/health`)

### Endpoint Structure
```
/api/trades/*          # Trade CRUD operations
/api/dashboard/*        # Dashboard statistics and charts
/api/calendar/*        # Calendar view data
/api/daily/*           # Daily journal data and notes
/api/charts/*          # Price data and chart data
/api/options/*         # Options chain data
/api/analytics/*       # Advanced analytics
/api/ai/*              # AI agent helper endpoints
/api/health            # Health check
/api/docs               # OpenAPI documentation
```

### Response Format
- **Success**: `200 OK` with JSON body
- **Created**: `201 Created` with created resource
- **Error**: `400 Bad Request`, `404 Not Found`, `500 Internal Server Error`
- **Pagination**: Include `limit`, `offset`, `total`, `has_more` in list responses

### Required Endpoints (Complete List)

See `IMPLEMENTATION_PLAN.md` for full API specification. Key endpoints:

**Trades**: GET, POST, PUT, PATCH, DELETE, bulk create, search
**Dashboard**: stats, cumulative-pnl, daily-pnl, drawdown, recent-trades
**Calendar**: month view, summary, date details
**Daily Journal**: full view, trades, summary, pnl-progression, notes CRUD
**Charts**: prices, trade overlay, cumulative-pnl, daily-pnl
**Options**: chain, greeks
**Analytics**: performance, by-ticker, by-type, by-playbook
**AI Helpers**: parse-trade, batch-create, suggestions

## Task Management System

### How to Claim Tasks

1. **Review Available Tasks**: Check the task list below
2. **Claim a Task**: Comment on the task with `CLAIMING: [task-id]` and your plan
3. **Update Status**: Mark task as `[IN PROGRESS]` when starting
4. **Complete Task**: Mark as `[COMPLETED]` when done, include summary

### Task Status
- `[PENDING]` - Not started
- `[IN PROGRESS]` - Currently being worked on
- `[COMPLETED]` - Finished and tested
- `[BLOCKED]` - Waiting on dependencies
- `[REVIEW]` - Needs review before completion

## Detailed Task List

### Phase 1: Foundation

#### T1.1: Project Structure Setup
**Status**: `[PENDING]`
**Priority**: High
**Dependencies**: None
**Description**: 
- Create project directory structure
- Set up `.gitignore` files
- Create `README.md` with setup instructions
- Initialize Git repository structure
**Files to Create**:
- `apps/trading-journal/.gitignore`
- `apps/trading-journal/README.md`
- Directory structure: `backend/`, `frontend/`, `data/`

#### T1.2: Docker Compose Configuration
**Status**: `[PENDING]`
**Priority**: High
**Dependencies**: T1.1
**Description**:
- Create `docker-compose.yml` with PostgreSQL, backend, and frontend services
- Configure volumes for data persistence
- Set up `my-network` external network
- Configure environment variables
- Add health checks for PostgreSQL
**Files to Create**:
- `apps/trading-journal/docker-compose.yml`
- `apps/trading-journal/env.template`

#### T1.3: PostgreSQL Database Setup
**Status**: `[PENDING]`
**Priority**: High
**Dependencies**: T1.2
**Description**:
- Create Alembic migration setup
- Create initial migration with all tables (trades, daily_summaries, price_cache, daily_notes)
- Add all indexes as specified
- Create database initialization script
**Files to Create**:
- `backend/alembic.ini`
- `backend/alembic/env.py`
- `backend/alembic/versions/001_initial_schema.py`
- `backend/app/database.py`

#### T1.4: FastAPI Backend Foundation
**Status**: `[PENDING]`
**Priority**: High
**Dependencies**: T1.3
**Description**:
- Set up FastAPI application structure
- Create `main.py` with app initialization
- Configure CORS, middleware, error handlers
- Set up API key authentication middleware
- Create configuration management (`config.py`)
- Set up database connection with SQLAlchemy async
- Create base API router structure
**Files to Create**:
- `backend/app/main.py`
- `backend/app/config.py`
- `backend/app/database.py`
- `backend/app/api/dependencies.py`
- `backend/requirements.txt`
- `backend/Dockerfile`

#### T1.5: SQLAlchemy Models
**Status**: `[PENDING]`
**Priority**: High
**Dependencies**: T1.4
**Description**:
- Create SQLAlchemy models for all tables
- Implement relationships and constraints
- Add model methods for calculations (P&L, ROI, R-multiple)
- Create model factories for testing
**Files to Create**:
- `backend/app/models/__init__.py`
- `backend/app/models/trade.py`
- `backend/app/models/daily_summary.py`
- `backend/app/models/price_cache.py`
- `backend/app/models/daily_note.py`

#### T1.6: Pydantic Schemas
**Status**: `[PENDING]`
**Priority**: High
**Dependencies**: T1.5
**Description**:
- Create Pydantic schemas for all API requests/responses
- TradeCreate, TradeUpdate, TradeResponse schemas
- Dashboard, Calendar, Daily Journal schemas
- Chart data schemas
- Validation rules for all fields
**Files to Create**:
- `backend/app/schemas/__init__.py`
- `backend/app/schemas/trade.py`
- `backend/app/schemas/dashboard.py`
- `backend/app/schemas/calendar.py`
- `backend/app/schemas/daily.py`
- `backend/app/schemas/charts.py`

#### T1.7: Trade CRUD API Endpoints
**Status**: `[PENDING]`
**Priority**: High
**Dependencies**: T1.6
**Description**:
- Implement GET /api/trades (list with filters)
- Implement GET /api/trades/:id
- Implement POST /api/trades
- Implement PUT /api/trades/:id
- Implement PATCH /api/trades/:id
- Implement DELETE /api/trades/:id
- Implement POST /api/trades/bulk
- Implement GET /api/trades/search
- Add pagination support
- Add API key authentication
**Files to Create/Modify**:
- `backend/app/api/routes/trades.py`
- `backend/app/services/trade_service.py`
- `backend/app/utils/calculations.py`
- `backend/app/utils/validators.py`

#### T1.8: React Frontend Foundation
**Status**: `[PENDING]`
**Priority**: High
**Dependencies**: T1.7
**Description**:
- Set up Vite + React + TypeScript project
- Configure build tools and dependencies
- Set up routing (React Router)
- Create base layout components (Sidebar, Header, Layout)
- Set up API client with Axios
- Configure environment variables
- Set up TanStack Query
**Files to Create**:
- `frontend/package.json`
- `frontend/vite.config.ts`
- `frontend/tsconfig.json`
- `frontend/Dockerfile`
- `frontend/src/main.tsx`
- `frontend/src/App.tsx`
- `frontend/src/api/client.ts`
- `frontend/src/components/layout/`

#### T1.9: Basic Trade Entry Form
**Status**: `[PENDING]`
**Priority**: Medium
**Dependencies**: T1.8
**Description**:
- Create trade entry form component
- Support all trade types (STOCK, OPTION, CRYPTO_SPOT, CRYPTO_PERP, PREDICTION_MARKET)
- Date picker (defaults to today)
- Options chain input fields (all Greeks)
- Form validation
- Submit to API
**Files to Create**:
- `frontend/src/components/trade-entry/TradeEntryForm.tsx`
- `frontend/src/components/trade-entry/OptionsChainInput.tsx`
- `frontend/src/hooks/useTrades.ts`

### Phase 2: Core Features

#### T2.1: P&L Calculation Utilities
**Status**: `[PENDING]`
**Priority**: High
**Dependencies**: T1.7
**Description**:
- Implement net P&L calculation
- Implement ROI calculation
- Implement R-multiple calculation
- Handle partial fills
- Handle different trade types
- Add unit tests
**Files to Create/Modify**:
- `backend/app/utils/calculations.py`
- `backend/tests/test_calculations.py`

#### T2.2: Dashboard Statistics Service
**Status**: `[PENDING]`
**Priority**: High
**Dependencies**: T2.1
**Description**:
- Implement dashboard statistics calculation
- Net P&L, Gross P&L
- Win rate, day win rate
- Profit factor
- Average win/loss
- Max drawdown
- Zella score (composite metric)
**Files to Create/Modify**:
- `backend/app/services/dashboard_service.py`
- `backend/app/api/routes/dashboard.py`

#### T2.3: Dashboard API Endpoints
**Status**: `[PENDING]`
**Priority**: High
**Dependencies**: T2.2
**Description**:
- GET /api/dashboard/stats
- GET /api/dashboard/cumulative-pnl
- GET /api/dashboard/daily-pnl
- GET /api/dashboard/drawdown
- GET /api/dashboard/recent-trades
- Add date range filtering
**Files to Create/Modify**:
- `backend/app/api/routes/dashboard.py`

#### T2.4: Dashboard Frontend Components
**Status**: `[PENDING]`
**Priority**: High
**Dependencies**: T2.3
**Description**:
- Create Dashboard main component
- Create KPI cards (Net P&L, Win Rate, Profit Factor, etc.)
- Create recent trades table
- Fetch and display data from API
- Add loading and error states
**Files to Create**:
- `frontend/src/components/dashboard/Dashboard.tsx`
- `frontend/src/components/dashboard/KPICard.tsx`
- `frontend/src/components/dashboard/RecentTrades.tsx`
- `frontend/src/hooks/useDashboard.ts`

#### T2.5: Calendar Service
**Status**: `[PENDING]`
**Priority**: High
**Dependencies**: T2.1
**Description**:
- Implement calendar data calculation
- Daily summaries with P&L and trade counts
- Month summary aggregation
- Color coding logic (green/red/gray)
**Files to Create/Modify**:
- `backend/app/services/calendar_service.py`
- `backend/app/api/routes/calendar.py`

#### T2.6: Calendar API Endpoints
**Status**: `[PENDING]`
**Priority**: High
**Dependencies**: T2.5
**Description**:
- GET /api/calendar/:year/:month
- GET /api/calendar/summary
- GET /api/calendar/date/:date
**Files to Create/Modify**:
- `backend/app/api/routes/calendar.py`

#### T2.7: Calendar Frontend Component
**Status**: `[PENDING]`
**Priority**: High
**Dependencies**: T2.6
**Description**:
- Create calendar view component
- Monthly grid with day cells
- Color coding (green/red/gray)
- Display P&L and trade count per day
- Month navigation
- Click date to view daily journal
**Files to Create**:
- `frontend/src/components/calendar/CalendarView.tsx`
- `frontend/src/components/calendar/CalendarGrid.tsx`
- `frontend/src/components/calendar/DayCell.tsx`

#### T2.8: Daily Journal Service
**Status**: `[PENDING]`
**Priority**: High
**Dependencies**: T2.1
**Description**:
- Implement daily journal data aggregation
- Trades for specific date
- Daily summary (winners, losers, winrate, etc.)
- P&L progression throughout day
- Daily notes retrieval
**Files to Create/Modify**:
- `backend/app/services/daily_service.py`
- `backend/app/api/routes/daily.py`

#### T2.9: Daily Journal API Endpoints
**Status**: `[PENDING]`
**Priority**: High
**Dependencies**: T2.8
**Description**:
- GET /api/daily/:date (complete view)
- GET /api/daily/:date/trades
- GET /api/daily/:date/summary
- GET /api/daily/:date/pnl-progression
- GET /api/daily/:date/notes
- POST /api/daily/:date/notes
- PUT /api/daily/:date/notes
- DELETE /api/daily/:date/notes
**Files to Create/Modify**:
- `backend/app/api/routes/daily.py`

#### T2.10: Daily Journal Frontend Components
**Status**: `[PENDING]`
**Priority**: High
**Dependencies**: T2.9
**Description**:
- Create daily journal main component
- Trade table with sortable columns
- Daily summary cards
- P&L progression chart (simple line chart)
- Notes editor
**Files to Create**:
- `frontend/src/components/daily-journal/DailyJournal.tsx`
- `frontend/src/components/daily-journal/TradeTable.tsx`
- `frontend/src/components/daily-journal/DailySummary.tsx`
- `frontend/src/components/daily-journal/PnLProgression.tsx`

### Phase 3: Charts & Visualization

#### T3.1: Price Data Service
**Status**: `[PENDING]`
**Priority**: High
**Dependencies**: T1.5
**Description**:
- Implement price data fetching from Alpha Vantage
- Fallback to yfinance
- Support crypto via CoinGecko
- Implement price caching in database
- Support all timeframes (1m, 5m, 15m, 1h, 1d)
- Configurable date range (default 1 year)
**Files to Create/Modify**:
- `backend/app/services/price_service.py`
- `backend/app/api/routes/charts.py`

#### T3.2: Charts API Endpoints
**Status**: `[PENDING]`
**Priority**: High
**Dependencies**: T3.1
**Description**:
- GET /api/charts/prices/:ticker
- GET /api/charts/prices/:ticker/range
- GET /api/charts/trade/:trade_id
- GET /api/charts/cumulative-pnl
- GET /api/charts/daily-pnl
**Files to Create/Modify**:
- `backend/app/api/routes/charts.py`

#### T3.3: TradingView Lightweight Charts Integration
**Status**: `[PENDING]`
**Priority**: High
**Dependencies**: T3.2
**Description**:
- Install and configure TradingView Lightweight Charts
- Create PriceChart component
- Support candlestick and line chart modes
- Support all timeframes
- Add timeframe selector
- Add date range selector
**Files to Create**:
- `frontend/src/components/charts/PriceChart.tsx`
- `frontend/src/components/charts/ChartControls.tsx`

#### T3.4: Trade Overlay on Charts
**Status**: `[PENDING]`
**Priority**: Medium
**Dependencies**: T3.3
**Description**:
- Overlay entry/exit points on price chart
- Visual markers for trade execution
- Tooltips with trade details
**Files to Create/Modify**:
- `frontend/src/components/charts/TradeOverlay.tsx`
- `frontend/src/components/charts/PriceChart.tsx`

#### T3.5: Dashboard Charts
**Status**: `[PENDING]`
**Priority**: High
**Dependencies**: T2.4, T3.2
**Description**:
- Cumulative P&L line chart
- Daily P&L bar chart
- Win/loss distribution charts
- Profit factor visualization
- Drawdown chart
**Files to Create**:
- `frontend/src/components/dashboard/PnLChart.tsx`
- `frontend/src/components/dashboard/DrawdownChart.tsx`

### Phase 4: Polish & Optimization

#### T4.1: Responsive Design
**Status**: `[PENDING]`
**Priority**: High
**Dependencies**: T2.10, T3.5
**Description**:
- Make all components mobile-responsive
- Test on mobile devices
- Optimize touch interactions
- Responsive charts
**Files to Modify**:
- All frontend components

#### T4.2: Error Handling & Loading States
**Status**: `[PENDING]`
**Priority**: High
**Dependencies**: All frontend tasks
**Description**:
- Add error boundaries
- Add loading spinners
- Add error messages
- Handle API errors gracefully
**Files to Create/Modify**:
- `frontend/src/components/common/ErrorBoundary.tsx`
- `frontend/src/components/common/LoadingSpinner.tsx`
- All components with API calls

#### T4.3: API Query Optimization
**Status**: `[PENDING]`
**Priority**: Medium
**Dependencies**: All API tasks
**Description**:
- Add database query optimization
- Add pagination to all list endpoints
- Add caching where appropriate
- Optimize daily summary calculations
**Files to Modify**:
- All service files

#### T4.4: Data Validation & Error Messages
**Status**: `[PENDING]`
**Priority**: Medium
**Dependencies**: All tasks
**Description**:
- Add comprehensive input validation
- Add user-friendly error messages
- Validate trade data (prices, quantities, dates)
- Validate options data (Greeks, IV, etc.)
**Files to Modify**:
- `backend/app/utils/validators.py`
- All API endpoints

#### T4.5: Options Chain API Endpoints
**Status**: `[PENDING]`
**Priority**: Medium
**Dependencies**: T3.1
**Description**:
- GET /api/options/chain/:ticker
- GET /api/options/chain/:ticker/:expiration
- GET /api/options/greeks/:ticker
- Integrate with options data provider (future: Polygon.io)
**Files to Create/Modify**:
- `backend/app/api/routes/options.py`
- `backend/app/services/options_service.py`

#### T4.6: Analytics API Endpoints
**Status**: `[PENDING]`
**Priority**: Low
**Dependencies**: T2.2
**Description**:
- GET /api/analytics/performance
- GET /api/analytics/by-ticker
- GET /api/analytics/by-type
- GET /api/analytics/by-playbook
**Files to Create/Modify**:
- `backend/app/api/routes/analytics.py`
- `backend/app/services/analytics_service.py`

#### T4.7: AI Agent Helper Endpoints
**Status**: `[PENDING]`
**Priority**: Medium
**Dependencies**: T1.7
**Description**:
- POST /api/ai/parse-trade
- POST /api/ai/batch-create
- GET /api/ai/suggestions/:ticker
**Files to Create/Modify**:
- `backend/app/api/routes/ai.py`
- `backend/app/services/ai_service.py`

#### T4.8: Documentation & README
**Status**: `[PENDING]`
**Priority**: Medium
**Dependencies**: All tasks
**Description**:
- Complete README with setup instructions
- API documentation (OpenAPI/Swagger)
- Code comments and docstrings
- Deployment guide
**Files to Create/Modify**:
- `apps/trading-journal/README.md`
- All code files (add docstrings)

#### T4.9: Traefik & Homepage Integration
**Status**: `[PENDING]`
**Priority**: Medium
**Dependencies**: T1.2
**Description**:
- Add Traefik labels for HTTPS routing
- Add Homepage labels
- Configure domain (trading-journal.server.unarmedpuppy.com)
- Update Cloudflare DDNS if needed
**Files to Modify**:
- `apps/trading-journal/docker-compose.yml`

## Coding Standards

### Backend (Python/FastAPI)

1. **Type Hints**: Use type hints everywhere
2. **Async/Await**: Use async SQLAlchemy and async endpoints
3. **Error Handling**: Use FastAPI HTTPException for errors
4. **Validation**: Use Pydantic for all request/response validation
5. **Database**: Always use SQLAlchemy ORM, never raw SQL
6. **Calculations**: Put all calculation logic in `utils/calculations.py`
7. **Services**: Business logic in services, not in routes
8. **Documentation**: Add docstrings to all functions and classes

### Frontend (React/TypeScript)

1. **TypeScript**: Strict mode, no `any` types
2. **Components**: Functional components with hooks
3. **State**: Use TanStack Query for server state, Zustand for client state
4. **Styling**: Use MUI or Tailwind consistently
5. **API Calls**: All via API client, never direct fetch
6. **Error Handling**: Use error boundaries and try-catch
7. **Loading States**: Always show loading indicators
8. **Responsive**: Mobile-first design

### API Design

1. **RESTful**: Follow REST principles
2. **Consistent**: Use consistent naming and structure
3. **Documented**: All endpoints in OpenAPI spec
4. **Validated**: Validate all inputs
5. **Error Responses**: Consistent error response format
6. **Pagination**: All list endpoints support pagination

## Deployment Workflow

1. **Local Development**: Make changes locally
2. **Test Locally**: Run `docker compose up` locally to test
3. **Commit & Push**: Git commit, push to origin/main
4. **Pull on Server**: `bash scripts/connect-server.sh "cd ~/server && git pull origin main"`
5. **Restart Services**: `bash scripts/connect-server.sh "cd ~/server/apps/trading-journal && docker compose up -d --build"`
6. **Verify**: Check logs and test endpoints

## Common Pitfalls to Avoid

1. **Direct DB Queries**: Frontend must use API, never query DB directly
2. **Missing API Endpoints**: Every UI action needs an API endpoint
3. **Calculation Errors**: Double-check P&L, ROI, R-multiple calculations
4. **Type Safety**: Don't use `any` in TypeScript, use proper types
5. **Missing Validation**: Validate all inputs on backend
6. **Port Conflicts**: Use ports 8100 (backend) and 8101 (frontend)
7. **Network Configuration**: Always use `my-network` external network
8. **Data Persistence**: Use volumes for PostgreSQL data
9. **Missing Error Handling**: Always handle errors gracefully
10. **Incomplete Tasks**: Complete tasks fully before moving on

## Testing Checklist

Before marking a task as `[REVIEW]` (which triggers code review):

- [ ] Code compiles/runs without errors
- [ ] API endpoints tested (use Swagger UI or curl)
- [ ] Frontend components render correctly
- [ ] Calculations are accurate (test with known values)
- [ ] Error handling works (test invalid inputs)
- [ ] Responsive design works on mobile
- [ ] No console errors or warnings
- [ ] Git committed and pushed
- [ ] **Pre-Submission Checklist completed** (see Code Review Process section above)
- [ ] **Self-Review completed** (see Self-Review Before Submission section above)

**Note**: After completing this checklist, mark your task as `[REVIEW]` in TASKS.md. A reviewer agent will then thoroughly review your work using `TRADING_JOURNAL_AGENT_REVIEWER_PROMPT.md`. Only mark as `[COMPLETED]` after receiving approval from the reviewer.

## Getting Help

**Essential Reading (in order):**
1. **`STARTUP_GUIDE.md`** - ⭐ START HERE - Formulas, API keys, setup details
2. **`IMPLEMENTATION_PLAN.md`** - Complete feature specification and architecture
3. **`TASKS.md`** - Available tasks and how to claim them
4. **`TRADING_JOURNAL_AGENT_REVIEWER_PROMPT.md`** - What reviewers will check (helps you prepare)

**Additional Resources:**
- **Server Setup**: See `agents/docs/SERVER_AGENT_PROMPT.md` for server context
- **API Spec**: See API endpoints section in `IMPLEMENTATION_PLAN.md`
- **Database Schema**: See database schema section in `IMPLEMENTATION_PLAN.md`
- **Calculation Formulas**: See `STARTUP_GUIDE.md` (critical for accurate calculations)

## Remember

- **API-First**: Design APIs before UI
- **Type Safety**: Use TypeScript and Pydantic
- **Test Thoroughly**: Test calculations and edge cases
- **Document Well**: Add comments and docstrings
- **Follow Patterns**: Use existing code as reference
- **Stay Focused**: Complete one task at a time
- **Ask Questions**: If unsure, ask for clarification
- **Prepare for Review**: Your work will be reviewed in detail - use the Pre-Submission Checklist and Self-Review before marking as `[REVIEW]`

---

**Last Updated**: Based on implementation plan v1.0
**Maintained By**: AI Agents working on Trading Journal application

