import type { Job, JobStatus } from '../../types/jobs';
import { RetroCard, RetroButton, RetroProgress } from '../ui';

interface JobCardProps {
  job: Job;
  onCancel?: (jobId: string) => void;
  onClick?: () => void;
  showAgent?: boolean;
}

const statusConfig: Record<JobStatus, { label: string; color: string; bg: string }> = {
  pending: { label: 'Pending', color: 'var(--retro-text-muted)', bg: 'rgba(92, 107, 138, 0.2)' },
  running: { label: 'Running', color: 'var(--retro-accent-cyan)', bg: 'rgba(91, 192, 190, 0.2)' },
  completed: { label: 'Completed', color: 'var(--retro-accent-green)', bg: 'rgba(0, 255, 65, 0.2)' },
  failed: { label: 'Failed', color: 'var(--retro-accent-red)', bg: 'rgba(255, 68, 68, 0.2)' },
  cancelled: { label: 'Cancelled', color: 'var(--retro-accent-yellow)', bg: 'rgba(255, 215, 0, 0.2)' },
};

function formatTimeAgo(dateString: string): string {
  const date = new Date(dateString);
  const now = new Date();
  const diffMs = now.getTime() - date.getTime();
  const diffSecs = Math.floor(diffMs / 1000);
  const diffMins = Math.floor(diffSecs / 60);
  const diffHours = Math.floor(diffMins / 60);
  const diffDays = Math.floor(diffHours / 24);

  if (diffSecs < 60) return `${diffSecs}s ago`;
  if (diffMins < 60) return `${diffMins}m ago`;
  if (diffHours < 24) return `${diffHours}h ago`;
  return `${diffDays}d ago`;
}

function formatDuration(startedAt: string | null, completedAt: string | null): string | null {
  if (!startedAt) return null;
  const start = new Date(startedAt);
  const end = completedAt ? new Date(completedAt) : new Date();
  const diffMs = end.getTime() - start.getTime();
  const diffSecs = Math.floor(diffMs / 1000);
  const mins = Math.floor(diffSecs / 60);
  const secs = diffSecs % 60;
  if (mins > 0) return `${mins}m ${secs}s`;
  return `${secs}s`;
}

function truncatePrompt(prompt: string, maxLength: number = 80): string {
  if (prompt.length <= maxLength) return prompt;
  return prompt.slice(0, maxLength) + '...';
}

export function JobCard({ job, onCancel, onClick, showAgent = true }: JobCardProps) {
  const isRunning = job.status === 'running';
  const isPending = job.status === 'pending';
  const canCancel = isRunning || isPending;
  const duration = formatDuration(job.started_at, job.completed_at);

  const handleCancel = (e: React.MouseEvent) => {
    e.stopPropagation();
    onCancel?.(job.job_id);
  };

  return (
    <RetroCard onClick={onClick} className="hover:bg-[var(--retro-bg-light)] transition-colors">
      <div className="flex flex-col gap-2">
        {/* Header row */}
        <div className="flex items-start justify-between gap-2">
          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-2 flex-wrap">
              <span
                className="text-xs font-bold uppercase tracking-wider px-2 py-0.5 rounded"
                style={{
                  color: statusConfig[job.status].color,
                  backgroundColor: statusConfig[job.status].bg,
                  border: `1px solid ${statusConfig[job.status].color}`,
                }}
              >
                {statusConfig[job.status].label}
              </span>
              {showAgent && (
                <span className="text-xs text-[var(--retro-text-muted)] font-mono uppercase">
                  {job.agent_id}
                </span>
              )}
              <span className="text-xs text-[var(--retro-text-muted)]">
                {formatTimeAgo(job.created_at)}
              </span>
            </div>
          </div>
          {canCancel && onCancel && (
            <RetroButton
              variant="danger"
              size="sm"
              onClick={handleCancel}
            >
              Cancel
            </RetroButton>
          )}
        </div>

        {/* Prompt */}
        <div className="text-sm text-[var(--retro-text-primary)] font-mono">
          {truncatePrompt(job.prompt)}
        </div>

        {/* Progress indicator for running jobs */}
        {isRunning && (
          <div className="mt-1">
            <RetroProgress value={-1} showLabel={false} />
          </div>
        )}

        {/* Meta info row */}
        <div className="flex items-center gap-4 text-xs text-[var(--retro-text-muted)]">
          <span className="uppercase">Model: {job.model}</span>
          {duration && (
            <span>Duration: {duration}</span>
          )}
          {job.turns > 0 && (
            <span>Turns: {job.turns}</span>
          )}
          {job.tokens_used && (
            <span>Tokens: {job.tokens_used.toLocaleString()}</span>
          )}
        </div>

        {/* Error message */}
        {job.error && (
          <div className="mt-2 p-2 bg-[rgba(255,68,68,0.1)] border border-[var(--retro-accent-red)] rounded text-xs text-[var(--retro-accent-red)] font-mono">
            {job.error}
          </div>
        )}

        {/* Result preview */}
        {job.result && job.status === 'completed' && (
          <div className="mt-2 p-2 bg-[var(--retro-bg-dark)] border border-[var(--retro-border)] rounded text-xs text-[var(--retro-text-secondary)] font-mono max-h-24 overflow-hidden">
            {truncatePrompt(job.result, 200)}
          </div>
        )}
      </div>
    </RetroCard>
  );
}

export default JobCard;
