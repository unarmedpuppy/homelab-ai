/**
 * Task types for the Tasks API.
 */

export type TaskStatus = 'OPEN' | 'IN_PROGRESS' | 'BLOCKED' | 'CLOSED';
export type TaskPriority = 'P0' | 'P1' | 'P2' | 'P3';

export interface Task {
  id: string;
  title: string;
  status: TaskStatus;
  priority: TaskPriority;
  repo: string;
  labels: string[];
  description: string;
  verification: string;
  epic: string | null;
}

export interface TaskCreate {
  id: string;
  title: string;
  priority?: TaskPriority;
  repo: string;
  labels?: string[];
  description?: string;
  verification?: string;
  epic?: string;
}

export interface TaskUpdate {
  title?: string;
  status?: TaskStatus;
  priority?: TaskPriority;
  repo?: string;
  labels?: string[];
  description?: string;
  verification?: string;
}

export interface TaskListResponse {
  tasks: Task[];
  total: number;
}

export interface TaskStats {
  total: number;
  by_status: Record<string, number>;
  by_priority: Record<string, number>;
  by_repo: Record<string, number>;
}

export interface TaskFilters {
  repos: string[];
  labels: string[];
  epics: string[];
  statuses: TaskStatus[];
  priorities: TaskPriority[];
}

export interface TaskListParams {
  status?: TaskStatus;
  priority?: TaskPriority;
  repo?: string;
  label?: string;
  epic?: string;
}
