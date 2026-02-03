import { useState, useCallback } from 'react';
import type { Job } from '../../types/jobs';
import { jobsAPI } from '../../api/client';
import { RetroPanel, RetroButton, RetroSelect } from '../ui';
import { useConditionalPolling } from '../../hooks/useDocumentVisibility';
import { JobCard } from './JobCard';

const ACTIVE_POLL_INTERVAL = 5000; // 5 seconds when jobs are running
const IDLE_POLL_INTERVAL = 30000; // 30 seconds when idle

interface JobQueuePanelProps {
  agentId?: string;
  onCreateJob?: () => void;
  compact?: boolean;
}

type StatusFilter = 'all' | 'active' | 'completed' | 'failed';

export function JobQueuePanel({ agentId, onCreateJob, compact = false }: JobQueuePanelProps) {
  const [jobs, setJobs] = useState<Job[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [statusFilter, setStatusFilter] = useState<StatusFilter>('all');

  const hasActiveJobs = jobs.some(j => j.status === 'running' || j.status === 'pending');

  const fetchJobs = useCallback(async () => {
    try {
      const params: { agent_id?: string; limit?: number } = { limit: 50 };
      if (agentId) {
        params.agent_id = agentId;
      }
      const response = await jobsAPI.list(params);
      setJobs(response.jobs);
      setError(null);
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Failed to fetch jobs');
      console.error('Failed to fetch jobs:', e);
    } finally {
      setLoading(false);
    }
  }, [agentId]);

  useConditionalPolling({
    callback: fetchJobs,
    activeInterval: ACTIVE_POLL_INTERVAL,
    idleInterval: IDLE_POLL_INTERVAL,
    isActive: hasActiveJobs,
    immediate: true,
  });

  const handleCancelJob = async (jobId: string) => {
    try {
      await jobsAPI.cancel(jobId, agentId);
      await fetchJobs();
    } catch (e) {
      console.error('Failed to cancel job:', e);
    }
  };

  const filteredJobs = jobs.filter(job => {
    switch (statusFilter) {
      case 'active':
        return job.status === 'running' || job.status === 'pending';
      case 'completed':
        return job.status === 'completed';
      case 'failed':
        return job.status === 'failed' || job.status === 'cancelled';
      default:
        return true;
    }
  });

  const activeCount = jobs.filter(j => j.status === 'running' || j.status === 'pending').length;
  const completedCount = jobs.filter(j => j.status === 'completed').length;
  const failedCount = jobs.filter(j => j.status === 'failed' || j.status === 'cancelled').length;

  const statusOptions = [
    { value: 'all', label: `All (${jobs.length})` },
    { value: 'active', label: `Active (${activeCount})` },
    { value: 'completed', label: `Completed (${completedCount})` },
    { value: 'failed', label: `Failed (${failedCount})` },
  ];

  const panelTitle = compact ? 'Jobs' : 'Job Queue';

  if (loading && jobs.length === 0) {
    return (
      <RetroPanel title={panelTitle}>
        <div className="text-center py-4 text-[var(--retro-text-muted)] text-sm">
          Loading jobs...
        </div>
      </RetroPanel>
    );
  }

  if (error && jobs.length === 0) {
    return (
      <RetroPanel title={panelTitle}>
        <div className="p-3 bg-[rgba(255,68,68,0.1)] border border-[var(--retro-accent-red)] rounded text-sm">
          <span className="text-[var(--retro-accent-red)]">Error: {error}</span>
        </div>
      </RetroPanel>
    );
  }

  return (
    <RetroPanel title={panelTitle}>
      <div className="space-y-3">
        {/* Header controls */}
        <div className="flex items-center justify-between gap-2 flex-wrap">
          <div className="flex items-center gap-2">
            <RetroSelect
              options={statusOptions}
              value={statusFilter}
              onChange={(e) => setStatusFilter(e.target.value as StatusFilter)}
              size="sm"
            />
          </div>
          <div className="flex items-center gap-2">
            {hasActiveJobs && (
              <span className="text-xs text-[var(--retro-accent-green)] animate-pulse">
                Polling every 5s
              </span>
            )}
            {onCreateJob && (
              <RetroButton variant="primary" size="sm" onClick={onCreateJob}>
                New Job
              </RetroButton>
            )}
          </div>
        </div>

        {/* Job list */}
        {filteredJobs.length === 0 ? (
          <div className="text-center py-8 text-[var(--retro-text-muted)] text-sm uppercase tracking-wider">
            {statusFilter === 'all' ? 'No jobs yet' : `No ${statusFilter} jobs`}
          </div>
        ) : (
          <div className="space-y-2 max-h-[500px] overflow-y-auto">
            {filteredJobs.map(job => (
              <JobCard
                key={job.job_id}
                job={job}
                onCancel={handleCancelJob}
                showAgent={!agentId}
              />
            ))}
          </div>
        )}
      </div>
    </RetroPanel>
  );
}

export default JobQueuePanel;
