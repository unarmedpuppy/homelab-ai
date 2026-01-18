import type { ReactNode } from 'react';

type BadgeVariant =
  | 'priority-critical'
  | 'priority-high'
  | 'priority-medium'
  | 'priority-low'
  | 'status-open'
  | 'status-progress'
  | 'status-done'
  | 'status-blocked'
  | 'agent'
  | 'label';

interface RetroBadgeProps {
  children: ReactNode;
  variant: BadgeVariant;
  size?: 'sm' | 'md';
  className?: string;
}

export function RetroBadge({
  children,
  variant,
  size = 'sm',
  className = '',
}: RetroBadgeProps) {
  const sizeClass = size === 'sm' ? '' : 'retro-badge-md';
  const variantClass = `retro-badge-${variant}`;

  return (
    <span className={`retro-badge ${sizeClass} ${variantClass} ${className}`.trim()}>
      {children}
    </span>
  );
}

// Helper function to get priority variant
export function getPriorityVariant(priority: number): BadgeVariant {
  switch (priority) {
    case 0:
      return 'priority-critical';
    case 1:
      return 'priority-high';
    case 2:
      return 'priority-medium';
    case 3:
    default:
      return 'priority-low';
  }
}

// Helper function to get priority label
export function getPriorityLabel(priority: number): string {
  switch (priority) {
    case 0:
      return 'CRITICAL';
    case 1:
      return 'HIGH';
    case 2:
      return 'MEDIUM';
    case 3:
    default:
      return 'LOW';
  }
}

// Helper function to get status variant
export function getStatusVariant(status: string): BadgeVariant {
  switch (status) {
    case 'in_progress':
      return 'status-progress';
    case 'closed':
      return 'status-done';
    case 'blocked':
      return 'status-blocked';
    case 'open':
    default:
      return 'status-open';
  }
}

// Helper function to get status label
export function getStatusLabel(status: string): string {
  switch (status) {
    case 'in_progress':
      return 'IN PROGRESS';
    case 'closed':
      return 'DONE';
    case 'blocked':
      return 'BLOCKED';
    case 'open':
    default:
      return 'OPEN';
  }
}

export default RetroBadge;
