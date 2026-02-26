import { Task } from '../types/game';

const BASE = '/api/tasks';

export async function fetchTasks(params: { status?: string; type?: string } = {}): Promise<Task[]> {
  const qs = new URLSearchParams();
  if (params.status) qs.set('status', params.status);
  if (params.type) qs.set('type', params.type);
  const res = await fetch(`${BASE}/v1/tasks?${qs}`);
  if (!res.ok) return [];
  const data = await res.json();
  return data.tasks ?? [];
}

export async function claimTask(id: string): Promise<void> {
  await fetch(`${BASE}/v1/tasks/${id}/claim`, { method: 'POST' });
}

export async function closeTask(id: string): Promise<void> {
  await fetch(`${BASE}/v1/tasks/${id}/close`, { method: 'POST' });
}
