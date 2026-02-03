import { useState, useCallback } from 'react';
import type { Agent } from '../../types/agents';
import type { Job } from '../../types/jobs';
import { jobsAPI } from '../../api/client';
import { RetroButton, RetroSelect, RetroPanel } from '../ui';
import { useConditionalPolling } from '../../hooks/useDocumentVisibility';
import { JobCard } from './JobCard';

interface QuickInteractProps {
  agent: Agent;
}

const MODEL_OPTIONS = [
  { value: 'haiku', label: 'Haiku (Fast)' },
  { value: 'sonnet', label: 'Sonnet (Default)' },
  { value: 'opus', label: 'Opus (Best)' },
];

const ACTIVE_POLL_INTERVAL = 3000; // 3 seconds when job is running
const IDLE_POLL_INTERVAL = 30000; // 30 seconds when idle

export function QuickInteract({ agent }: QuickInteractProps) {
  const [prompt, setPrompt] = useState('');
  const [model, setModel] = useState('sonnet');
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [currentJob, setCurrentJob] = useState<Job | null>(null);
  const [recentJobs, setRecentJobs] = useState<Job[]>([]);

  const isOnline = agent.health.status === 'online';
  const hasActiveJob = currentJob && (currentJob.status === 'running' || currentJob.status === 'pending');
  const canSubmit = isOnline && prompt.trim() && !submitting && !hasActiveJob;

  const fetchJobStatus = useCallback(async () => {
    if (!currentJob) return;

    try {
      const job = await jobsAPI.get(currentJob.job_id, agent.id);
      setCurrentJob(job);

      if (job.status === 'completed' || job.status === 'failed' || job.status === 'cancelled') {
        setRecentJobs(prev => [job, ...prev.slice(0, 4)]);
        setCurrentJob(null);
      }
    } catch (e) {
      console.error('Failed to fetch job status:', e);
    }
  }, [currentJob, agent.id]);

  useConditionalPolling({
    callback: fetchJobStatus,
    activeInterval: ACTIVE_POLL_INTERVAL,
    idleInterval: IDLE_POLL_INTERVAL,
    isActive: !!hasActiveJob,
    immediate: false,
  });

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!canSubmit) return;

    setSubmitting(true);
    setError(null);

    try {
      const job = await jobsAPI.create({
        agent_id: agent.id,
        prompt: prompt.trim(),
        model,
      });
      setCurrentJob(job);
      setPrompt('');
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Failed to create job');
    } finally {
      setSubmitting(false);
    }
  };

  const handleCancelJob = async (jobId: string) => {
    try {
      await jobsAPI.cancel(jobId, agent.id);
      if (currentJob?.job_id === jobId) {
        setCurrentJob(null);
      }
    } catch (e) {
      console.error('Failed to cancel job:', e);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && (e.metaKey || e.ctrlKey)) {
      handleSubmit(e);
    }
  };

  if (!isOnline) {
    return (
      <div className="h-full flex items-center justify-center p-4">
        <div className="text-center">
          <div className="text-[var(--retro-accent-yellow)] text-lg mb-2">Agent Offline</div>
          <p className="text-sm text-[var(--retro-text-muted)]">
            Cannot interact with offline agents
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="h-full flex flex-col p-4 overflow-y-auto">
      {/* Quick prompt form */}
      <RetroPanel title="Quick Prompt">
        <form onSubmit={handleSubmit} className="space-y-3">
          <div className="space-y-1">
            <textarea
              value={prompt}
              onChange={(e) => setPrompt(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder="Enter a prompt for the agent..."
              rows={3}
              className="retro-input w-full resize-none font-mono text-sm"
              disabled={!isOnline || !!hasActiveJob}
            />
            <div className="text-xs text-[var(--retro-text-muted)]">
              Press Cmd+Enter or Ctrl+Enter to submit
            </div>
          </div>

          <div className="flex items-center justify-between gap-2">
            <RetroSelect
              options={MODEL_OPTIONS}
              value={model}
              onChange={(e) => setModel(e.target.value)}
              size="sm"
              disabled={!!hasActiveJob}
            />
            <RetroButton
              type="submit"
              variant="primary"
              size="sm"
              disabled={!canSubmit}
            >
              {submitting ? 'Sending...' : hasActiveJob ? 'Job Running...' : 'Send'}
            </RetroButton>
          </div>

          {error && (
            <div className="p-2 bg-[rgba(255,68,68,0.1)] border border-[var(--retro-accent-red)] rounded text-xs text-[var(--retro-accent-red)]">
              {error}
            </div>
          )}
        </form>
      </RetroPanel>

      {/* Current job */}
      {currentJob && (
        <div className="mt-4">
          <RetroPanel title="Current Job">
            <JobCard
              job={currentJob}
              onCancel={handleCancelJob}
              showAgent={false}
            />
            {hasActiveJob && (
              <div className="mt-2 text-xs text-[var(--retro-accent-cyan)] animate-pulse text-center">
                Polling every 3 seconds...
              </div>
            )}
          </RetroPanel>
        </div>
      )}

      {/* Recent jobs */}
      {recentJobs.length > 0 && (
        <div className="mt-4">
          <RetroPanel title="Recent Jobs">
            <div className="space-y-2">
              {recentJobs.map(job => (
                <JobCard
                  key={job.job_id}
                  job={job}
                  showAgent={false}
                />
              ))}
            </div>
          </RetroPanel>
        </div>
      )}
    </div>
  );
}

export default QuickInteract;
