import type {
  TraceSession,
  TraceSessionDetail,
  TraceStatsResponse,
  TraceListParams,
} from '../types/traces';

const FLEET_GATEWAY_URL =
  import.meta.env.VITE_FLEET_GATEWAY_URL ||
  'https://fleet-gateway.server.unarmedpuppy.com';

export const tracesAPI = {
  list: async (params?: TraceListParams): Promise<TraceSession[]> => {
    const searchParams = new URLSearchParams();
    if (params?.machine_id) searchParams.set('machine_id', params.machine_id);
    if (params?.agent_label) searchParams.set('agent_label', params.agent_label);
    if (params?.interactive !== undefined)
      searchParams.set('interactive', String(params.interactive));
    if (params?.from_time) searchParams.set('from_time', params.from_time);
    if (params?.to_time) searchParams.set('to_time', params.to_time);
    if (params?.limit) searchParams.set('limit', String(params.limit));
    if (params?.offset) searchParams.set('offset', String(params.offset));

    const url = `${FLEET_GATEWAY_URL}/traces${searchParams.toString() ? `?${searchParams}` : ''}`;
    const response = await fetch(url);
    if (!response.ok) throw new Error(`Failed to list sessions: ${response.statusText}`);
    return response.json();
  },

  get: async (sessionId: string): Promise<TraceSessionDetail> => {
    const response = await fetch(`${FLEET_GATEWAY_URL}/traces/${sessionId}`);
    if (!response.ok) throw new Error(`Failed to get session: ${response.statusText}`);
    return response.json();
  },

  stats: async (): Promise<TraceStatsResponse> => {
    const response = await fetch(`${FLEET_GATEWAY_URL}/traces/stats`);
    if (!response.ok) throw new Error(`Failed to get trace stats: ${response.statusText}`);
    return response.json();
  },
};
