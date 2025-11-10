/**
 * Calendar page component.
 */

import { useState } from 'react'
import {
  Box,
  Typography,
  IconButton,
  Paper,
  Grid,
  Card,
  CardContent,
  useTheme,
} from '@mui/material'
import {
  ChevronLeft,
  ChevronRight,
  TrendingUp,
  TrendingDown,
  Assessment,
} from '@mui/icons-material'
import { format, addMonths, subMonths } from 'date-fns'
import { useNavigate } from 'react-router-dom'
import { useCalendarMonth } from '../hooks/useCalendar'
import CalendarGrid from '../components/calendar/CalendarGrid'

export default function Calendar() {
  const theme = useTheme()
  const navigate = useNavigate()
  const [currentDate, setCurrentDate] = useState(new Date())
  const year = currentDate.getFullYear()
  const month = currentDate.getMonth() + 1

  const { data: calendarData, isLoading, error } = useCalendarMonth(year, month)

  const handlePreviousMonth = () => {
    setCurrentDate(subMonths(currentDate, 1))
  }

  const handleNextMonth = () => {
    setCurrentDate(addMonths(currentDate, 1))
  }

  const handleDayClick = (date: string) => {
    // Navigate to daily journal view
    navigate(`/daily/${date}`)
  }

  const formatCurrency = (value: number): string => {
    if (value === 0) return '$0'
    if (Math.abs(value) >= 1000000) {
      return `$${(value / 1000000).toFixed(2)}M`
    } else if (Math.abs(value) >= 1000) {
      return `$${(value / 1000).toFixed(2)}K`
    }
    return `$${value.toFixed(2)}`
  }

  return (
    <Box sx={{ p: 3 }}>
      {/* Header with month navigation */}
      <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', mb: 3 }}>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
          <IconButton onClick={handlePreviousMonth} color="primary">
            <ChevronLeft />
          </IconButton>
          <Typography variant="h4" component="h1">
            {format(currentDate, 'MMMM yyyy')}
          </Typography>
          <IconButton onClick={handleNextMonth} color="primary">
            <ChevronRight />
          </IconButton>
        </Box>
        <IconButton
          onClick={() => setCurrentDate(new Date())}
          color="primary"
          sx={{ ml: 'auto' }}
        >
          <Typography variant="body2">Today</Typography>
        </IconButton>
      </Box>

      {/* Month summary cards */}
      {calendarData && (
        <Grid container spacing={2} sx={{ mb: 3 }}>
          <Grid item xs={12} sm={6} md={3}>
            <Card>
              <CardContent>
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                  <Assessment color="primary" />
                  <Typography variant="body2" color="text.secondary">
                    Total P&L
                  </Typography>
                </Box>
                <Typography
                  variant="h5"
                  sx={{
                    mt: 1,
                    fontWeight: 'bold',
                    color:
                      calendarData.month_summary.total_pnl >= 0
                        ? theme.palette.success.main
                        : theme.palette.error.main,
                  }}
                >
                  {formatCurrency(calendarData.month_summary.total_pnl)}
                </Typography>
              </CardContent>
            </Card>
          </Grid>
          <Grid item xs={12} sm={6} md={3}>
            <Card>
              <CardContent>
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                  <Assessment color="primary" />
                  <Typography variant="body2" color="text.secondary">
                    Total Trades
                  </Typography>
                </Box>
                <Typography variant="h5" sx={{ mt: 1, fontWeight: 'bold' }}>
                  {calendarData.month_summary.total_trades}
                </Typography>
              </CardContent>
            </Card>
          </Grid>
          <Grid item xs={12} sm={6} md={3}>
            <Card>
              <CardContent>
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                  <TrendingUp color="success" />
                  <Typography variant="body2" color="text.secondary">
                    Profitable Days
                  </Typography>
                </Box>
                <Typography
                  variant="h5"
                  sx={{ mt: 1, fontWeight: 'bold', color: theme.palette.success.main }}
                >
                  {calendarData.month_summary.profitable_days}
                </Typography>
              </CardContent>
            </Card>
          </Grid>
          <Grid item xs={12} sm={6} md={3}>
            <Card>
              <CardContent>
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                  <TrendingDown color="error" />
                  <Typography variant="body2" color="text.secondary">
                    Losing Days
                  </Typography>
                </Box>
                <Typography
                  variant="h5"
                  sx={{ mt: 1, fontWeight: 'bold', color: theme.palette.error.main }}
                >
                  {calendarData.month_summary.losing_days}
                </Typography>
              </CardContent>
            </Card>
          </Grid>
        </Grid>
      )}

      {/* Calendar grid */}
      <Paper sx={{ p: 2 }}>
        <CalendarGrid
          year={year}
          month={month}
          days={calendarData?.days || []}
          isLoading={isLoading}
          error={error as Error | null}
          onDayClick={handleDayClick}
        />
      </Paper>

      {/* Legend */}
      <Box sx={{ mt: 3, display: 'flex', gap: 3, flexWrap: 'wrap' }}>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
          <Box
            sx={{
              width: 20,
              height: 20,
              borderRadius: 1,
              backgroundColor: 'rgba(16, 185, 129, 0.2)',
              border: '2px solid #10b981',
            }}
          />
          <Typography variant="body2">Profitable Day</Typography>
        </Box>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
          <Box
            sx={{
              width: 20,
              height: 20,
              borderRadius: 1,
              backgroundColor: 'rgba(239, 68, 68, 0.2)',
              border: '2px solid #ef4444',
            }}
          />
          <Typography variant="body2">Losing Day</Typography>
        </Box>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
          <Box
            sx={{
              width: 20,
              height: 20,
              borderRadius: 1,
              backgroundColor: 'rgba(107, 114, 128, 0.1)',
            }}
          />
          <Typography variant="body2">No Trades</Typography>
        </Box>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
          <Box
            sx={{
              width: 20,
              height: 20,
              borderRadius: 1,
              border: '2px solid #9c27b0',
            }}
          />
          <Typography variant="body2">Today</Typography>
        </Box>
      </Box>
    </Box>
  )
}
