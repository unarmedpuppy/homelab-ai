import React, { useEffect, useState } from 'react';
import { agentRunsAPI } from '../api/client';
import type { AgentRunRecord, AgentRunWithSteps, AgentRunsStats } from '../types/api';

export default function AgentRuns() {
  const [runs, setRuns] = useState<AgentRunRecord[]>([]);
  const [expandedRun, setExpandedRun] = useState<string | null>(null);
  const [expandedRunData, setExpandedRunData] = useState<AgentRunWithSteps | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [stats, setStats] = useState<AgentRunsStats | null>(null);
  const [loadingStats, setLoadingStats] = useState(true);

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

  const getStatusBadge = (status: string) => {
    const baseClasses = 'px-2 py-1 rounded text-xs font-medium border';
    switch (status) {
      case 'completed':
        return `${baseClasses} bg-green-500/20 text-green-400 border-green-500/30`;
      case 'failed':
        return `${baseClasses} bg-red-500/20 text-red-400 border-red-500/30`;
      case 'running':
        return `${baseClasses} bg-yellow-500/20 text-yellow-400 border-yellow-500/30`;
      case 'cancelled':
        return `${baseClasses} bg-gray-500/20 text-gray-400 border-gray-500/30`;
      case 'max_steps':
        return `${baseClasses} bg-orange-500/20 text-orange-400 border-orange-500/30`;
      default:
        return `${baseClasses} bg-gray-500/20 text-gray-400 border-gray-500/30`;
    }
  };

  const getStatusIcon = (status: string) => {
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
  };

  const truncateText = (text: string, maxLength: number = 80) => {
    return text.length > maxLength ? text.slice(0, maxLength) + '...' : text;
  };

  if (loading && runs.length === 0) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-gray-400">Loading agent runs...</div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-red-900/20 border border-red-500 rounded-lg p-4">
        <h3 className="text-red-400 font-semibold mb-2">Error Loading Agent Runs</h3>
        <p className="text-red-300">{error}</p>
        <button
          onClick={fetchRuns}
          className="mt-3 px-4 py-2 bg-red-500 hover:bg-red-600 rounded text-white text-sm"
        >
          Retry
        </button>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header with refresh button */}
      <div className="flex justify-between items-center">
        <h2 className="text-3xl font-bold text-white">Agent Runs</h2>
        <button
          onClick={() => {
            fetchRuns();
            fetchStats();
          }}
          className="px-4 py-2 bg-blue-500 hover:bg-blue-600 rounded text-white text-sm font-medium transition-colors"
        >
          Refresh
        </button>
      </div>

      {/* Stats Cards */}
      {stats && !loadingStats && (
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <div className="bg-gray-800 rounded-lg p-4 border border-gray-700">
            <div className="text-gray-400 text-sm">Total Runs</div>
            <div className="text-2xl font-bold text-white mt-1">{stats.total_runs}</div>
          </div>
          <div className="bg-gray-800 rounded-lg p-4 border border-gray-700">
            <div className="text-gray-400 text-sm">Completed</div>
            <div className="text-2xl font-bold text-green-400 mt-1">{stats.completed_runs}</div>
          </div>
          <div className="bg-gray-800 rounded-lg p-4 border border-gray-700">
            <div className="text-gray-400 text-sm">Failed</div>
            <div className="text-2xl font-bold text-red-400 mt-1">{stats.failed_runs}</div>
          </div>
          <div className="bg-gray-800 rounded-lg p-4 border border-gray-700">
            <div className="text-gray-400 text-sm">Avg Duration</div>
            <div className="text-2xl font-bold text-blue-400 mt-1">{formatDuration(stats.avg_duration_ms)}</div>
          </div>
        </div>
      )}

      {/* Runs Table */}
      <div className="bg-gray-800 border border-gray-700 rounded-lg overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead className="bg-gray-900 border-b border-gray-700">
              <tr>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-400 uppercase tracking-wider">Status</th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-400 uppercase tracking-wider">Task</th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-400 uppercase tracking-wider">Steps</th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-400 uppercase tracking-wider">Duration</th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-400 uppercase tracking-wider">Source</th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-400 uppercase tracking-wider">Started</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-700">
              {runs.map((run) => (
                <React.Fragment key={run.id}>
                  <tr
                    className="hover:bg-gray-700/50 cursor-pointer transition-colors"
                    onClick={() => handleRowClick(run.id)}
                  >
                    <td className="px-4 py-3 whitespace-nowrap">
                      <span className={getStatusBadge(run.status)}>
                        {getStatusIcon(run.status)} {run.status}
                      </span>
                    </td>
                    <td className="px-4 py-3">
                      <div className="text-sm text-gray-300" title={run.task}>
                        {truncateText(run.task)}
                      </div>
                      {run.model_used && (
                        <div className="text-xs text-gray-500 mt-1">{run.model_used}</div>
                      )}
                    </td>
                    <td className="px-4 py-3 whitespace-nowrap text-sm text-gray-300">
                      {run.total_steps}
                    </td>
                    <td className="px-4 py-3 whitespace-nowrap text-sm text-gray-300">
                      {formatDuration(run.duration_ms)}
                    </td>
                    <td className="px-4 py-3 whitespace-nowrap text-sm text-gray-300">
                      {run.source || 'N/A'}
                    </td>
                    <td className="px-4 py-3 whitespace-nowrap text-sm text-gray-300">
                      {formatTimestamp(run.started_at)}
                    </td>
                  </tr>
                  {expandedRun === run.id && expandedRunData && (
                    <tr className="bg-gray-900/50">
                      <td colSpan={6} className="px-4 py-4">
                        <div className="space-y-4">
                          <div className="border-b border-gray-700 pb-2">
                            <h4 className="text-sm font-semibold text-white mb-2">Run Details</h4>
                            <div className="grid grid-cols-2 gap-4 text-sm">
                              <div>
                                <span className="text-gray-400">ID:</span>
                                <span className="text-gray-300 ml-2">{run.id}</span>
                              </div>
                              <div>
                                <span className="text-gray-400">Triggered By:</span>
                                <span className="text-gray-300 ml-2">{run.triggered_by || 'N/A'}</span>
                              </div>
                              <div>
                                <span className="text-gray-400">Working Directory:</span>
                                <span className="text-gray-300 ml-2">{run.working_directory || 'N/A'}</span>
                              </div>
                              <div>
                                <span className="text-gray-400">Backend:</span>
                                <span className="text-gray-300 ml-2">{run.backend || 'N/A'}</span>
                              </div>
                            </div>
                            {run.error && (
                              <div className="mt-2 p-2 bg-red-900/20 border border-red-500/30 rounded text-sm text-red-400">
                                <strong>Error:</strong> {run.error}
                              </div>
                            )}
                            {run.final_answer && (
                              <div className="mt-2">
                                <strong className="text-gray-300">Final Answer:</strong>
                                <div className="mt-1 p-2 bg-gray-800 rounded text-sm text-gray-300">
                                  {truncateText(run.final_answer, 200)}
                                </div>
                              </div>
                            )}
                          </div>

                          <div>
                            <h4 className="text-sm font-semibold text-white mb-2">Execution Steps</h4>
                            <div className="space-y-2">
                              {expandedRunData.steps.map((step) => (
                                <div key={step.id} className="bg-gray-800 rounded p-3 text-sm">
                                  <div className="flex items-start justify-between mb-2">
                                    <span className="text-white font-medium">
                                      Step {step.step_number}: {step.action_type}
                                    </span>
                                    <span className="text-xs text-gray-500">
                                      {formatDuration(step.duration_ms)}
                                    </span>
                                  </div>
                                  {step.tool_name && (
                                    <div className="text-xs text-blue-400 mb-1">
                                      Tool: {step.tool_name}
                                    </div>
                                  )}
                                  {step.thinking && (
                                    <div className="text-xs text-gray-400 mb-1">
                                      <strong>Thinking:</strong> {truncateText(step.thinking, 150)}
                                    </div>
                                  )}
                                  {step.tool_args && (
                                    <div className="text-xs text-gray-400 mb-1">
                                      <strong>Args:</strong> {JSON.stringify(step.tool_args, null, 2)}
                                    </div>
                                  )}
                                  {step.tool_result && (
                                    <div className="text-xs text-gray-300 mb-1">
                                      <strong>Result:</strong> {truncateText(step.tool_result, 150)}
                                    </div>
                                  )}
                                  {step.error && (
                                    <div className="text-xs text-red-400">
                                      <strong>Error:</strong> {step.error}
                                    </div>
                                  )}
                                </div>
                              ))}
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
      </div>

      {runs.length === 0 && (
        <div className="text-center py-8 text-gray-400">
          No agent runs found.
        </div>
      )}
    </div>
  );
}