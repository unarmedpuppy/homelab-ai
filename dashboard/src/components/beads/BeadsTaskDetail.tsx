import { useState } from 'react';
import type { BeadTask } from '../../types/beads';
import {
  RetroButton,
  RetroPanel,
  RetroBadge,
  getPriorityVariant,
  getPriorityLabel,
  getStatusVariant,
  getStatusLabel,
} from '../ui';
import { beadsAPI } from '../../api/client';

interface BeadsTaskDetailProps {
  task: BeadTask;
  onClose: () => void;
  onUpdate: () => void;
}

export function BeadsTaskDetail({
  task,
  onClose,
  onUpdate,
}: BeadsTaskDetailProps) {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleClaim = async () => {
    setLoading(true);
    setError(null);
    try {
      await beadsAPI.updateTask(task.id, { status: 'in_progress' });
      onUpdate();
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Failed to claim task');
    } finally {
      setLoading(false);
    }
  };

  const handleComplete = async () => {
    setLoading(true);
    setError(null);
    try {
      await beadsAPI.updateTask(task.id, { status: 'closed' });
      onUpdate();
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Failed to complete task');
    } finally {
      setLoading(false);
    }
  };

  const handleReopen = async () => {
    setLoading(true);
    setError(null);
    try {
      await beadsAPI.updateTask(task.id, { status: 'open' });
      onUpdate();
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Failed to reopen task');
    } finally {
      setLoading(false);
    }
  };

  const repoLabel = task.labels.find(l => l.startsWith('repo:'));
  const otherLabels = task.labels.filter(l => !l.startsWith('repo:'));

  return (
    <div className="h-full flex flex-col bg-[var(--retro-bg-card)]">
      {/* Header */}
      <div className="flex items-center justify-between p-4 border-b border-[var(--retro-border)]">
        <h2 className="text-sm font-bold uppercase tracking-wider text-[var(--retro-text-secondary)]">
          Task Details
        </h2>
        <RetroButton variant="ghost" size="sm" onClick={onClose}>
          ✕
        </RetroButton>
      </div>

      {/* Content */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {/* ID */}
        <div className="text-xs text-[var(--retro-text-muted)] font-mono">
          {task.id}
        </div>

        {/* Title */}
        <h1 className="text-lg font-bold text-[var(--retro-text-primary)]">
          {task.title}
        </h1>

        {/* Status & Priority */}
        <div className="flex flex-wrap gap-2">
          <RetroBadge variant={getStatusVariant(task.status)} size="md">
            {getStatusLabel(task.status)}
          </RetroBadge>
          <RetroBadge variant={getPriorityVariant(task.priority)} size="md">
            {getPriorityLabel(task.priority)}
          </RetroBadge>
          <RetroBadge variant="label" size="md">
            {task.issue_type.toUpperCase()}
          </RetroBadge>
        </div>

        {/* Labels */}
        <RetroPanel title="Labels">
          <div className="flex flex-wrap gap-2">
            {repoLabel && (
              <span className="text-xs px-2 py-1 bg-[var(--retro-bg-dark)] text-[var(--retro-accent-blue)] rounded border border-[var(--retro-accent-blue)]">
                {repoLabel}
              </span>
            )}
            {otherLabels.map(label => (
              <span
                key={label}
                className="text-xs px-2 py-1 bg-[var(--retro-bg-dark)] text-[var(--retro-text-secondary)] rounded border border-[var(--retro-border)]"
              >
                {label}
              </span>
            ))}
            {task.labels.length === 0 && (
              <span className="text-xs text-[var(--retro-text-muted)]">No labels</span>
            )}
          </div>
        </RetroPanel>

        {/* Description */}
        {task.description && (
          <RetroPanel title="Description">
            <div className="text-sm text-[var(--retro-text-primary)] whitespace-pre-wrap">
              {task.description}
            </div>
          </RetroPanel>
        )}

        {/* Metadata */}
        <RetroPanel title="Info">
          <div className="grid grid-cols-2 gap-2 text-xs">
            <div>
              <span className="text-[var(--retro-text-muted)]">Age:</span>{' '}
              <span className="text-[var(--retro-text-primary)]">{task.age_days} days</span>
            </div>
            <div>
              <span className="text-[var(--retro-text-muted)]">Created:</span>{' '}
              <span className="text-[var(--retro-text-primary)]">
                {new Date(task.created_at).toLocaleDateString()}
              </span>
            </div>
            {task.owner && (
              <div className="col-span-2">
                <span className="text-[var(--retro-text-muted)]">Owner:</span>{' '}
                <span className="text-[var(--retro-text-primary)]">{task.owner}</span>
              </div>
            )}
          </div>
        </RetroPanel>

        {/* Blocked by */}
        {task.blocked_by && task.blocked_by.length > 0 && (
          <RetroPanel title="Blocked By">
            <div className="space-y-1">
              {task.blocked_by.map(id => (
                <div
                  key={id}
                  className="text-xs font-mono text-[var(--retro-accent-red)]"
                >
                  {id}
                </div>
              ))}
            </div>
          </RetroPanel>
        )}

        {/* Error */}
        {error && (
          <div className="p-3 bg-[rgba(255,68,68,0.1)] border border-[var(--retro-accent-red)] rounded text-sm text-[var(--retro-accent-red)]">
            {error}
          </div>
        )}
      </div>

      {/* Actions */}
      <div className="p-4 border-t border-[var(--retro-border)] space-y-2">
        {task.status === 'open' && (
          <RetroButton
            variant="primary"
            className="w-full"
            onClick={handleClaim}
            disabled={loading || Boolean(task.dependency_count && task.dependency_count > 0)}
            loading={loading}
          >
            {task.dependency_count && task.dependency_count > 0 ? 'BLOCKED' : 'CLAIM TASK'}
          </RetroButton>
        )}
        {task.status === 'in_progress' && (
          <RetroButton
            variant="success"
            className="w-full"
            onClick={handleComplete}
            disabled={loading}
            loading={loading}
          >
            MARK COMPLETE
          </RetroButton>
        )}
        {task.status === 'closed' && (
          <RetroButton
            variant="warning"
            className="w-full"
            onClick={handleReopen}
            disabled={loading}
            loading={loading}
          >
            REOPEN TASK
          </RetroButton>
        )}
      </div>
    </div>
  );
}

export default BeadsTaskDetail;
