/**
 * TypeScript types for calendar-related data structures.
 * 
 * These types match the Pydantic schemas from the backend.
 */

export interface CalendarDay {
  date: string // ISO date string
  pnl: number
  trade_count: number
  is_profitable: boolean
}

export interface CalendarSummary {
  total_pnl: number
  total_trades: number
  profitable_days: number
  losing_days: number
}

export interface CalendarMonth {
  year: number
  month: number
  days: CalendarDay[]
  month_summary: CalendarSummary
}

