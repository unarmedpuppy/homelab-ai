/**
 * Agent Fleet types - for agent-gateway integration
 */

export type AgentType = 'server' | 'cli';
export type AgentStatus = 'online' | 'offline' | 'degraded' | 'unknown';

export interface AgentProfile {
  role: string | null;
  model: string | null;
  permissions: string | null;
}

export interface AgentHealth {
  status: AgentStatus;
  last_check: string | null;
  last_success: string | null;
  response_time_ms: number | null;
  consecutive_failures: number;
  error: string | null;
  version: string | null;
  profile: AgentProfile | null;
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

export interface AgentSkill {
  name: string;
  description: string;
}

export interface ScheduleJob {
  name: string;
  enabled: boolean;
  cron: string | null;
  interval_hours: number | null;
  action: string;
  prompt_preview: string | null;
  deliver_to: { channel: string; contact: string } | null;
  reply_to: string | null;
  next_run: string | null;
}

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
