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
    const response = await apiClient.get<Conversation[]>('/memory/search', {
      params: { query, limit },
    });
    return response.data;
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

export { apiClient };
