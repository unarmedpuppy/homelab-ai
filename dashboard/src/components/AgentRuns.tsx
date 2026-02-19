import React, { useEffect, useState } from 'react';
import { agentRunsAPI } from '../api/client';
import type { AgentRunRecord, AgentRunWithSteps, AgentRunsStats } from '../types/api';
import { RetroPanel, RetroButton, RetroBadge, RetroCard, RetroStatCard } from './ui';

// Hook for mobile detection
function useIsMobile(breakpoint = 768) {
  const [isMobile, setIsMobile] = useState(
    typeof window !== 'undefined' ? window.innerWidth < breakpoint : false
  );

  useEffect(() => {
    const handleResize = () => {
      setIsMobile(window.innerWidth < breakpoint);
    };

    window.addEventListener('resize', handleResize);
    return () => window.removeEventListener('resize', handleResize);
  }, [breakpoint]);

  return isMobile;
}

function ExpandableContent({
  content,
  label,
  maxLength = 150,
  isJson = false,
  className = '',
}: {
  content: string;
  label: string;
  maxLength?: number;
  isJson?: boolean;
  className?: string;
}) {
  const [expanded, setExpanded] = useState(false);

  const displayContent = isJson ? content : content;
  const needsExpansion = displayContent.length > maxLength;

  if (!needsExpansion) {
    return (
      <div className={`text-xs ${className}`}>
        <strong className="text-[var(--retro-text-secondary)]">{label}:</strong>{' '}
        {isJson ? (
          <pre className="inline whitespace-pre-wrap font-mono text-[var(--retro-text-primary)]">{displayContent}</pre>
        ) : (
          <span className="text-[var(--retro-text-primary)]">{displayContent}</span>
        )}
      </div>
    );
  }

  return (
    <div className={`text-xs ${className}`}>
      <div className="flex items-start justify-between gap-2">
        <strong className="shrink-0 text-[var(--retro-text-secondary)]">{label}:</strong>
        <button
          onClick={(e) => {
            e.stopPropagation();
            setExpanded(!expanded);
          }}
          className="text-[var(--retro-accent-cyan)] hover:text-[var(--retro-text-primary)] text-xs shrink-0 uppercase font-bold"
        >
          {expanded ? 'Collapse' : 'Expand'}
        </button>
      </div>
      {expanded ? (
        <pre className="mt-1 p-2 bg-[var(--retro-bg-dark)] rounded max-h-64 overflow-y-auto whitespace-pre-wrap font-mono text-xs border border-[var(--retro-border)] text-[var(--retro-text-primary)]">
          {displayContent}
        </pre>
      ) : (
        <span className="text-[var(--retro-text-muted)]">
          {displayContent.slice(0, maxLength)}...
        </span>
      )}
    </div>
  );
}

// Map agent run status to retro badge variant
type BadgeVariant = 'status-open' | 'status-progress' | 'status-done' | 'status-blocked';

function getAgentStatusVariant(status: string): BadgeVariant {
  switch (status) {
    case 'completed':
      return 'status-done';
    case 'running':
      return 'status-progress';
    case 'failed':
      return 'status-blocked';
    case 'cancelled':
    case 'max_steps':
      return 'status-open';
    default:
      return 'status-open';
  }
}

function getStatusIcon(status: string): string {
  switch (status) {
    case 'completed':
      return '✓';
    case 'failed':
      return '✗';
    case 'running':
      return '⟳';
    case 'cancelled':
      return '⊘';
    case 'max_steps':
      return '⚠';
    default:
      return '?';
  }
}

export default function AgentRuns() {
  const [runs, setRuns] = useState<AgentRunRecord[]>([]);
  const [expandedRun, setExpandedRun] = useState<string | null>(null);
  const [expandedRunData, setExpandedRunData] = useState<AgentRunWithSteps | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [stats, setStats] = useState<AgentRunsStats | null>(null);
  const [loadingStats, setLoadingStats] = useState(true);
  const isMobile = useIsMobile();

  const fetchRuns = async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await agentRunsAPI.list({ limit: 50 });
      setRuns(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch agent runs');
      console.error('Error fetching agent runs:', err);
    } finally {
      setLoading(false);
    }
  };

  const fetchStats = async () => {
    try {
      setLoadingStats(true);
      const data = await agentRunsAPI.getStats();
      setStats(data);
    } catch (err) {
      console.error('Error fetching stats:', err);
    } finally {
      setLoadingStats(false);
    }
  };

  const fetchRunDetails = async (id: string) => {
    try {
      const data = await agentRunsAPI.get(id);
      setExpandedRunData(data);
    } catch (err) {
      console.error('Error fetching run details:', err);
    }
  };

  useEffect(() => {
    fetchRuns();
    fetchStats();
  }, []);

  const handleRowClick = (id: string) => {
    if (expandedRun === id) {
      setExpandedRun(null);
      setExpandedRunData(null);
    } else {
      setExpandedRun(id);
      fetchRunDetails(id);
    }
  };

  const formatTimestamp = (timestamp: string) => {
    const date = new Date(timestamp);
    const now = new Date();
    const diff = now.getTime() - date.getTime();
    const seconds = Math.floor(diff / 1000);

    if (seconds < 60) return `${seconds}s ago`;
    if (seconds < 3600) return `${Math.floor(seconds / 60)}m ago`;
    if (seconds < 86400) return `${Math.floor(seconds / 3600)}h ago`;
    return date.toLocaleDateString();
  };

  const formatDuration = (durationMs: number | null) => {
    if (!durationMs) return 'N/A';
    if (durationMs < 1000) return `${durationMs}ms`;
    if (durationMs < 60000) return `${(durationMs / 1000).toFixed(1)}s`;
    return `${(durationMs / 60000).toFixed(1)}m`;
  };

  const truncateText = (text: string, maxLength: number = 80) => {
    return text.length > maxLength ? text.slice(0, maxLength) + '...' : text;
  };

  if (loading && runs.length === 0) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-[var(--retro-text-muted)] retro-animate-pulse text-sm">
          Loading agent runs...
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="p-4 bg-[rgba(255,68,68,0.1)] border border-[var(--retro-accent-red)] rounded">
        <h3 className="text-[var(--retro-accent-red)] font-bold mb-2">
          Error Loading Agent Runs
        </h3>
        <p className="text-[var(--retro-accent-red)] text-sm mb-3">{error}</p>
        <RetroButton variant="danger" onClick={fetchRuns} size="sm">
          Retry
        </RetroButton>
      </div>
    );
  }

  return (
    <div className="space-y-4 sm:space-y-6 p-4">
      {/* Header with refresh button */}
      <div className="flex justify-between items-center">
        <h2 className="text-xl sm:text-2xl font-bold text-[var(--retro-text-primary)]">
          Agent Runs
        </h2>
        <RetroButton
          variant="primary"
          size="sm"
          onClick={() => {
            fetchRuns();
            fetchStats();
          }}
        >
          Refresh
        </RetroButton>
      </div>

      {/* Stats Cards */}
      {stats && !loadingStats && (
        <div className="grid grid-cols-2 md:grid-cols-4 gap-3 sm:gap-4">
          <RetroStatCard
            label="Total Runs"
            value={stats.total_runs}
            color="default"
          />
          <RetroStatCard
            label="Completed"
            value={stats.completed_runs}
            color="green"
          />
          <RetroStatCard
            label="Failed"
            value={stats.failed_runs}
            color="red"
          />
          <RetroStatCard
            label="Avg Duration"
            value={formatDuration(stats.avg_duration_ms)}
            color="blue"
          />
        </div>
      )}

      {/* Mobile Card List */}
      {isMobile ? (
        <div className="space-y-3">
          {runs.map((run) => (
            <React.Fragment key={run.id}>
              <RetroCard
                onClick={() => handleRowClick(run.id)}
                selected={expandedRun === run.id}
                size="responsive"
              >
                <div className="space-y-2">
                  {/* Status + Task */}
                  <div className="flex items-start justify-between gap-2">
                    <span className="text-sm text-[var(--retro-text-primary)] flex-1 line-clamp-2">
                      {truncateText(run.task, 60)}
                    </span>
                    <RetroBadge variant={getAgentStatusVariant(run.status)} size="sm">
                      {getStatusIcon(run.status)} {run.status}
                    </RetroBadge>
                  </div>

                  {/* Model / Duration / Steps */}
                  <div className="flex flex-wrap items-center gap-2 text-xs text-[var(--retro-text-muted)]">
                    {run.model_used && (
                      <span className="text-[var(--retro-accent-cyan)] font-mono">
                        {run.model_used.replace('qwen2.5-', 'qwen/')}
                      </span>
                    )}
                    <span>•</span>
                    <span>{formatDuration(run.duration_ms)}</span>
                    <span>•</span>
                    <span>{run.total_steps} steps</span>
                  </div>

                  {/* Source + Time */}
                  <div className="flex items-center justify-between text-[0.625rem] text-[var(--retro-text-muted)] uppercase tracking-wide">
                    <span>{run.source || 'N/A'}</span>
                    <span>{formatTimestamp(run.started_at)}</span>
                  </div>
                </div>
              </RetroCard>

              {/* Expanded Details - Mobile */}
              {expandedRun === run.id && expandedRunData && (
                <RetroPanel title="Run Details" className="mt-2">
                  <div className="space-y-4">
                    {/* Details Grid */}
                    <div className="grid grid-cols-2 gap-2 text-xs">
                      <div>
                        <span className="text-[var(--retro-text-muted)]">ID:</span>
                        <span className="text-[var(--retro-text-primary)] ml-1 font-mono text-[0.625rem] break-all">
                          {run.id}
                        </span>
                      </div>
                      <div>
                        <span className="text-[var(--retro-text-muted)]">Triggered:</span>
                        <span className="text-[var(--retro-text-primary)] ml-1">
                          {run.triggered_by || 'N/A'}
                        </span>
                      </div>
                      <div className="col-span-2">
                        <span className="text-[var(--retro-text-muted)]">Directory:</span>
                        <span className="text-[var(--retro-text-primary)] ml-1 font-mono text-[0.625rem] break-all">
                          {run.working_directory || 'N/A'}
                        </span>
                      </div>
                    </div>

                    {/* System Prompt */}
                    {expandedRunData.system_prompt && (
                      <ExpandableContent
                        content={expandedRunData.system_prompt}
                        label="System Prompt"
                        maxLength={200}
                      />
                    )}

                    {/* Error */}
                    {run.error && (
                      <div className="p-2 bg-[rgba(255,68,68,0.1)] border border-[var(--retro-accent-red)] rounded text-xs text-[var(--retro-accent-red)]">
                        <strong>Error:</strong> {run.error}
                      </div>
                    )}

                    {/* Final Answer */}
                    {run.final_answer && (
                      <ExpandableContent
                        content={run.final_answer}
                        label="Final Answer"
                        maxLength={200}
                      />
                    )}

                    {/* Execution Steps */}
                    <div>
                      <h4 className="text-xs font-bold text-[var(--retro-text-secondary)] mb-2">
                        Execution Steps
                      </h4>
                      <div className="space-y-2">
                        {expandedRunData.steps.map((step, index) => {
                          const cumulativePrompt = expandedRunData.steps
                            .slice(0, index + 1)
                            .reduce((sum, s) => sum + (s.prompt_tokens || 0), 0);
                          const cumulativeCompletion = expandedRunData.steps
                            .slice(0, index + 1)
                            .reduce((sum, s) => sum + (s.completion_tokens || 0), 0);
                          const hasTokens = step.prompt_tokens || step.completion_tokens;

                          return (
                            <div
                              key={step.id}
                              className="bg-[var(--retro-bg-light)] border border-[var(--retro-border)] rounded p-2 text-xs"
                            >
                              <div className="flex items-start justify-between mb-1 gap-2">
                                <span className="text-[var(--retro-text-primary)] font-medium">
                                  Step {step.step_number}: {step.action_type}
                                </span>
                                <div className="flex items-center gap-2 text-[0.625rem] shrink-0">
                                  {hasTokens && (
                                    <span className="text-[var(--retro-accent-purple)]">
                                      {cumulativePrompt + cumulativeCompletion} tok
                                    </span>
                                  )}
                                  <span className="text-[var(--retro-text-muted)]">
                                    {formatDuration(step.duration_ms)}
                                  </span>
                                </div>
                              </div>
                              {step.tool_name && (
                                <div className="text-[var(--retro-accent-cyan)] mb-1">
                                  Tool: {step.tool_name}
                                </div>
                              )}
                              {step.thinking && (
                                <ExpandableContent
                                  content={step.thinking}
                                  label="Thinking"
                                  maxLength={100}
                                  className="mb-1"
                                />
                              )}
                              {step.tool_args && (
                                <ExpandableContent
                                  content={JSON.stringify(step.tool_args, null, 2)}
                                  label="Args"
                                  maxLength={100}
                                  isJson={true}
                                  className="mb-1"
                                />
                              )}
                              {step.tool_result && (
                                <ExpandableContent
                                  content={step.tool_result}
                                  label="Result"
                                  maxLength={100}
                                  className="mb-1"
                                />
                              )}
                              {step.error && (
                                <div className="text-[var(--retro-accent-red)]">
                                  <strong>Error:</strong> {step.error}
                                </div>
                              )}
                            </div>
                          );
                        })}
                      </div>
                    </div>
                  </div>
                </RetroPanel>
              )}
            </React.Fragment>
          ))}
        </div>
      ) : (
        /* Desktop Table */
        <RetroPanel title="Run History">
          <div className="overflow-x-auto -mx-4 sm:mx-0">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-[var(--retro-border)]">
                  <th className="px-3 py-2 text-left text-xs font-bold text-[var(--retro-text-secondary)]">
                    Status
                  </th>
                  <th className="px-3 py-2 text-left text-xs font-bold text-[var(--retro-text-secondary)]">
                    Task
                  </th>
                  <th className="px-3 py-2 text-left text-xs font-bold text-[var(--retro-text-secondary)]">
                    Model / Backend
                  </th>
                  <th className="px-3 py-2 text-left text-xs font-bold text-[var(--retro-text-secondary)]">
                    Steps
                  </th>
                  <th className="px-3 py-2 text-left text-xs font-bold text-[var(--retro-text-secondary)]">
                    Duration
                  </th>
                  <th className="px-3 py-2 text-left text-xs font-bold text-[var(--retro-text-secondary)]">
                    Source
                  </th>
                  <th className="px-3 py-2 text-left text-xs font-bold text-[var(--retro-text-secondary)]">
                    Started
                  </th>
                </tr>
              </thead>
              <tbody className="divide-y divide-[var(--retro-border)]">
                {runs.map((run) => (
                  <React.Fragment key={run.id}>
                    <tr
                      className="hover:bg-[var(--retro-bg-light)] cursor-pointer transition-colors"
                      onClick={() => handleRowClick(run.id)}
                    >
                      <td className="px-3 py-3 whitespace-nowrap">
                        <RetroBadge variant={getAgentStatusVariant(run.status)} size="sm">
                          {getStatusIcon(run.status)} {run.status}
                        </RetroBadge>
                      </td>
                      <td className="px-3 py-3">
                        <div
                          className="text-[var(--retro-text-primary)]"
                          title={run.task}
                        >
                          {truncateText(run.task)}
                        </div>
                      </td>
                      <td className="px-3 py-3 whitespace-nowrap">
                        {run.model_used || run.backend ? (
                          <div>
                            {run.model_used && (
                              <div className="text-[var(--retro-accent-cyan)] font-mono text-xs">
                                {run.model_used.replace('qwen2.5-', 'qwen/')}
                              </div>
                            )}
                            {(run.backend_name || run.backend) && (
                              <div className="text-[var(--retro-text-muted)] text-xs mt-0.5">
                                {run.backend_name || run.backend}
                              </div>
                            )}
                          </div>
                        ) : (
                          <span className="text-[var(--retro-text-muted)]">auto</span>
                        )}
                      </td>
                      <td className="px-3 py-3 whitespace-nowrap text-[var(--retro-text-primary)] font-mono">
                        {run.total_steps}
                      </td>
                      <td className="px-3 py-3 whitespace-nowrap text-[var(--retro-text-primary)] font-mono">
                        {formatDuration(run.duration_ms)}
                      </td>
                      <td className="px-3 py-3 whitespace-nowrap text-[var(--retro-text-muted)]">
                        {run.source || 'N/A'}
                      </td>
                      <td className="px-3 py-3 whitespace-nowrap text-[var(--retro-text-muted)]">
                        {formatTimestamp(run.started_at)}
                      </td>
                    </tr>
                    {expandedRun === run.id && expandedRunData && (
                      <tr className="bg-[var(--retro-bg-medium)]">
                        <td colSpan={7} className="px-4 py-4">
                          <div className="space-y-4">
                            <div className="border-b border-[var(--retro-border)] pb-3">
                              <h4 className="text-xs font-bold text-[var(--retro-text-secondary)] mb-3">
                                Run Details
                              </h4>
                              <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 text-sm">
                                <div>
                                  <span className="text-[var(--retro-text-muted)]">ID:</span>
                                  <span className="text-[var(--retro-text-primary)] ml-2 font-mono text-xs">
                                    {run.id}
                                  </span>
                                </div>
                                <div>
                                  <span className="text-[var(--retro-text-muted)]">Triggered By:</span>
                                  <span className="text-[var(--retro-text-primary)] ml-2">
                                    {run.triggered_by || 'N/A'}
                                  </span>
                                </div>
                                <div>
                                  <span className="text-[var(--retro-text-muted)]">Working Directory:</span>
                                  <span className="text-[var(--retro-text-primary)] ml-2 font-mono text-xs">
                                    {run.working_directory || 'N/A'}
                                  </span>
                                </div>
                                <div>
                                  <span className="text-[var(--retro-text-muted)]">Backend:</span>
                                  <span className="text-[var(--retro-text-primary)] ml-2">
                                    {run.backend_name || run.backend || 'N/A'}
                                  </span>
                                </div>
                                <div>
                                  <span className="text-[var(--retro-text-muted)]">Model Used:</span>
                                  <span className="text-[var(--retro-text-primary)] ml-2">
                                    {run.model_used || 'auto'}
                                  </span>
                                </div>
                              </div>
                              {expandedRunData.system_prompt && (
                                <div className="mt-3">
                                  <ExpandableContent
                                    content={expandedRunData.system_prompt}
                                    label="System Prompt"
                                    maxLength={200}
                                  />
                                </div>
                              )}
                              {run.error && (
                                <div className="mt-2 p-2 bg-[rgba(255,68,68,0.1)] border border-[var(--retro-accent-red)] rounded text-sm text-[var(--retro-accent-red)]">
                                  <strong>Error:</strong> {run.error}
                                </div>
                              )}
                              {run.final_answer && (
                                <div className="mt-2">
                                  <ExpandableContent
                                    content={run.final_answer}
                                    label="Final Answer"
                                    maxLength={200}
                                  />
                                </div>
                              )}
                            </div>

                            <div>
                              <h4 className="text-xs font-bold text-[var(--retro-text-secondary)] mb-3">
                                Execution Steps
                              </h4>
                              <div className="space-y-2">
                                {expandedRunData.steps.map((step, index) => {
                                  const cumulativePrompt = expandedRunData.steps
                                    .slice(0, index + 1)
                                    .reduce((sum, s) => sum + (s.prompt_tokens || 0), 0);
                                  const cumulativeCompletion = expandedRunData.steps
                                    .slice(0, index + 1)
                                    .reduce((sum, s) => sum + (s.completion_tokens || 0), 0);
                                  const hasTokens = step.prompt_tokens || step.completion_tokens;

                                  return (
                                    <div
                                      key={step.id}
                                      className="bg-[var(--retro-bg-card)] border border-[var(--retro-border)] rounded p-3 text-sm"
                                    >
                                      <div className="flex items-start justify-between mb-2">
                                        <span className="text-[var(--retro-text-primary)] font-medium">
                                          Step {step.step_number}: {step.action_type}
                                        </span>
                                        <div className="flex items-center gap-3 text-xs">
                                          {hasTokens && (
                                            <span
                                              className="text-[var(--retro-accent-purple)]"
                                              title={`Step: ${step.prompt_tokens || 0}+${step.completion_tokens || 0} | Cumulative: ${cumulativePrompt}+${cumulativeCompletion}`}
                                            >
                                              {cumulativePrompt + cumulativeCompletion} tok
                                            </span>
                                          )}
                                          <span className="text-[var(--retro-text-muted)]">
                                            {formatDuration(step.duration_ms)}
                                          </span>
                                        </div>
                                      </div>
                                      {step.tool_name && (
                                        <div className="text-xs text-[var(--retro-accent-cyan)] mb-1">
                                          Tool: {step.tool_name}
                                        </div>
                                      )}
                                      {step.thinking && (
                                        <ExpandableContent
                                          content={step.thinking}
                                          label="Thinking"
                                          maxLength={150}
                                          className="mb-1"
                                        />
                                      )}
                                      {step.tool_args && (
                                        <ExpandableContent
                                          content={JSON.stringify(step.tool_args, null, 2)}
                                          label="Args"
                                          maxLength={150}
                                          isJson={true}
                                          className="mb-1"
                                        />
                                      )}
                                      {step.tool_result && (
                                        <ExpandableContent
                                          content={step.tool_result}
                                          label="Result"
                                          maxLength={150}
                                          className="mb-1"
                                        />
                                      )}
                                      {step.error && (
                                        <div className="text-xs text-[var(--retro-accent-red)]">
                                          <strong>Error:</strong> {step.error}
                                        </div>
                                      )}
                                    </div>
                                  );
                                })}
                              </div>
                            </div>
                          </div>
                        </td>
                      </tr>
                    )}
                  </React.Fragment>
                ))}
              </tbody>
            </table>
          </div>
        </RetroPanel>
      )}

      {runs.length === 0 && (
        <div className="text-center py-8 text-[var(--retro-text-muted)]">
          No agent runs found.
        </div>
      )}
    </div>
  );
}
