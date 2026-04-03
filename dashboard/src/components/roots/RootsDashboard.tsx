import { useState, useEffect, useCallback, useRef } from 'react';
import { tasksAPI } from '../../api/client';
import type { Task } from '../../types/tasks';

interface RootsWorkstream {
  task: Task;
  roots_state: string;
  roots_machine: string;
  roots_branch: string;
  roots_worktree: string;
  roots_port: string | number | null;
  roots_pr_url: string | null;
}

function extractWorkstream(task: Task): RootsWorkstream | null {
  const m = task.metadata;
  const roots_state = m.roots_state;
  if (!roots_state || roots_state === 'archived') return null;

  return {
    task,
    roots_state: String(roots_state),
    roots_machine: m.roots_machine ? String(m.roots_machine) : 'unknown',
    roots_branch: m.roots_branch ? String(m.roots_branch) : '',
    roots_worktree: m.roots_worktree ? String(m.roots_worktree) : '',
    roots_port: m.roots_port != null ? (m.roots_port as string | number) : null,
    roots_pr_url: m.roots_pr_url ? String(m.roots_pr_url) : null,
  };
}

function formatAge(createdAt: string): string {
  const now = Date.now();
  const created = new Date(createdAt).getTime();
  const diffMs = now - created;
  const diffSecs = Math.floor(diffMs / 1000);
  if (diffSecs < 60) return `${diffSecs}s ago`;
  const diffMins = Math.floor(diffSecs / 60);
  if (diffMins < 60) return `${diffMins}m ago`;
  const diffHours = Math.floor(diffMins / 60);
  if (diffHours < 24) return `${diffHours}h ago`;
  const diffDays = Math.floor(diffHours / 24);
  return `${diffDays}d ago`;
}

interface WorkstreamRowProps {
  ws: RootsWorkstream;
}

function WorkstreamRow({ ws }: WorkstreamRowProps) {
  const isRunning = ws.roots_state === 'running';

  return (
    <div className="flex items-start gap-4 px-4 py-3 border-b border-[var(--retro-border)] last:border-b-0 hover:bg-[var(--retro-bg-dark)] transition-colors">
      {/* Task ID */}
      <span className="font-mono text-xs text-[#67e8f9] flex-shrink-0 w-28 pt-0.5">
        {ws.task.id}
      </span>

      {/* Title + branch */}
      <div className="flex-1 min-w-0">
        <div className="text-sm text-[var(--retro-text-primary)] truncate">
          {ws.task.title}
        </div>
        {ws.roots_branch && (
          <div className="font-mono text-xs text-[var(--retro-text-muted)] truncate mt-0.5">
            {ws.roots_branch}
          </div>
        )}
      </div>

      {/* State badge */}
      <div className="flex-shrink-0 flex items-center gap-3">
        {isRunning ? (
          <span className="text-xs px-1.5 py-0.5 rounded border border-green-600 text-green-400 font-mono">
            running
          </span>
        ) : (
          <span className="text-xs px-1.5 py-0.5 rounded border border-[var(--retro-border)] text-[var(--retro-text-muted)] font-mono">
            {ws.roots_state}
          </span>
        )}

        {/* PR link */}
        {ws.roots_pr_url && (
          <a
            href={ws.roots_pr_url}
            target="_blank"
            rel="noopener noreferrer"
            className="text-xs font-mono text-[#67e8f9] hover:underline flex-shrink-0"
            onClick={(e) => e.stopPropagation()}
          >
            PR
          </a>
        )}

        {/* Age */}
        <span className="text-xs font-mono text-[var(--retro-text-muted)] flex-shrink-0 w-16 text-right">
          {formatAge(ws.task.created_at)}
        </span>
      </div>
    </div>
  );
}

interface MachineGroupProps {
  machine: string;
  workstreams: RootsWorkstream[];
}

function MachineGroup({ machine, workstreams }: MachineGroupProps) {
  return (
    <div className="mb-4 bg-[var(--retro-bg-medium)] border border-[var(--retro-border)] rounded">
      <div className="flex items-center justify-between px-4 py-2.5 border-b border-[var(--retro-border)] bg-[var(--retro-bg-light)] rounded-t">
        <span className="font-mono text-sm font-semibold text-[var(--retro-text-primary)]">
          {machine}
        </span>
        <span className="text-xs px-2 py-0.5 bg-[var(--retro-bg-dark)] rounded-full text-[var(--retro-text-secondary)] font-mono">
          {workstreams.length}
        </span>
      </div>
      <div>
        {workstreams.map((ws) => (
          <WorkstreamRow key={ws.task.id} ws={ws} />
        ))}
      </div>
    </div>
  );
}

export default function RootsDashboard() {
  const [workstreams, setWorkstreams] = useState<RootsWorkstream[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [lastRefresh, setLastRefresh] = useState<Date | null>(null);
  const intervalRef = useRef<ReturnType<typeof setInterval> | null>(null);

  const loadData = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);

      const res = await tasksAPI.list();
      const active = res.tasks
        .map(extractWorkstream)
        .filter((ws): ws is RootsWorkstream => ws !== null);

      setWorkstreams(active);
      setLastRefresh(new Date());
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load workstreams');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadData();
    intervalRef.current = setInterval(loadData, 30_000);
    return () => {
      if (intervalRef.current) clearInterval(intervalRef.current);
    };
  }, [loadData]);

  // Group by machine
  const byMachine = workstreams.reduce<Record<string, RootsWorkstream[]>>((acc, ws) => {
    const key = ws.roots_machine;
    if (!acc[key]) acc[key] = [];
    acc[key].push(ws);
    return acc;
  }, {});

  const machines = Object.keys(byMachine).sort();

  if (loading && workstreams.length === 0) {
    return (
      <div className="flex items-center justify-center h-full">
        <div className="text-[var(--retro-text-secondary)]">Loading workstreams...</div>
      </div>
    );
  }

  return (
    <div className="h-full flex flex-col p-4 overflow-auto">
      {/* Header */}
      <div className="flex items-center justify-between mb-4 flex-shrink-0">
        <div>
          <h2 className="text-xl font-bold text-[var(--retro-text-primary)]">Roots</h2>
          {lastRefresh && (
            <p className="text-xs text-[var(--retro-text-muted)] mt-0.5">
              Last updated {formatAge(lastRefresh.toISOString())}
            </p>
          )}
        </div>
        <button
          onClick={loadData}
          disabled={loading}
          className="px-3 py-1.5 bg-[var(--retro-bg-light)] border border-[var(--retro-border)] rounded text-sm text-[var(--retro-text-primary)] hover:border-[var(--retro-border-active)] transition-colors disabled:opacity-50"
        >
          {loading ? 'Loading...' : 'Refresh'}
        </button>
      </div>

      {/* Summary bar */}
      {workstreams.length > 0 && (
        <div className="flex flex-wrap gap-4 mb-4 p-4 bg-[var(--retro-bg-medium)] rounded border border-[var(--retro-border)] flex-shrink-0">
          <div className="text-center">
            <div className="text-2xl font-bold font-mono text-green-400">{workstreams.length}</div>
            <div className="text-xs text-[var(--retro-text-secondary)] uppercase tracking-wide">Active</div>
          </div>
          <div className="border-l border-[var(--retro-border)] pl-4">
            <div className="flex gap-4">
              {machines.map((machine) => (
                <div key={machine} className="text-center">
                  <div className="text-lg font-bold font-mono text-[var(--retro-text-primary)]">
                    {byMachine[machine].length}
                  </div>
                  <div className="text-xs text-[var(--retro-text-muted)] font-mono">{machine}</div>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}

      {/* Error */}
      {error && (
        <div className="mb-4 p-3 bg-red-900/20 border border-red-500 rounded text-red-400 text-sm flex-shrink-0">
          {error}
        </div>
      )}

      {/* Machine groups */}
      {workstreams.length === 0 && !loading && (
        <div className="flex items-center justify-center flex-1">
          <div className="text-center">
            <p className="text-[var(--retro-text-muted)] text-sm">
              No active workstreams across the fleet.
            </p>
          </div>
        </div>
      )}

      {machines.map((machine) => (
        <MachineGroup
          key={machine}
          machine={machine}
          workstreams={byMachine[machine]}
        />
      ))}
    </div>
  );
}
