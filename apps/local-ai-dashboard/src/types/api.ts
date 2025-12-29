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
  started_date: string;
  days_active: number;
  most_active_day: string;
  most_active_day_count: number;
  activity_chart: ActivityDay[];
  top_models: Array<{ model: string; count: number; percentage: number; total_tokens: number }>;
  providers_used: Record<string, number>;
  total_sessions: number;
  total_messages: number;
  total_tokens: number;
  unique_projects: number;
  longest_streak: number;
  cost_savings: number | null;
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
