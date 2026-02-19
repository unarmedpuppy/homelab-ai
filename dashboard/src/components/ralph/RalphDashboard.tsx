import React, { useState, useRef, useCallback } from 'react';
import type { RalphStatus, RalphStartParams } from '../../types/ralph';
import { ralphAPI } from '../../api/client';
import {
  RetroPanel,
  RetroButton,
  RetroInput,
  RetroSelect,
  RetroCheckbox,
  RetroProgress,
  RetroBadge,
} from '../ui';
import { useConditionalPolling, useVisibilityPolling } from '../../hooks/useDocumentVisibility';

const STATUS_POLL_INTERVAL = 5000; // 5s when running
const IDLE_POLL_INTERVAL = 30000; // 30s when idle
const LOG_POLL_INTERVAL = 10000; // 10s

export function RalphDashboard() {
  const [status, setStatus] = useState<RalphStatus | null>(null);
  const [logs, setLogs] = useState<string[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Form state
  const [formLabel, setFormLabel] = useState('');
  const [formPriority, setFormPriority] = useState<string>('');
  const [formMaxTasks, setFormMaxTasks] = useState(0);
  const [formDryRun, setFormDryRun] = useState(false);
  const [starting, setStarting] = useState(false);
  const [stopping, setStopping] = useState(false);

  const logViewerRef = useRef<HTMLDivElement>(null);

  const fetchStatus = useCallback(async () => {
    try {
      const s = await ralphAPI.getStatus();
      setStatus(s);
      setError(null);
    } catch (e) {
      // Don't set error for status failures, just log
      console.warn('Failed to fetch Ralph status:', e);
    } finally {
      setLoading(false);
    }
  }, []);

  const fetchLogs = useCallback(async () => {
    try {
      const { logs: logLines } = await ralphAPI.getLogs(100);
      setLogs(logLines);
      // Auto-scroll to bottom
      if (logViewerRef.current) {
        logViewerRef.current.scrollTop = logViewerRef.current.scrollHeight;
      }
    } catch (e) {
      console.warn('Failed to fetch Ralph logs:', e);
    }
  }, []);

  // Visibility-aware status polling with conditional intervals
  // Polls faster when running, slower when idle, pauses when tab hidden
  useConditionalPolling({
    callback: fetchStatus,
    activeInterval: STATUS_POLL_INTERVAL,
    idleInterval: IDLE_POLL_INTERVAL,
    isActive: status?.running ?? false,
    immediate: true,
  });

  // Visibility-aware log polling (only when running)
  useVisibilityPolling({
    callback: fetchLogs,
    interval: LOG_POLL_INTERVAL,
    enabled: status?.running ?? false,
    immediate: true,
  });

  const handleStart = async () => {
    if (!formLabel) {
      setError('Please select a label');
      return;
    }

    setStarting(true);
    setError(null);

    try {
      const params: RalphStartParams = {
        label: formLabel,
        dry_run: formDryRun,
      };
      if (formPriority) {
        params.priority = parseInt(formPriority);
      }
      if (formMaxTasks > 0) {
        params.max_tasks = formMaxTasks;
      }

      await ralphAPI.start(params);
      await fetchStatus();
      await fetchLogs();
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Failed to start Ralph');
    } finally {
      setStarting(false);
    }
  };

  const handleStop = async () => {
    setStopping(true);
    setError(null);

    try {
      await ralphAPI.stop();
      await fetchStatus();
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Failed to stop Ralph');
    } finally {
      setStopping(false);
    }
  };

  const getStatusColor = () => {
    if (!status) return 'var(--retro-text-muted)';
    switch (status.status) {
      case 'running':
        return 'var(--retro-accent-green)';
      case 'stopping':
        return 'var(--retro-accent-yellow)';
      case 'completed':
        return 'var(--retro-accent-cyan)';
      case 'failed':
        return 'var(--retro-accent-red)';
      default:
        return 'var(--retro-text-muted)';
    }
  };

  const progress = status?.total_tasks
    ? (status.completed_tasks / status.total_tasks) * 100
    : 0;

  return (
    <div className="h-full flex flex-col bg-[var(--retro-bg-dark)] overflow-y-auto">
      {/* Header */}
      <div className="p-4 bg-[var(--retro-bg-medium)] border-b border-[var(--retro-border)]">
        <h1 className="text-lg font-bold text-[var(--retro-text-primary)]">
          Ralph-Wiggum Task Runner
        </h1>
        <p className="text-xs text-[var(--retro-text-muted)] mt-1">
          Autonomous task processing loop
        </p>
      </div>

      <div className="flex-1 p-4 space-y-4 max-w-4xl">
        {/* Status Panel */}
        <RetroPanel title="Current Status">
          {loading ? (
            <div className="text-sm text-[var(--retro-text-muted)] retro-animate-pulse">
              Loading status...
            </div>
          ) : status ? (
            <div className="space-y-4">
              {/* Status indicator */}
              <div className="flex items-center gap-3">
                <span
                  className="w-3 h-3 rounded-full"
                  style={{
                    backgroundColor: getStatusColor(),
                    boxShadow: 'none',
                  }}
                />
                <span className="text-sm font-bold uppercase" style={{ color: getStatusColor() }}>
                  {status.status}
                </span>
                {status.label && (
                  <RetroBadge variant="label" size="sm">
                    {status.label}
                  </RetroBadge>
                )}
              </div>

              {/* Progress */}
              {status.running && status.total_tasks > 0 && (
                <div className="space-y-2">
                  <RetroProgress value={progress} showLabel variant="default" size="md" />
                  <div className="text-xs text-[var(--retro-text-muted)]">
                    {status.completed_tasks} / {status.total_tasks} tasks completed
                    {status.failed_tasks > 0 && (
                      <span className="text-[var(--retro-accent-red)] ml-2">
                        ({status.failed_tasks} failed)
                      </span>
                    )}
                  </div>
                </div>
              )}

              {/* Current task */}
              {status.current_task && (
                <div className="space-y-1">
                  <div className="text-xs text-[var(--retro-text-muted)]">Current Task:</div>
                  <div className="text-sm text-[var(--retro-accent-cyan)]">
                    <span className="text-[var(--retro-text-muted)] mr-2">{status.current_task}</span>
                    {status.current_task_title && (
                      <span className="text-[var(--retro-text-primary)]">
                        - "{status.current_task_title}"
                      </span>
                    )}
                  </div>
                </div>
              )}

              {/* Timestamps */}
              <div className="grid grid-cols-2 gap-2 text-xs text-[var(--retro-text-muted)]">
                {status.started_at && (
                  <div>
                    Started: {new Date(status.started_at).toLocaleString()}
                  </div>
                )}
                {status.last_update && (
                  <div>
                    Last update: {new Date(status.last_update).toLocaleString()}
                  </div>
                )}
              </div>

              {/* Message */}
              {status.message && (
                <div className="text-xs text-[var(--retro-text-secondary)] italic">
                  {status.message}
                </div>
              )}

              {/* Stop button */}
              {status.running && (
                <RetroButton
                  variant="danger"
                  onClick={handleStop}
                  disabled={stopping}
                  loading={stopping}
                  className="w-full sm:w-auto"
                >
                  STOP LOOP
                </RetroButton>
              )}
            </div>
          ) : (
            <div className="text-sm text-[var(--retro-text-muted)]">
              Unable to fetch status. Is Claude Harness running?
            </div>
          )}
        </RetroPanel>

        {/* Start New Loop */}
        {(!status || !status.running) && (
          <RetroPanel title="Start New Loop">
            <div className="space-y-4">
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <RetroInput
                  label="Label (required)"
                  value={formLabel}
                  onChange={(e) => setFormLabel(e.target.value)}
                  placeholder="Enter task label..."
                />
                <RetroSelect
                  label="Priority Filter"
                  value={formPriority}
                  onChange={(e) => setFormPriority(e.target.value)}
                  options={[
                    { value: '', label: 'All priorities' },
                    { value: '0', label: 'Critical (0)' },
                    { value: '1', label: 'High (1)' },
                    { value: '2', label: 'Medium (2)' },
                    { value: '3', label: 'Low (3)' },
                  ]}
                />
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <RetroInput
                  label="Max Tasks (0 = unlimited)"
                  type="number"
                  min={0}
                  value={formMaxTasks.toString()}
                  onChange={(e) => setFormMaxTasks(parseInt(e.target.value) || 0)}
                />
                <div className="flex items-end">
                  <RetroCheckbox
                    label="Dry Run (don't execute)"
                    checked={formDryRun}
                    onChange={(e) => setFormDryRun(e.target.checked)}
                  />
                </div>
              </div>

              <RetroButton
                variant="success"
                onClick={handleStart}
                disabled={starting || !formLabel}
                loading={starting}
                className="w-full sm:w-auto"
              >
                START RALPH LOOP
              </RetroButton>
            </div>
          </RetroPanel>
        )}

        {/* Error */}
        {error && (
          <div className="p-3 bg-[rgba(255,68,68,0.1)] border border-[var(--retro-accent-red)] rounded text-sm text-[var(--retro-accent-red)]">
            {error}
          </div>
        )}

        {/* Logs */}
        <RetroPanel
          title="Execution Log"
          actions={
            <RetroButton variant="ghost" size="sm" onClick={fetchLogs}>
              ↻
            </RetroButton>
          }
        >
          <div
            ref={logViewerRef}
            className="retro-log-viewer max-h-64"
          >
            {logs.length === 0 ? (
              <div className="text-[var(--retro-text-muted)]">No logs available</div>
            ) : (
              logs.map((line, i) => (
                <div key={i} className="retro-log-line">
                  {formatLogLine(line)}
                </div>
              ))
            )}
          </div>
        </RetroPanel>
      </div>
    </div>
  );
}

function formatLogLine(line: string): React.ReactNode {
  // Simple log formatting - colorize based on keywords
  const timestampMatch = line.match(/^\[([^\]]+)\]/);
  const timestamp = timestampMatch ? timestampMatch[0] : '';
  const rest = timestampMatch ? line.slice(timestamp.length) : line;

  let className = '';
  if (rest.includes('ERROR') || rest.includes('error') || rest.includes('failed')) {
    className = 'retro-log-error';
  } else if (rest.includes('WARN') || rest.includes('warning')) {
    className = 'retro-log-warn';
  } else if (rest.includes('INFO') || rest.includes('Starting') || rest.includes('Completed')) {
    className = 'retro-log-info';
  }

  return (
    <>
      {timestamp && <span className="retro-log-timestamp">{timestamp}</span>}
      <span className={className}>{rest}</span>
    </>
  );
}

export default RalphDashboard;
