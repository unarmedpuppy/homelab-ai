import type { BeadTask } from '../../types/beads';
import { RetroBadge, getPriorityVariant, getPriorityLabel, getStatusVariant, getStatusLabel } from '../ui';

interface BeadsTaskCardProps {
  task: BeadTask;
  selected?: boolean;
  onClick: () => void;
  compact?: boolean;
}

export function BeadsTaskCard({
  task,
  selected = false,
  onClick,
  compact = false,
}: BeadsTaskCardProps) {
  // Get repo label if present
  const repoLabel = task.labels.find(l => l.startsWith('repo:'));
  const otherLabels = task.labels.filter(l => !l.startsWith('repo:')).slice(0, 2);

  return (
    <div
      className={`
        retro-card p-3 cursor-pointer transition-all
        ${selected ? 'retro-card-selected' : ''}
        ${task.dependency_count && task.dependency_count > 0 ? 'opacity-60' : ''}
      `}
      onClick={onClick}
    >
      {/* Header: Priority + Status */}
      <div className="flex items-center justify-between mb-2">
        <RetroBadge variant={getPriorityVariant(task.priority)} size="sm">
          {getPriorityLabel(task.priority)}
        </RetroBadge>
        {task.status === 'in_progress' && (
          <RetroBadge variant={getStatusVariant(task.status)} size="sm">
            {getStatusLabel(task.status)}
          </RetroBadge>
        )}
      </div>

      {/* Title */}
      <h3 className={`
        text-sm font-medium text-[var(--retro-text-primary)] mb-2
        ${compact ? 'line-clamp-1' : 'line-clamp-2'}
      `}>
        {task.title}
      </h3>

      {/* Labels */}
      {!compact && (
        <div className="flex flex-wrap gap-1 mb-2">
          {repoLabel && (
            <span className="text-[0.625rem] px-1.5 py-0.5 bg-[var(--retro-bg-dark)] text-[var(--retro-accent-blue)] rounded">
              {repoLabel.replace('repo:', '')}
            </span>
          )}
          {otherLabels.map(label => (
            <span
              key={label}
              className="text-[0.625rem] px-1.5 py-0.5 bg-[var(--retro-bg-dark)] text-[var(--retro-text-muted)] rounded"
            >
              {label}
            </span>
          ))}
        </div>
      )}

      {/* Footer: Age + Type */}
      <div className="flex items-center justify-between text-[0.625rem] text-[var(--retro-text-muted)]">
        <span className="uppercase">{task.issue_type}</span>
        <span>{task.age_days}d</span>
      </div>

      {/* Blocked indicator */}
      {task.dependency_count && task.dependency_count > 0 && (
        <div className="mt-2 text-[0.625rem] text-[var(--retro-accent-red)] flex items-center gap-1">
          <span>🔒</span>
          <span>Blocked by {task.dependency_count} task{task.dependency_count > 1 ? 's' : ''}</span>
        </div>
      )}
    </div>
  );
}

export default BeadsTaskCard;
