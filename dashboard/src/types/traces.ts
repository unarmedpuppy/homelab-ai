export interface TraceSession {
  session_id: string;
  machine_id: string;
  agent_label: string;
  interactive: boolean;
  model: string | null;
  cwd: string | null;
  start_time: string;
  end_time: string | null;
  span_count: number;
}

export interface TraceSpan {
  span_id: string;
  session_id: string;
  parent_span_id: string | null;
  tool_name: string;
  event_type: string;
  input_json: string | null;
  output_summary: string | null;
  status: 'in_progress' | 'completed' | 'failed';
  start_time: string;
  end_time: string | null;
  agent_id: string | null;
  agent_transcript_path: string | null;
}

export interface TraceSessionDetail extends TraceSession {
  spans: TraceSpan[];
}

export interface TraceMachineDay {
  machine_id: string;
  day: string;
  count: number;
}

export interface TraceStatsResponse {
  by_machine_day: TraceMachineDay[];
  active_sessions: number;
  sessions_today: number;
}

export interface TraceListParams {
  machine_id?: string;
  agent_label?: string;
  interactive?: boolean;
  from_time?: string;
  to_time?: string;
  limit?: number;
  offset?: number;
}
