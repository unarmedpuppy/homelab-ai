# Complete Agent System Visualization

**Comprehensive visual guide to the entire agent system architecture, workflows, and observability.**

---

## Table of Contents

1. [System Overview](#system-overview)
2. [Agent Onboarding Flow](#agent-onboarding-flow)
3. [Core Components](#core-components)
4. [Tool Ecosystem](#tool-ecosystem)
5. [Observability Stack](#observability-stack)
6. [Data Flow Architecture](#data-flow-architecture)
7. [Communication Patterns](#communication-patterns)
8. [Task Coordination Flow](#task-coordination-flow)
9. [Memory System Flow](#memory-system-flow)
10. [Agent Lifecycle](#agent-lifecycle)
11. [Complete Workflow Diagram](#complete-workflow-diagram)

---

## System Overview

The agent system is a comprehensive, self-improving ecosystem for managing home server infrastructure through AI agents. It provides structured workflows, observability, and coordination mechanisms.

**Architecture**: **Local-First** - All agent infrastructure runs locally on your machine.

```mermaid
graph TB
    subgraph "Local Machine"
        subgraph "Entry Points"
            A[New Agent Session] --> B[Start Infrastructure]
            B --> C[QUICK_START.md]
            C --> D[prompts/base.md]
            D --> E[prompts/server.md]
        end
        
        subgraph "Infrastructure Layer"
            F[Agent Monitoring<br/>localhost:3001/3012]
            G[Grafana<br/>localhost:3011]
            H[InfluxDB<br/>localhost:8087]
        end
        
        subgraph "Core Systems"
            I[Task Coordination]
            J[Agent Communication]
            K[Memory System<br/>Local SQLite]
            L[Agent Registry]
        end
        
        subgraph "Tool Ecosystem"
            M[MCP Server<br/>71 Tools<br/>Local Python]
            N[Skills Library<br/>Reusable Workflows]
        end
        
        subgraph "Observability"
            O[Monitoring Dashboard<br/>localhost:3012]
            P[Grafana Metrics<br/>localhost:3011]
            Q[Activity Logs<br/>Local SQLite]
        end
    end
    
    subgraph "Server (192.168.86.47)"
        R[Docker Services]
        S[Media Download]
        T[Other Services]
    end
    
    B --> F
    C --> I
    C --> J
    C --> K
    C --> M
    C --> N
    
    M --> F
    M --> K
    N --> M
    F --> O
    F --> P
    F --> Q
    
    I --> L
    J --> L
    K --> L
    
    M -.SSH/Network.-> R
    M -.SSH/Network.-> S
    M -.SSH/Network.-> T
    
    style B fill:#4caf50
    style F fill:#2196f3
    style M fill:#ff9800
    style O fill:#4caf50
```

---

## Agent Onboarding Flow

### Step-by-Step Onboarding Process

```mermaid
flowchart TD
    Start([New Agent Session]) --> Step0[Start Infrastructure<br/>start_agent_infrastructure]
    Step0 --> Step0_5[Verify Services<br/>check_agent_infrastructure]
    Step0_5 --> Step1[Read QUICK_START.md<br/>5-minute guide]
    Step1 --> Step2[Read prompts/base.md<br/>Complete guide]
    Step2 --> Step3{Server Management?}
    Step3 -->|Yes| Step4[Read prompts/server.md<br/>Server-specific context]
    Step3 -->|No| Step5[Start Monitoring Session]
    Step4 --> Step5
    
    Step5 --> Step6[Call start_agent_session<br/>Make yourself visible]
    Step6 --> Step7[Call update_agent_status<br/>Set status to active]
    Step7 --> Step8[Check for Messages<br/>get_agent_messages]
    Step8 --> Step9[Query Memory<br/>memory_query_decisions]
    Step9 --> Step10[Check Skills<br/>agents/skills/]
    Step10 --> Step11[Check MCP Tools<br/>agents/apps/agent-mcp/]
    Step11 --> Step12[Query Tasks<br/>query_tasks]
    Step12 --> Step13[Start Working]
    
    style Start fill:#e1f5ff
    style Step0 fill:#4caf50
    style Step0_5 fill:#4caf50
    style Step13 fill:#c8e6c9
```

### Documentation Hierarchy

```mermaid
graph TD
    A[agents/README.md<br/>Main Entry Point] --> B[Start Infrastructure<br/>start-agent-infrastructure.sh]
    A --> C[QUICK_START.md<br/>5-minute guide]
    A --> D[prompts/base.md<br/>Complete guide]
    A --> E[docs/README.md<br/>Documentation index]
    
    B --> C
    C --> D
    D --> F[prompts/server.md<br/>Server-specific]
    D --> G[SYSTEM_ARCHITECTURE.md<br/>System overview]
    D --> H[DATA_MODEL.md<br/>Data structure]
    D --> I[COMMUNICATION_GUIDELINES.md<br/>Channel usage]
    
    E --> J[AGENT_WORKFLOW.md<br/>Workflow guide]
    E --> K[MCP_TOOL_DISCOVERY.md<br/>Tool discovery]
    E --> L[WORKFLOW_GENERATOR_PROMPT.md<br/>Meta-prompt]
    
    style A fill:#ffeb3b
    style B fill:#4caf50
    style C fill:#4caf50
    style D fill:#2196f3
```

---

## Core Components

### Component Architecture

```mermaid
graph LR
    subgraph "Agent Layer"
        A1[Agent Session]
        A2[Agent Prompt]
    end
    
    subgraph "Coordination Layer"
        B1[Task Coordination<br/>registry.md]
        B2[Agent Communication<br/>messages/]
        B3[Agent Registry<br/>agent-registry.md]
    end
    
    subgraph "Knowledge Layer"
        C1[Memory System<br/>memory.db]
        C2[Skills Library<br/>skills/]
    end
    
    subgraph "Infrastructure Layer"
        D0[Infrastructure Management<br/>3 Tools]
        D1[MCP Server<br/>71 Tools<br/>Local Python]
        D2[Activity Monitoring<br/>4 Tools]
    end
    
    subgraph "Observability Layer"
        E1[Monitoring Dashboard<br/>Next.js<br/>localhost:3012]
        E2[Grafana<br/>Time-series<br/>localhost:3011]
        E3[SQLite DB<br/>Activity Logs<br/>Local]
    end
    
    A1 --> B1
    A1 --> B2
    A1 --> C1
    A1 --> D0
    A1 --> D1
    A1 --> D2
    
    D0 --> E1
    D1 --> E3
    D2 --> E3
    E3 --> E1
    E3 --> E2
    
    B1 --> C1
    B2 --> C1
    C2 --> D1
```

### Component Details

| Component | Location | Purpose | Key Files |
|-----------|----------|---------|-----------|
| **Agent Prompts** | `agents/docs/` | Agent instructions and context | `prompts/base.md`, `SERVER_prompts/base.md` |
| **Task Coordination** | `agents/tasks/` | Central task registry | `registry.md`, MCP tools |
| **Agent Communication** | `agents/communication/` | Inter-agent messaging | `messages/`, `protocol.md` |
| **Memory System** | `agents/memory/` | Persistent knowledge | `memory.db`, MCP tools |
| **Agent Registry** | `agents/registry/` | Agent definitions | `agent-registry.md`, `agent-definitions/` |
| **MCP Server** | `agents/apps/agent-mcp/` | Tool execution | `tools/`, `server.py` |
| **Skills Library** | `agents/skills/` | Reusable workflows | `skills/`, `README.md` |
| **Monitoring** | `agents/apps/agent-monitoring/` | Observability | Dashboard, Grafana, DB |

---

## Tool Ecosystem

### MCP Tools (71 Total)

```mermaid
graph TB
    subgraph "Infrastructure Management - 3 Tools"
        A0[start_agent_infrastructure]
        A0_1[check_agent_infrastructure]
        A0_2[stop_agent_infrastructure]
    end
    
    subgraph "Activity Monitoring - 4 Tools"
        A1[start_agent_session]
        A2[update_agent_status]
        A3[get_agent_status]
        A4[end_agent_session]
    end
    
    subgraph "Agent Communication - 5 Tools"
        B1[send_agent_message]
        B2[get_agent_messages]
        B3[acknowledge_message]
        B4[mark_message_resolved]
        B5[query_messages]
    end
    
    subgraph "Memory Management - 9 Tools"
        C1[memory_query_decisions]
        C2[memory_query_patterns]
        C3[memory_search]
        C4[memory_record_decision]
        C5[memory_record_pattern]
        C6[memory_save_context]
        C7[memory_get_recent_context]
        C8[memory_get_context_by_task]
        C9[memory_export_to_markdown]
    end
    
    subgraph "Task Coordination - 6 Tools"
        D1[register_task]
        D2[query_tasks]
        D3[get_task]
        D4[claim_task]
        D5[update_task_status]
        D6[check_task_dependencies]
    end
    
    subgraph "Agent Management - 6 Tools"
        E1[create_agent_definition]
        E2[query_agent_registry]
        E3[assign_task_to_agent]
        E4[archive_agent]
        E5[reactivate_agent]
        E6[sync_agent_registry]
    end
    
    subgraph "Skill Management - 5 Tools"
        F1[propose_skill]
        F2[list_skill_proposals]
        F3[query_skills]
        F4[analyze_patterns_for_skills]
        F5[auto_propose_skill_from_pattern]
    end
    
    subgraph "Server Management - 33 Tools"
        G1[Docker - 8 tools]
        G2[Media Download - 13 tools]
        G3[System Monitoring - 5 tools]
        G4[Troubleshooting - 3 tools]
        G5[Git Operations - 4 tools]
        G6[Networking - 4 tools]
        G7[System Utilities - 3 tools]
    end
    
    style A0 fill:#4caf50
    style A1 fill:#4caf50
    style B1 fill:#2196f3
    style C1 fill:#ff9800
    style D1 fill:#9c27b0
    style E1 fill:#f44336
    style F1 fill:#00bcd4
```

### Tool Discovery Priority

```mermaid
flowchart TD
    Start([Agent Starts]) --> Step0[0. Start Infrastructure<br/>start_agent_infrastructure]
    Step0 --> Step0_25[0.25. Verify Services<br/>check_agent_infrastructure]
    Step0_25 --> Step0_5[0.5. Start Monitoring<br/>start_agent_session]
    Step0_5 --> Step0_75[0.75. Check Messages<br/>get_agent_messages]
    Step0_75 --> Step1[1. Query Memory<br/>memory_query_*]
    Step1 --> Step2[2. Check Skills<br/>agents/skills/]
    Step2 --> Step3[3. Check MCP Tools<br/>agents/apps/agent-mcp/]
    Step3 --> Step4[4. Query Tasks<br/>query_tasks]
    Step4 --> Step5[5. Use Tools/Skills]
    Step5 --> Step6{Need New Tool?}
    Step6 -->|Yes| Step7[6. Create MCP Tool]
    Step6 -->|No| Step8[7. Use Existing]
    Step7 --> Step8
    Step8 --> End([Work Complete])
    
    style Step0 fill:#4caf50
    style Step0_25 fill:#4caf50
    style Step0_5 fill:#4caf50
    style Step0_75 fill:#4caf50
    style Step1 fill:#ff9800
    style Step2 fill:#2196f3
    style Step3 fill:#2196f3
```

---

## Observability Stack

### Observability Architecture (Local-First)

```mermaid
graph TB
    subgraph "Local Machine"
        subgraph "Agent Actions"
            A1[MCP Tool Calls<br/>Local Python]
            A2[Status Updates<br/>Local]
            A3[Session Events<br/>Local]
        end
        
        subgraph "Data Collection"
            B1[Activity Monitoring Tools<br/>4 MCP Tools]
            B2[Automatic Logging<br/>All 71 MCP Tools]
            B3[Activity Logger<br/>Python Module]
        end
        
        subgraph "Backend API (Local)"
            E1[Node.js API<br/>localhost:3001]
        end
        
        subgraph "Storage Layer (Local)"
            C1[SQLite DB<br/>agent_activity.db<br/>Local File System]
            C2[Agent Status Table]
            C3[Agent Actions Table]
            C4[Agent Sessions Table]
        end
        
        subgraph "Visualization Layer (Local)"
            D1[Next.js Dashboard<br/>localhost:3012]
            D2[Grafana<br/>localhost:3011]
            D3[InfluxDB<br/>localhost:8087]
        end
    end
    
    A1 --> B2
    A2 --> B1
    A3 --> B1
    
    B1 --> B3
    B2 --> B3
    B3 --> E1
    E1 --> C1
    
    C1 --> C2
    C1 --> C3
    C1 --> C4
    
    C1 --> D1
    C1 --> D2
    C2 --> D3
    C3 --> D3
    
    style A1 fill:#e1f5ff
    style E1 fill:#2196f3
    style D1 fill:#4caf50
    style D2 fill:#ff9800
    style C1 fill:#9c27b0
```

### Observability Flow

```mermaid
sequenceDiagram
    participant Agent
    participant MCP as MCP Server
    participant Monitor as Activity Monitor
    participant DB as SQLite DB
    participant Dashboard
    participant Grafana
    
    Agent->>MCP: Call MCP Tool
    MCP->>Monitor: Log Tool Call
    Monitor->>DB: Store Action
    Monitor-->>Agent: Return Result
    
    Agent->>Monitor: update_agent_status()
    Monitor->>DB: Update Status
    Monitor-->>Agent: Status Updated
    
    DB->>Dashboard: Real-time Updates
    DB->>Grafana: Time-series Export
    
    Dashboard->>DB: Query Status
    Grafana->>DB: Query Metrics
```

### What Gets Observed

| Action Type | Observable | Not Observable |
|-------------|------------|----------------|
| **MCP Tool Calls** | ✅ All automatically logged | ❌ |
| **Status Updates** | ✅ Via `update_agent_status()` | ❌ |
| **Session Events** | ✅ Start/end sessions | ❌ |
| **SSH Commands** | ❌ | ✅ Not logged |
| **Custom Scripts** | ❌ | ✅ Not logged |
| **Direct File Edits** | ❌ | ✅ Not logged |

**Key Principle**: Always use MCP tools for observability!

---

## Data Flow Architecture

### Complete Data Flow

```mermaid
graph TB
    subgraph "Agent Actions"
        A1[Agent Session]
    end
    
    subgraph "MCP Server Layer"
        B1[Tool Execution]
        B2[Automatic Logging]
    end
    
    subgraph "Data Storage (Local)"
        C1[Monitoring DB<br/>agent_activity.db<br/>Local SQLite]
        C2[Task Registry<br/>registry.md<br/>Local Markdown]
        C3[Message Queue<br/>messages/*.md<br/>Local Files]
        C4[Memory DB<br/>memory.db<br/>Local SQLite]
        C5[Agent Registry<br/>agent-registry.md<br/>Local Markdown]
    end
    
    subgraph "Sync & Generation"
        D1[sync_registry.py<br/>Auto-generate]
        D2[Query Scripts<br/>Helper tools]
    end
    
    subgraph "Visualization"
        E1[Dashboard]
        E2[Grafana]
    end
    
    A1 --> B1
    B1 --> B2
    B2 --> C1
    B1 --> C2
    B1 --> C3
    B1 --> C4
    B1 --> C5
    
    C1 --> D1
    D1 --> C5
    
    C1 --> E1
    C1 --> E2
    C4 --> E2
    
    style C1 fill:#4caf50
    style C2 fill:#2196f3
    style C3 fill:#ff9800
    style C4 fill:#9c27b0
    style C5 fill:#f44336
```

### Data Storage Strategy

```mermaid
graph LR
    subgraph "Primary Storage"
        A1[SQLite DBs<br/>Fast Queries]
        A2[Markdown Files<br/>Human Readable]
    end
    
    subgraph "Storage Types"
        B1[Agent Status<br/>DB → Auto-gen MD]
        B2[Tasks<br/>MD Primary]
        B3[Messages<br/>MD Files + JSON Index]
        B4[Memory<br/>DB Primary + MD Export]
        B5[Activity<br/>DB Only]
    end
    
    A1 --> B1
    A1 --> B4
    A1 --> B5
    
    A2 --> B2
    A2 --> B3
    
    B1 --> A2
    B4 --> A2
    
    style A1 fill:#4caf50
    style A2 fill:#2196f3
```

---

## Communication Patterns

### Inter-Agent Communication Flow

```mermaid
sequenceDiagram
    participant A1 as Agent 1
    participant CP as Communication Protocol
    participant MQ as Message Queue
    participant A2 as Agent 2
    participant TC as Task Coordination
    
    A1->>CP: send_agent_message()
    CP->>MQ: Create message file
    CP->>MQ: Update index.json
    CP-->>A1: Message sent
    
    A2->>CP: get_agent_messages()
    CP->>MQ: Query index.json
    CP->>MQ: Load message files
    CP-->>A2: Return messages
    
    A2->>CP: acknowledge_message()
    CP->>MQ: Update status
    CP-->>A2: Acknowledged
    
    A2->>TC: Link to task (optional)
    A2->>CP: mark_message_resolved()
    CP->>MQ: Update status
    CP-->>A2: Resolved
```

### Communication Channel Decision Tree

```mermaid
flowchart TD
    Start([Need to Communicate?]) --> Q1{Formal Task Assignment?}
    Q1 -->|Yes| TC[Task Coordination System]
    Q1 -->|No| Q2{Direct Message to Agent?}
    Q2 -->|Yes| CP[Communication Protocol]
    Q2 -->|No| Q3{Long-term Knowledge?}
    Q3 -->|Yes| MS[Memory System]
    Q3 -->|No| Q4{High-level Status?}
    Q4 -->|Yes| AM[Agent Monitoring]
    Q4 -->|No| Q5{Detailed Work Notes?}
    Q5 -->|Yes| PF[Per-Agent Files]
    Q5 -->|No| End([Re-evaluate Need])
    
    style TC fill:#9c27b0
    style CP fill:#2196f3
    style MS fill:#ff9800
    style AM fill:#4caf50
```

---

## Task Coordination Flow

### Complete Task Lifecycle

```mermaid
stateDiagram-v2
    [*] --> pending: register_task()
    pending --> claimed: claim_task()
    claimed --> in_progress: update_task_status()
    in_progress --> review: update_task_status()
    in_progress --> blocked: Dependencies not met
    blocked --> pending: Dependencies completed
    review --> completed: update_task_status()
    review --> in_progress: Needs revision
    pending --> cancelled: update_task_status()
    in_progress --> cancelled: update_task_status()
    completed --> [*]
    cancelled --> [*]
    
    note right of pending
        Available to claim
        Dependencies validated
    end note
    
    note right of blocked
        Auto-blocked if
        dependencies not met
    end note
```

### Task Coordination Architecture

```mermaid
graph TB
    subgraph "Task Registration"
        A1[register_task<br/>Create new task]
        A2[Set dependencies]
        A3[Set priority]
    end
    
    subgraph "Task Discovery"
        B1[query_tasks<br/>Filter by status/assignee]
        B2[get_task<br/>Get single task]
        B3[check_task_dependencies<br/>Validate deps]
    end
    
    subgraph "Task Execution"
        C1[claim_task<br/>Assign to agent]
        C2[update_task_status<br/>Update progress]
        C3[Auto-update dependents]
    end
    
    subgraph "Storage"
        D1[registry.md<br/>Central registry]
        D2[Task ID Format<br/>T{project}.{task}]
    end
    
    A1 --> A2
    A2 --> A3
    A3 --> D1
    
    B1 --> D1
    B2 --> D1
    B3 --> D1
    
    C1 --> C2
    C2 --> C3
    C3 --> D1
    
    style D1 fill:#2196f3
```

---

## Memory System Flow

### Memory Operations

```mermaid
graph LR
    subgraph "Memory Input"
        A1[Record Decision<br/>memory_record_decision]
        A2[Record Pattern<br/>memory_record_pattern]
        A3[Save Context<br/>memory_save_context]
    end
    
    subgraph "Storage"
        B1[SQLite DB<br/>memory.db]
        B2[Decisions Table]
        B3[Patterns Table]
        B4[Context Table]
    end
    
    subgraph "Memory Query"
        C1[Query Decisions<br/>memory_query_decisions]
        C2[Query Patterns<br/>memory_query_patterns]
        C3[Full-text Search<br/>memory_search]
        C4[Get Context<br/>memory_get_context_*]
    end
    
    subgraph "Export"
        D1[Markdown Export<br/>memory_export_to_markdown]
        D2[Human Readable<br/>memory/export/]
    end
    
    A1 --> B1
    A2 --> B1
    A3 --> B1
    
    B1 --> B2
    B1 --> B3
    B1 --> B4
    
    B1 --> C1
    B1 --> C2
    B1 --> C3
    B1 --> C4
    
    B1 --> D1
    D1 --> D2
    
    style B1 fill:#ff9800
    style D2 fill:#4caf50
```

### Memory Integration

```mermaid
sequenceDiagram
    participant Agent
    participant Memory as Memory System
    participant Skills as Skill Management
    participant Patterns as Pattern Learning
    
    Agent->>Memory: Query past decisions
    Memory-->>Agent: Return relevant decisions
    
    Agent->>Memory: Record new decision
    Memory->>Memory: Store in DB
    
    Agent->>Memory: Record pattern
    Memory->>Memory: Store pattern
    
    Memory->>Patterns: Analyze patterns
    Patterns->>Skills: Auto-propose skill
    Skills-->>Agent: New skill available
    
    Agent->>Memory: Save work context
    Memory->>Memory: Store context
```

---

## Agent Lifecycle

### Lifecycle States

```mermaid
stateDiagram-v2
    [*] --> ready: create_agent_definition()
    ready --> active: Human activates
    active --> idle: No activity (30+ days)
    active --> archived: All tasks complete
    idle --> archived: Auto-archive policy
    archived --> ready: reactivate_agent()
    ready --> [*]
    active --> [*]
    archived --> [*]
    
    note right of ready
        Definition created
        Waiting for activation
    end note
    
    note right of active
        Working on tasks
        Status tracked in DB
    end note
    
    note right of archived
        Moved to archive/
        Historical reference
    end note
```

### Lifecycle Management Flow

```mermaid
graph TB
    subgraph "Agent Creation"
        A1[create_agent_definition]
        A2[Generate agent ID]
        A3[Create definition file]
        A4[Add to registry]
    end
    
    subgraph "Agent Activation"
        B1[Human opens session]
        B2[Load agent prompt]
        B3[Start monitoring]
        B4[Status: active]
    end
    
    subgraph "Agent Work"
        C1[Work on tasks]
        C2[Update status]
        C3[Track activity]
    end
    
    subgraph "Agent Archiving"
        D1[archive_agent]
        D2[Move to archive/]
        D3[Update registry]
        D4[Status: archived]
    end
    
    subgraph "Agent Reactivation"
        E1[reactivate_agent]
        E2[Move to active/]
        E3[Update registry]
        E4[Status: ready/active]
    end
    
    A1 --> A2
    A2 --> A3
    A3 --> A4
    A4 --> B1
    B1 --> B2
    B2 --> B3
    B3 --> B4
    B4 --> C1
    C1 --> C2
    C2 --> C3
    C3 --> D1
    D1 --> D2
    D2 --> D3
    D3 --> D4
    D4 --> E1
    E1 --> E2
    E2 --> E3
    E3 --> E4
```

---

## Complete Workflow Diagram

### End-to-End Agent Workflow

```mermaid
flowchart TB
    Start([Agent Session Starts]) --> Onboard[Onboarding]
    
    subgraph Onboarding
        O0[Start Infrastructure<br/>start_agent_infrastructure]
        O1[Read QUICK_START.md]
        O2[Read prompts/base.md]
        O3[Read prompts/server.md if needed]
    end
    
    Onboard --> Monitor[Start Monitoring]
    
    subgraph Monitor
        M1[start_agent_session]
        M2[update_agent_status]
    end
    
    Monitor --> Discover[Discovery Phase]
    
    subgraph Discover
        D1[Check Messages]
        D2[Query Memory]
        D3[Check Skills]
        D4[Check MCP Tools]
        D5[Query Tasks]
    end
    
    Discover --> Work[Work Phase]
    
    subgraph Work
        W1[Claim Task]
        W2[Execute Work]
        W3[Use MCP Tools]
        W4[Use Skills]
        W5[Record Decisions]
        W6[Update Status]
    end
    
    Work --> Review[Review Phase]
    
    subgraph Review
        R1[Update to review]
        R2[Wait for reviewer]
        R3[Address feedback]
    end
    
    Review --> Complete[Complete]
    
    subgraph Complete
        C1[Update to completed]
        C2[End session]
        C3[Save context]
    end
    
    Complete --> End([Session Ends])
    
    style Start fill:#e1f5ff
    style Monitor fill:#4caf50
    style Work fill:#2196f3
    style Complete fill:#c8e6c9
```

### System Integration Flow

```mermaid
graph TB
    subgraph "Agent Session"
        A1[Agent Starts]
        A2[Agent Works]
        A3[Agent Completes]
    end
    
    subgraph "Coordination Systems"
        B1[Task Coordination]
        B2[Agent Communication]
        B3[Agent Registry]
    end
    
    subgraph "Knowledge Systems"
        C1[Memory System]
        C2[Skills Library]
    end
    
    subgraph "Execution Systems"
        D1[MCP Server]
        D2[Activity Monitoring]
    end
    
    subgraph "Observability"
        E1[Monitoring Dashboard]
        E2[Grafana]
        E3[Activity Logs]
    end
    
    A1 --> B1
    A1 --> B2
    A1 --> C1
    A1 --> D1
    A1 --> D2
    
    A2 --> B1
    A2 --> B2
    A2 --> C1
    A2 --> C2
    A2 --> D1
    
    A3 --> B1
    A3 --> C1
    A3 --> D2
    
    D1 --> E3
    D2 --> E3
    E3 --> E1
    E3 --> E2
    
    B1 --> C1
    B2 --> C1
    C2 --> D1
    
    style A1 fill:#e1f5ff
    style D1 fill:#2196f3
    style E1 fill:#4caf50
```

---

## Key Documentation Files

### Primary Entry Points

| File | Purpose | When to Use |
|------|---------|-------------|
| `agents/README.md` | Main entry point | First file to read |
| `agents/docs/QUICK_START.md` | 5-minute quick start | New agent onboarding |
| `agents/prompts/base.md` | Complete agent guide | Full agent context |
| `agents/prompts/server.md` | Server-specific guide | Server management agents |

### System Documentation

| File | Purpose | When to Use |
|------|---------|-------------|
| `agents/docs/SYSTEM_ARCHITECTURE.md` | System overview | Understanding architecture |
| `agents/docs/DATA_MODEL.md` | Data structure | Understanding storage |
| `agents/docs/COMMUNICATION_GUIDELINES.md` | Channel usage | Which channel to use |
| `agents/docs/AGENT_WORKFLOW.md` | Workflow guide | Understanding workflows |
| `agents/docs/MCP_TOOL_DISCOVERY.md` | Tool discovery | Finding tools |

### Reference Documentation

| File | Purpose | When to Use |
|------|---------|-------------|
| `agents/apps/agent-mcp/README.md` | MCP tools catalog | Finding tools |
| `agents/skills/README.md` | Skills catalog | Finding workflows |
| `agents/tasks/README.md` | Task coordination | Task management |
| `agents/communication/README.md` | Communication protocol | Inter-agent messaging |
| `agents/memory/README.md` | Memory system | Knowledge management |

---

## System Principles

### 1. Observability First
- **Always use MCP tools** - They're automatically logged
- **Start monitoring session** - Make yourself visible
- **Update status regularly** - Keep dashboard current
- **Avoid SSH/custom scripts** - They're not observable

### 2. Centralized Coordination
- **Task Coordination** - All tasks in central registry
- **Agent Communication** - Structured messaging protocol
- **Agent Registry** - Single source of truth
- **Memory System** - Shared knowledge base

### 3. Human-Readable Storage
- **Markdown First** - All data in human-readable format
- **Version Controlled** - All files in Git
- **Auto-Generated Views** - DB → Markdown sync
- **Queryable** - MCP tools and scripts for queries

### 4. Self-Improving System
- **Pattern Learning** - Auto-identify patterns
- **Skill Creation** - Convert patterns to skills
- **Memory Integration** - Learn from past decisions
- **Lifecycle Management** - Archive/reactivate agents

---

## Quick Reference

### Essential MCP Tools (Use First!)

```python
# 0. Start Infrastructure (DO THIS FIRST!)
await start_agent_infrastructure()
# Or: ./agents/scripts/start-agent-infrastructure.sh

# 1. Start Monitoring (DO THIS SECOND!)
start_agent_session(agent_id="your-agent-id")
update_agent_status(agent_id="your-agent-id", status="active", current_task_id="T1.1")

# 2. Check Messages
get_agent_messages(agent_id="your-agent-id", status="pending")

# 3. Query Memory
memory_query_decisions(project="home-server", search_text="deployment")
memory_query_patterns(severity="high")

# 4. Query Tasks
query_tasks(status="pending", priority="high")
claim_task(task_id="T1.1", agent_id="your-agent-id")

# 5. Update Task Status
update_task_status(task_id="T1.1", status="in_progress", agent_id="your-agent-id")

# 6. Record Decisions
memory_record_decision(content="Use PostgreSQL", rationale="ACID compliance")

# 7. End Session
end_agent_session(agent_id="your-agent-id", session_id="...", tasks_completed=1)
```

### Essential Documentation Path

```
1. agents/README.md (START HERE)
   ↓
2. agents/docs/QUICK_START.md (5 minutes)
   ↓
3. agents/prompts/base.md (Complete guide)
   ↓
4. agents/prompts/server.md (If server management)
   ↓
5. agents/docs/SYSTEM_ARCHITECTURE.md (System overview)
   ↓
6. Reference docs as needed
```

---

## System Metrics

### Current System State

- **Total MCP Tools**: 71 tools
- **Skills Available**: 7+ reusable workflows
- **Documentation Files**: 30+ markdown files
- **Active Systems**: 7 core systems
- **Storage Locations**: 5 primary storage systems (all local)
- **Observability**: 3 visualization layers (all localhost)
- **Architecture**: Local-first (all infrastructure runs locally)

### Tool Breakdown

- Infrastructure Management: 3 tools ⭐ NEW
- Activity Monitoring: 4 tools
- Agent Communication: 5 tools
- Memory Management: 9 tools
- Task Coordination: 6 tools
- Agent Management: 6 tools
- Skill Management: 5 tools
- Server Management: 33 tools

---

## Summary

This agent system provides:

✅ **Local-First Architecture** - All infrastructure runs locally (localhost)  
✅ **Structured Onboarding** - Clear entry points and documentation hierarchy  
✅ **Comprehensive Tooling** - 71 MCP tools for all operations  
✅ **Full Observability** - Dashboard (localhost:3012), Grafana (localhost:3011), and activity logs  
✅ **Centralized Coordination** - Task, communication, and registry systems  
✅ **Persistent Memory** - Learn from past decisions and patterns (local SQLite)  
✅ **Self-Improvement** - Pattern learning and auto-skill creation  
✅ **Lifecycle Management** - Archive/reactivate agents as needed  
✅ **Infrastructure Management** - Startup/stop tools for local infrastructure  

**All operations are observable, all data is human-readable, all systems are integrated, and everything runs locally.**

---

**Last Updated**: 2025-01-13  
**Status**: Active (Local-First Architecture)  
**Architecture**: All infrastructure runs locally on localhost  
**See Also**:
- `agents/README.md` - Main entry point and directory structure
- `agents/docs/SYSTEM_ARCHITECTURE.md` - Detailed architecture
- `agents/docs/DATA_MODEL.md` - Data structure details
- `agents/docs/COMMUNICATION_GUIDELINES.md` - Communication usage
- `agents/docs/QUICK_START.md` - Quick start guide
- `agents/scripts/start-agent-infrastructure.sh` - Infrastructure startup script

