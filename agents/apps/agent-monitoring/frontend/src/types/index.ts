/**
 * TypeScript types matching backend API
 */

export interface Agent {
  id: number;
  agent_id: string;
  status: 'active' | 'idle' | 'blocked' | 'completed';
  current_task_id: string | null;
  progress: string | null;
  blockers: string | null;
  last_updated: string;
}

export interface AgentDetails extends Agent {
  recentActions: Action[];
  toolUsage: ToolUsage[];
  taskHistory: Task[];
  sessionStats: SessionStats;
}

export interface Action {
  id: number;
  agent_id: string;
  action_type: 'mcp_tool' | 'memory_query' | 'memory_record' | 'task_update' | 'status_update' | 'session_start' | 'session_end';
  tool_name: string | null;
  parameters: Record<string, any> | null;
  result_status: 'success' | 'error';
  duration_ms: number | null;
  error: string | null;
  timestamp: string;
}

export interface ToolUsage {
  tool_name: string;
  count: number;
  success_count: number;
  error_count: number;
  avg_duration_ms: number;
}

export interface Task {
  task_id: string;
  title: string;
  description: string;
  status: string;
  assignee: string;
  priority: string;
  dependencies: string;
  project: string;
  created: string;
  updated: string;
}

export interface SessionStats {
  total_sessions: number;
  total_tasks_completed: number;
  total_tools_called: number;
  avg_session_duration_minutes: number;
}

export interface SystemStats {
  totalAgents: number;
  activeAgents: number;
  idleAgents: number;
  blockedAgents: number;
  totalActions: number;
  actionsLast24h: number;
  toolUsage: Record<string, number>;
  taskStats: {
    pending: number;
    in_progress: number;
    completed: number;
  };
}

export interface ApiResponse<T> {
  status: 'success' | 'error' | 'not_found';
  message?: string;
  count?: number;
  [key: string]: any;
}

