import { useState, useEffect } from 'react';
import type { TraceSession, TraceSessionDetail } from '../../types/traces';
import { tracesAPI } from '../../api/traces';
import { RetroButton, RetroPanel } from '../ui';
import { SpanWaterfall } from './SpanWaterfall';

function formatDuration(startTime: string, endTime: string | null): string {
  const start = new Date(startTime).getTime();
  const end = endTime ? new Date(endTime).getTime() : Date.now();
  const secs = Math.round((end - start) / 1000);
  if (secs < 60) return `${secs}s`;
  const mins = Math.floor(secs / 60);
  const rem = secs % 60;
  return rem > 0 ? `${mins}m ${rem}s` : `${mins}m`;
}

interface SessionDetailProps {
  session: TraceSession;
  onClose: () => void;
}

export function SessionDetail({ session, onClose }: SessionDetailProps) {
  const [detail, setDetail] = useState<TraceSessionDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    tracesAPI
      .get(session.session_id)
      .then(setDetail)
      .catch((e) => setError(e instanceof Error ? e.message : 'Failed to load'))
      .finally(() => setLoading(false));
  }, [session.session_id]);

  const isActive = !session.end_time;

  return (
    <div className="h-full flex flex-col bg-[var(--retro-bg-dark)] overflow-y-auto">
      {/* Header */}
      <div className="p-4 bg-[var(--retro-bg-medium)] border-b border-[var(--retro-border)] flex items-center gap-3">
        <RetroButton variant="ghost" size="sm" onClick={onClose}>
          ← Back
        </RetroButton>
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2">
            <span className="text-sm font-bold text-[var(--retro-text-primary)] truncate">
              {session.session_id.slice(0, 8)}…
            </span>
            {isActive && (
              <span className="text-xs px-1.5 py-0.5 rounded bg-[rgba(0,255,100,0.1)] text-[var(--retro-accent-green)] border border-[var(--retro-accent-green)]">
                active
              </span>
            )}
          </div>
          <p className="text-xs text-[var(--retro-text-muted)] mt-0.5">
            {session.machine_id} · {session.agent_label} · {formatDuration(session.start_time, session.end_time)}
          </p>
        </div>
      </div>

      <div className="flex-1 p-4 space-y-4 max-w-4xl">
        {/* Metadata */}
        <RetroPanel title="Session Info">
          <div className="grid grid-cols-2 sm:grid-cols-3 gap-3 text-sm">
            <div>
              <div className="text-xs text-[var(--retro-text-muted)] uppercase tracking-wide mb-0.5">Machine</div>
              <div className="text-[var(--retro-text-primary)]">{session.machine_id}</div>
            </div>
            <div>
              <div className="text-xs text-[var(--retro-text-muted)] uppercase tracking-wide mb-0.5">Agent</div>
              <div className="text-[var(--retro-text-primary)]">{session.agent_label}</div>
            </div>
            <div>
              <div className="text-xs text-[var(--retro-text-muted)] uppercase tracking-wide mb-0.5">Spans</div>
              <div className="text-[var(--retro-text-primary)]">{session.span_count}</div>
            </div>
            <div>
              <div className="text-xs text-[var(--retro-text-muted)] uppercase tracking-wide mb-0.5">Started</div>
              <div className="text-[var(--retro-text-primary)]">{new Date(session.start_time).toLocaleString()}</div>
            </div>
            <div>
              <div className="text-xs text-[var(--retro-text-muted)] uppercase tracking-wide mb-0.5">Duration</div>
              <div className="text-[var(--retro-text-primary)]">{formatDuration(session.start_time, session.end_time)}</div>
            </div>
            {session.model && (
              <div>
                <div className="text-xs text-[var(--retro-text-muted)] uppercase tracking-wide mb-0.5">Model</div>
                <div className="text-[var(--retro-text-primary)] truncate">{session.model}</div>
              </div>
            )}
            {session.cwd && (
              <div className="col-span-2 sm:col-span-3">
                <div className="text-xs text-[var(--retro-text-muted)] uppercase tracking-wide mb-0.5">Directory</div>
                <div className="text-[var(--retro-text-primary)] text-xs font-mono truncate">{session.cwd}</div>
              </div>
            )}
          </div>
        </RetroPanel>

        {/* Tool breakdown summary */}
        {detail && detail.spans.length > 0 && (() => {
          const counts: Record<string, number> = {};
          let failed = 0;
          for (const span of detail.spans) {
            const group =
              span.tool_name === 'Bash' ? 'bash' :
              ['Edit', 'Write', 'MultiEdit', 'NotebookEdit'].includes(span.tool_name) ? 'edits' :
              ['Read', 'Glob', 'Grep'].includes(span.tool_name) ? 'reads' :
              span.tool_name === 'Agent' ? 'agents' :
              'other';
            counts[group] = (counts[group] ?? 0) + 1;
            if (span.status === 'failed') failed++;
          }
          const chips = [
            counts.bash && { label: `${counts.bash} bash`, color: '#3b82f6' },
            counts.edits && { label: `${counts.edits} edit${counts.edits !== 1 ? 's' : ''}`, color: '#f97316' },
            counts.reads && { label: `${counts.reads} read${counts.reads !== 1 ? 's' : ''}`, color: '#6b7280' },
            counts.agents && { label: `${counts.agents} agent${counts.agents !== 1 ? 's' : ''}`, color: '#a855f7' },
            counts.other && { label: `${counts.other} other`, color: 'var(--retro-text-muted)' },
            failed > 0 && { label: `${failed} failed`, color: 'var(--retro-accent-red)' },
          ].filter(Boolean) as { label: string; color: string }[];

          return (
            <div className="flex flex-wrap gap-2">
              {chips.map((chip) => (
                <span
                  key={chip.label}
                  className="text-xs px-2 py-0.5 rounded"
                  style={{ background: chip.color + '20', color: chip.color }}
                >
                  {chip.label}
                </span>
              ))}
            </div>
          );
        })()}

        {/* Span waterfall */}
        <RetroPanel title={`Tool Calls (${session.span_count})`}>
          {loading ? (
            <div className="text-xs text-[var(--retro-text-muted)] py-4 text-center retro-animate-pulse">
              Loading spans…
            </div>
          ) : error ? (
            <div className="text-xs text-[var(--retro-accent-red)] py-4 text-center">{error}</div>
          ) : detail ? (
            <SpanWaterfall session={session} spans={detail.spans} />
          ) : null}
        </RetroPanel>
      </div>
    </div>
  );
}
