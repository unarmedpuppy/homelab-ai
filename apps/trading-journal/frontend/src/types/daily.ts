/**
 * TypeScript types for daily journal-related data structures.
 * 
 * These types match the Pydantic schemas from the backend.
 */

import { TradeResponse } from './trade'

export interface DailySummary {
  total_trades: number
  winners: number
  losers: number
  winrate: number | null
  gross_pnl: number
  commissions: number
  volume: number
  profit_factor: number | null
}

export interface PnLProgressionPoint {
  time: string // ISO datetime string
  cumulative_pnl: number
}

export interface DailyJournal {
  date: string // ISO date string
  net_pnl: number
  trades: TradeResponse[]
  summary: DailySummary
  notes: string | null
  pnl_progression: PnLProgressionPoint[]
}

export interface DailyNoteResponse {
  id: number
  date: string // ISO date string
  notes: string | null
  created_at: string // ISO datetime string
  updated_at: string // ISO datetime string
}

export interface DailyNoteCreate {
  notes: string
}

export interface DailyNoteUpdate {
  notes: string
}

