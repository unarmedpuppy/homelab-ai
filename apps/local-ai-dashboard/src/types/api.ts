// TypeScript types matching the API responses

export interface Message {
  id: string;
  conversation_id: string;
  role: 'user' | 'assistant' | 'system';
  content: string;
  model_used?: string;
  backend?: string;
  tokens_prompt?: number;
  tokens_completion?: number;
  created_at: string;
}

export interface Conversation {
  id: string;
  session_id?: string;
  user_id?: string;
  project?: string;
  created_at: string;
  updated_at: string;
  message_count?: number;
  messages?: Message[];
}

export interface Metric {
  id: string;
  conversation_id?: string;
  session_id?: string;
  endpoint: string;
  model_requested: string;
  model_used?: string;
  backend?: string;
  prompt_tokens?: number;
  completion_tokens?: number;
  total_tokens?: number;
  duration_ms: number;
  success: boolean;
  error?: string;
  streaming: boolean;
  tool_calls_count?: number;
  user_id?: string;
  project?: string;
  created_at: string;
}

export interface DailyMetric {
  date: string;
  request_count: number;
  total_tokens: number;
  avg_duration_ms: number;
  success_rate: number;
}

export interface ActivityDay {
  date: string;
  count: number;
}

export interface ModelUsage {
  model: string;
  count: number;
}

export interface DashboardStats {
  total_conversations: number;
  total_messages: number;
  total_requests: number;
  total_tokens: number;
  avg_tokens_per_request: number;
  success_rate: number;
  avg_duration_ms: number;
  top_models: Array<{ model: string; count: number }>;
  top_backends: Array<{ backend: string; count: number }>;
  activity_by_day: ActivityDay[];
  daily_metrics: DailyMetric[];
}

export interface MemoryStats {
  total_conversations: number;
  total_messages: number;
  avg_messages_per_conversation: number;
  unique_users: number;
  unique_sessions: number;
}

export interface RAGResult {
  conversation_id: string;
  conversation_created_at: string;
  message_count: number;
  similarity_score: number;
  sample_messages: Array<{
    role: string;
    content: string;
    created_at: string;
  }>;
}

export interface RAGSearchResponse {
  query: string;
  results: RAGResult[];
  count: number;
}
