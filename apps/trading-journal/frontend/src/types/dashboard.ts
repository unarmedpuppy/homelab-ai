/**
 * TypeScript types for dashboard-related data structures.
 * 
 * These types match the Pydantic schemas from the backend.
 */

export interface DashboardStats {
  net_pnl: number
  gross_pnl: number
  total_trades: number
  winners: number
  losers: number
  win_rate: number | null
  day_win_rate: number | null
  profit_factor: number | null
  avg_win: number | null
  avg_loss: number | null
  max_drawdown: number | null
  zella_score: number | null
}

export interface CumulativePnLPoint {
  date: string // ISO date string
  cumulative_pnl: number
}

export interface DailyPnLPoint {
  date: string // ISO date string
  pnl: number
  trade_count: number
}

export interface DrawdownData {
  date: string // ISO date string
  peak: number
  trough: number
  drawdown: number
  drawdown_pct: number
  recovery_date: string | null // ISO date string
}

export interface RecentTrade {
  id: number
  ticker: string
  trade_type: string
  side: string
  entry_time: string // ISO date string
  exit_time: string | null // ISO date string
  net_pnl: number | null
  status: string
}

