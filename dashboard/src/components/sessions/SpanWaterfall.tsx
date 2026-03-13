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

function extractSpanSummary(span: TraceSpan): string {
  if (!span.input_json) return '';
  try {
    const input = JSON.parse(span.input_json);
    switch (span.tool_name) {
      case 'Bash':
        return input.command ?? '';
      case 'Edit':
      case 'MultiEdit':
        return input.file_path ?? input.path ?? '';
      case 'Write':
        return input.file_path ?? '';
      case 'Read':
        return input.file_path
          ? `${input.file_path}${input.offset ? ` (line ${input.offset})` : ''}`
          : '';
      case 'Glob':
        return `${input.pattern ?? ''}${input.path ? ` in ${input.path}` : ''}`;
      case 'Grep':
        return `/${input.pattern ?? ''}/${input.path ? `  ${input.path}` : ''}`;
      case 'Agent':
        return input.description ?? (input.prompt as string | undefined)?.slice(0, 120) ?? '';
      case 'WebFetch':
        return input.url ?? '';
      case 'WebSearch':
        return input.query ?? '';
      case 'Task':
        return input.subject ?? input.description ?? '';
      default:
        return '';
    }
  } catch {
    return '';
  }
}

function formatSpanDuration(span: TraceSpan): string {
  if (!span.end_time) return span.status === 'in_progress' ? '…' : '';
  const ms = new Date(span.end_time).getTime() - new Date(span.start_time).getTime();
  if (ms < 1000) return `${ms}ms`;
  const secs = ms / 1000;
  if (secs < 60) return `${secs.toFixed(1)}s`;
  const mins = Math.floor(secs / 60);
  const rem = Math.round(secs % 60);
  return rem > 0 ? `${mins}m ${rem}s` : `${mins}m`;
}

function truncatePath(p: string, maxLen = 60): string {
  if (p.length <= maxLen) return p;
  return '…' + p.slice(-(maxLen - 1));
}

// Render the drawer content specific to each tool type
function SpanInputDetail({ span }: { span: TraceSpan }) {
  if (!span.input_json) return null;
  let input: Record<string, unknown>;
  try {
    input = JSON.parse(span.input_json);
  } catch {
    return (
      <pre className="text-xs text-[var(--retro-text-muted)] bg-[var(--retro-bg-dark)] p-3 rounded whitespace-pre-wrap break-words">
        {span.input_json}
      </pre>
    );
  }

  switch (span.tool_name) {
    case 'Bash':
      return (
        <pre className="text-xs text-[var(--retro-text-primary)] bg-[var(--retro-bg-dark)] p-3 rounded overflow-auto whitespace-pre-wrap break-all font-mono">
          {String(input.command ?? '')}
        </pre>
      );
    case 'Edit':
    case 'MultiEdit': {
      const edits = span.tool_name === 'MultiEdit'
        ? (input.edits as Array<{ old_string: string; new_string: string }> ?? [])
        : [{ old_string: input.old_string as string, new_string: input.new_string as string }];
      return (
        <div className="space-y-3">
          <div className="text-xs font-mono text-[var(--retro-text-secondary)] break-all">
            {String(input.file_path ?? '')}
          </div>
          {edits.map((edit, i) => (
            <div key={i} className="space-y-1">
              {edits.length > 1 && (
                <div className="text-xs text-[var(--retro-text-muted)]">Edit {i + 1}</div>
              )}
              {edit.old_string !== undefined && (
                <pre className="text-xs text-[#ef4444] bg-[rgba(239,68,68,0.08)] p-2 rounded overflow-auto whitespace-pre-wrap break-words max-h-32">
                  {String(edit.old_string).slice(0, 500)}
                </pre>
              )}
              {edit.new_string !== undefined && (
                <pre className="text-xs text-[#22c55e] bg-[rgba(34,197,94,0.08)] p-2 rounded overflow-auto whitespace-pre-wrap break-words max-h-32">
                  {String(edit.new_string).slice(0, 500)}
                </pre>
              )}
            </div>
          ))}
        </div>
      );
    }
    case 'Write':
      return (
        <div className="space-y-2">
          <div className="text-xs font-mono text-[var(--retro-text-secondary)] break-all">
            {String(input.file_path ?? '')}
          </div>
          {!!input.content && (
            <pre className="text-xs text-[var(--retro-text-muted)] bg-[var(--retro-bg-dark)] p-2 rounded overflow-auto whitespace-pre-wrap break-words max-h-48">
              {String(input.content).slice(0, 800)}
            </pre>
          )}
        </div>
      );
    case 'Read':
      return (
        <div className="text-xs font-mono text-[var(--retro-text-secondary)] break-all">
          {String(input.file_path ?? '')}
          {!!input.offset && <span className="text-[var(--retro-text-muted)]"> offset={String(input.offset)}</span>}
          {!!input.limit && <span className="text-[var(--retro-text-muted)]"> limit={String(input.limit)}</span>}
        </div>
      );
    case 'Glob':
    case 'Grep':
      return (
        <div className="space-y-1 text-xs font-mono">
          <div className="text-[var(--retro-text-primary)]">{String(input.pattern ?? '')}</div>
          {(!!input.path || !!input.glob) && (
            <div className="text-[var(--retro-text-muted)]">
              {!!input.path && `path: ${String(input.path)}`}
              {!!input.glob && ` glob: ${String(input.glob)}`}
            </div>
          )}
        </div>
      );
    case 'Agent':
      return (
        <div className="space-y-2">
          {!!input.description && (
            <div className="text-xs text-[var(--retro-text-primary)]">{String(input.description)}</div>
          )}
          {!!input.prompt && (
            <pre className="text-xs text-[var(--retro-text-muted)] bg-[var(--retro-bg-dark)] p-2 rounded whitespace-pre-wrap break-words max-h-48 overflow-auto">
              {String(input.prompt).slice(0, 800)}
            </pre>
          )}
        </div>
      );
    default:
      return (
        <pre className="text-xs text-[var(--retro-text-muted)] bg-[var(--retro-bg-dark)] p-3 rounded overflow-auto max-h-48 whitespace-pre-wrap break-words">
          {JSON.stringify(input, null, 2)}
        </pre>
      );
  }
}

function SpanDrawer({ span, onClose }: { span: TraceSpan; onClose: () => void }) {
  const [showRaw, setShowRaw] = useState(false);
  const color = getSpanColor(span.tool_name, span.status);
  const duration = formatSpanDuration(span);

  return (
    <div
      className="fixed inset-0 z-50 flex items-end sm:items-center justify-center bg-black/60"
      onClick={onClose}
    >
      <div
        className="w-full sm:max-w-2xl max-h-[80vh] overflow-auto bg-[var(--retro-bg-medium)] border border-[var(--retro-border)] rounded-t-lg sm:rounded-lg"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <div className="flex items-center justify-between p-4 border-b border-[var(--retro-border)]">
          <div className="flex items-center gap-2">
            <span
              className="text-xs font-bold px-2 py-0.5 rounded"
              style={{ background: color + '25', color }}
            >
              {span.tool_name}
            </span>
            {span.status !== 'completed' && (
              <span className={`text-xs px-1.5 py-0.5 rounded border ${
                span.status === 'failed'
                  ? 'text-[var(--retro-accent-red)] border-[var(--retro-accent-red)] bg-[rgba(255,68,68,0.08)]'
                  : 'text-[var(--retro-accent-green)] border-[var(--retro-accent-green)] bg-[rgba(0,255,100,0.08)]'
              }`}>
                {span.status}
              </span>
            )}
            {duration && (
              <span className="text-xs text-[var(--retro-text-muted)]">{duration}</span>
            )}
          </div>
          <button
            onClick={onClose}
            className="text-[var(--retro-text-muted)] hover:text-[var(--retro-text-primary)] text-lg leading-none"
          >
            ✕
          </button>
        </div>

        <div className="p-4 space-y-4">
          {/* Timestamp */}
          <div className="text-xs text-[var(--retro-text-muted)]">
            {new Date(span.start_time).toLocaleTimeString()}
            {span.end_time && ` → ${new Date(span.end_time).toLocaleTimeString()}`}
          </div>

          {/* Tool-specific input */}
          {span.input_json && (
            <div>
              <div className="text-xs font-semibold text-[var(--retro-text-secondary)] uppercase tracking-wide mb-2">
                Input
              </div>
              <SpanInputDetail span={span} />
            </div>
          )}

          {/* Output */}
          {span.output_summary && (
            <div>
              <div className="text-xs font-semibold text-[var(--retro-text-secondary)] uppercase tracking-wide mb-2">
                Output
              </div>
              <pre className="text-xs text-[var(--retro-text-muted)] bg-[var(--retro-bg-dark)] p-3 rounded overflow-auto max-h-48 whitespace-pre-wrap break-words">
                {span.output_summary}
              </pre>
            </div>
          )}

          {/* Raw JSON toggle */}
          {span.input_json && !['Bash', 'Glob', 'Grep', 'Read'].includes(span.tool_name) && (
            <div>
              <button
                onClick={() => setShowRaw((v) => !v)}
                className="text-xs text-[var(--retro-text-muted)] hover:text-[var(--retro-text-secondary)] underline"
              >
                {showRaw ? 'hide raw input' : 'show raw input'}
              </button>
              {showRaw && (
                <pre className="mt-2 text-xs text-[var(--retro-text-muted)] bg-[var(--retro-bg-dark)] p-3 rounded overflow-auto max-h-48 whitespace-pre-wrap break-words">
                  {(() => {
                    try { return JSON.stringify(JSON.parse(span.input_json!), null, 2); }
                    catch { return span.input_json; }
                  })()}
                </pre>
              )}
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
      {/* Compact timeline strip */}
      <div className="relative h-3 bg-[var(--retro-bg-dark)] rounded mb-3 overflow-hidden">
        {spans.map((span) => {
          const spanStart = new Date(span.start_time).getTime();
          const spanEnd = span.end_time ? new Date(span.end_time).getTime() : sessionEnd;
          const left = ((spanStart - sessionStart) / totalDuration) * 100;
          const width = Math.max(((spanEnd - spanStart) / totalDuration) * 100, 0.5);
          return (
            <div
              key={span.span_id}
              className="absolute inset-y-0"
              style={{
                left: `${left}%`,
                width: `${width}%`,
                minWidth: '3px',
                background: getSpanColor(span.tool_name, span.status),
                opacity: 0.7,
              }}
            />
          );
        })}
      </div>

      {/* Span list */}
      {spans.map((span) => {
        const summary = extractSpanSummary(span);
        const duration = formatSpanDuration(span);
        const color = getSpanColor(span.tool_name, span.status);
        const isFailed = span.status === 'failed';
        const isActive = span.status === 'in_progress';

        return (
          <div
            key={span.span_id}
            className={`flex items-center gap-2 px-2 py-1.5 rounded cursor-pointer hover:bg-[var(--retro-bg-light)] transition-colors group ${
              isFailed ? 'border-l-2 border-[var(--retro-accent-red)]' : ''
            }`}
            onClick={() => setSelectedSpan(span)}
          >
            {/* Tool badge */}
            <span
              className="text-xs font-mono font-bold px-1.5 py-0.5 rounded flex-shrink-0 w-20 text-center"
              style={{ background: color + '20', color }}
            >
              {span.tool_name}
            </span>

            {/* Summary */}
            <span className="flex-1 text-xs text-[var(--retro-text-muted)] font-mono truncate min-w-0">
              {summary ? truncatePath(summary) : (
                <span className="text-[var(--retro-text-muted)] opacity-50 italic">
                  {span.tool_name.toLowerCase()}
                </span>
              )}
            </span>

            {/* Duration */}
            <span className={`text-xs flex-shrink-0 tabular-nums ${
              isActive
                ? 'text-[var(--retro-accent-green)] retro-animate-pulse'
                : 'text-[var(--retro-text-muted)]'
            }`}>
              {duration}
            </span>
          </div>
        );
      })}

      {selectedSpan && (
        <SpanDrawer span={selectedSpan} onClose={() => setSelectedSpan(null)} />
      )}
    </div>
  );
}
