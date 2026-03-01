import { useState, useEffect } from 'react';
import type { TraceSession, TraceSessionDetail, TraceTranscript, TranscriptMessage } from '../../types/traces';
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

function TranscriptView({ transcript, loading, unavailable, agentLabel }: {
  transcript: TraceTranscript | null;
  loading: boolean;
  unavailable: boolean;
  agentLabel?: string;
}) {
  const senderLabel = agentLabel && agentLabel !== 'interactive' ? agentLabel : 'you';
  if (loading) {
    return (
      <div className="text-xs text-[var(--retro-text-muted)] py-4 text-center retro-animate-pulse">
        Loading transcript…
      </div>
    );
  }

  if (unavailable) {
    return (
      <div className="text-xs text-[var(--retro-text-muted)] py-4 text-center">
        Transcript not available — only server/Ralph sessions are accessible
      </div>
    );
  }

  if (!transcript || transcript.messages.length === 0) {
    return (
      <div className="text-xs text-[var(--retro-text-muted)] py-4 text-center">
        No conversation messages found
      </div>
    );
  }

  return (
    <div className="space-y-3">
      {transcript.truncated && (
        <div className="text-xs text-[var(--retro-text-muted)] text-center pb-1 border-b border-[var(--retro-border)]">
          Showing first {transcript.messages.length} messages (session truncated)
        </div>
      )}
      {transcript.messages.map((msg: TranscriptMessage, i: number) => (
        <div
          key={i}
          className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}
        >
          <div
            className={`max-w-[85%] rounded-lg px-3 py-2 text-xs space-y-1 ${
              msg.role === 'user'
                ? 'bg-[rgba(0,200,255,0.08)] border border-[rgba(0,200,255,0.2)]'
                : 'bg-[var(--retro-bg-light)] border border-[var(--retro-border)]'
            }`}
          >
            <div className={`text-[10px] font-semibold uppercase tracking-wide mb-1 ${
              msg.role === 'user' ? 'text-[var(--retro-accent-cyan)]' : 'text-[var(--retro-text-muted)]'
            }`}>
              {msg.role === 'user' ? senderLabel : 'claude'}
            </div>
            {msg.text && (
              <div className="text-[var(--retro-text-secondary)] whitespace-pre-wrap break-words leading-relaxed">
                {msg.text}
              </div>
            )}
            {msg.tool_calls.length > 0 && (
              <div className="flex flex-wrap gap-1 pt-1">
                {msg.tool_calls.map((tc, j) => (
                  <span
                    key={j}
                    className="text-[10px] px-1.5 py-0.5 rounded bg-[var(--retro-bg-dark)] text-[var(--retro-text-muted)] font-mono"
                  >
                    {tc.name}
                  </span>
                ))}
              </div>
            )}
          </div>
        </div>
      ))}
    </div>
  );
}

export function SessionDetail({ session, onClose }: SessionDetailProps) {
  const [detail, setDetail] = useState<TraceSessionDetail | null>(null);
  const [spansLoading, setSpansLoading] = useState(true);
  const [spansError, setSpansError] = useState<string | null>(null);

  const [transcript, setTranscript] = useState<TraceTranscript | null>(null);
  const [transcriptLoading, setTranscriptLoading] = useState(true);
  const [transcriptUnavailable, setTranscriptUnavailable] = useState(false);

  const [activeTab, setActiveTab] = useState<'spans' | 'transcript'>('spans');

  const isActive = !session.end_time;

  useEffect(() => {
    tracesAPI
      .get(session.session_id)
      .then(setDetail)
      .catch((e) => setSpansError(e instanceof Error ? e.message : 'Failed to load'))
      .finally(() => setSpansLoading(false));

    // Fetch transcript eagerly to get the slug for the header
    tracesAPI.getTranscript(session.session_id)
      .then(setTranscript)
      .catch((e: Error) => {
        if (e.message.startsWith('404')) setTranscriptUnavailable(true);
      })
      .finally(() => setTranscriptLoading(false));
  }, [session.session_id]);

  const slug = transcript?.slug ?? null;

  return (
    <div className="h-full flex flex-col bg-[var(--retro-bg-dark)] overflow-y-auto">
      {/* Header */}
      <div className="p-4 bg-[var(--retro-bg-medium)] border-b border-[var(--retro-border)] flex items-center gap-3">
        <RetroButton variant="ghost" size="sm" onClick={onClose}>
          ← Back
        </RetroButton>
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 flex-wrap">
            {slug ? (
              <span className="text-sm font-bold text-[var(--retro-text-primary)]">
                {slug}
              </span>
            ) : (
              <span className="text-sm font-bold text-[var(--retro-text-primary)] font-mono">
                {session.session_id.slice(0, 8)}…
              </span>
            )}
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

        {/* Tabs */}
        <div className="flex gap-1 border-b border-[var(--retro-border)]">
          {(['spans', 'transcript'] as const).map((tab) => (
            <button
              key={tab}
              onClick={() => setActiveTab(tab)}
              className={`px-4 py-2 text-xs font-medium capitalize transition-colors ${
                activeTab === tab
                  ? 'text-[var(--retro-text-primary)] border-b-2 border-[var(--retro-accent-green)] -mb-px'
                  : 'text-[var(--retro-text-muted)] hover:text-[var(--retro-text-secondary)]'
              }`}
            >
              {tab === 'spans' ? `Tool Calls (${session.span_count})` : 'Conversation'}
            </button>
          ))}
        </div>

        {activeTab === 'spans' ? (
          <RetroPanel title="">
            {spansLoading ? (
              <div className="text-xs text-[var(--retro-text-muted)] py-4 text-center retro-animate-pulse">
                Loading spans…
              </div>
            ) : spansError ? (
              <div className="text-xs text-[var(--retro-accent-red)] py-4 text-center">{spansError}</div>
            ) : detail ? (
              <SpanWaterfall session={session} spans={detail.spans} />
            ) : null}
          </RetroPanel>
        ) : (
          <RetroPanel title="">
            <TranscriptView
              transcript={transcript}
              loading={transcriptLoading}
              unavailable={transcriptUnavailable}
              agentLabel={session.agent_label}
            />
          </RetroPanel>
        )}
      </div>
    </div>
  );
}
