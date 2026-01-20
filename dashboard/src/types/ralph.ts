/**
 * Ralph Wiggum types - Autonomous task runner
 */

export interface RalphStatus {
  running: boolean;
  status: string; // idle, running, stopping, completed
  label?: string;
  total_tasks: number;
  completed_tasks: number;
  failed_tasks: number;
  current_task?: string;
  current_task_title?: string;
  started_at?: string;
  last_update?: string;
  message?: string;
}

export interface RalphStartParams {
  label: string;
  priority?: number;
  max_tasks?: number;
  dry_run?: boolean;
}

export interface RalphStartResponse {
  message: string;
  label: string;
  status_url: string;
  stop_url: string;
  instances_url: string;
}

export interface RalphLogs {
  logs: string[];
  count: number;
  label?: string;
  log_file?: string;
  message?: string;
}
