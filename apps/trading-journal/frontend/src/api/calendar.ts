/**
 * Calendar API endpoints.
 */

import apiClient from './client'
import { CalendarDay, CalendarMonth, CalendarSummary } from '../types/calendar'

/**
 * Get calendar data for a specific month.
 */
export const getCalendarMonth = async (
  year: number,
  month: number
): Promise<CalendarMonth> => {
  const response = await apiClient.get<CalendarMonth>(`/calendar/${year}/${month}`)
  return response.data
}

/**
 * Get calendar data for a specific day.
 */
export const getCalendarDay = async (date: string): Promise<CalendarDay> => {
  const response = await apiClient.get<CalendarDay>(`/calendar/date/${date}`)
  return response.data
}

/**
 * Get calendar summary for a date range.
 */
export const getCalendarSummary = async (
  dateFrom?: string,
  dateTo?: string
): Promise<CalendarSummary> => {
  const params: Record<string, string> = {}
  if (dateFrom) params.date_from = dateFrom
  if (dateTo) params.date_to = dateTo
  
  const response = await apiClient.get<CalendarSummary>('/calendar/summary', { params })
  return response.data
}

