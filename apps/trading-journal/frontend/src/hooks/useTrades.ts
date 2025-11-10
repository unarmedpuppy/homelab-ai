/**
 * React Query hooks for trade operations.
 */

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import {
  getTrades,
  getTrade,
  createTrade,
  updateTrade,
  patchTrade,
  deleteTrade,
  bulkCreateTrades,
  searchTrades,
  TradeFilters,
  TradeSearchParams,
} from '../api/trades'
import { TradeCreate, TradeUpdate, TradeResponse } from '../types/trade'

// Query keys
export const tradeKeys = {
  all: ['trades'] as const,
  lists: () => [...tradeKeys.all, 'list'] as const,
  list: (filters: TradeFilters) => [...tradeKeys.lists(), filters] as const,
  details: () => [...tradeKeys.all, 'detail'] as const,
  detail: (id: number) => [...tradeKeys.details(), id] as const,
  searches: () => [...tradeKeys.all, 'search'] as const,
  search: (params: TradeSearchParams) => [...tradeKeys.searches(), params] as const,
}

/**
 * Hook to fetch paginated list of trades with filters.
 */
export function useTrades(filters: TradeFilters = {}) {
  return useQuery({
    queryKey: tradeKeys.list(filters),
    queryFn: () => getTrades(filters),
  })
}

/**
 * Hook to fetch a single trade by ID.
 */
export function useTrade(id: number) {
  return useQuery({
    queryKey: tradeKeys.detail(id),
    queryFn: () => getTrade(id),
    enabled: !!id,
  })
}

/**
 * Hook to search trades.
 */
export function useSearchTrades(params: TradeSearchParams) {
  return useQuery({
    queryKey: tradeKeys.search(params),
    queryFn: () => searchTrades(params),
    enabled: !!params.q && params.q.length > 0,
  })
}

/**
 * Hook to create a new trade.
 */
export function useCreateTrade() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (trade: TradeCreate) => createTrade(trade),
    onSuccess: () => {
      // Invalidate trade lists to refetch
      queryClient.invalidateQueries({ queryKey: tradeKeys.lists() })
    },
  })
}

/**
 * Hook to update a trade (full update).
 */
export function useUpdateTrade() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: ({ id, trade }: { id: number; trade: TradeUpdate }) => updateTrade(id, trade),
    onSuccess: (data) => {
      // Invalidate specific trade and lists
      queryClient.invalidateQueries({ queryKey: tradeKeys.detail(data.id) })
      queryClient.invalidateQueries({ queryKey: tradeKeys.lists() })
    },
  })
}

/**
 * Hook to partially update a trade.
 */
export function usePatchTrade() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: ({ id, trade }: { id: number; trade: Partial<TradeUpdate> }) =>
      patchTrade(id, trade),
    onSuccess: (data) => {
      // Invalidate specific trade and lists
      queryClient.invalidateQueries({ queryKey: tradeKeys.detail(data.id) })
      queryClient.invalidateQueries({ queryKey: tradeKeys.lists() })
    },
  })
}

/**
 * Hook to delete a trade.
 */
export function useDeleteTrade() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (id: number) => deleteTrade(id),
    onSuccess: () => {
      // Invalidate trade lists
      queryClient.invalidateQueries({ queryKey: tradeKeys.lists() })
    },
  })
}

/**
 * Hook to bulk create trades.
 */
export function useBulkCreateTrades() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (trades: TradeCreate[]) => bulkCreateTrades(trades),
    onSuccess: () => {
      // Invalidate trade lists
      queryClient.invalidateQueries({ queryKey: tradeKeys.lists() })
    },
  })
}

