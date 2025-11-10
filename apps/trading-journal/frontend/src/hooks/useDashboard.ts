/**
 * React Query hooks for dashboard operations.
 */

import { useQuery } from '@tanstack/react-query'
import {
  getDashboardStats,
  getCumulativePnL,
  getDailyPnL,
  getDrawdownData,
  getRecentTrades,
  DashboardFilters,
} from '../api/dashboard'

// Query keys
export const dashboardKeys = {
  all: ['dashboard'] as const,
  stats: (filters: DashboardFilters = {}) => [...dashboardKeys.all, 'stats', filters] as const,
  cumulativePnL: (filters: DashboardFilters & { group_by?: string } = {}) =>
    [...dashboardKeys.all, 'cumulative-pnl', filters] as const,
  dailyPnL: (filters: DashboardFilters = {}) =>
    [...dashboardKeys.all, 'daily-pnl', filters] as const,
  drawdown: (filters: DashboardFilters = {}) =>
    [...dashboardKeys.all, 'drawdown', filters] as const,
  recentTrades: (limit: number = 10) =>
    [...dashboardKeys.all, 'recent-trades', limit] as const,
}

/**
 * Hook to fetch dashboard statistics.
 */
export function useDashboardStats(filters: DashboardFilters = {}) {
  return useQuery({
    queryKey: dashboardKeys.stats(filters),
    queryFn: () => getDashboardStats(filters),
  })
}

/**
 * Hook to fetch cumulative P&L data.
 */
export function useCumulativePnL(
  filters: DashboardFilters & { group_by?: 'day' | 'week' | 'month' } = {}
) {
  return useQuery({
    queryKey: dashboardKeys.cumulativePnL(filters),
    queryFn: () => getCumulativePnL(filters),
  })
}

/**
 * Hook to fetch daily P&L data.
 */
export function useDailyPnL(filters: DashboardFilters = {}) {
  return useQuery({
    queryKey: dashboardKeys.dailyPnL(filters),
    queryFn: () => getDailyPnL(filters),
  })
}

/**
 * Hook to fetch drawdown data.
 */
export function useDrawdownData(filters: DashboardFilters = {}) {
  return useQuery({
    queryKey: dashboardKeys.drawdown(filters),
    queryFn: () => getDrawdownData(filters),
  })
}

/**
 * Hook to fetch recent trades.
 */
export function useRecentTrades(limit: number = 10) {
  return useQuery({
    queryKey: dashboardKeys.recentTrades(limit),
    queryFn: () => getRecentTrades(limit),
  })
}

