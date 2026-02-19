import type { ReactNode } from 'react';

interface StatItem {
  label: string;
  value: string | number;
  color?: 'default' | 'green' | 'yellow' | 'red' | 'blue';
}

interface RetroStatsProps {
  stats: StatItem[];
  className?: string;
}

export function RetroStats({ stats, className = '' }: RetroStatsProps) {
  const colorClasses = {
    default: 'text-[var(--retro-accent-cyan)]',
    green: 'text-[var(--retro-accent-green)]',
    yellow: 'text-[var(--retro-accent-yellow)]',
    red: 'text-[var(--retro-accent-red)]',
    blue: 'text-[var(--retro-accent-blue)]',
  };

  return (
    <div className={`retro-stats-bar ${className}`.trim()}>
      {stats.map((stat, index) => (
        <div key={index} className="retro-stat">
          <span className="retro-stat-label">{stat.label}:</span>
          <span className={`retro-stat-value ${colorClasses[stat.color || 'default']}`}>
            {stat.value}
          </span>
        </div>
      ))}
    </div>
  );
}

interface RetroStatCardProps {
  label: string;
  value: string | number;
  icon?: ReactNode;
  color?: 'default' | 'green' | 'yellow' | 'red' | 'blue';
  className?: string;
}

export function RetroStatCard({
  label,
  value,
  icon,
  color = 'default',
  className = '',
}: RetroStatCardProps) {
  const colorClasses = {
    default: 'text-[var(--retro-accent-cyan)]',
    green: 'text-[var(--retro-accent-green)]',
    yellow: 'text-[var(--retro-accent-yellow)]',
    red: 'text-[var(--retro-accent-red)]',
    blue: 'text-[var(--retro-accent-blue)]',
  };

  return (
    <div className={`retro-panel ${className}`.trim()}>
      <div className="retro-panel-content text-center">
        {icon && (
          <div className="text-2xl mb-2">{icon}</div>
        )}
        <div className={`text-3xl font-bold ${colorClasses[color]} mb-1`}>
          {value}
        </div>
        <div className="text-xs text-[var(--retro-text-muted)]">
          {label}
        </div>
      </div>
    </div>
  );
}

export default RetroStats;
