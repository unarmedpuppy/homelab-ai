import axios from 'axios';
import type {
  Conversation,
  Metric,
  DashboardStats,
  MemoryStats,
  RAGSearchResponse,
  DailyMetric,
  ActivityDay,
  ModelUsage,
  ChatMessage,
  ChatCompletionResponse,
  ProvidersResponse,
  AdminProvidersResponse,
  StreamEvent,
} from '../types/api';

// API base URL - defaults to public router endpoint
// For local dev: VITE_API_URL=http://localhost:8012
// For production: uses public HTTPS endpoint
const API_BASE_URL = import.meta.env.VITE_API_URL || 'https://local-ai-api.server.unarmedpuppy.com';

const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Memory API
export const memoryAPI = {
  listConversations: async (params?: {
    user_id?: string;
    session_id?: string;
    project?: string;
    limit?: number;
    offset?: number;
  }) => {
    const response = await apiClient.get<Conversation[]>('/memory/conversations', { params });
    return response.data;
  },

  getConversation: async (id: string) => {
    const response = await apiClient.get<Conversation>(`/memory/conversations/${id}`);
    return response.data;
  },

  searchConversations: async (query: string, limit: number = 10) => {
    const response = await apiClient.post<RAGSearchResponse>('/memory/search', {
      q: query,
      limit,
    });
    // Convert search results to Conversation[] for compatibility
    return response.data.map(r => r.conversation);
  },

  getStats: async () => {
    const response = await apiClient.get<MemoryStats>('/memory/stats');
    return response.data;
  },
};

// Metrics API
export const metricsAPI = {
  getRecent: async (params?: {
    limit?: number;
    model?: string;
    backend?: string;
    success?: boolean;
  }) => {
    const response = await apiClient.get<Metric[]>('/metrics/recent', { params });
    return response.data;
  },

  getDaily: async (days: number = 30) => {
    const response = await apiClient.get<DailyMetric[]>('/metrics/daily', {
      params: { days },
    });
    return response.data;
  },

  getActivity: async (days: number = 90) => {
    const response = await apiClient.get<ActivityDay[]>('/metrics/activity', {
      params: { days },
    });
    return response.data;
  },

  getModels: async () => {
    const response = await apiClient.get<ModelUsage[]>('/metrics/models');
    return response.data;
  },

  getDashboard: async () => {
    const response = await apiClient.get<DashboardStats>('/metrics/dashboard');
    return response.data;
  },
};

// RAG API (text search)
export const ragAPI = {
  search: async (params: {
    query: string;
    limit?: number;
    similarity_threshold?: number;
    user_id?: string;
    project?: string;
  }) => {
    // Map 'query' to 'q' for API compatibility
    const { query, ...rest } = params;
    const response = await apiClient.post<RAGSearchResponse>('/memory/search', {
      q: query,
      ...rest,
    });
    return response.data;
  },

  getContext: async (params: {
    query: string;
    limit?: number;
    user_id?: string;
    project?: string;
  }) => {
    const { query, ...rest } = params;
    const response = await apiClient.post<{ query: string; context: string }>('/memory/context', {
      q: query,
      ...rest,
    });
    return response.data;
  },
};

// Chat API
export const chatAPI = {
  sendMessage: async (params: {
    model: string;
    messages: ChatMessage[];
    conversationId?: string;
    temperature?: number;
    max_tokens?: number;
    top_p?: number;
    frequency_penalty?: number;
    presence_penalty?: number;
  }) => {
    const { conversationId, messages, model, temperature, max_tokens, top_p, frequency_penalty, presence_penalty } = params;

    const headers: Record<string, string> = {
      'X-Enable-Memory': 'true',
      'X-Project': 'dashboard',
      'X-User-ID': 'dashboard-user',
    };

    if (conversationId) {
      headers['X-Conversation-ID'] = conversationId;
    }

    const requestBody: Record<string, unknown> = {
      model,
      messages,
    };

    if (temperature !== undefined) requestBody.temperature = temperature;
    if (max_tokens !== undefined) requestBody.max_tokens = max_tokens;
    if (top_p !== undefined) requestBody.top_p = top_p;
    if (frequency_penalty !== undefined) requestBody.frequency_penalty = frequency_penalty;
    if (presence_penalty !== undefined) requestBody.presence_penalty = presence_penalty;

    const response = await apiClient.post<ChatCompletionResponse>(
      '/v1/chat/completions',
      requestBody,
      { headers }
    );

    return response.data;
  },

  sendMessageStream: async function* (params: {
    model: string;
    messages: ChatMessage[];
    conversationId?: string;
    temperature?: number;
    max_tokens?: number;
    top_p?: number;
    frequency_penalty?: number;
    presence_penalty?: number;
  }): AsyncGenerator<StreamEvent, void, unknown> {
    const { conversationId, messages, model, temperature, max_tokens, top_p, frequency_penalty, presence_penalty } = params;

    const headers: Record<string, string> = {
      'X-Enable-Memory': 'true',
      'X-Project': 'dashboard',
      'X-User-ID': 'dashboard-user',
    };

    if (conversationId) {
      headers['X-Conversation-ID'] = conversationId;
    }

    const requestBody = {
      model,
      messages,
      stream: true,
    };

    if (temperature !== undefined) requestBody.temperature = temperature;
    if (max_tokens !== undefined) requestBody.max_tokens = max_tokens;
    if (top_p !== undefined) requestBody.top_p = top_p;
    if (frequency_penalty !== undefined) requestBody.frequency_penalty = frequency_penalty;
    if (presence_penalty !== undefined) requestBody.presence_penalty = presence_penalty;

    const response = await fetch(`${API_BASE_URL}/v1/chat/completions`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        ...headers,
      },
      body: JSON.stringify(requestBody),
    });

    if (!response.ok) {
      throw new Error(`HTTP ${response.status}: ${response.statusText}`);
    }

    const reader = response.body!.getReader();
    const decoder = new TextDecoder();
    let buffer = '';

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;

      buffer += decoder.decode(value, { stream: true });
      const lines = buffer.split('\n');
      buffer = lines.pop() || '';

      for (const line of lines) {
        if (line.startsWith('data: ')) {
          const data = line.slice(6);
          if (data === '[DONE]') return;

          try {
            const event = JSON.parse(data) as StreamEvent;
            yield event;
          } catch (e) {
            console.error('Failed to parse SSE event:', data);
          }
        }
      }
    }
  },

  sendMessageStreaming: async (params: {
    model: string;
    messages: ChatMessage[];
    conversationId?: string;
    temperature?: number;
    max_tokens?: number;
    top_p?: number;
    frequency_penalty?: number;
    presence_penalty?: number;
    onToken: (token: string) => void;
    onComplete: (response: ChatCompletionResponse) => void;
    onError: (error: Error) => void;
  }) => {
    const {
      conversationId,
      messages,
      model,
      temperature,
      max_tokens,
      top_p,
      frequency_penalty,
      presence_penalty,
      onToken,
      onComplete,
      onError,
    } = params;

    const headers: Record<string, string> = {
      'Content-Type': 'application/json',
      'X-Enable-Memory': 'true',
      'X-Project': 'dashboard',
      'X-User-ID': 'dashboard-user',
    };

    if (conversationId) {
      headers['X-Conversation-ID'] = conversationId;
    }

    const requestBody: Record<string, unknown> = {
      model,
      messages,
      stream: true, // Enable streaming
    };

    if (temperature !== undefined) requestBody.temperature = temperature;
    if (max_tokens !== undefined) requestBody.max_tokens = max_tokens;
    if (top_p !== undefined) requestBody.top_p = top_p;
    if (frequency_penalty !== undefined) requestBody.frequency_penalty = frequency_penalty;
    if (presence_penalty !== undefined) requestBody.presence_penalty = presence_penalty;

    try {
      const response = await fetch(`${API_BASE_URL}/v1/chat/completions`, {
        method: 'POST',
        headers,
        body: JSON.stringify(requestBody),
      });

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }

      if (!response.body) {
        throw new Error('Response body is null');
      }

      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let buffer = '';
      let fullContent = '';
      let metadata: any = {};

      while (true) {
        const { done, value } = await reader.read();

        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split('\n');
        buffer = lines.pop() || ''; // Keep incomplete line in buffer

        for (const line of lines) {
          if (!line.trim() || line.startsWith(':')) continue; // Skip empty lines and comments

          if (line.startsWith('data: ')) {
            const data = line.slice(6); // Remove 'data: ' prefix

            if (data === '[DONE]') {
              // Stream complete - construct final response
              onComplete({
                id: metadata.id || 'unknown',
                object: 'chat.completion',
                created: metadata.created || Math.floor(Date.now() / 1000),
                model: metadata.model || model,
                choices: [
                  {
                    index: 0,
                    message: {
                      role: 'assistant',
                      content: fullContent,
                    },
                    finish_reason: metadata.finish_reason || 'stop',
                  },
                ],
                usage: metadata.usage,
                provider: metadata.provider,
              } as ChatCompletionResponse);
              return;
            }

            try {
              const parsed = JSON.parse(data);

              // Store metadata from first chunk
              if (parsed.id) metadata.id = parsed.id;
              if (parsed.model) metadata.model = parsed.model;
              if (parsed.created) metadata.created = parsed.created;
              if (parsed.provider) metadata.provider = parsed.provider;
              if (parsed.usage) metadata.usage = parsed.usage;

              // Extract token from delta
              if (parsed.choices?.[0]?.delta?.content) {
                const token = parsed.choices[0].delta.content;
                fullContent += token;
                onToken(token);
              }

              // Store finish reason
              if (parsed.choices?.[0]?.finish_reason) {
                metadata.finish_reason = parsed.choices[0].finish_reason;
              }
            } catch (e) {
              console.error('Failed to parse SSE data:', data, e);
            }
          }
        }
      }
    } catch (error) {
      onError(error instanceof Error ? error : new Error(String(error)));
    }
  },
};

// Providers API
export const providersAPI = {
  list: async () => {
    const response = await apiClient.get<ProvidersResponse>('/providers');
    return response.data;
  },

  listAdmin: async () => {
    const response = await apiClient.get<AdminProvidersResponse>('/admin/providers');
    return response.data;
  },
};

export { apiClient };
