/**
 * React Query hooks for chart operations.
 */

import { useQuery } from '@tanstack/react-query'
import { getPriceData, getPriceDataRange, getTradeChart, getTradeOverlay } from '../api/charts'
import { PriceDataResponse, TradeOverlayData } from '../types/charts'

// Query keys
export const chartKeys = {
  all: ['charts'] as const,
  prices: (ticker: string, startDate?: string, endDate?: string, timeframe?: string) =>
    [...chartKeys.all, 'prices', ticker, startDate, endDate, timeframe] as const,
  priceRange: (ticker: string, days: number, timeframe?: string) =>
    [...chartKeys.all, 'priceRange', ticker, days, timeframe] as const,
  trade: (tradeId: number, daysBefore?: number, daysAfter?: number, timeframe?: string) =>
    [...chartKeys.all, 'trade', tradeId, daysBefore, daysAfter, timeframe] as const,
  tradeOverlay: (tradeId: number) => [...chartKeys.all, 'tradeOverlay', tradeId] as const,
}

/**
 * Hook to fetch price data for a ticker.
 */
export function usePriceData(
  ticker: string | undefined,
  startDate?: string,
  endDate?: string,
  timeframe: string = '1h'
) {
  return useQuery<PriceDataResponse>({
    queryKey: chartKeys.prices(ticker || '', startDate, endDate, timeframe),
    queryFn: () => getPriceData(ticker!, startDate, endDate, timeframe),
    enabled: !!ticker,
  })
}

/**
 * Hook to fetch price data for a ticker for a specified number of days.
 */
export function usePriceDataRange(
  ticker: string | undefined,
  days: number = 365,
  timeframe: string = '1h'
) {
  return useQuery<PriceDataResponse>({
    queryKey: chartKeys.priceRange(ticker || '', days, timeframe),
    queryFn: () => getPriceDataRange(ticker!, days, timeframe),
    enabled: !!ticker,
  })
}

/**
 * Hook to fetch price data for a specific trade.
 */
export function useTradeChart(
  tradeId: number | undefined,
  daysBefore: number = 30,
  daysAfter: number = 30,
  timeframe: string = '1h'
) {
  return useQuery<PriceDataResponse>({
    queryKey: chartKeys.trade(tradeId || 0, daysBefore, daysAfter, timeframe),
    queryFn: () => getTradeChart(tradeId!, daysBefore, daysAfter, timeframe),
    enabled: !!tradeId,
  })
}

/**
 * Hook to fetch trade overlay data.
 */
export function useTradeOverlay(tradeId: number | undefined) {
  return useQuery<TradeOverlayData>({
    queryKey: chartKeys.tradeOverlay(tradeId || 0),
    queryFn: () => getTradeOverlay(tradeId!),
    enabled: !!tradeId,
  })
}

