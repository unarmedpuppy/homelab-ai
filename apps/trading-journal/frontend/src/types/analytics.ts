/**
 * TypeScript types for analytics-related data structures.
 * 
 * These types match the Pydantic schemas from the backend.
 */

export interface PerformanceMetrics {
  sharpe_ratio?: number
  sortino_ratio?: number
  max_drawdown?: number
  avg_drawdown?: number
  win_rate?: number
  profit_factor?: number
  avg_win?: number
  avg_loss?: number
  best_trade?: number
  worst_trade?: number
  total_trades: number
  as_of: string // ISO datetime string
}

export interface TickerPerformance {
  ticker: string
  total_trades: number
  net_pnl: number
  gross_pnl: number
  win_rate?: number
  profit_factor?: number
  avg_win?: number
  avg_loss?: number
  winners: number
  losers: number
}

export interface TickerPerformanceResponse {
  date_from?: string
  date_to?: string
  tickers: TickerPerformance[]
  as_of: string
}

export interface TypePerformance {
  trade_type: string
  total_trades: number
  net_pnl: number
  gross_pnl: number
  win_rate?: number
  profit_factor?: number
  avg_win?: number
  avg_loss?: number
  winners: number
  losers: number
}

export interface TypePerformanceResponse {
  date_from?: string
  date_to?: string
  types: TypePerformance[]
  as_of: string
}

export interface PlaybookPerformance {
  playbook: string
  total_trades: number
  net_pnl: number
  gross_pnl: number
  win_rate?: number
  profit_factor?: number
  avg_win?: number
  avg_loss?: number
  winners: number
  losers: number
}

export interface PlaybookPerformanceResponse {
  date_from?: string
  date_to?: string
  playbooks: PlaybookPerformance[]
  as_of: string
}

