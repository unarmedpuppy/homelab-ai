import axios from 'axios';
import type { Run, RunListResponse, Post, PostListResponse, Stats } from '../types/api';

const API_BASE_URL = import.meta.env.VITE_API_URL || '/api';

const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

export const runsAPI = {
  list: async (params?: { limit?: number; offset?: number }) => {
    const response = await apiClient.get<RunListResponse>('/runs', { params });
    return response.data;
  },

  get: async (id: string) => {
    const response = await apiClient.get<Run>(`/runs/${id}`);
    return response.data;
  },
};

export const postsAPI = {
  list: async (params?: {
    page?: number;
    page_size?: number;
    run_id?: string;
    source?: string;
    author?: string;
    search?: string;
  }) => {
    const response = await apiClient.get<PostListResponse>('/posts', { params });
    return response.data;
  },

  get: async (id: string) => {
    const response = await apiClient.get<Post>(`/posts/${id}`);
    return response.data;
  },

  bookmarks: async (params?: {
    page?: number;
    page_size?: number;
    author?: string;
    search?: string;
  }) => {
    const response = await apiClient.get<PostListResponse>('/posts/bookmarks', { params });
    return response.data;
  },

  likes: async (params?: {
    page?: number;
    page_size?: number;
    author?: string;
    search?: string;
  }) => {
    const response = await apiClient.get<PostListResponse>('/posts/likes', { params });
    return response.data;
  },
};

export const statsAPI = {
  get: async () => {
    const response = await apiClient.get<Stats>('/stats');
    return response.data;
  },
};

export { apiClient };
