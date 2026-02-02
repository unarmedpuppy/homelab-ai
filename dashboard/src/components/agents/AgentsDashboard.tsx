import { useState, useCallback } from 'react';
import type { Agent, FleetStats } from '../../types/agents';
import { agentsAPI } from '../../api/client';
import { RetroButton, RetroPanel } from '../ui';
import { useVisibilityPolling } from '../../hooks/useDocumentVisibility';
import { FleetOverview } from './FleetOverview';
import { AgentCard } from './AgentCard';
import { AgentDetailPanel } from './AgentDetailPanel';

const POLL_INTERVAL = 30000; // 30 seconds

export function AgentsDashboard() {
  const [agents, setAgents] = useState<Agent[]>([]);
  const [stats, setStats] = useState<FleetStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [checkingAgent, setCheckingAgent] = useState<string | null>(null);
  const [selectedAgent, setSelectedAgent] = useState<Agent | null>(null);

  const fetchData = useCallback(async () => {
    try {
      const [agentsData, statsData] = await Promise.all([
        agentsAPI.list(),
        agentsAPI.getStats(),
      ]);
      setAgents(agentsData);
      setStats(statsData);
      setError(null);

      // Update selected agent if it's still in the list
      if (selectedAgent) {
        const updated = agentsData.find((a) => a.id === selectedAgent.id);
        if (updated) {
          setSelectedAgent(updated);
        }
      }
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Failed to fetch agent data');
      console.error('Failed to fetch agent data:', e);
    } finally {
      setLoading(false);
    }
  }, [selectedAgent]);

  // Visibility-aware polling - pauses when tab is hidden
  useVisibilityPolling({
    callback: fetchData,
    interval: POLL_INTERVAL,
    enabled: true,
    immediate: true,
  });

  const handleForceCheck = async (agentId: string) => {
    setCheckingAgent(agentId);
    try {
      await agentsAPI.forceCheck(agentId);
      // Refresh data after check
      await fetchData();
    } catch (e) {
      console.error('Failed to force health check:', e);
    } finally {
      setCheckingAgent(null);
    }
  };

  const handleRefresh = () => {
    setLoading(true);
    fetchData();
  };

  const handleAgentClick = (agent: Agent) => {
    setSelectedAgent(agent);
  };

  const handleCloseDetail = () => {
    setSelectedAgent(null);
  };

  // Show detail panel if an agent is selected
  if (selectedAgent) {
    return (
      <AgentDetailPanel
        agent={selectedAgent}
        onClose={handleCloseDetail}
      />
    );
  }

  if (loading && agents.length === 0) {
    return (
      <div className="h-full flex flex-col bg-[var(--retro-bg-dark)]">
        <div className="p-4 bg-[var(--retro-bg-medium)] border-b border-[var(--retro-border)]">
          <h1 className="text-lg font-bold uppercase tracking-wider text-[var(--retro-accent-green)]">
            Agent Fleet
          </h1>
        </div>
        <div className="flex-1 flex items-center justify-center">
          <div className="text-[var(--retro-text-muted)] retro-animate-pulse uppercase tracking-wider text-sm">
            Loading fleet status...
          </div>
        </div>
      </div>
    );
  }

  if (error && agents.length === 0) {
    return (
      <div className="h-full flex flex-col bg-[var(--retro-bg-dark)]">
        <div className="p-4 bg-[var(--retro-bg-medium)] border-b border-[var(--retro-border)]">
          <h1 className="text-lg font-bold uppercase tracking-wider text-[var(--retro-accent-green)]">
            Agent Fleet
          </h1>
        </div>
        <div className="flex-1 p-4">
          <div className="p-4 bg-[rgba(255,68,68,0.1)] border-2 border-[var(--retro-accent-red)] rounded">
            <h3 className="text-[var(--retro-accent-red)] font-bold mb-2 uppercase tracking-wider">
              Connection Error
            </h3>
            <p className="text-[var(--retro-text-muted)] text-sm mb-3">{error}</p>
            <RetroButton variant="danger" onClick={handleRefresh} size="sm">
              Retry
            </RetroButton>
          </div>
        </div>
      </div>
    );
  }

  // Sort agents: online first, then by name
  const sortedAgents = [...agents].sort((a, b) => {
    // Online agents first
    if (a.health.status === 'online' && b.health.status !== 'online') return -1;
    if (a.health.status !== 'online' && b.health.status === 'online') return 1;
    // Then by name
    return a.name.localeCompare(b.name);
  });

  return (
    <div className="h-full flex flex-col bg-[var(--retro-bg-dark)] overflow-y-auto">
      {/* Header */}
      <div className="p-4 bg-[var(--retro-bg-medium)] border-b border-[var(--retro-border)]">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-lg font-bold uppercase tracking-wider text-[var(--retro-accent-green)]">
              Agent Fleet
            </h1>
            <p className="text-xs text-[var(--retro-text-muted)] mt-1">
              {stats ? `${stats.online_count}/${stats.total_agents} agents online` : 'Monitoring Claude Code agents'}
            </p>
          </div>
          <RetroButton variant="ghost" size="sm" onClick={handleRefresh}>
            Refresh
          </RetroButton>
        </div>
      </div>

      <div className="flex-1 p-4 space-y-4 max-w-6xl">
        {/* Fleet Overview Stats */}
        <RetroPanel title="Fleet Status">
          <FleetOverview stats={stats} loading={loading} />
        </RetroPanel>

        {/* Agent Cards Grid */}
        <RetroPanel title="Agents">
          {agents.length === 0 ? (
            <div className="text-center py-8 text-[var(--retro-text-muted)] uppercase tracking-wider">
              No agents configured
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {sortedAgents.map((agent) => (
                <AgentCard
                  key={agent.id}
                  agent={agent}
                  onForceCheck={handleForceCheck}
                  isChecking={checkingAgent === agent.id}
                  onClick={() => handleAgentClick(agent)}
                />
              ))}
            </div>
          )}
        </RetroPanel>

        {/* Last updated indicator */}
        {stats?.last_updated && (
          <div className="text-xs text-[var(--retro-text-muted)] text-center">
            Last updated: {new Date(stats.last_updated).toLocaleTimeString()}
            <span className="mx-2">|</span>
            Auto-refresh every 30s (paused when tab hidden)
          </div>
        )}
      </div>
    </div>
  );
}

export default AgentsDashboard;
