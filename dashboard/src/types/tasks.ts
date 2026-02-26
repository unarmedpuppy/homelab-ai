/**
 * Task types for the Tasks API.
 */

export type TaskStatus = 'OPEN' | 'IN_PROGRESS' | 'BLOCKED' | 'CLOSED';
export type TaskPriority = 'P0' | 'P1' | 'P2' | 'P3';
export type TaskType = 'engineering' | 'personal' | 'home' | 'family' | 'research';
export type TaskAssignee = 'unassigned' | 'human' | 'avery' | 'gilfoyle' | 'ralph' | 'jobin';
export type TaskSource = 'human' | 'avery' | 'claude-code' | 'agent-harness' | 'import';
// Maps to aoe-canvas BuildingType for visual organization
export type BuildingType = 'town-center' | 'barracks' | 'market' | 'university' | 'castle';

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
  // Classification
  type: TaskType;
  assignee: TaskAssignee;
  source: TaskSource;
  // aoe-canvas alignment
  building_type: BuildingType | null;
  project_id: string | null;
  // Extensible metadata (aoe tile coords, job metrics, etc.)
  metadata: Record<string, unknown>;
  created_at: string;
  updated_at: string;
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
  type?: TaskType;
  assignee?: TaskAssignee;
  source?: TaskSource;
  building_type?: BuildingType;
  project_id?: string;
  metadata?: Record<string, unknown>;
}

export interface TaskUpdate {
  title?: string;
  status?: TaskStatus;
  priority?: TaskPriority;
  repo?: string;
  labels?: string[];
  description?: string;
  verification?: string;
  epic?: string;
  type?: TaskType;
  assignee?: TaskAssignee;
  source?: TaskSource;
  building_type?: BuildingType;
  project_id?: string;
  metadata?: Record<string, unknown>;
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
  by_type: Record<string, number>;
  by_assignee: Record<string, number>;
}

export interface TaskFilters {
  repos: string[];
  labels: string[];
  epics: string[];
  project_ids: string[];
  statuses: TaskStatus[];
  priorities: TaskPriority[];
  types: TaskType[];
  assignees: TaskAssignee[];
  sources: TaskSource[];
  building_types: BuildingType[];
}

export interface TaskListParams {
  status?: TaskStatus;
  priority?: TaskPriority;
  repo?: string;
  label?: string;
  epic?: string;
  type?: TaskType;
  assignee?: TaskAssignee;
  source?: TaskSource;
  building_type?: BuildingType;
  project_id?: string;
}
