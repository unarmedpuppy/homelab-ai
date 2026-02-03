/**
 * Job types - for agent job management
 */

export type JobStatus = 'pending' | 'running' | 'completed' | 'failed' | 'cancelled';

export interface Job {
  job_id: string;
  agent_id: string;
  prompt: string;
  model: string;
  status: JobStatus;
  created_at: string;
  started_at: string | null;
  completed_at: string | null;
  result: string | null;
  error: string | null;
  turns: number;
  tokens_used: number | null;
}

export interface JobCreateRequest {
  agent_id: string;
  prompt: string;
  model?: string;
  working_directory?: string;
  allowed_tools?: string[];
  max_turns?: number;
}

export interface JobListResponse {
  jobs: Job[];
  total: number;
}

export interface JobListParams {
  agent_id?: string;
  status?: JobStatus;
  limit?: number;
}
