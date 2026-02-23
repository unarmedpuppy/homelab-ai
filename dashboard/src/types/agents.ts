/**
 * Agent Fleet types - for agent-gateway integration
 */

export type AgentType = 'server' | 'cli';
export type AgentStatus = 'online' | 'offline' | 'degraded' | 'unknown';

export interface AgentHealth {
  status: AgentStatus;
  last_check: string | null;
  last_success: string | null;
  response_time_ms: number | null;
  consecutive_failures: number;
  error: string | null;
  version: string | null;
}

export interface Agent {
  id: string;
  name: string;
  description: string;
  endpoint: string;
  agent_type: AgentType;
  expected_online: boolean;
  tags: string[];
  health: AgentHealth;
}

export type AgentDetails = Agent;

export interface FleetStats {
  total_agents: number;
  online_count: number;
  offline_count: number;
  degraded_count: number;
  unknown_count: number;
  expected_online_count: number;
  unexpected_offline_count: number;
  avg_response_time_ms: number | null;
  last_updated: string;
}
