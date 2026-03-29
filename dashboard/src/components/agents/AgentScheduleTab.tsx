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
  return job.action ?? '—';
}

export function AgentScheduleTab({ agent }: AgentScheduleTabProps) {
  const [jobs, setJobs] = useState<ScheduleJob[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [togglingJob, setTogglingJob] = useState<string | null>(null);
  const [triggeringJob, setTriggeringJob] = useState<string | null>(null);

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

  const handleToggle = async (job: ScheduleJob) => {
    setTogglingJob(job.name);
    try {
      await agentsAPI.patchScheduleJob(agent.id, job.name, { enabled: !job.enabled });
      // Optimistic update
      setJobs((prev) => prev.map((j) => j.name === job.name ? { ...j, enabled: !j.enabled } : j));
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Failed to toggle job');
    } finally {
      setTogglingJob(null);
    }
  };

  const handleTrigger = async (job: ScheduleJob) => {
    setTriggeringJob(job.name);
    try {
      await agentsAPI.triggerScheduleJob(agent.id, job.name);
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Failed to trigger job');
    } finally {
      setTriggeringJob(null);
    }
  };

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
                  : 'bg-[var(--retro-bg-dark)] border-[var(--retro-border)] opacity-60'
              }`}
            >
              {/* Header row */}
              <div className="flex items-center justify-between mb-1.5">
                <div className="flex items-center gap-2 min-w-0">
                  <span className="font-mono text-xs font-bold text-[var(--retro-text-primary)] truncate">
                    {job.name}
                  </span>
                  <span className={`text-xs font-bold uppercase shrink-0 ${job.enabled ? 'text-[var(--retro-accent-green)]' : 'text-[var(--retro-text-muted)]'}`}>
                    {job.enabled ? 'active' : 'disabled'}
                  </span>
                </div>
                {job.next_run && job.enabled && (
                  <span className="text-xs text-[var(--retro-accent-yellow)] shrink-0 ml-2">
                    {formatNextRun(job.next_run)}
                  </span>
                )}
              </div>

              {/* Cadence */}
              <div className="text-xs text-[var(--retro-text-muted)] font-mono mb-1.5">
                {formatCadence(job)}
              </div>

              {/* Prompt preview */}
              {job.prompt_preview && (
                <div className="text-xs text-[var(--retro-text-muted)] italic truncate mb-2">
                  {job.prompt_preview}
                </div>
              )}

              {/* Deliver-to */}
              {job.deliver_to && (
                <div className="text-xs text-[var(--retro-text-muted)] mb-2">
                  → {job.deliver_to.channel}
                  {job.deliver_to.contact ? ` / ${job.deliver_to.contact}` : ''}
                </div>
              )}

              {/* Actions */}
              <div className="flex items-center gap-2 mt-2">
                <RetroButton
                  variant="ghost"
                  size="sm"
                  onClick={() => handleToggle(job)}
                  disabled={togglingJob === job.name}
                >
                  {togglingJob === job.name ? '...' : job.enabled ? 'Disable' : 'Enable'}
                </RetroButton>
                {job.enabled && (
                  <RetroButton
                    variant="secondary"
                    size="sm"
                    onClick={() => handleTrigger(job)}
                    disabled={triggeringJob === job.name}
                  >
                    {triggeringJob === job.name ? 'Firing...' : 'Run Now'}
                  </RetroButton>
                )}
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  );
}

export default AgentScheduleTab;
