import { useState, useEffect } from 'react';
import type { TraceStatsResponse } from '../../types/traces';
import { tracesAPI } from '../../api/traces';

interface StatCardProps {
  label: string;
  value: string | number;
  dim?: boolean;
}

function StatCard({ label, value, dim }: StatCardProps) {
  return (
    <div className="bg-[var(--retro-bg-dark)] border border-[var(--retro-border)] rounded p-3">
      <div className="text-xs text-[var(--retro-text-muted)] uppercase tracking-wide mb-1">{label}</div>
      <div
        className={`text-xl font-bold ${dim ? 'text-[var(--retro-text-muted)]' : 'text-[var(--retro-text-primary)]'}`}
      >
        {value}
      </div>
    </div>
  );
}

export function SessionsOverviewCards() {
  const [stats, setStats] = useState<TraceStatsResponse | null>(null);

  useEffect(() => {
    tracesAPI.stats().then(setStats).catch(() => {});
  }, []);

  if (!stats) return null;

  return (
    <div className="grid grid-cols-2 gap-3">
      <StatCard
        label="Active sessions"
        value={stats.active_sessions}
        dim={stats.active_sessions === 0}
      />
      <StatCard label="Sessions today" value={stats.sessions_today} />
    </div>
  );
}
