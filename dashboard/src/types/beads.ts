// Beads Task Management Types

export interface BeadTask {
  id: string;
  title: string;
  description?: string | null;
  status: 'open' | 'in_progress' | 'closed';
  priority: 0 | 1 | 2 | 3; // 0=critical, 1=high, 2=medium, 3=low
  issue_type: 'task' | 'bug' | 'feature' | 'epic' | 'chore';
  labels: string[];
  blocked_by?: string[];
  dependency_count?: number;
  dependent_count?: number;
  created_at: string;
  updated_at: string;
  created_by?: string;
  owner?: string;
  age_days: number; // computed by API
}

export interface BeadsTasksResponse {
  tasks: BeadTask[];
  total: number;
}

export interface BeadsStats {
  total_tasks: number;
  backlog_count: number; // open + unblocked
  in_progress_count: number;
  done_count: number;
  blocked_count: number;
  by_label: Record<string, number>;
  by_priority: Record<string, number>;
  by_type: Record<string, number>;
}

export interface BeadsLabelsResponse {
  labels: string[];
  repo_labels: string[];
  other_labels: string[];
}

export interface BeadsTaskCreate {
  title: string;
  priority?: number;
  type?: string;
  labels?: string[];
  description?: string;
  blocked_by?: string[];
}

export interface BeadsTaskUpdate {
  status?: 'open' | 'in_progress' | 'closed';
  priority?: number;
  labels_add?: string[];
  labels_remove?: string[];
}

// Ralph-Wiggum Types

export interface RalphStatus {
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

export interface RalphStartParams {
  label: string;
  priority?: number;
  max_tasks?: number;
  dry_run?: boolean;
}

export interface RalphStartResponse {
  message: string;
  status_url: string;
  stop_url: string;
}

export interface RalphLogs {
  logs: string[];
  count: number;
}

// Known repo labels for task creation
export const REPO_LABELS = [
  { value: 'repo:home-server', label: 'home-server', description: 'Server infrastructure' },
  { value: 'repo:homelab-ai', label: 'homelab-ai', description: 'AI services, dashboard' },
  { value: 'repo:polyjuiced', label: 'polyjuiced', description: 'Trading bot' },
  { value: 'repo:trading-journal', label: 'trading-journal', description: 'Trade tracking' },
  { value: 'repo:pokedex', label: 'pokedex', description: 'Pokemon app' },
  { value: 'repo:beads-viewer', label: 'beads-viewer', description: 'Task viewer' },
  { value: 'repo:maptapdat', label: 'maptapdat', description: 'Maptap dashboard' },
  { value: 'repo:shua-ledger', label: 'shua-ledger', description: 'Personal finance' },
  { value: 'repo:agent-gateway', label: 'agent-gateway', description: 'Agent gateway' },
  { value: 'repo:bird', label: 'bird', description: 'Twitter/X data' },
] as const;

export const TASK_TYPES = [
  { value: 'task', label: 'Task' },
  { value: 'bug', label: 'Bug' },
  { value: 'feature', label: 'Feature' },
  { value: 'epic', label: 'Epic' },
  { value: 'chore', label: 'Chore' },
] as const;

export const PRIORITIES = [
  { value: 0, label: 'Critical', color: 'red' },
  { value: 1, label: 'High', color: 'orange' },
  { value: 2, label: 'Medium', color: 'yellow' },
  { value: 3, label: 'Low', color: 'cyan' },
] as const;
