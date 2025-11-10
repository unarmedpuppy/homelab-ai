/**
 * Trade API endpoints.
 */

import apiClient from './client'
import { TradeResponse, TradeCreate, TradeUpdate, TradeListResponse } from '../types/trade'

export interface TradeFilters {
  skip?: number
  limit?: number
  date_from?: string
  date_to?: string
  ticker?: string
  trade_type?: string
  status?: string
  side?: string
}

export interface TradeSearchParams {
  q: string
  tags?: string
  skip?: number
  limit?: number
}

/**
 * Get paginated list of trades with optional filters.
 */
export const getTrades = async (filters: TradeFilters = {}): Promise<TradeListResponse> => {
  const response = await apiClient.get<TradeListResponse>('/trades', { params: filters })
  return response.data
}

/**
 * Get a single trade by ID.
 */
export const getTrade = async (id: number): Promise<TradeResponse> => {
  const response = await apiClient.get<TradeResponse>(`/trades/${id}`)
  return response.data
}

/**
 * Create a new trade.
 */
export const createTrade = async (trade: TradeCreate): Promise<TradeResponse> => {
  const response = await apiClient.post<TradeResponse>('/trades', trade)
  return response.data
}

/**
 * Update a trade (full update).
 */
export const updateTrade = async (id: number, trade: TradeUpdate): Promise<TradeResponse> => {
  const response = await apiClient.put<TradeResponse>(`/trades/${id}`, trade)
  return response.data
}

/**
 * Partially update a trade.
 */
export const patchTrade = async (id: number, trade: Partial<TradeUpdate>): Promise<TradeResponse> => {
  const response = await apiClient.patch<TradeResponse>(`/trades/${id}`, trade)
  return response.data
}

/**
 * Delete a trade.
 */
export const deleteTrade = async (id: number): Promise<void> => {
  await apiClient.delete(`/trades/${id}`)
}

/**
 * Bulk create trades.
 */
export const bulkCreateTrades = async (trades: TradeCreate[]): Promise<TradeResponse[]> => {
  const response = await apiClient.post<TradeResponse[]>('/trades/bulk', trades)
  return response.data
}

/**
 * Search trades by query string and optional tags.
 */
export const searchTrades = async (params: TradeSearchParams): Promise<TradeListResponse> => {
  const response = await apiClient.get<TradeListResponse>('/trades/search', { params })
  return response.data
}

