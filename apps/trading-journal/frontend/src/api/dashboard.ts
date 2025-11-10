/**
 * Dashboard API endpoints.
 */

import apiClient from './client'
import {
  DashboardStats,
  CumulativePnLPoint,
  DailyPnLPoint,
  DrawdownData,
  RecentTrade,
} from '../types/dashboard'

export interface DashboardFilters {
  date_from?: string // YYYY-MM-DD
  date_to?: string // YYYY-MM-DD
}

/**
 * Get comprehensive dashboard statistics.
 */
export const getDashboardStats = async (
  filters: DashboardFilters = {}
): Promise<DashboardStats> => {
  const response = await apiClient.get<DashboardStats>('/dashboard/stats', {
    params: filters,
  })
  return response.data
}

/**
 * Get cumulative P&L data points for charting.
 */
export const getCumulativePnL = async (
  filters: DashboardFilters & { group_by?: 'day' | 'week' | 'month' } = {}
): Promise<CumulativePnLPoint[]> => {
  const response = await apiClient.get<CumulativePnLPoint[]>('/dashboard/cumulative-pnl', {
    params: filters,
  })
  return response.data
}

/**
 * Get daily P&L data points for charting.
 */
export const getDailyPnL = async (
  filters: DashboardFilters = {}
): Promise<DailyPnLPoint[]> => {
  const response = await apiClient.get<DailyPnLPoint[]>('/dashboard/daily-pnl', {
    params: filters,
  })
  return response.data
}

/**
 * Get drawdown data for charting.
 */
export const getDrawdownData = async (
  filters: DashboardFilters = {}
): Promise<DrawdownData[]> => {
  const response = await apiClient.get<DrawdownData[]>('/dashboard/drawdown', {
    params: filters,
  })
  return response.data
}

/**
 * Get recent closed trades for dashboard display.
 */
export const getRecentTrades = async (limit: number = 10): Promise<RecentTrade[]> => {
  const response = await apiClient.get<RecentTrade[]>('/dashboard/recent-trades', {
    params: { limit },
  })
  return response.data
}

