'use client';

import { Agent } from '@/types';
import Link from 'next/link';

interface AgentCardProps {
  agent: Agent;
}

const statusColors = {
  active: 'bg-green-100 text-green-800 border-green-300',
  idle: 'bg-gray-100 text-gray-800 border-gray-300',
  blocked: 'bg-red-100 text-red-800 border-red-300',
  completed: 'bg-blue-100 text-blue-800 border-blue-300',
};

export default function AgentCard({ agent }: AgentCardProps) {
  const statusColor = statusColors[agent.status] || statusColors.idle;

  return (
    <Link href={`/agents/${agent.agent_id}`}>
      <div className="bg-white rounded-lg shadow-md p-6 hover:shadow-lg transition-shadow cursor-pointer border-l-4 border-l-blue-500">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-lg font-semibold text-gray-900">{agent.agent_id}</h3>
          <span className={`px-3 py-1 rounded-full text-xs font-medium border ${statusColor}`}>
            {agent.status}
          </span>
        </div>

        {agent.current_task_id && (
          <div className="mb-2">
            <span className="text-sm text-gray-500">Task:</span>
            <span className="text-sm font-medium text-gray-900 ml-2">{agent.current_task_id}</span>
          </div>
        )}

        {agent.progress && (
          <p className="text-sm text-gray-600 mb-2 line-clamp-2">{agent.progress}</p>
        )}

        {agent.blockers && (
          <div className="mt-2 p-2 bg-red-50 rounded text-sm text-red-700">
            <span className="font-medium">Blocked:</span> {agent.blockers}
          </div>
        )}

        <div className="mt-4 text-xs text-gray-500">
          Updated: {new Date(agent.last_updated).toLocaleString()}
        </div>
      </div>
    </Link>
  );
}

