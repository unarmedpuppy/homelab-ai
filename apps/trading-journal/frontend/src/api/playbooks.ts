/**
 * API client functions for playbooks.
 */

import apiClient from './client'
import type {
  PlaybookResponse,
  PlaybookCreate,
  PlaybookUpdate,
  PlaybookListResponse,
  PlaybookPerformance,
  PlaybookTemplateResponse,
  PlaybookTemplateCreate,
} from '../types/playbook'
import type { TradeResponse } from '../types/trade'

export interface PlaybookListParams {
  search?: string
  is_active?: boolean
  is_shared?: boolean
  skip?: number
  limit?: number
}

export interface PlaybookTradesParams {
  date_from?: string // YYYY-MM-DD
  date_to?: string // YYYY-MM-DD
}

/**
 * Get list of playbooks with optional filters.
 */
export async function getPlaybooks(params?: PlaybookListParams): Promise<PlaybookListResponse> {
  const response = await apiClient.get<PlaybookListResponse>('/api/playbooks', { params })
  return response.data
}

/**
 * Get a single playbook by ID.
 */
export async function getPlaybook(id: number): Promise<PlaybookResponse> {
  const response = await apiClient.get<PlaybookResponse>(`/api/playbooks/${id}`)
  return response.data
}

/**
 * Create a new playbook.
 */
export async function createPlaybook(data: PlaybookCreate): Promise<PlaybookResponse> {
  const response = await apiClient.post<PlaybookResponse>('/api/playbooks', data)
  return response.data
}

/**
 * Update a playbook.
 */
export async function updatePlaybook(id: number, data: PlaybookUpdate): Promise<PlaybookResponse> {
  const response = await apiClient.put<PlaybookResponse>(`/api/playbooks/${id}`, data)
  return response.data
}

/**
 * Delete a playbook.
 */
export async function deletePlaybook(id: number): Promise<void> {
  await apiClient.delete(`/api/playbooks/${id}`)
}

/**
 * Get all trades for a playbook.
 */
export async function getPlaybookTrades(
  id: number,
  params?: PlaybookTradesParams
): Promise<TradeResponse[]> {
  const response = await apiClient.get<TradeResponse[]>(`/api/playbooks/${id}/trades`, { params })
  return response.data
}

/**
 * Get performance metrics for a playbook.
 */
export async function getPlaybookPerformance(
  id: number,
  params?: PlaybookTradesParams
): Promise<PlaybookPerformance> {
  const response = await apiClient.get<PlaybookPerformance>(`/api/playbooks/${id}/performance`, {
    params,
  })
  return response.data
}

/**
 * Get all playbook templates.
 */
export async function getPlaybookTemplates(): Promise<PlaybookTemplateResponse[]> {
  const response = await apiClient.get<PlaybookTemplateResponse[]>('/api/playbooks/templates')
  return response.data
}

/**
 * Create a new playbook template.
 */
export async function createPlaybookTemplate(
  data: PlaybookTemplateCreate
): Promise<PlaybookTemplateResponse> {
  const response = await apiClient.post<PlaybookTemplateResponse>('/api/playbooks/templates', data)
  return response.data
}

