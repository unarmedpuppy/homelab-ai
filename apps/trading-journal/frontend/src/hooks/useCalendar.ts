/**
 * React Query hooks for calendar operations.
 */

import { useQuery } from '@tanstack/react-query'
import { getCalendarMonth, getCalendarDay, getCalendarSummary } from '../api/calendar'

// Query keys
export const calendarKeys = {
  all: ['calendar'] as const,
  month: (year: number, month: number) => [...calendarKeys.all, 'month', year, month] as const,
  day: (date: string) => [...calendarKeys.all, 'day', date] as const,
  summary: (dateFrom?: string, dateTo?: string) =>
    [...calendarKeys.all, 'summary', dateFrom, dateTo] as const,
}

/**
 * Hook to fetch calendar data for a specific month.
 */
export function useCalendarMonth(year: number, month: number) {
  return useQuery({
    queryKey: calendarKeys.month(year, month),
    queryFn: () => getCalendarMonth(year, month),
  })
}

/**
 * Hook to fetch calendar data for a specific day.
 */
export function useCalendarDay(date: string) {
  return useQuery({
    queryKey: calendarKeys.day(date),
    queryFn: () => getCalendarDay(date),
    enabled: !!date,
  })
}

/**
 * Hook to fetch calendar summary for a date range.
 */
export function useCalendarSummary(dateFrom?: string, dateTo?: string) {
  return useQuery({
    queryKey: calendarKeys.summary(dateFrom, dateTo),
    queryFn: () => getCalendarSummary(dateFrom, dateTo),
  })
}

