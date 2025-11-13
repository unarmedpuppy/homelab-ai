import { api } from '@/lib/api';
import AgentCard from '@/components/AgentCard';
import ActivityFeed from '@/components/ActivityFeed';
import StatsCards from '@/components/StatsCards';
import DashboardWrapper from '@/components/DashboardWrapper';

export const revalidate = 5; // Revalidate every 5 seconds

export default async function DashboardPage() {
  // Fetch data in parallel
  const [agentsData, statsData, recentActionsData] = await Promise.all([
    api.getAgents().catch(() => ({ status: 'error', count: 0, agents: [] })),
    api.getStats().catch(() => ({ status: 'error', stats: {
      totalAgents: 0,
      activeAgents: 0,
      idleAgents: 0,
      blockedAgents: 0,
      totalActions: 0,
      actionsLast24h: 0,
      toolUsage: {},
      taskStats: { pending: 0, in_progress: 0, completed: 0 },
    }})),
    api.getRecentActions().catch(() => ({ status: 'error', count: 0, actions: [] })),
  ]);

  const agents = agentsData.agents || [];
  const stats = statsData.stats;
  const recentActions = recentActionsData.actions || [];

  return (
    <DashboardWrapper>
      <div className="min-h-screen bg-gray-50 p-6">
        <div className="max-w-7xl mx-auto">
          <div className="mb-8">
            <h1 className="text-3xl font-bold text-gray-900 mb-2">Agent Monitoring Dashboard</h1>
            <p className="text-gray-600">Real-time monitoring of all AI agents</p>
          </div>

          {/* Stats Cards */}
          <StatsCards stats={stats} />

          {/* Main Content Grid */}
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            {/* Agents List */}
            <div className="lg:col-span-2">
              <div className="mb-4">
                <h2 className="text-xl font-semibold text-gray-900 mb-4">
                  Agents ({agents.length})
                </h2>
                {agents.length === 0 ? (
                  <div className="bg-white rounded-lg shadow-md p-8 text-center">
                    <p className="text-gray-500">No agents found</p>
                  </div>
                ) : (
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    {agents.map((agent) => (
                      <AgentCard key={agent.id} agent={agent} />
                    ))}
                  </div>
                )}
              </div>
            </div>

            {/* Activity Feed */}
            <div className="lg:col-span-1">
              <ActivityFeed initialActions={recentActions} autoRefresh={true} />
            </div>
          </div>
        </div>
      </div>
    </DashboardWrapper>
  );
}
