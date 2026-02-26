import type { Job, Project, MapState } from '../types/game';

const BASE = '/api/harness';

export async function fetchJobs(limit = 50): Promise<Job[]> {
  const res = await fetch(`${BASE}/v1/jobs?limit=${limit}`);
  if (!res.ok) return [];
  const data = await res.json();
  return data.jobs || [];
}

export async function createJob(payload: {
  prompt: string;
  agent?: string;
  working_directory?: string;
  model?: string;
  permission_mode?: string;
}): Promise<{ job_id: string; status: string; poll_url: string }> {
  const res = await fetch(`${BASE}/v1/jobs`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  });
  if (!res.ok) throw new Error(`Failed to create job: ${res.status}`);
  return res.json();
}

export async function cancelJob(jobId: string): Promise<void> {
  await fetch(`${BASE}/v1/jobs/${jobId}/cancel`, { method: 'POST' });
}

export async function fetchProjects(): Promise<Project[]> {
  const res = await fetch(`${BASE}/v1/projects`);
  if (!res.ok) return [];
  const data = await res.json();
  return data.projects || [];
}

export async function createProject(payload: {
  name: string;
  type: string;
  building_type: string;
  description?: string;
}): Promise<Project> {
  const res = await fetch(`${BASE}/v1/projects`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  });
  if (!res.ok) throw new Error(`Failed to create project: ${res.status}`);
  return res.json();
}

export async function deleteProject(id: string): Promise<void> {
  await fetch(`${BASE}/v1/projects/${id}`, { method: 'DELETE' });
}

export async function fetchMapState(): Promise<MapState | null> {
  const res = await fetch(`${BASE}/v1/map/state`);
  if (!res.ok) return null;
  return res.json();
}

export async function saveMapState(state: MapState): Promise<void> {
  await fetch(`${BASE}/v1/map/state`, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(state),
  });
}

export async function fetchHarnessHealth() {
  const res = await fetch(`${BASE}/health`);
  if (!res.ok) return null;
  return res.json();
}
