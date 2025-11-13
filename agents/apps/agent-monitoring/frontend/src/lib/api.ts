/**
 * API client for backend integration
 */

import { Agent, AgentDetails, Action, SystemStats, ToolUsage, Task } from '@/types';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:3001';

class ApiClient {
  private baseUrl: string;

  constructor(baseUrl?: string) {
    this.baseUrl = baseUrl || API_BASE_URL;
  }

  private async fetch<T>(endpoint: string, options?: RequestInit): Promise<T> {
    const url = `${this.baseUrl}${endpoint}`;
    const response = await fetch(url, {
      ...options,
      headers: {
        'Content-Type': 'application/json',
        ...options?.headers,
      },
    });

    if (!response.ok) {
      throw new Error(`API error: ${response.statusText}`);
    }

    return response.json();
  }

  // Agents
  async getAgents(status?: string): Promise<{ status: string; count: number; agents: Agent[] }> {
    const query = status ? `?status=${status}` : '';
    return this.fetch(`/api/agents${query}`);
  }

  async getAgent(agentId: string): Promise<{ status: string; agent: AgentDetails }> {
    return this.fetch(`/api/agents/${agentId}`);
  }

  // Actions
  async getActions(params?: {
    limit?: number;
    offset?: number;
    agentId?: string;
    actionType?: string;
    toolName?: string;
    startTime?: string;
    endTime?: string;
  }): Promise<{ status: string; count: number; actions: Action[] }> {
    const queryParams = new URLSearchParams();
    if (params) {
      Object.entries(params).forEach(([key, value]) => {
        if (value !== undefined) {
          queryParams.append(key, String(value));
        }
      });
    }
    const query = queryParams.toString() ? `?${queryParams.toString()}` : '';
    return this.fetch(`/api/actions${query}`);
  }

  async getRecentActions(): Promise<{ status: string; count: number; actions: Action[] }> {
    return this.fetch('/api/actions/recent');
  }

  // Statistics
  async getStats(): Promise<{ status: string; stats: SystemStats }> {
    return this.fetch('/api/stats');
  }

  async getToolUsage(agentId?: string, limit?: number): Promise<{ status: string; count: number; toolUsage: ToolUsage[] }> {
    const queryParams = new URLSearchParams();
    if (agentId) queryParams.append('agentId', agentId);
    if (limit) queryParams.append('limit', String(limit));
    const query = queryParams.toString() ? `?${queryParams.toString()}` : '';
    return this.fetch(`/api/stats/tool-usage${query}`);
  }

  // Tasks
  async getTasks(): Promise<{ status: string; count: number; tasks: Task[]; stats: any }> {
    return this.fetch('/api/tasks');
  }

  // Health
  async getHealth(): Promise<{ status: string; service: string; timestamp: string }> {
    return this.fetch('/health');
  }
}

export const api = new ApiClient();

