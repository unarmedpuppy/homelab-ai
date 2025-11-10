/**
 * Calendar grid component displaying a monthly calendar.
 */

import { Grid, Box, Typography, CircularProgress, Alert } from '@mui/material'
import { format, startOfMonth, endOfMonth, eachDayOfInterval, getDay, isSameDay } from 'date-fns'
import { CalendarDay } from '../../types/calendar'
import DayCell from './DayCell'

interface CalendarGridProps {
  year: number
  month: number
  days: CalendarDay[]
  isLoading?: boolean
  error?: Error | null
  onDayClick?: (date: string) => void
}

const WEEKDAYS = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat']

export default function CalendarGrid({
  year,
  month,
  days,
  isLoading,
  error,
  onDayClick,
}: CalendarGridProps) {
  if (isLoading) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', p: 3 }}>
        <CircularProgress />
      </Box>
    )
  }

  if (error) {
    return (
      <Alert severity="error" sx={{ m: 2 }}>
        Failed to load calendar data: {error.message}
      </Alert>
    )
  }

  // Create a map of date strings to CalendarDay for quick lookup
  // Backend returns dates as ISO strings (YYYY-MM-DD)
  const daysMap = new Map<string, CalendarDay>()
  days.forEach((day) => {
    // Ensure date is in YYYY-MM-DD format for lookup
    const dateKey = typeof day.date === 'string' ? day.date : day.date.split('T')[0]
    daysMap.set(dateKey, day)
  })

  // Get first and last day of the month
  const monthStart = startOfMonth(new Date(year, month - 1, 1))
  const monthEnd = endOfMonth(monthStart)

  // Get all days in the month
  const monthDays = eachDayOfInterval({ start: monthStart, end: monthEnd })

  // Get the first day of the week for the month start (0 = Sunday, 6 = Saturday)
  const startDayOfWeek = getDay(monthStart)

  // Create array of all days to display (including leading/trailing days from adjacent months)
  const calendarDays: Array<{ date: Date; isCurrentMonth: boolean }> = []

  // Add leading days from previous month
  for (let i = 0; i < startDayOfWeek; i++) {
    const date = new Date(monthStart)
    date.setDate(date.getDate() - (startDayOfWeek - i))
    calendarDays.push({ date, isCurrentMonth: false })
  }

  // Add days from current month
  monthDays.forEach((date) => {
    calendarDays.push({ date, isCurrentMonth: true })
  })

  // Add trailing days from next month to complete the grid (6 rows = 42 days)
  const remainingDays = 42 - calendarDays.length
  for (let i = 1; i <= remainingDays; i++) {
    const date = new Date(monthEnd)
    date.setDate(date.getDate() + i)
    calendarDays.push({ date, isCurrentMonth: false })
  }

  const today = new Date()

  return (
    <Box>
      {/* Weekday headers */}
      <Grid container spacing={1} sx={{ mb: 1 }}>
        {WEEKDAYS.map((day) => (
          <Grid item xs key={day}>
            <Box
              sx={{
                textAlign: 'center',
                py: 1,
                fontWeight: 'bold',
                color: 'text.secondary',
              }}
            >
              <Typography variant="caption">{day}</Typography>
            </Box>
          </Grid>
        ))}
      </Grid>

      {/* Calendar grid */}
      <Grid container spacing={1}>
        {calendarDays.map(({ date, isCurrentMonth }) => {
          const dateStr = format(date, 'yyyy-MM-dd')
          const day = daysMap.get(dateStr) || {
            date: dateStr,
            pnl: 0,
            trade_count: 0,
            is_profitable: false,
          }
          const isToday = isSameDay(date, today)

          return (
            <Grid item xs key={dateStr}>
              <DayCell
                day={day}
                isCurrentMonth={isCurrentMonth}
                isToday={isToday}
                onClick={onDayClick ? () => onDayClick(dateStr) : undefined}
              />
            </Grid>
          )
        })}
      </Grid>
    </Box>
  )
}

