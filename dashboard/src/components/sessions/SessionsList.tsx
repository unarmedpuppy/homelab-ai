import { useState, useCallback } from 'react';
import type { TraceSession } from '../../types/traces';
import { tracesAPI } from '../../api/traces';
import { RetroButton, RetroPanel } from '../ui';
import { useVisibilityPolling } from '../../hooks/useDocumentVisibility';

const POLL_INTERVAL = 30000;

const MACHINES = ['mac-mini', 'server', 'gaming-pc', 'macbook-air'];

function extractProjectName(cwd: string | null): string | null {
  if (!cwd) return null;
  const parts = cwd.replace(/\/$/, '').split('/');
  return parts[parts.length - 1] || null;
}

function formatDuration(startTime: string, endTime: string | null): string {
  const start = new Date(startTime).getTime();
  const end = endTime ? new Date(endTime).getTime() : Date.now();
  const secs = Math.round((end - start) / 1000);
  if (secs < 60) return `${secs}s`;
  const mins = Math.floor(secs / 60);
  const rem = secs % 60;
  return rem > 0 ? `${mins}m ${rem}s` : `${mins}m`;
}

function MachineChip({
  label,
  active,
  onClick,
}: {
  label: string;
  active: boolean;
  onClick: () => void;
}) {
  return (
    <button
      onClick={onClick}
      className={`px-2.5 py-1 text-xs rounded border transition-colors ${
        active
          ? 'bg-[var(--retro-bg-light)] border-[var(--retro-border-active)] text-[var(--retro-text-primary)]'
          : 'border-[var(--retro-border)] text-[var(--retro-text-muted)] hover:border-[var(--retro-border-active)] hover:text-[var(--retro-text-secondary)]'
      }`}
    >
      {label}
    </button>
  );
}

interface SessionsListProps {
  onSelect: (session: TraceSession) => void;
}

export function SessionsList({ onSelect }: SessionsListProps) {
  const [sessions, setSessions] = useState<TraceSession[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Filters
  const [machineFilter, setMachineFilter] = useState<string | null>(null);
  const [agentFilter, setAgentFilter] = useState<string | null>(null);
  const [interactiveOnly, setInteractiveOnly] = useState(false);

  const fetchSessions = useCallback(async () => {
    try {
      const data = await tracesAPI.list({
        machine_id: machineFilter ?? undefined,
        agent_label: agentFilter ?? undefined,
        interactive: interactiveOnly || undefined,
        limit: 100,
      });
      setSessions(data);
      setError(null);
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Failed to load sessions');
    } finally {
      setLoading(false);
    }
  }, [machineFilter, agentFilter, interactiveOnly]);

  useVisibilityPolling({
    callback: fetchSessions,
    interval: POLL_INTERVAL,
    enabled: true,
    immediate: true,
  });

  // Collect unique agent labels for filter chips
  const agentLabels = Array.from(new Set(sessions.map((s) => s.agent_label))).sort();

  return (
    <div className="h-full flex flex-col bg-[var(--retro-bg-dark)] overflow-y-auto">
      <div className="p-4 bg-[var(--retro-bg-medium)] border-b border-[var(--retro-border)]">
        <div className="flex items-center justify-between mb-3">
          <h1 className="text-lg font-bold text-[var(--retro-text-primary)]">Sessions</h1>
          <RetroButton variant="ghost" size="sm" onClick={() => { setLoading(true); fetchSessions(); }}>
            Refresh
          </RetroButton>
        </div>

        {/* Filters */}
        <div className="space-y-2">
          <div className="flex flex-wrap gap-1.5 items-center">
            <span className="text-xs text-[var(--retro-text-muted)] mr-1">Machine:</span>
            <MachineChip
              label="All"
              active={machineFilter === null}
              onClick={() => setMachineFilter(null)}
            />
            {MACHINES.map((m) => (
              <MachineChip
                key={m}
                label={m}
                active={machineFilter === m}
                onClick={() => setMachineFilter(machineFilter === m ? null : m)}
              />
            ))}
          </div>

          {agentLabels.length > 1 && (
            <div className="flex flex-wrap gap-1.5 items-center">
              <span className="text-xs text-[var(--retro-text-muted)] mr-1">Agent:</span>
              <MachineChip
                label="All"
                active={agentFilter === null}
                onClick={() => setAgentFilter(null)}
              />
              {agentLabels.map((l) => (
                <MachineChip
                  key={l}
                  label={l}
                  active={agentFilter === l}
                  onClick={() => setAgentFilter(agentFilter === l ? null : l)}
                />
              ))}
            </div>
          )}

          <label className="flex items-center gap-2 cursor-pointer">
            <input
              type="checkbox"
              checked={interactiveOnly}
              onChange={(e) => setInteractiveOnly(e.target.checked)}
              className="accent-[var(--retro-accent-green)]"
            />
            <span className="text-xs text-[var(--retro-text-muted)]">Interactive only</span>
          </label>
        </div>
      </div>

      <div className="flex-1 p-4 max-w-4xl">
        {loading && sessions.length === 0 ? (
          <div className="flex items-center justify-center h-32 text-[var(--retro-text-muted)] text-sm retro-animate-pulse">
            Loading sessions…
          </div>
        ) : error ? (
          <div className="p-4 bg-[rgba(255,68,68,0.1)] border border-[var(--retro-accent-red)] rounded text-sm text-[var(--retro-accent-red)]">
            {error}
          </div>
        ) : sessions.length === 0 ? (
          <div className="flex items-center justify-center h-32 text-[var(--retro-text-muted)] text-sm">
            No sessions recorded yet
          </div>
        ) : (
          <RetroPanel title={`${sessions.length} session${sessions.length !== 1 ? 's' : ''}`}>
            <div className="divide-y divide-[var(--retro-border)]">
              {sessions.map((session) => {
                const isActive = !session.end_time;
                return (
                  <button
                    key={session.session_id}
                    onClick={() => onSelect(session)}
                    className="w-full text-left px-3 py-3 hover:bg-[var(--retro-bg-light)] transition-colors"
                  >
                    <div className="flex items-start justify-between gap-2">
                      <div className="flex-1 min-w-0">
                        {/* Title row: project name + badges */}
                        <div className="flex items-center gap-2 flex-wrap">
                          <span className="text-sm font-semibold text-[var(--retro-text-primary)] truncate">
                            {extractProjectName(session.cwd) ?? session.session_id.slice(0, 8)}
                          </span>
                          <span className="text-xs text-[var(--retro-text-muted)]">
                            {session.machine_id}
                          </span>
                          <span
                            className="text-xs px-1.5 py-0.5 rounded"
                            style={{
                              background: session.interactive
                                ? 'rgba(0,200,255,0.1)'
                                : 'rgba(160,100,255,0.1)',
                              color: session.interactive
                                ? 'var(--retro-accent-cyan)'
                                : '#a855f7',
                            }}
                          >
                            {session.agent_label}
                          </span>
                          {isActive && (
                            <span className="text-xs px-1 py-0.5 rounded bg-[rgba(0,255,100,0.1)] text-[var(--retro-accent-green)] border border-[var(--retro-accent-green)]">
                              live
                            </span>
                          )}
                        </div>
                        {/* Full path as secondary line */}
                        {session.cwd && (
                          <div className="text-xs text-[var(--retro-text-muted)] truncate mt-0.5 font-mono opacity-60">
                            {session.cwd}
                          </div>
                        )}
                      </div>
                      <div className="flex-shrink-0 text-right">
                        <div className="text-xs text-[var(--retro-text-muted)]">
                          {new Date(session.start_time).toLocaleTimeString([], {
                            hour: '2-digit',
                            minute: '2-digit',
                          })}
                        </div>
                        <div className="text-xs text-[var(--retro-text-muted)]">
                          {formatDuration(session.start_time, session.end_time)}
                          {' · '}
                          {session.span_count} spans
                        </div>
                      </div>
                    </div>
                  </button>
                );
              })}
            </div>
          </RetroPanel>
        )}
      </div>
    </div>
  );
}
