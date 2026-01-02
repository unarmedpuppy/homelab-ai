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
  ImageRef,
  AgentRunRecord,
  AgentRunWithSteps,
  AgentRunsStats,
} from '../types/api';

// API base URL - defaults to public router endpoint
// For local dev: VITE_API_URL=http://localhost:8012
// For production: uses public HTTPS endpoint
const API_BASE_URL = import.meta.env.VITE_API_URL || 'https://homelab-ai-api.server.unarmedpuppy.com';

// TTS is proxied through nginx at /tts/ to the Gaming PC manager
// Configure TTS_API_URL in docker-compose environment

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

  updateConversation: async (id: string, update: { title?: string; metadata?: Record<string, unknown> }) => {
    const response = await apiClient.patch<Conversation>(`/memory/conversations/${id}`, update);
    return response.data;
  },

  deleteConversation: async (id: string) => {
    const response = await apiClient.delete<{ status: string; conversation_id: string }>(`/memory/conversations/${id}`);
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

    const response = await fetch('/api/v1/chat/completions', {
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

    return response.json() as Promise<ChatCompletionResponse>;
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
      'X-Enhanced-Streaming': 'true',  // Enable status events with conversation_id
      'X-Project': 'dashboard',
      'X-User-ID': 'dashboard-user',
    };

    if (conversationId) {
      headers['X-Conversation-ID'] = conversationId;
    }

    const requestBody: {
      model: string;
      messages: ChatMessage[];
      stream: boolean;
      temperature?: number;
      max_tokens?: number;
      top_p?: number;
      frequency_penalty?: number;
      presence_penalty?: number;
    } = {
      model,
      messages,
      stream: true,
    };

    if (temperature !== undefined) requestBody.temperature = temperature;
    if (max_tokens !== undefined) requestBody.max_tokens = max_tokens;
    if (top_p !== undefined) requestBody.top_p = top_p;
    if (frequency_penalty !== undefined) requestBody.frequency_penalty = frequency_penalty;
    if (presence_penalty !== undefined) requestBody.presence_penalty = presence_penalty;

    const response = await fetch('/api/v1/chat/completions', {
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
      const response = await fetch('/api/v1/chat/completions', {
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

// Image API
export const imageAPI = {
  upload: async (file: File, conversationId: string, messageId: string): Promise<ImageRef> => {
    const formData = new FormData();
    formData.append('file', file);

    const response = await fetch(
      `/api/v1/images/upload?conversation_id=${encodeURIComponent(conversationId)}&message_id=${encodeURIComponent(messageId)}`,
      {
        method: 'POST',
        body: formData,
      }
    );

    if (!response.ok) {
      const error = await response.json().catch(() => ({ detail: response.statusText }));
      throw new Error(error.detail || 'Failed to upload image');
    }

    return response.json();
  },

  getUrl: (imageRef: ImageRef): string => {
    const parts = imageRef.path.split('/');
    const conversationId = parts[parts.length - 3];
    const messageId = parts[parts.length - 2];
    const filename = parts[parts.length - 1];
    return `/api/v1/images/${conversationId}/${messageId}/${filename}`;
  },
};

export const agentRunsAPI = {
  list: async (params?: {
    status?: string;
    source?: string;
    limit?: number;
    offset?: number;
  }) => {
    const response = await apiClient.get<AgentRunRecord[]>('/agent/runs', { params });
    return response.data;
  },

  get: async (id: string) => {
    const response = await apiClient.get<AgentRunWithSteps>(`/agent/runs/${id}`);
    return response.data;
  },

  getStats: async () => {
    const response = await apiClient.get<AgentRunsStats>('/agent/runs/stats');
    return response.data;
  },
};

let ttsAvailableCache: boolean | null = null;

export class TTSError extends Error {
  code: string;
  userMessage: string;
  
  constructor(code: string, userMessage: string, technicalMessage?: string) {
    super(technicalMessage || userMessage);
    this.code = code;
    this.userMessage = userMessage;
    this.name = 'TTSError';
  }
}

export const ttsAPI = {
  checkAvailable: async (): Promise<boolean> => {
    if (ttsAvailableCache !== null) return ttsAvailableCache;
    try {
      const response = await fetch('/api/health');
      ttsAvailableCache = response.ok;
    } catch {
      ttsAvailableCache = false;
    }
    return ttsAvailableCache;
  },

  isAvailable: (): boolean => {
    return ttsAvailableCache === true;
  },

  resetCache: () => {
    ttsAvailableCache = null;
  },

  generateSpeech: async (text: string, voice: string = 'default'): Promise<Blob> => {
    const response = await fetch('/api/v1/audio/speech', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        model: 'chatterbox-turbo',
        input: text,
        voice,
        response_format: 'wav',
      }),
    });

    if (!response.ok) {
      const errorText = await response.text().catch(() => 'Unknown error');
      
      if (response.status === 401) {
        throw new TTSError('AUTH_ERROR', 'TTS authentication failed. Please check API key configuration.');
      } else if (response.status === 503) {
        throw new TTSError('SERVICE_UNAVAILABLE', 'TTS service is unavailable. Gaming PC may be offline or in gaming mode.');
      } else if (response.status === 504) {
        throw new TTSError('TIMEOUT', 'TTS generation timed out. Try a shorter text.');
      } else {
        throw new TTSError('GENERATION_FAILED', `TTS generation failed: ${errorText}`);
      }
    }

    return response.blob();
  },

  playAudio: (blob: Blob): Promise<void> => {
    return new Promise((resolve, reject) => {
      const url = URL.createObjectURL(blob);
      const audio = new Audio(url);
      
      audio.onended = () => {
        URL.revokeObjectURL(url);
        resolve();
      };
      
      audio.onerror = (e) => {
        URL.revokeObjectURL(url);
        reject(new TTSError('PLAYBACK_FAILED', 'Audio playback failed. Check browser audio settings.', String(e)));
      };
      
      audio.play().catch((e) => {
        URL.revokeObjectURL(url);
        reject(new TTSError('PLAYBACK_BLOCKED', 'Audio playback was blocked. Click to enable audio.', String(e)));
      });
    });
  },
};

export { apiClient };
