import { useState, useEffect, useCallback } from 'react';
import type { Agent, ScheduleJob } from '../../types/agents';
import { agentsAPI } from '../../api/client';
import { RetroButton } from '../ui';

interface AgentScheduleTabProps {
  agent: Agent;
}

function formatNextRun(nextRun: string | null): string {
  if (!nextRun) return '—';
  const d = new Date(nextRun);
  const now = new Date();
  const diffMs = d.getTime() - now.getTime();
  const diffMins = Math.round(diffMs / 60000);
  if (diffMins < 0) return 'overdue';
  if (diffMins < 60) return `in ${diffMins}m`;
  const diffHours = Math.round(diffMins / 60);
  if (diffHours < 24) return `in ${diffHours}h`;
  return d.toLocaleDateString(undefined, { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' });
}

function formatCadence(job: ScheduleJob): string {
  if (job.cron) return `cron: ${job.cron}`;
  if (job.interval_hours) return `every ${job.interval_hours}h`;
  return job.action;
}

export function AgentScheduleTab({ agent }: AgentScheduleTabProps) {
  const [jobs, setJobs] = useState<ScheduleJob[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const isOnline = agent.health.status === 'online';

  const fetchSchedule = useCallback(async () => {
    if (!isOnline) {
      setLoading(false);
      setError('Agent is offline — cannot fetch schedule');
      return;
    }
    try {
      setLoading(true);
      setError(null);
      const data = await agentsAPI.getSchedule(agent.id);
      setJobs(data.jobs);
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Failed to fetch schedule');
    } finally {
      setLoading(false);
    }
  }, [agent.id, isOnline]);

  useEffect(() => {
    fetchSchedule();
  }, [fetchSchedule]);

  if (loading) {
    return (
      <div className="flex items-center justify-center h-32 text-[var(--retro-text-muted)] text-sm">
        Loading schedule...
      </div>
    );
  }

  if (error) {
    return (
      <div className="p-4">
        <div className="p-3 bg-[rgba(255,68,68,0.1)] border border-[var(--retro-accent-red)] rounded text-xs text-[var(--retro-accent-red)]">
          {error}
        </div>
      </div>
    );
  }

  const enabled = jobs.filter((j) => j.enabled);
  const disabled = jobs.filter((j) => !j.enabled);

  return (
    <div className="flex flex-col h-full overflow-hidden">
      {/* Toolbar */}
      <div className="p-3 border-b border-[var(--retro-border)] flex items-center justify-between">
        <span className="text-xs text-[var(--retro-text-muted)]">
          {enabled.length} active · {disabled.length} disabled
        </span>
        <RetroButton variant="ghost" size="sm" onClick={fetchSchedule}>
          Refresh
        </RetroButton>
      </div>

      <div className="flex-1 overflow-y-auto p-3 space-y-2">
        {jobs.length === 0 ? (
          <div className="text-center py-8 text-[var(--retro-text-muted)] text-sm">
            No scheduled jobs configured
          </div>
        ) : (
          jobs.map((job) => (
            <div
              key={job.name}
              className={`p-3 border rounded ${
                job.enabled
                  ? 'bg-[var(--retro-bg-medium)] border-[var(--retro-border)]'
                  : 'bg-[var(--retro-bg-dark)] border-[var(--retro-border)] opacity-50'
              }`}
            >
              <div className="flex items-center justify-between mb-1.5">
                <div className="flex items-center gap-2">
                  <span className="font-mono text-xs font-bold text-[var(--retro-text-primary)]">
                    {job.name}
                  </span>
                  <span className={`text-xs font-bold uppercase ${job.enabled ? 'text-[var(--retro-accent-green)]' : 'text-[var(--retro-text-muted)]'}`}>
                    {job.enabled ? 'active' : 'disabled'}
                  </span>
                </div>
                {job.next_run && job.enabled && (
                  <span className="text-xs text-[var(--retro-accent-yellow)]">
                    {formatNextRun(job.next_run)}
                  </span>
                )}
              </div>
              <div className="text-xs text-[var(--retro-text-muted)] font-mono mb-1">
                {formatCadence(job)}
              </div>
              {job.prompt_preview && (
                <div className="text-xs text-[var(--retro-text-muted)] italic truncate">
                  {job.prompt_preview}
                </div>
              )}
              {job.deliver_to && (
                <div className="text-xs text-[var(--retro-text-muted)] mt-1">
                  → {job.deliver_to.channel}
                  {job.deliver_to.contact ? ` / ${job.deliver_to.contact}` : ''}
                </div>
              )}
            </div>
          ))
        )}
      </div>
    </div>
  );
}

export default AgentScheduleTab;
