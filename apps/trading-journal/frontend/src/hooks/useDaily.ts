/**
 * React Query hooks for daily journal operations.
 */

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import {
  getDailyJournal,
  getDailyTrades,
  getDailySummary,
  getDailyPnLProgression,
  getDailyNotes,
  createOrUpdateDailyNotes,
  updateDailyNotes,
  deleteDailyNotes,
  DailyNoteCreate,
  DailyNoteUpdate,
} from '../api/daily'

// Query keys
export const dailyKeys = {
  all: ['daily'] as const,
  journal: (date: string) => [...dailyKeys.all, 'journal', date] as const,
  trades: (date: string) => [...dailyKeys.all, 'trades', date] as const,
  summary: (date: string) => [...dailyKeys.all, 'summary', date] as const,
  pnlProgression: (date: string) => [...dailyKeys.all, 'pnl-progression', date] as const,
  notes: (date: string) => [...dailyKeys.all, 'notes', date] as const,
}

/**
 * Hook to fetch complete daily journal data.
 */
export function useDailyJournal(date: string) {
  return useQuery({
    queryKey: dailyKeys.journal(date),
    queryFn: () => getDailyJournal(date),
    enabled: !!date,
  })
}

/**
 * Hook to fetch daily trades.
 */
export function useDailyTrades(date: string) {
  return useQuery({
    queryKey: dailyKeys.trades(date),
    queryFn: () => getDailyTrades(date),
    enabled: !!date,
  })
}

/**
 * Hook to fetch daily summary.
 */
export function useDailySummary(date: string) {
  return useQuery({
    queryKey: dailyKeys.summary(date),
    queryFn: () => getDailySummary(date),
    enabled: !!date,
  })
}

/**
 * Hook to fetch P&L progression.
 */
export function useDailyPnLProgression(date: string) {
  return useQuery({
    queryKey: dailyKeys.pnlProgression(date),
    queryFn: () => getDailyPnLProgression(date),
    enabled: !!date,
  })
}

/**
 * Hook to fetch daily notes.
 */
export function useDailyNotes(date: string) {
  return useQuery({
    queryKey: dailyKeys.notes(date),
    queryFn: () => getDailyNotes(date),
    enabled: !!date,
    retry: false, // Don't retry on 404
  })
}

/**
 * Hook to create or update daily notes.
 */
export function useCreateOrUpdateDailyNotes() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: ({ date, noteData }: { date: string; noteData: DailyNoteCreate }) =>
      createOrUpdateDailyNotes(date, noteData),
    onSuccess: (data, variables) => {
      // Invalidate notes and journal queries
      queryClient.invalidateQueries({ queryKey: dailyKeys.notes(variables.date) })
      queryClient.invalidateQueries({ queryKey: dailyKeys.journal(variables.date) })
    },
  })
}

/**
 * Hook to update daily notes.
 */
export function useUpdateDailyNotes() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: ({ date, noteData }: { date: string; noteData: DailyNoteUpdate }) =>
      updateDailyNotes(date, noteData),
    onSuccess: (data, variables) => {
      // Invalidate notes and journal queries
      queryClient.invalidateQueries({ queryKey: dailyKeys.notes(variables.date) })
      queryClient.invalidateQueries({ queryKey: dailyKeys.journal(variables.date) })
    },
  })
}

/**
 * Hook to delete daily notes.
 */
export function useDeleteDailyNotes() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (date: string) => deleteDailyNotes(date),
    onSuccess: (_, date) => {
      // Invalidate notes and journal queries
      queryClient.invalidateQueries({ queryKey: dailyKeys.notes(date) })
      queryClient.invalidateQueries({ queryKey: dailyKeys.journal(date) })
    },
  })
}

