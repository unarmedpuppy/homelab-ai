import { api } from '@/lib/api';
import { notFound } from 'next/navigation';
import Link from 'next/link';
import LinkToGrafana from '@/components/LinkToGrafana';

interface AgentDetailPageProps {
  params: {
    id: string;
  };
}

export const revalidate = 5; // Revalidate every 5 seconds

export default async function AgentDetailPage({ params }: AgentDetailPageProps) {
  let agentData;
  try {
    agentData = await api.getAgent(params.id);
  } catch (error) {
    notFound();
  }

  if (agentData.status !== 'success') {
    notFound();
  }

  const agent = agentData.agent;

  const statusColors = {
    active: 'bg-green-100 text-green-800 border-green-300',
    idle: 'bg-gray-100 text-gray-800 border-gray-300',
    blocked: 'bg-red-100 text-red-800 border-red-300',
    completed: 'bg-blue-100 text-blue-800 border-blue-300',
  };

  return (
    <div className="min-h-screen bg-gray-50 p-6">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="mb-6">
          <Link href="/" className="text-blue-600 hover:text-blue-800 mb-4 inline-block">
            ← Back to Dashboard
          </Link>
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-3xl font-bold text-gray-900">{agent.agent_id}</h1>
              <p className="text-gray-600 mt-1">Agent Details</p>
            </div>
            <div className="flex items-center space-x-4">
              <LinkToGrafana />
              <span className={`px-4 py-2 rounded-full text-sm font-medium border ${statusColors[agent.status]}`}>
                {agent.status}
              </span>
            </div>
          </div>
        </div>

        {/* Stats Grid */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-6">
          <div className="bg-white rounded-lg shadow-md p-6">
            <p className="text-sm text-gray-600 mb-2">Total Sessions</p>
            <p className="text-3xl font-bold text-gray-900">{agent.sessionStats.total_sessions}</p>
          </div>
          <div className="bg-white rounded-lg shadow-md p-6">
            <p className="text-sm text-gray-600 mb-2">Tasks Completed</p>
            <p className="text-3xl font-bold text-gray-900">{agent.sessionStats.total_tasks_completed}</p>
          </div>
          <div className="bg-white rounded-lg shadow-md p-6">
            <p className="text-sm text-gray-600 mb-2">Tools Called</p>
            <p className="text-3xl font-bold text-gray-900">{agent.sessionStats.total_tools_called}</p>
          </div>
        </div>

        {/* Main Content */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Current Status */}
          <div className="bg-white rounded-lg shadow-md p-6">
            <h2 className="text-xl font-semibold text-gray-900 mb-4">Current Status</h2>
            <div className="space-y-4">
              {agent.current_task_id && (
                <div>
                  <p className="text-sm text-gray-600 mb-1">Current Task</p>
                  <p className="text-lg font-medium text-gray-900">{agent.current_task_id}</p>
                </div>
              )}
              {agent.progress && (
                <div>
                  <p className="text-sm text-gray-600 mb-1">Progress</p>
                  <p className="text-gray-900">{agent.progress}</p>
                </div>
              )}
              {agent.blockers && (
                <div>
                  <p className="text-sm text-gray-600 mb-1">Blockers</p>
                  <p className="text-red-700 bg-red-50 p-3 rounded">{agent.blockers}</p>
                </div>
              )}
              <div>
                <p className="text-sm text-gray-600 mb-1">Last Updated</p>
                <p className="text-gray-900">{new Date(agent.last_updated).toLocaleString()}</p>
              </div>
            </div>
          </div>

          {/* Tool Usage */}
          <div className="bg-white rounded-lg shadow-md p-6">
            <h2 className="text-xl font-semibold text-gray-900 mb-4">Tool Usage</h2>
            {agent.toolUsage.length === 0 ? (
              <p className="text-gray-500">No tool usage data</p>
            ) : (
              <div className="space-y-3">
                {agent.toolUsage.map((tool) => (
                  <div key={tool.tool_name} className="border-b pb-3 last:border-0">
                    <div className="flex items-center justify-between mb-2">
                      <span className="font-medium text-gray-900">{tool.tool_name}</span>
                      <span className="text-sm text-gray-600">{tool.count} calls</span>
                    </div>
                    <div className="flex items-center space-x-4 text-xs text-gray-500">
                      <span>✅ {tool.success_count}</span>
                      <span>❌ {tool.error_count}</span>
                      <span>⏱️ {Math.round(tool.avg_duration_ms || 0)}ms avg</span>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* Recent Actions */}
          <div className="lg:col-span-2 bg-white rounded-lg shadow-md p-6">
            <h2 className="text-xl font-semibold text-gray-900 mb-4">Recent Actions</h2>
            {agent.recentActions.length === 0 ? (
              <p className="text-gray-500">No recent actions</p>
            ) : (
              <div className="space-y-2">
                {agent.recentActions.map((action) => (
                  <div
                    key={action.id}
                    className="flex items-center justify-between p-3 rounded-lg hover:bg-gray-50"
                  >
                    <div className="flex items-center space-x-3">
                      <span className="text-xl">
                        {action.action_type === 'mcp_tool' ? '🔧' : 
                         action.action_type.includes('memory') ? '🧠' : '⚡'}
                      </span>
                      <div>
                        <p className="text-sm font-medium text-gray-900">
                          {action.tool_name || action.action_type}
                        </p>
                        <p className="text-xs text-gray-500">
                          {new Date(action.timestamp).toLocaleString()}
                        </p>
                      </div>
                    </div>
                    <div className="flex items-center space-x-4 text-sm">
                      <span className={action.result_status === 'success' ? 'text-green-600' : 'text-red-600'}>
                        {action.result_status}
                      </span>
                      {action.duration_ms && (
                        <span className="text-gray-500">{action.duration_ms}ms</span>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

