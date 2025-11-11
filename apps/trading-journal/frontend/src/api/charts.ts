/**
 * Charts API endpoints.
 */

import apiClient from './client'
import { PriceDataResponse, TradeOverlayData } from '../types/charts'

/**
 * Get price data for a ticker.
 */
export const getPriceData = async (
  ticker: string,
  startDate?: string,
  endDate?: string,
  timeframe: string = '1h'
): Promise<PriceDataResponse> => {
  const params: Record<string, string> = { timeframe }
  if (startDate) params.start_date = startDate
  if (endDate) params.end_date = endDate
  
  const response = await apiClient.get<PriceDataResponse>(`/charts/prices/${ticker}`, { params })
  return response.data
}

/**
 * Get price data for a ticker for a specified number of days.
 */
export const getPriceDataRange = async (
  ticker: string,
  days: number = 365,
  timeframe: string = '1h'
): Promise<PriceDataResponse> => {
  const response = await apiClient.get<PriceDataResponse>(`/charts/prices/${ticker}/range`, {
    params: { days, timeframe },
  })
  return response.data
}

/**
 * Get price data for a specific trade with context.
 */
export const getTradeChart = async (
  tradeId: number,
  daysBefore: number = 30,
  daysAfter: number = 30,
  timeframe: string = '1h'
): Promise<PriceDataResponse> => {
  const response = await apiClient.get<PriceDataResponse>(`/charts/trade/${tradeId}`, {
    params: { days_before: daysBefore, days_after: daysAfter, timeframe },
  })
  return response.data
}

/**
 * Get trade overlay data for chart visualization.
 */
export const getTradeOverlay = async (tradeId: number): Promise<TradeOverlayData> => {
  const response = await apiClient.get<TradeOverlayData>(`/charts/trade/${tradeId}/overlay`)
  return response.data
}

