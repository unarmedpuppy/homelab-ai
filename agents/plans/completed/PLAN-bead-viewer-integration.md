# Bead Viewer Integration Plan

## Overview

Build a custom bead viewer integrated into the homelab-ai dashboard with:
- Retro/pixel-art "command center" UI inspired by VIBE CODING CORP reference
- Live-updating Kanban board for beads tasks
- Agent monitoring and assignment
- Ralph-wiggum loop management
- **Full dashboard migration** to new design system
- **Mobile-first responsive design** across all views

## Scope Additions

Per user requirements:
1. **Task creation from dashboard** - Following WORKSPACE-AGENTS conventions (proper repo labels)
2. **Polling-based live updates** (5s interval), WebSocket as future enhancement
3. **Full migration** - All existing views (Chat, Providers, Stats, Agents) will use retro components
4. **Mobile-first layouts** - All views must work correctly on mobile devices

## UX Reference Analysis

From `/workspace/beads-viewer/agents/reference/ux-inspiration.jpeg`:

```
┌────────────────────────────────────────────────────────────────────────────────┐
│ [CREATE TASK] [BULK ASSIGN] [AUTO-FILL]  TASKS:87 IN_PROG:34 IDLE:5 LOAD:68%  │
├────────────┬────────────────────────────────────────────────┬──────────────────┤
│ CATEGORIES │          KANBAN COLUMNS                        │  TASK DETAILS    │
│            │                                                │                  │
│ □ CORE     │  BACKLOG    │  IN PROGRESS  │    DONE         │ Project: xxx     │
│ □ FRONTEND │  ┌──────┐   │  ┌──────────┐ │   ┌──────┐      │ Status: xxx      │
│ □ BACKEND  │  │ Task │   │  │ Task     │ │   │ Task │      │ Agent: xxx       │
│ □ ANALYTICS│  │ ──── │   │  │ Agent:01 │ │   │      │      │                  │
│            │  │ NONE │   │  │ ████45%  │ │   │      │      │ Checklist:       │
│            │  │ HIGH │   │  │ CRITICAL │ │   │      │      │ □ Item 1         │
│            │  │ 4d   │   │  │ 1d       │ │   │      │      │ □ Item 2         │
│            │  └──────┘   │  └──────────┘ │   └──────┘      │                  │
│            │             │               │                  │ [EDIT PROMPT]    │
│            │             │               │                  │                  │
│            │             │               │                  │ Agent: [▼ Select]│
└────────────┴─────────────┴───────────────┴──────────────────┴──────────────────┘
```

Key elements:
- Header stats bar with action buttons
- Left sidebar for label filters
- 3-column Kanban: Backlog → In Progress → Done
- Right panel for task details
- Progress bars on in-progress tasks
- Agent assignment dropdown

---

## Architecture Decisions

### 1. Integration Location
- **Add to**: `/workspace/homelab-ai/dashboard/`
- **New views**: `/beads` route for Kanban board, `/ralph` route for loop management
- **Deprecate**: `beads-viewer` repo after migration

### 2. Data Source
- **Primary**: `/workspace/home-server/.beads/` (version-controlled JSONL)
- **Access**: New API endpoints in llm-router to read beads via `bd` CLI

### 3. Design System
- Create reusable "retro" UI component library
- Pixelated borders, terminal-green accents, CRT-style glow effects
- Consistent across all dashboard views (migrate existing views later)

---

## Phase 1: Backend API Layer

### 1.1 Beads API Endpoints (llm-router)

New file: `/workspace/homelab-ai/llm-router/beads_api.py`

```python
# Endpoints to add to router.py

GET  /beads/tasks                 # List all tasks (with filters)
GET  /beads/tasks/{id}            # Get task details
GET  /beads/stats                 # Aggregate stats (total, by status, by label)
POST /beads/tasks                 # Create new task
PATCH /beads/tasks/{id}           # Update task (claim, close, update)
GET  /beads/labels                # List all unique labels
GET  /beads/agents                # List available agents for assignment

# WebSocket for live updates
WS   /beads/ws                    # Real-time task changes
```

### 1.2 Beads Data Models

```python
class BeadTask:
    id: str
    title: str
    description: str | None
    status: Literal["open", "in_progress", "closed"]
    priority: int  # 0-3 (critical, high, medium, low)
    type: Literal["task", "bug", "feature", "epic", "chore"]
    labels: list[str]
    blocked_by: list[str]
    created_at: str
    updated_at: str
    age_days: int  # computed
    assigned_agent: str | None  # for display

class BeadsStats:
    total_tasks: int
    backlog_count: int  # open + unblocked
    in_progress_count: int
    done_count: int
    blocked_count: int
    by_label: dict[str, int]
    by_priority: dict[int, int]
```

### 1.3 Beads CLI Wrapper

Create helper to execute `bd` commands safely:

```python
# /workspace/homelab-ai/llm-router/beads_cli.py

import subprocess
import json
from pathlib import Path

BEADS_DIR = Path("/workspace/home-server/.beads")

async def bd_command(*args, json_output=True) -> dict | list | str:
    """Execute bd command and return parsed output."""
    cmd = ["bd"] + list(args)
    if json_output:
        cmd.append("--json")

    result = subprocess.run(
        cmd,
        cwd=BEADS_DIR.parent,
        capture_output=True,
        text=True,
        env={**os.environ, "BEADS_DIR": str(BEADS_DIR)}
    )

    if result.returncode != 0:
        raise BeadsError(result.stderr)

    return json.loads(result.stdout) if json_output else result.stdout

# Wrapper functions
async def list_tasks(status=None, label=None, priority=None):
    args = ["list"]
    if status: args.extend(["--status", status])
    if label: args.extend(["--label", label])
    return await bd_command(*args)

async def get_ready_tasks(label=None):
    args = ["ready"]
    if label: args.extend(["--label", label])
    return await bd_command(*args)

async def claim_task(task_id: str):
    return await bd_command("claim", task_id, json_output=False)

async def close_task(task_id: str):
    return await bd_command("close", task_id, json_output=False)

async def create_task(title: str, **kwargs):
    args = ["create", title]
    if kwargs.get("priority"): args.extend(["-p", str(kwargs["priority"])])
    if kwargs.get("type"): args.extend(["-t", kwargs["type"]])
    if kwargs.get("labels"):
        for label in kwargs["labels"]:
            args.extend(["-l", label])
    return await bd_command(*args, json_output=False)
```

---

## Phase 2: Design System Components

### 2.1 Component Library Structure

```
/dashboard/src/
├── components/
│   └── ui/                    # NEW: Reusable UI primitives
│       ├── RetroCard.tsx      # Pixelated border card
│       ├── RetroButton.tsx    # Action buttons
│       ├── RetroBadge.tsx     # Status/priority badges
│       ├── RetroProgress.tsx  # Progress bar with segments
│       ├── RetroPanel.tsx     # Bordered panel with title
│       ├── RetroSelect.tsx    # Dropdown selector
│       ├── RetroInput.tsx     # Text input
│       ├── RetroCheckbox.tsx  # Checkbox with label
│       ├── RetroStats.tsx     # Stats display bar
│       └── index.ts           # Barrel export
├── styles/
│   └── retro-theme.css        # CSS custom properties for theme
```

### 2.2 Theme Variables

```css
/* /dashboard/src/styles/retro-theme.css */

:root {
  /* Retro color palette */
  --retro-bg-dark: #1a1a2e;
  --retro-bg-medium: #16213e;
  --retro-bg-light: #1f3460;
  --retro-border: #3a506b;
  --retro-border-highlight: #5bc0be;

  --retro-text-primary: #e8e8e8;
  --retro-text-secondary: #8b9dc3;
  --retro-text-muted: #5c6b8a;

  --retro-accent-green: #00ff41;
  --retro-accent-yellow: #ffd700;
  --retro-accent-red: #ff4444;
  --retro-accent-blue: #00d4ff;
  --retro-accent-orange: #ff8c00;

  /* Priority colors */
  --retro-priority-critical: #ff4444;
  --retro-priority-high: #ff8c00;
  --retro-priority-medium: #ffd700;
  --retro-priority-low: #5bc0be;

  /* Status colors */
  --retro-status-open: #5bc0be;
  --retro-status-progress: #ffd700;
  --retro-status-done: #00ff41;
  --retro-status-blocked: #ff4444;

  /* Effects */
  --retro-glow: 0 0 10px rgba(91, 192, 190, 0.3);
  --retro-border-width: 2px;
  --retro-radius: 4px;
}
```

### 2.3 Core Components

**RetroCard.tsx**
```tsx
interface RetroCardProps {
  children: React.ReactNode;
  title?: string;
  variant?: 'default' | 'highlight' | 'warning' | 'success';
  className?: string;
  onClick?: () => void;
  selected?: boolean;
}

// Features:
// - Pixelated/stepped border effect
// - Optional title bar with icon
// - Hover glow effect
// - Selected state with accent border
```

**RetroBadge.tsx**
```tsx
interface RetroBadgeProps {
  children: React.ReactNode;
  variant: 'priority-critical' | 'priority-high' | 'priority-medium' | 'priority-low'
         | 'status-open' | 'status-progress' | 'status-done' | 'status-blocked'
         | 'agent' | 'label';
  size?: 'sm' | 'md';
}
```

**RetroProgress.tsx**
```tsx
interface RetroProgressProps {
  value: number;  // 0-100
  showLabel?: boolean;
  variant?: 'default' | 'success' | 'warning';
}

// Features:
// - Segmented bar (like old loading bars)
// - Percentage label option
// - Animation on value change
```

---

## Phase 3: Beads Viewer Views

### 3.1 Main Kanban Board View

**File**: `/dashboard/src/components/BeadsBoard.tsx`

```tsx
// Main Kanban board with three columns

interface BeadsBoardProps {
  // Component manages its own state via API
}

// Structure:
// - Header: Stats bar + Action buttons
// - Left sidebar: Label filters (collapsible)
// - Main area: 3 Kanban columns
// - Right panel: Task details (when selected)

// Features:
// - Drag-and-drop between columns (optional, phase 2)
// - Click to select and view details
// - Live updates via polling (5s) or WebSocket
// - Filter by label, priority, type
```

### 3.2 Task Card Component

**File**: `/dashboard/src/components/BeadsTaskCard.tsx`

```tsx
interface BeadsTaskCardProps {
  task: BeadTask;
  selected?: boolean;
  onClick: () => void;
  showAgent?: boolean;
}

// Displays:
// - Title (truncated)
// - Labels as colored badges
// - Priority indicator
// - Age (e.g., "4d")
// - Agent name if assigned
// - Progress bar if in_progress
```

### 3.3 Task Detail Panel

**File**: `/dashboard/src/components/BeadsTaskDetail.tsx`

```tsx
interface BeadsTaskDetailProps {
  task: BeadTask;
  onClose: () => void;
  onClaim: () => void;
  onComplete: () => void;
  onAssignAgent: (agentId: string) => void;
}

// Displays:
// - Full title
// - Status badge
// - Priority badge
// - All labels
// - Description (markdown rendered)
// - Blocked by (if any)
// - Action buttons: Claim / Mark Done
// - Agent selector dropdown
```

### 3.4 Stats Header Component

**File**: `/dashboard/src/components/BeadsStatsHeader.tsx`

```tsx
interface BeadsStatsHeaderProps {
  stats: BeadsStats;
  onCreateTask: () => void;
  onRefresh: () => void;
}

// Displays:
// - Total Tasks count
// - In Progress count
// - Idle Agents count (from provider API)
// - System Load % (from provider API)
// - CREATE TASK button
// - REFRESH button
```

---

## Phase 4: Ralph-Wiggum Management

### 4.1 Ralph API Client

Add to `/dashboard/src/api/client.ts`:

```typescript
// Claude-harness base URL
const CLAUDE_HARNESS_URL = import.meta.env.VITE_CLAUDE_HARNESS_URL
  || 'https://claude-harness.server.unarmedpuppy.com';

export const ralphAPI = {
  getStatus: async (): Promise<RalphStatus> => {
    const response = await fetch(`${CLAUDE_HARNESS_URL}/v1/ralph/status`);
    return response.json();
  },

  start: async (params: RalphStartParams): Promise<RalphStartResponse> => {
    const response = await fetch(`${CLAUDE_HARNESS_URL}/v1/ralph/start`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(params),
    });
    return response.json();
  },

  stop: async (): Promise<{ message: string }> => {
    const response = await fetch(`${CLAUDE_HARNESS_URL}/v1/ralph/stop`, {
      method: 'POST',
    });
    return response.json();
  },

  getLogs: async (lines: number = 100): Promise<RalphLogs> => {
    const response = await fetch(`${CLAUDE_HARNESS_URL}/v1/ralph/logs?lines=${lines}`);
    return response.json();
  },
};
```

### 4.2 Ralph Types

```typescript
interface RalphStatus {
  running: boolean;
  status: 'idle' | 'running' | 'stopping' | 'completed' | 'failed';
  label: string | null;
  total_tasks: number;
  completed_tasks: number;
  failed_tasks: number;
  current_task: string | null;
  current_task_title: string | null;
  started_at: string | null;
  last_update: string | null;
  message: string | null;
}

interface RalphStartParams {
  label: string;
  priority?: number;
  max_tasks?: number;
  dry_run?: boolean;
}

interface RalphLogs {
  logs: string[];
  count: number;
}
```

### 4.3 Ralph Dashboard View

**File**: `/dashboard/src/components/RalphDashboard.tsx`

```
┌─────────────────────────────────────────────────────────────────────┐
│                    RALPH-WIGGUM TASK RUNNER                         │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  Status: [● RUNNING]  Label: mercury                                │
│  Progress: ████████░░░░░░░░░░░░ 3/60 tasks (5%)                    │
│  Current: home-server-abc123 - "Add retry logic to API client"     │
│  Started: 2 hours ago  |  Last update: 5 seconds ago               │
│                                                                     │
│  [STOP LOOP]                                                        │
│                                                                     │
├─────────────────────────────────────────────────────────────────────┤
│                      START NEW LOOP                                 │
│                                                                     │
│  Label: [mercury        ▼]   Priority: [All ▼]                     │
│  Max Tasks: [0 (unlimited)]  Dry Run: [ ]                          │
│                                                                     │
│  [START RALPH LOOP]                                                 │
│                                                                     │
├─────────────────────────────────────────────────────────────────────┤
│                        EXECUTION LOG                                │
│ ┌─────────────────────────────────────────────────────────────────┐│
│ │ [2026-01-18 00:48:29] INFO: Ralph Wiggum Starting               ││
│ │ [2026-01-18 00:48:29] INFO: Label filter: mercury               ││
│ │ [2026-01-18 00:48:24] INFO: Found 10 ready tasks                ││
│ │ [2026-01-18 00:48:29] INFO: Task 1 of 10: home-server-rspl      ││
│ │ ...                                                              ││
│ └─────────────────────────────────────────────────────────────────┘│
│                                                                     │
│                      [REFRESH LOGS]                                 │
└─────────────────────────────────────────────────────────────────────┘
```

Features:
- Real-time status display (polling every 5s when running)
- Progress bar with task counts
- Current task display with link to beads detail
- Start new loop form with label selector
- Log viewer with auto-scroll
- Stop button (only when running)

---

## Phase 5: Agent Classification & Display

### 5.1 Agent Types

Based on existing infrastructure:

| Agent Type | ID | Description | Status Source |
|------------|-------|-------------|---------------|
| Qwen 7B | `server-3070` | RTX 3070, always-on | `/admin/providers` |
| Qwen 14B | `gaming-pc-3090` | RTX 3090, on-demand | `/admin/providers` |
| Z.ai GLM | `zai` | Cloud fallback | `/admin/providers` |
| Claude Harness | `claude-harness` | Claude Max CLI | `/admin/providers` |

### 5.2 Agent Status Integration

The Provider Monitoring view already shows agent status. For the beads viewer:

1. **Idle Agents**: Count providers with `utilization < 100%` and `is_healthy`
2. **System Load**: Average utilization across all healthy providers
3. **Agent Selector**: Show dropdown with healthy agents for assignment

### 5.3 Agent Assignment (Future)

Currently, Ralph assigns work automatically based on label→directory mapping. Future enhancement could allow:
- Manual agent assignment from beads detail panel
- Auto-fill idle agents button (starts Ralph loops for unassigned ready tasks)

---

## Phase 6: Navigation Integration

### 6.1 Updated App Routes

```tsx
// /dashboard/src/App.tsx

<Routes>
  <Route path="/" element={<ChatView />} />
  <Route path="/chat/:conversationId" element={<ChatView />} />
  <Route path="/providers" element={<ProvidersView />} />
  <Route path="/stats" element={<StatsView />} />
  <Route path="/agents" element={<AgentsView />} />
  {/* NEW ROUTES */}
  <Route path="/beads" element={<BeadsView />} />
  <Route path="/ralph" element={<RalphView />} />
</Routes>
```

### 6.2 Updated Navigation

```tsx
// Add to AppNavigation component

<Link to="/beads" className={...}>
  📋 Beads Board
</Link>
<Link to="/ralph" className={...}>
  🔄 Ralph Loops
</Link>
```

---

## Phase 6.5: Task Creation Modal

### Task Creation Requirements (WORKSPACE-AGENTS Conventions)

Tasks created from dashboard MUST follow these conventions:

**Required Fields:**
- `title`: Descriptive task name
- `type`: task | bug | feature | epic | chore
- `priority`: 0-3 (critical, high, medium, low)
- `labels[]`: MUST include at least one repo label

**Repo Labels (Required):**
| Label | Working Directory | Description |
|-------|-------------------|-------------|
| `mercury` | `/workspace` | Cross-repo work |
| `trading-bot`, `polyjuiced` | `/workspace/polyjuiced` | Trading bot |
| `home-server`, `infrastructure` | `/workspace/home-server` | Server infra |
| `homelab-ai`, `ai-services`, `claude-harness` | `/workspace/homelab-ai` | AI services |
| `pokedex` | `/workspace/pokedex` | Pokemon app |
| `trading-journal` | `/workspace/trading-journal` | Trade tracking |
| `shua-ledger` | `/workspace/shua-ledger` | Finance |
| `beads-viewer` | `/workspace/beads-viewer` | Beads UI |
| `maptapdat` | `/workspace/maptapdat` | Maptap dashboard |
| `bird` | `/workspace/bird` | Twitter/X data |
| `agent-gateway` | `/workspace/agent-gateway` | Agent gateway |

**Create Task Modal UI:**
```
┌─────────────────────────────────────────────────────────┐
│                    CREATE NEW TASK                       │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  Title: [_____________________________________]         │
│                                                         │
│  Type: [▼ task    ]    Priority: [▼ medium (2)]        │
│                                                         │
│  Repository Label: (required)                           │
│  [○ mercury     ] [○ trading-bot ] [○ home-server ]    │
│  [○ homelab-ai  ] [○ pokedex     ] [○ other...    ]    │
│                                                         │
│  Additional Labels: (optional)                          │
│  [ ai ] [ urgent ] [ +add ]                             │
│                                                         │
│  Description: (optional)                                │
│  ┌───────────────────────────────────────────────────┐ │
│  │ Markdown supported...                              │ │
│  └───────────────────────────────────────────────────┘ │
│                                                         │
│           [CANCEL]              [CREATE TASK]           │
└─────────────────────────────────────────────────────────┘
```

**API Call:**
```bash
POST /beads/tasks
{
  "title": "Add retry logic to API",
  "type": "feature",
  "priority": 1,
  "labels": ["trading-bot", "api"],  // First label = repo
  "description": "Optional markdown description"
}
```

---

## Phase 7: Mobile-First Responsive Design

### Breakpoints

```css
/* Mobile-first breakpoints */
--breakpoint-sm: 640px;   /* Small tablets */
--breakpoint-md: 768px;   /* Tablets */
--breakpoint-lg: 1024px;  /* Desktop */
--breakpoint-xl: 1280px;  /* Large desktop */
```

### Layout Patterns

**Mobile (< 640px):**
- Single column layout
- Collapsible sidebar (hamburger menu)
- Stacked Kanban columns (swipeable)
- Bottom navigation bar
- Task detail as full-screen modal
- Condensed stats header

**Tablet (640px - 1024px):**
- Two column Kanban (Backlog+InProgress | Done)
- Slide-out sidebar
- Task detail as side panel

**Desktop (> 1024px):**
- Full three-column Kanban
- Persistent sidebar
- Task detail as right panel
- All stats visible

### Mobile Navigation Component

```tsx
// MobileNav.tsx - Bottom navigation for mobile

interface MobileNavProps {
  currentView: string;
}

// Sticky bottom bar with icons:
// 💬 Chat | 📋 Beads | 🔄 Ralph | 🔌 Providers | 📊 Stats
```

### Responsive Kanban

**Mobile View:**
```
┌─────────────────────────┐
│ [☰] BEADS   [+] [⟳]     │  <- Header with hamburger menu
├─────────────────────────┤
│ Tasks: 87 | In Prog: 34 │  <- Condensed stats
├─────────────────────────┤
│ [BACKLOG ▼]             │  <- Column selector dropdown
├─────────────────────────┤
│ ┌─────────────────────┐ │
│ │ Task 1              │ │
│ │ HIGH • 4d           │ │
│ └─────────────────────┘ │
│ ┌─────────────────────┐ │
│ │ Task 2              │ │
│ │ MEDIUM • 2d         │ │
│ └─────────────────────┘ │
│         ...             │
├─────────────────────────┤
│ 💬  📋  🔄  🔌  📊     │  <- Bottom nav
└─────────────────────────┘
```

**Swipe Gestures:**
- Swipe left/right to change columns
- Pull down to refresh
- Tap card to view details (full-screen modal)

### Component Responsive Props

All retro components should accept responsive props:

```tsx
interface RetroCardProps {
  // ... existing props
  size?: 'sm' | 'md' | 'lg' | 'responsive';
  stackOnMobile?: boolean;
}

interface RetroPanelProps {
  // ... existing props
  collapsible?: boolean;  // For mobile sidebars
  defaultCollapsed?: boolean;
}
```

---

## Phase 8: Full Dashboard Migration

### Migration Strategy

Migrate existing views to use new design system while preserving functionality:

| View | Priority | Complexity | Changes Needed |
|------|----------|------------|----------------|
| **ProviderMonitoring** | High | Medium | Replace cards with RetroCard, add mobile layout |
| **AgentRuns** | High | Medium | Replace table with RetroCard list on mobile |
| **Dashboard (Stats)** | Medium | Low | Replace stat cards with RetroPanel |
| **ChatInterface** | Low | High | Restyle message bubbles, input (keep last) |
| **ConversationSidebar** | Low | Medium | Make collapsible, retro styling |

### Component Mapping

| Current Pattern | Retro Replacement |
|-----------------|-------------------|
| `bg-gray-800 rounded-lg p-4 border border-gray-700` | `<RetroCard>` |
| `px-2 py-1 rounded text-xs font-medium` | `<RetroBadge variant={...}>` |
| `bg-blue-500 hover:bg-blue-600 rounded` | `<RetroButton variant="primary">` |
| `bg-gray-900 rounded border border-gray-700` | `<RetroPanel>` |
| Manual progress bars | `<RetroProgress value={...}>` |

### Migration Checklist

**ProviderMonitoring.tsx:**
- [ ] Replace stat cards with `<RetroPanel>`
- [ ] Replace provider cards with `<RetroCard>`
- [ ] Replace status badges with `<RetroBadge variant="status-*">`
- [ ] Replace progress bar with `<RetroProgress>`
- [ ] Add mobile stacking layout
- [ ] Make cards full-width on mobile

**AgentRuns.tsx:**
- [ ] Replace header stats with `<RetroPanel>`
- [ ] On desktop: Keep table, style with retro theme
- [ ] On mobile: Convert to card list layout
- [ ] Replace status badges with `<RetroBadge>`
- [ ] Replace expand/collapse with retro accordion
- [ ] Add pull-to-refresh on mobile

**Dashboard.tsx:**
- [ ] Replace stat cards with `<RetroPanel>`
- [ ] Style activity heatmap with retro colors
- [ ] Make charts responsive
- [ ] Stack cards vertically on mobile

**ChatInterface.tsx:** (last priority)
- [ ] Keep functionality, apply retro styling
- [ ] Message bubbles with retro borders
- [ ] Input field with `<RetroInput>`
- [ ] Send button with `<RetroButton>`
- [ ] Mobile keyboard handling

---

## Implementation Order (Updated)

### Sprint 1: Foundation (Backend + Design System)
1. [ ] Create `beads_cli.py` wrapper in llm-router
2. [ ] Add beads API endpoints to router.py
3. [ ] Create retro theme CSS variables with responsive breakpoints
4. [ ] Build core UI components with mobile-first design:
   - [ ] RetroCard (responsive sizes)
   - [ ] RetroBadge
   - [ ] RetroButton
   - [ ] RetroPanel (collapsible)
   - [ ] RetroProgress
   - [ ] RetroSelect
   - [ ] RetroInput
   - [ ] RetroModal (full-screen on mobile)
5. [ ] Create MobileNav bottom navigation component
6. [ ] Create responsive layout wrapper components

### Sprint 2: Beads Board (Mobile-First)
7. [ ] Create BeadsBoard.tsx with responsive layout
8. [ ] Create BeadsTaskCard.tsx (compact for mobile)
9. [ ] Create BeadsTaskDetail.tsx (modal on mobile, panel on desktop)
10. [ ] Create BeadsStatsHeader.tsx (condensed on mobile)
11. [ ] Create BeadsLabelFilter.tsx (drawer on mobile)
12. [ ] Add swipe gestures for column navigation
13. [ ] Add `/beads` route and navigation
14. [ ] Implement polling for live updates

### Sprint 3: Task Creation & Ralph Management
15. [ ] Create CreateTaskModal.tsx with repo label requirements
16. [ ] Add ralphAPI to client.ts
17. [ ] Create RalphDashboard.tsx with mobile layout
18. [ ] Add `/ralph` route and navigation
19. [ ] Implement start/stop controls
20. [ ] Add log viewer with auto-refresh

### Sprint 4: Dashboard Migration
21. [ ] Migrate ProviderMonitoring.tsx
22. [ ] Migrate AgentRuns.tsx
23. [ ] Migrate Dashboard.tsx (stats)
24. [ ] Update App.tsx navigation with MobileNav
25. [ ] Test all views on mobile devices

### Sprint 5: Polish & Completion
26. [ ] Migrate ChatInterface.tsx (if time permits)
27. [ ] Migrate ConversationSidebar.tsx
28. [ ] Cross-browser testing
29. [ ] Performance optimization (lazy loading)
30. [ ] Deprecate beads-viewer repo
31. [ ] Update AGENTS.md documentation

---

## File Changes Summary

### New Files
```
/homelab-ai/llm-router/
├── beads_cli.py                    # Beads CLI wrapper
└── beads_api.py                    # Beads API endpoints (or add to router.py)

/homelab-ai/dashboard/src/
├── styles/
│   └── retro-theme.css             # Theme variables
├── components/
│   ├── ui/
│   │   ├── RetroCard.tsx
│   │   ├── RetroBadge.tsx
│   │   ├── RetroButton.tsx
│   │   ├── RetroPanel.tsx
│   │   ├── RetroProgress.tsx
│   │   ├── RetroSelect.tsx
│   │   ├── RetroInput.tsx
│   │   ├── RetroCheckbox.tsx
│   │   ├── RetroStats.tsx
│   │   └── index.ts
│   ├── BeadsBoard.tsx
│   ├── BeadsTaskCard.tsx
│   ├── BeadsTaskDetail.tsx
│   ├── BeadsStatsHeader.tsx
│   ├── BeadsLabelFilter.tsx
│   └── RalphDashboard.tsx
└── types/
    └── beads.ts                    # Beads type definitions
```

### Modified Files
```
/homelab-ai/llm-router/router.py    # Add beads API routes
/homelab-ai/dashboard/src/
├── App.tsx                         # Add new routes
├── api/client.ts                   # Add beadsAPI and ralphAPI
├── types/api.ts                    # Add beads and ralph types
└── index.css                       # Import retro theme
```

---

## API Endpoint Specifications

### GET /beads/tasks

Query params:
- `status`: open | in_progress | closed (optional)
- `label`: string (optional, filter by label)
- `priority`: 0-3 (optional)
- `type`: task | bug | feature | epic (optional)
- `ready`: boolean (optional, only unblocked open tasks)

Response:
```json
{
  "tasks": [
    {
      "id": "home-server-abc123",
      "title": "Add retry logic to API client",
      "description": "Implement exponential backoff...",
      "status": "open",
      "priority": 1,
      "type": "feature",
      "labels": ["mercury", "trading-bot"],
      "blocked_by": [],
      "created_at": "2026-01-15T10:00:00Z",
      "updated_at": "2026-01-15T10:00:00Z",
      "age_days": 3
    }
  ],
  "total": 87
}
```

### GET /beads/stats

Response:
```json
{
  "total_tasks": 87,
  "backlog_count": 45,
  "in_progress_count": 34,
  "done_count": 8,
  "blocked_count": 12,
  "by_label": {
    "mercury": 10,
    "trading-bot": 25,
    "infrastructure": 15
  },
  "by_priority": {
    "0": 5,
    "1": 20,
    "2": 40,
    "3": 22
  }
}
```

### POST /beads/tasks

Request:
```json
{
  "title": "New task title",
  "type": "task",
  "priority": 1,
  "labels": ["mercury"],
  "description": "Optional description"
}
```

### PATCH /beads/tasks/{id}

Request:
```json
{
  "status": "in_progress"  // or "closed"
}
```

---

## Open Questions

1. **WebSocket vs Polling**: Start with polling (simpler), add WebSocket later if needed?
2. **Task Creation**: Allow from dashboard or only via CLI?
3. **Agent Assignment UI**: Show in beads board or keep separate in Ralph management?
4. **Bulk Operations**: Include bulk assign in initial build?

---

## Success Criteria

### Core Functionality
- [ ] Beads board shows all tasks in correct columns (Backlog/In Progress/Done)
- [ ] Tasks update in real-time (within 5s of change via polling)
- [ ] Can view task details including description
- [ ] Can create new tasks from dashboard with proper repo labels
- [ ] Ralph status displays correctly (running/idle/progress)
- [ ] Can start/stop Ralph loops from dashboard
- [ ] Ralph logs are visible and auto-refresh

### Design System
- [ ] Retro UI components are reusable across all views
- [ ] Consistent styling matches VIBE CODING CORP aesthetic
- [ ] All components have mobile-first responsive design
- [ ] CSS uses custom properties for theming

### Mobile Experience
- [ ] All views work correctly on mobile devices (< 640px)
- [ ] Bottom navigation is usable on mobile
- [ ] Kanban board has swipe navigation on mobile
- [ ] Task detail opens as full-screen modal on mobile
- [ ] Touch targets are appropriately sized (min 44x44px)
- [ ] No horizontal scrolling on mobile

### Dashboard Migration
- [ ] ProviderMonitoring uses new retro components
- [ ] AgentRuns uses new retro components
- [ ] Dashboard (stats) uses new retro components
- [ ] Consistent look across all views

### Technical Quality
- [ ] TypeScript types for all new components and APIs
- [ ] No console errors in development
- [ ] Polling cleanup on component unmount
- [ ] Proper loading and error states
