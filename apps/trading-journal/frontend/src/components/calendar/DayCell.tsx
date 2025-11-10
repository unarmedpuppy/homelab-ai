/**
 * Day cell component for calendar grid.
 */

import { Box, Typography, Tooltip } from '@mui/material'
import { format } from 'date-fns'
import { CalendarDay } from '../../types/calendar'

interface DayCellProps {
  day: CalendarDay
  isCurrentMonth: boolean
  isToday: boolean
  onClick?: () => void
}

export default function DayCell({ day, isCurrentMonth, isToday, onClick }: DayCellProps) {
  const dayNumber = parseInt(format(new Date(day.date), 'd'))
  
  // Determine background color based on profitability
  const getBackgroundColor = () => {
    if (!isCurrentMonth) return 'transparent'
    if (day.trade_count === 0) return 'rgba(107, 114, 128, 0.1)' // Gray for no trades
    if (day.is_profitable) return 'rgba(16, 185, 129, 0.2)' // Green for profitable
    return 'rgba(239, 68, 68, 0.2)' // Red for losing
  }
  
  // Determine border color
  const getBorderColor = () => {
    if (isToday) return '#9c27b0' // Purple for today
    if (day.is_profitable) return '#10b981' // Green border for profitable
    if (day.trade_count > 0 && !day.is_profitable) return '#ef4444' // Red border for losing
    return 'transparent'
  }
  
  const formatPnl = (pnl: number): string => {
    if (pnl === 0) return '$0'
    if (Math.abs(pnl) >= 1000) {
      return `$${(pnl / 1000).toFixed(1)}K`
    }
    return `$${pnl.toFixed(0)}`
  }
  
  return (
    <Tooltip
      title={
        <Box>
          <Typography variant="body2" fontWeight="bold">
            {format(new Date(day.date), 'MMMM d, yyyy')}
          </Typography>
          <Typography variant="body2">P&L: {formatPnl(day.pnl)}</Typography>
          <Typography variant="body2">Trades: {day.trade_count}</Typography>
        </Box>
      }
      arrow
    >
      <Box
        onClick={onClick}
        sx={{
          minHeight: '80px',
          border: `2px solid ${getBorderColor()}`,
          borderRadius: 1,
          backgroundColor: getBackgroundColor(),
          p: 1,
          cursor: onClick ? 'pointer' : 'default',
          opacity: isCurrentMonth ? 1 : 0.4,
          transition: 'all 0.2s',
          '&:hover': onClick
            ? {
                backgroundColor: isCurrentMonth
                  ? day.is_profitable
                    ? 'rgba(16, 185, 129, 0.3)'
                    : day.trade_count > 0
                    ? 'rgba(239, 68, 68, 0.3)'
                    : 'rgba(107, 114, 128, 0.2)'
                  : 'transparent',
                transform: 'scale(1.05)',
              }
            : {},
        }}
      >
        <Typography
          variant="caption"
          sx={{
            fontWeight: isToday ? 'bold' : 'normal',
            color: isToday ? '#9c27b0' : 'text.primary',
          }}
        >
          {dayNumber}
        </Typography>
        {day.trade_count > 0 && (
          <Box sx={{ mt: 0.5 }}>
            <Typography
              variant="caption"
              sx={{
                display: 'block',
                fontWeight: 'bold',
                color: day.is_profitable ? '#10b981' : '#ef4444',
                fontSize: '0.7rem',
              }}
            >
              {formatPnl(day.pnl)}
            </Typography>
            <Typography
              variant="caption"
              sx={{
                display: 'block',
                color: 'text.secondary',
                fontSize: '0.65rem',
              }}
            >
              {day.trade_count} {day.trade_count === 1 ? 'trade' : 'trades'}
            </Typography>
          </Box>
        )}
      </Box>
    </Tooltip>
  )
}

