/**
 * TypeScript types for chart-related data structures.
 * 
 * These types match the Pydantic schemas from the backend.
 */

export interface PriceDataPoint {
  timestamp: string // ISO datetime string
  open: number
  high: number
  low: number
  close: number
  volume?: number | null
}

export interface PriceDataResponse {
  ticker: string
  timeframe: string
  start_date: string // ISO datetime string
  end_date: string // ISO datetime string
  data: PriceDataPoint[]
}

export interface TradeOverlayData {
  trade_id: number
  ticker: string
  entry_time: string // ISO datetime string
  entry_price: number
  exit_time?: string | null // ISO datetime string
  exit_price?: number | null
  side: string
  net_pnl?: number | null
}

export type Timeframe = '1m' | '5m' | '15m' | '1h' | '1d'
export type ChartMode = 'candlestick' | 'line'

export interface ChartColorConfig {
  // Chart background and layout
  background?: string
  textColor?: string
  gridLines?: string
  borderColor?: string
  
  // Candlestick colors
  upColor?: string
  downColor?: string
  wickUpColor?: string
  wickDownColor?: string
  
  // Line chart color
  lineColor?: string
  
  // Indicator colors
  volumeColor?: string
  movingAverageColor?: string
  movingAverageColor2?: string
}

export interface ChartIndicatorConfig {
  // Moving averages
  showSMA?: boolean
  smaPeriod?: number
  showEMA?: boolean
  emaPeriod?: number
  
  // Volume
  showVolume?: boolean
  
  // Other indicators (can be added later)
  showRSI?: boolean
  rsiPeriod?: number
}

