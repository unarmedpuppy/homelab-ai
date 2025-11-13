'use client';

import { Action } from '@/types';
import { useEffect, useState } from 'react';

interface ActivityFeedProps {
  initialActions?: Action[];
  autoRefresh?: boolean;
  refreshInterval?: number;
}

export default function ActivityFeed({ 
  initialActions = [], 
  autoRefresh = true,
  refreshInterval = 5000 
}: ActivityFeedProps) {
  const [actions, setActions] = useState<Action[]>(initialActions);
  const [loading, setLoading] = useState(false);

  const fetchActions = async () => {
    setLoading(true);
    try {
      const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:3001';
      const response = await fetch(`${apiUrl}/api/actions/recent`, {
        cache: 'no-store', // Always fetch fresh data
      });
      const data = await response.json();
      if (data.status === 'success') {
        setActions(data.actions);
      }
    } catch (error) {
      console.error('Failed to fetch actions:', error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (autoRefresh) {
      fetchActions();
      const interval = setInterval(fetchActions, refreshInterval);
      return () => clearInterval(interval);
    }
  }, [autoRefresh, refreshInterval]);

  const getActionIcon = (actionType: string) => {
    switch (actionType) {
      case 'mcp_tool':
        return '🔧';
      case 'memory_query':
      case 'memory_record':
        return '🧠';
      case 'task_update':
        return '📋';
      case 'status_update':
        return '📊';
      default:
        return '⚡';
    }
  };

  const getStatusColor = (status: string) => {
    return status === 'success' ? 'text-green-600' : 'text-red-600';
  };

  return (
    <div className="bg-white rounded-lg shadow-md p-6">
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-xl font-semibold text-gray-900">Recent Activity</h2>
        {loading && <span className="text-sm text-gray-500">Refreshing...</span>}
      </div>

      <div className="space-y-3 max-h-96 overflow-y-auto">
        {actions.length === 0 ? (
          <p className="text-gray-500 text-center py-8">No recent activity</p>
        ) : (
          actions.map((action) => (
            <div
              key={action.id}
              className="flex items-start space-x-3 p-3 rounded-lg hover:bg-gray-50 transition-colors"
            >
              <span className="text-2xl">{getActionIcon(action.action_type)}</span>
              <div className="flex-1 min-w-0">
                <div className="flex items-center justify-between">
                  <span className="text-sm font-medium text-gray-900">
                    {action.agent_id}
                  </span>
                  <span className={`text-xs font-medium ${getStatusColor(action.result_status)}`}>
                    {action.result_status}
                  </span>
                </div>
                <p className="text-sm text-gray-600">
                  {action.tool_name || action.action_type}
                </p>
                {action.duration_ms && (
                  <p className="text-xs text-gray-500 mt-1">
                    {action.duration_ms}ms
                  </p>
                )}
                <p className="text-xs text-gray-400 mt-1">
                  {new Date(action.timestamp).toLocaleString()}
                </p>
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  );
}

