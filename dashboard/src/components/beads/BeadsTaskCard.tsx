import type { BeadTask } from '../../types/beads';
import { RetroBadge, RetroProgress, getPriorityVariant, getPriorityLabel } from '../ui';

interface BeadsTaskCardProps {
  task: BeadTask;
  selected?: boolean;
  onClick: () => void;
  compact?: boolean;  // For mobile - condensed layout
}

/**
 * BeadsTaskCard - Task card component for Kanban board
 *
 * Full Layout:
 * ┌──────────────────────────────────┐
 * │ PROJECT: Task Title Here         │  <- Title (truncated)
 * │ AGENT: NONE                      │  <- Agent if assigned
 * │ PRIORITY: HIGH                   │  <- Priority badge
 * │ AGE: 4 DAYS                      │  <- Age indicator
 * │ ████████░░░░░░ 45%              │  <- Progress (if in_progress)
 * │ [label1] [label2]               │  <- Labels as badges
 * └──────────────────────────────────┘
 *
 * Compact Layout (Mobile):
 * ┌──────────────────────────────────┐
 * │ Task Title Here                  │
 * │ HIGH • 4d • [mercury]            │
 * └──────────────────────────────────┘
 */
export function BeadsTaskCard({
  task,
  selected = false,
  onClick,
  compact = false,
}: BeadsTaskCardProps) {
  // Extract repo label from labels array
  const repoLabel = task.labels.find(l => l.startsWith('repo:'));
  const repoName = repoLabel ? repoLabel.replace('repo:', '') : null;
  const otherLabels = task.labels.filter(l => !l.startsWith('repo:')).slice(0, 3);

  // Check if task is blocked
  const isBlocked = (task.dependency_count && task.dependency_count > 0) ||
                    (task.blocked_by && task.blocked_by.length > 0);

  // Get agent from owner field (if assigned)
  const assignedAgent = task.owner || null;

  // Determine priority color for left border indicator
  const priorityBorderColors: Record<number, string> = {
    0: 'var(--retro-priority-critical)',
    1: 'var(--retro-priority-high)',
    2: 'var(--retro-priority-medium)',
    3: 'var(--retro-priority-low)',
  };
  const borderColor = priorityBorderColors[task.priority] || priorityBorderColors[3];

  // Compact layout for mobile
  if (compact) {
    return (
      <div
        className={`
          retro-card p-2.5 cursor-pointer transition-all relative
          ${selected ? 'retro-card--selected' : ''}
          ${isBlocked ? 'opacity-60' : ''}
        `}
        onClick={onClick}
        style={{ borderLeftWidth: '3px', borderLeftColor: borderColor }}
        role="button"
        tabIndex={0}
        onKeyDown={(e) => {
          if (e.key === 'Enter' || e.key === ' ') {
            e.preventDefault();
            onClick();
          }
        }}
      >
        {/* Title */}
        <h3 className="text-sm font-medium text-[var(--retro-text-primary)] line-clamp-1 mb-1.5">
          {task.title}
        </h3>

        {/* Compact info row: PRIORITY • AGE • [repo] */}
        <div className="flex items-center gap-1.5 text-[0.625rem] flex-wrap">
          <span
            className="font-bold uppercase"
            style={{ color: borderColor }}
          >
            {getPriorityLabel(task.priority)}
          </span>
          <span className="text-[var(--retro-text-muted)]">•</span>
          <span className="text-[var(--retro-text-muted)]">{task.age_days}d</span>
          {repoName && (
            <>
              <span className="text-[var(--retro-text-muted)]">•</span>
              <span className="px-1.5 py-0.5 bg-[var(--retro-bg-dark)] text-[var(--retro-accent-blue)] rounded">
                {repoName}
              </span>
            </>
          )}
          {isBlocked && (
            <>
              <span className="text-[var(--retro-text-muted)]">•</span>
              <span className="text-[var(--retro-accent-red)]">🔒</span>
            </>
          )}
        </div>
      </div>
    );
  }

  // Full layout for desktop
  return (
    <div
      className={`
        retro-card p-3 cursor-pointer transition-all relative
        ${selected ? 'retro-card--selected' : ''}
        ${isBlocked ? 'opacity-60' : ''}
      `}
      onClick={onClick}
      style={{ borderLeftWidth: '4px', borderLeftColor: borderColor }}
      role="button"
      tabIndex={0}
      onKeyDown={(e) => {
        if (e.key === 'Enter' || e.key === ' ') {
          e.preventDefault();
          onClick();
        }
      }}
    >
      {/* Project + Title row */}
      {repoName && (
        <div className="text-[0.625rem] font-bold uppercase text-[var(--retro-accent-blue)] mb-0.5 tracking-wide">
          PROJECT: {repoName.toUpperCase()}
        </div>
      )}

      {/* Title */}
      <h3 className="text-sm font-medium text-[var(--retro-text-primary)] line-clamp-2 mb-2">
        {task.title}
      </h3>

      {/* Agent display */}
      <div className="text-[0.625rem] text-[var(--retro-text-muted)] mb-1.5 uppercase tracking-wide">
        AGENT: {assignedAgent ? (
          <span className="text-[var(--retro-accent-green)]">{assignedAgent}</span>
        ) : (
          <span className="text-[var(--retro-text-muted)]">NONE</span>
        )}
      </div>

      {/* Priority + Age row */}
      <div className="flex items-center justify-between mb-2">
        <div className="flex items-center gap-2">
          <RetroBadge variant={getPriorityVariant(task.priority)} size="sm">
            {getPriorityLabel(task.priority)}
          </RetroBadge>
          <span className="text-[0.625rem] text-[var(--retro-text-muted)] uppercase">
            {task.issue_type}
          </span>
        </div>
        <span className="text-[0.625rem] text-[var(--retro-text-muted)] uppercase tracking-wide">
          AGE: {task.age_days} DAY{task.age_days !== 1 ? 'S' : ''}
        </span>
      </div>

      {/* Progress bar for in_progress tasks */}
      {task.status === 'in_progress' && (
        <div className="mb-2">
          <RetroProgress
            value={50} // TODO: Replace with actual progress when available
            showLabel
            variant="warning"
            size="sm"
            segments={12}
          />
        </div>
      )}

      {/* Labels */}
      {otherLabels.length > 0 && (
        <div className="flex flex-wrap gap-1 mb-2">
          {otherLabels.map(label => (
            <span
              key={label}
              className="text-[0.625rem] px-1.5 py-0.5 bg-[var(--retro-bg-dark)] text-[var(--retro-text-secondary)] rounded border border-[var(--retro-border)]"
            >
              {label}
            </span>
          ))}
        </div>
      )}

      {/* Blocked indicator */}
      {isBlocked && (
        <div className="mt-1 pt-2 border-t border-[var(--retro-border)]">
          <div className="text-[0.625rem] text-[var(--retro-accent-red)] flex items-center gap-1.5">
            <span>🔒</span>
            <span className="uppercase tracking-wide">
              Blocked by {task.dependency_count || task.blocked_by?.length || 0} task
              {(task.dependency_count || task.blocked_by?.length || 0) !== 1 ? 's' : ''}
            </span>
          </div>
        </div>
      )}
    </div>
  );
}

export default BeadsTaskCard;
