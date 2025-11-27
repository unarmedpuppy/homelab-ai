/**
 * API client functions for analytics.
 */

import apiClient from './client'
import type {
  PerformanceMetrics,
  TickerPerformanceResponse,
  TypePerformanceResponse,
  PlaybookPerformanceResponse,
} from '../types/analytics'

export interface AnalyticsParams {
  date_from?: string // YYYY-MM-DD
  date_to?: string // YYYY-MM-DD
}

/**
 * Get comprehensive performance metrics.
 */
export async function getPerformanceMetrics(params?: AnalyticsParams): Promise<PerformanceMetrics> {
  const response = await apiClient.get<PerformanceMetrics>('/analytics/performance', { params })
  return response.data
}

/**
 * Get performance breakdown by ticker.
 */
export async function getPerformanceByTicker(params?: AnalyticsParams): Promise<TickerPerformanceResponse> {
  const response = await apiClient.get<TickerPerformanceResponse>('/analytics/by-ticker', { params })
  return response.data
}

/**
 * Get performance breakdown by trade type.
 */
export async function getPerformanceByType(params?: AnalyticsParams): Promise<TypePerformanceResponse> {
  const response = await apiClient.get<TypePerformanceResponse>('/analytics/by-type', { params })
  return response.data
}

/**
 * Get performance breakdown by playbook/strategy.
 */
export async function getPerformanceByPlaybook(params?: AnalyticsParams): Promise<PlaybookPerformanceResponse> {
  const response = await apiClient.get<PlaybookPerformanceResponse>('/analytics/by-playbook', { params })
  return response.data
}

