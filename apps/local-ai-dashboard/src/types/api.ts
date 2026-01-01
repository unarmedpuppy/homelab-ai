// TypeScript types matching the API responses

export interface Message {
  id: string;
  conversation_id: string;
  role: 'user' | 'assistant' | 'system';
  content: string;
  model_used?: string;
  model_requested?: string;
  backend?: string;
  provider_name?: string;
  tokens_prompt?: number;
  tokens_completion?: number;
  timestamp: string;
  metadata?: {
    model_requested?: string;
    provider_name?: string;
    [key: string]: unknown;
  };
}

export interface Conversation {
  id: string;
  session_id?: string;
  user_id?: string;
  project?: string;
  username?: string;
  source?: string;
  display_name?: string;
  title?: string;
  created_at: string;
  updated_at: string;
  message_count?: number;
  total_tokens?: number;
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
  conversation: {
    id: string;
    created_at: string;
    message_count: number;
  };
  messages: Array<{
    role: string;
    content: string;
    timestamp: string;
  }>;
  relevance_score: number;
}

// API returns array directly, not wrapped in object
export type RAGSearchResponse = RAGResult[];

// Image Types
export interface ImageRef {
  filename: string;
  path: string;
  size: number;
  mimeType: string;
  width: number;
  height: number;
}

// Chat Completion Types (OpenAI-compatible)
export interface ChatMessage {
  role: 'user' | 'assistant' | 'system';
  content: string;
  image_refs?: ImageRef[];
}

// Stream Event Types for SSE streaming with status
export interface StreamEvent {
  status: 'routing' | 'loading' | 'generating' | 'streaming' | 'done' | 'error';
  message?: string;
  content?: string;
  model?: string;
  backend?: string;
  provider_name?: string;
  timestamp: number;
  estimated_time?: number;
  delta?: string;
  finish_reason?: string;
  usage?: {
    prompt_tokens: number;
    completion_tokens: number;
    total_tokens: number;
  };
  error_detail?: string;
  conversation_id?: string;
}

export interface ChatCompletionRequest {
  model: string;
  messages: ChatMessage[];
  temperature?: number;
  max_tokens?: number;
  top_p?: number;
  frequency_penalty?: number;
  presence_penalty?: number;
}

export interface ChatCompletionResponse {
  id: string;
  object: string;
  created: number;
  model: string;
  choices: Array<{
    index: number;
    message: ChatMessage;
    finish_reason: string;
  }>;
  usage?: {
    prompt_tokens: number;
    completion_tokens: number;
    total_tokens: number;
  };
}

// Provider Types
export interface Provider {
  id: string;
  name: string;
  type: 'local' | 'cloud';
  status: 'online' | 'offline';
  priority: number;
  gpu?: string | null;
  location?: string | null;
  lastHealthCheck?: string | null;
}

export interface ProvidersResponse {
  providers: Provider[];
}

export interface ProviderModel {
  id: string;
  name: string;
  context_window?: number;
  max_tokens?: number;
  is_default?: boolean;
  capabilities: {
    vision?: boolean;
    function_calling?: boolean;
    streaming?: boolean;
    json_mode?: boolean;
  };
  tags?: string[];
}

export interface ProviderHealth {
  is_healthy: boolean;
  response_time_ms?: number;
  checked_at?: string;
  error?: string;
  consecutive_failures: number;
}

export interface ProviderLoad {
  current_requests: number;
  max_concurrent: number;
  utilization: number;
}

export interface ProviderConfig {
  health_check_interval: number;
  health_check_timeout: number;
  health_check_path: string;
  max_retries: number;
  circuit_breaker_threshold: number;
}

export interface AdminProvider {
  id: string;
  name: string;
  type: 'local' | 'cloud';
  description?: string;
  endpoint: string;
  priority: number;
  enabled: boolean;
  health: ProviderHealth;
  load: ProviderLoad;
  models: ProviderModel[];
  config: ProviderConfig;
  metadata?: Record<string, any>;
}

export interface AdminProvidersResponse {
  providers: AdminProvider[];
  total_providers: number;
  healthy_providers: number;
}

export interface AgentRunRecord {
  id: string;
  task: string;
  working_directory: string | null;
  model_requested: string | null;
  model_used: string | null;
  backend: string | null;
  backend_name: string | null;
  status: 'running' | 'completed' | 'failed' | 'max_steps' | 'cancelled';
  final_answer: string | null;
  total_steps: number;
  started_at: string;
  completed_at: string | null;
  duration_ms: number | null;
  source: string | null;
  triggered_by: string | null;
  error: string | null;
}

export interface AgentStepRecord {
  id: number;
  agent_run_id: string;
  step_number: number;
  action_type: string;
  tool_name: string | null;
  tool_args: Record<string, unknown> | null;
  tool_result: string | null;
  thinking: string | null;
  error: string | null;
  started_at: string;
  duration_ms: number | null;
}

export interface AgentRunWithSteps extends AgentRunRecord {
  steps: AgentStepRecord[];
}

export interface AgentRunsStats {
  total_runs: number;
  completed_runs: number;
  failed_runs: number;
  running_runs: number;
  avg_duration_ms: number;
  most_used_model: string;
  runs_by_status: Record<string, number>;
  runs_by_source: Record<string, number>;
}
