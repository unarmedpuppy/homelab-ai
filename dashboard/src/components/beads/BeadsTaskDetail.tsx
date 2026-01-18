import { useState } from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import type { Components } from 'react-markdown';
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
  onSelectTask?: (taskId: string) => void;
}

// Retro-themed markdown components
const markdownComponents: Components = {
  pre: ({ children }) => (
    <pre className="bg-[var(--retro-bg-dark)] border border-[var(--retro-border)] rounded p-3 my-2 overflow-x-auto text-sm font-mono">
      {children}
    </pre>
  ),
  code: ({ className, children, ...props }) => {
    const isInline = !className;
    if (isInline) {
      return (
        <code className="bg-[var(--retro-bg-dark)] px-1.5 py-0.5 rounded text-[var(--retro-accent-cyan)] text-sm font-mono" {...props}>
          {children}
        </code>
      );
    }
    return (
      <code className="text-[var(--retro-text-primary)]" {...props}>
        {children}
      </code>
    );
  },
  h1: ({ children }) => <h1 className="text-base font-bold text-[var(--retro-text-primary)] mt-3 mb-2">{children}</h1>,
  h2: ({ children }) => <h2 className="text-sm font-semibold text-[var(--retro-text-primary)] mt-2 mb-1">{children}</h2>,
  h3: ({ children }) => <h3 className="text-sm font-semibold text-[var(--retro-text-secondary)] mt-2 mb-1">{children}</h3>,
  ul: ({ children }) => <ul className="list-disc list-inside my-2 space-y-1 text-[var(--retro-text-primary)]">{children}</ul>,
  ol: ({ children }) => <ol className="list-decimal list-inside my-2 space-y-1 text-[var(--retro-text-primary)]">{children}</ol>,
  li: ({ children }) => <li className="text-[var(--retro-text-primary)]">{children}</li>,
  a: ({ href, children }) => (
    <a href={href} className="text-[var(--retro-accent-blue)] hover:underline" target="_blank" rel="noopener noreferrer">
      {children}
    </a>
  ),
  p: ({ children }) => <p className="my-2 text-[var(--retro-text-primary)]">{children}</p>,
  blockquote: ({ children }) => (
    <blockquote className="border-l-4 border-[var(--retro-border)] pl-4 my-2 text-[var(--retro-text-muted)] italic">
      {children}
    </blockquote>
  ),
  table: ({ children }) => (
    <div className="overflow-x-auto my-2">
      <table className="min-w-full border border-[var(--retro-border)] text-sm">{children}</table>
    </div>
  ),
  thead: ({ children }) => <thead className="bg-[var(--retro-bg-light)]">{children}</thead>,
  th: ({ children }) => <th className="px-3 py-2 border border-[var(--retro-border)] text-left font-semibold text-[var(--retro-text-primary)]">{children}</th>,
  td: ({ children }) => <td className="px-3 py-2 border border-[var(--retro-border)] text-[var(--retro-text-primary)]">{children}</td>,
  hr: () => <hr className="border-[var(--retro-border)] my-4" />,
  strong: ({ children }) => <strong className="font-bold text-[var(--retro-text-primary)]">{children}</strong>,
  em: ({ children }) => <em className="italic">{children}</em>,
};

export function BeadsTaskDetail({
  task,
  onClose,
  onUpdate,
  onSelectTask,
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

  const handleBlockedByClick = (blockedId: string) => {
    if (onSelectTask) {
      onSelectTask(blockedId);
    }
  };

  const repoLabel = task.labels.find(l => l.startsWith('repo:'));
  const otherLabels = task.labels.filter(l => !l.startsWith('repo:'));

  // Format relative time for display
  const formatRelativeTime = (dateString: string) => {
    const date = new Date(dateString);
    const now = new Date();
    const diffMs = now.getTime() - date.getTime();
    const diffMins = Math.floor(diffMs / 60000);
    const diffHours = Math.floor(diffMs / 3600000);
    const diffDays = Math.floor(diffMs / 86400000);

    if (diffMins < 60) return `${diffMins} min ago`;
    if (diffHours < 24) return `${diffHours} hours ago`;
    if (diffDays < 7) return `${diffDays} days ago`;
    return date.toLocaleDateString();
  };

  return (
    <div className="h-full flex flex-col bg-[var(--retro-bg-card)] retro-task-detail-panel">
      {/* Header */}
      <div className="flex items-center justify-between p-4 border-b border-[var(--retro-border)] bg-[var(--retro-bg-light)]">
        <h2 className="text-sm font-bold uppercase tracking-wider text-[var(--retro-text-secondary)]">
          Task Details
        </h2>
        <RetroButton variant="ghost" size="sm" onClick={onClose}>
          ✕
        </RetroButton>
      </div>

      {/* Content */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {/* Title */}
        <div>
          <div className="text-xs text-[var(--retro-text-muted)] font-mono mb-1">
            {task.id}
          </div>
          <h1 className="text-lg font-bold text-[var(--retro-text-primary)] leading-tight">
            {task.title}
          </h1>
        </div>

        {/* Status & Priority Row */}
        <div className="flex flex-wrap gap-2 items-center">
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
        <RetroPanel title="Labels" collapsible defaultCollapsed={false}>
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
          <RetroPanel title="Description" collapsible defaultCollapsed={false}>
            <div className="text-sm retro-markdown-content">
              <ReactMarkdown remarkPlugins={[remarkGfm]} components={markdownComponents}>
                {task.description}
              </ReactMarkdown>
            </div>
          </RetroPanel>
        )}

        {/* Blocked by */}
        {task.blocked_by && task.blocked_by.length > 0 && (
          <RetroPanel title="Blocked By" collapsible defaultCollapsed={false}>
            <div className="space-y-2">
              {task.blocked_by.map(id => (
                <button
                  key={id}
                  onClick={() => handleBlockedByClick(id)}
                  className="w-full text-left text-xs font-mono px-2 py-1.5 rounded bg-[var(--retro-bg-dark)] border border-[var(--retro-accent-red)] text-[var(--retro-accent-red)] hover:bg-[rgba(255,68,68,0.1)] transition-colors cursor-pointer flex items-center gap-2"
                  title={`View task ${id}`}
                >
                  <span className="text-[0.625rem]">●</span>
                  <span className="truncate">{id}</span>
                </button>
              ))}
            </div>
          </RetroPanel>
        )}

        {/* Metadata */}
        <RetroPanel title="Info" collapsible defaultCollapsed={false}>
          <div className="grid grid-cols-2 gap-3 text-xs">
            <div>
              <span className="text-[var(--retro-text-muted)] block">Age</span>
              <span className="text-[var(--retro-text-primary)] font-medium">{task.age_days} days</span>
            </div>
            <div>
              <span className="text-[var(--retro-text-muted)] block">Created</span>
              <span className="text-[var(--retro-text-primary)] font-medium">
                {formatRelativeTime(task.created_at)}
              </span>
            </div>
            <div>
              <span className="text-[var(--retro-text-muted)] block">Updated</span>
              <span className="text-[var(--retro-text-primary)] font-medium">
                {formatRelativeTime(task.updated_at)}
              </span>
            </div>
            {task.owner && (
              <div>
                <span className="text-[var(--retro-text-muted)] block">Owner</span>
                <span className="text-[var(--retro-text-primary)] font-medium">{task.owner}</span>
              </div>
            )}
            {task.dependency_count !== undefined && task.dependency_count > 0 && (
              <div>
                <span className="text-[var(--retro-text-muted)] block">Dependencies</span>
                <span className="text-[var(--retro-accent-red)] font-medium">{task.dependency_count} blocking</span>
              </div>
            )}
            {task.dependent_count !== undefined && task.dependent_count > 0 && (
              <div>
                <span className="text-[var(--retro-text-muted)] block">Dependents</span>
                <span className="text-[var(--retro-accent-cyan)] font-medium">{task.dependent_count} waiting</span>
              </div>
            )}
          </div>
        </RetroPanel>

        {/* Error */}
        {error && (
          <div className="p-3 bg-[rgba(255,68,68,0.1)] border border-[var(--retro-accent-red)] rounded text-sm text-[var(--retro-accent-red)]">
            {error}
          </div>
        )}
      </div>

      {/* Actions - sticky footer */}
      <div className="p-4 border-t border-[var(--retro-border)] bg-[var(--retro-bg-card)] space-y-2 flex-shrink-0">
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
