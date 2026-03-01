import { useState } from 'react';
import type { TraceSpan, TraceSession } from '../../types/traces';

function getSpanColor(toolName: string, status: string): string {
  if (status === 'failed') return 'var(--retro-accent-red)';
  switch (toolName) {
    case 'Bash': return '#3b82f6';
    case 'Edit':
    case 'Write':
    case 'MultiEdit':
    case 'NotebookEdit': return '#f97316';
    case 'Read':
    case 'Glob':
    case 'Grep': return '#6b7280';
    case 'Agent': return '#a855f7';
    default: return 'var(--retro-accent-green)';
  }
}

function SpanDrawer({ span, onClose }: { span: TraceSpan; onClose: () => void }) {
  return (
    <div
      className="fixed inset-0 z-50 flex items-end sm:items-center justify-center bg-black/60"
      onClick={onClose}
    >
      <div
        className="w-full sm:max-w-2xl max-h-[80vh] overflow-auto bg-[var(--retro-bg-medium)] border border-[var(--retro-border)] rounded-t-lg sm:rounded-lg"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="flex items-center justify-between p-4 border-b border-[var(--retro-border)]">
          <div>
            <span className="text-sm font-bold text-[var(--retro-text-primary)]">
              {span.tool_name}
            </span>
            <span
              className="ml-2 text-xs px-1.5 py-0.5 rounded"
              style={{
                background: getSpanColor(span.tool_name, span.status) + '30',
                color: getSpanColor(span.tool_name, span.status),
              }}
            >
              {span.status}
            </span>
          </div>
          <button
            onClick={onClose}
            className="text-[var(--retro-text-muted)] hover:text-[var(--retro-text-primary)] text-lg leading-none"
          >
            ✕
          </button>
        </div>

        <div className="p-4 space-y-4">
          <div className="text-xs text-[var(--retro-text-muted)]">
            {new Date(span.start_time).toLocaleTimeString()}
            {span.end_time && (
              <> — {new Date(span.end_time).toLocaleTimeString()} ({Math.round((new Date(span.end_time).getTime() - new Date(span.start_time).getTime()) / 100) / 10}s)</>
            )}
          </div>

          {span.input_json && (
            <div>
              <div className="text-xs font-semibold text-[var(--retro-text-secondary)] mb-1 uppercase tracking-wide">
                Input
              </div>
              <pre className="text-xs text-[var(--retro-text-muted)] bg-[var(--retro-bg-dark)] p-3 rounded overflow-auto max-h-48 whitespace-pre-wrap break-words">
                {(() => {
                  try {
                    return JSON.stringify(JSON.parse(span.input_json), null, 2);
                  } catch {
                    return span.input_json;
                  }
                })()}
              </pre>
            </div>
          )}

          {span.output_summary && (
            <div>
              <div className="text-xs font-semibold text-[var(--retro-text-secondary)] mb-1 uppercase tracking-wide">
                Output
              </div>
              <pre className="text-xs text-[var(--retro-text-muted)] bg-[var(--retro-bg-dark)] p-3 rounded overflow-auto max-h-48 whitespace-pre-wrap break-words">
                {span.output_summary}
              </pre>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

interface SpanWaterfallProps {
  session: TraceSession;
  spans: TraceSpan[];
}

export function SpanWaterfall({ session, spans }: SpanWaterfallProps) {
  const [selectedSpan, setSelectedSpan] = useState<TraceSpan | null>(null);

  if (spans.length === 0) {
    return (
      <div className="text-xs text-[var(--retro-text-muted)] py-4 text-center">
        No spans recorded
      </div>
    );
  }

  const sessionStart = new Date(session.start_time).getTime();
  const sessionEnd = session.end_time
    ? new Date(session.end_time).getTime()
    : Date.now();
  const totalDuration = Math.max(sessionEnd - sessionStart, 1);

  return (
    <div className="space-y-1">
      {spans.map((span) => {
        const spanStart = new Date(span.start_time).getTime();
        const spanEnd = span.end_time ? new Date(span.end_time).getTime() : sessionEnd;
        const left = ((spanStart - sessionStart) / totalDuration) * 100;
        const width = Math.max(((spanEnd - spanStart) / totalDuration) * 100, 0.3);
        const color = getSpanColor(span.tool_name, span.status);

        return (
          <div key={span.span_id} className="flex items-center gap-2 group">
            <div className="w-20 flex-shrink-0 text-right">
              <span className="text-xs text-[var(--retro-text-muted)] truncate block">
                {span.tool_name}
              </span>
            </div>
            <div className="flex-1 relative h-5">
              <div
                className="absolute inset-y-0 rounded cursor-pointer transition-opacity hover:opacity-80"
                style={{
                  left: `${left}%`,
                  width: `${width}%`,
                  minWidth: '4px',
                  background: color,
                  opacity: span.status === 'in_progress' ? 0.6 : 1,
                }}
                title={`${span.tool_name} — ${span.status}`}
                onClick={() => setSelectedSpan(span)}
              />
            </div>
          </div>
        );
      })}

      {selectedSpan && (
        <SpanDrawer span={selectedSpan} onClose={() => setSelectedSpan(null)} />
      )}
    </div>
  );
}
