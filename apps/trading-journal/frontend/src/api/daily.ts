/**
 * Daily journal API endpoints.
 */

import apiClient from './client'
import {
  DailyJournal,
  DailySummary,
  PnLProgressionPoint,
  DailyNoteResponse,
  DailyNoteCreate,
  DailyNoteUpdate,
} from '../types/daily'
import { TradeResponse } from '../types/trade'

// Export types for use in hooks
export type { DailyNoteCreate, DailyNoteUpdate }

/**
 * Get complete daily journal data for a specific date.
 */
export const getDailyJournal = async (date: string): Promise<DailyJournal> => {
  const response = await apiClient.get<DailyJournal>(`/daily/${date}`)
  return response.data
}

/**
 * Get trades for a specific date.
 */
export const getDailyTrades = async (date: string): Promise<TradeResponse[]> => {
  const response = await apiClient.get<TradeResponse[]>(`/daily/${date}/trades`)
  return response.data
}

/**
 * Get daily summary for a specific date.
 */
export const getDailySummary = async (date: string): Promise<DailySummary> => {
  const response = await apiClient.get<DailySummary>(`/daily/${date}/summary`)
  return response.data
}

/**
 * Get P&L progression for a specific date.
 */
export const getDailyPnLProgression = async (
  date: string
): Promise<PnLProgressionPoint[]> => {
  const response = await apiClient.get<PnLProgressionPoint[]>(
    `/daily/${date}/pnl-progression`
  )
  return response.data
}

/**
 * Get daily notes for a specific date.
 */
export const getDailyNotes = async (date: string): Promise<DailyNoteResponse> => {
  const response = await apiClient.get<DailyNoteResponse>(`/daily/${date}/notes`)
  return response.data
}

/**
 * Create or update daily notes for a specific date.
 */
export const createOrUpdateDailyNotes = async (
  date: string,
  noteData: DailyNoteCreate
): Promise<DailyNoteResponse> => {
  const response = await apiClient.post<DailyNoteResponse>(
    `/daily/${date}/notes`,
    noteData
  )
  return response.data
}

/**
 * Update daily notes for a specific date.
 */
export const updateDailyNotes = async (
  date: string,
  noteData: DailyNoteUpdate
): Promise<DailyNoteResponse> => {
  const response = await apiClient.put<DailyNoteResponse>(
    `/daily/${date}/notes`,
    noteData
  )
  return response.data
}

/**
 * Delete daily notes for a specific date.
 */
export const deleteDailyNotes = async (date: string): Promise<void> => {
  await apiClient.delete(`/daily/${date}/notes`)
}

