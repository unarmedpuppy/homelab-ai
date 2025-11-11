/**
 * Daily P&L bar chart component.
 */

import { Box, Paper, Typography, CircularProgress, Alert } from '@mui/material'
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Legend,
  Cell,
} from 'recharts'
import { useDailyPnL } from '../../hooks/useDashboard'
import { format } from 'date-fns'

interface DailyPnLChartProps {
  dateFrom?: string
  dateTo?: string
  height?: number
}

export default function DailyPnLChart({
  dateFrom,
  dateTo,
  height = 300,
}: DailyPnLChartProps) {
  const { data, isLoading, error } = useDailyPnL({
    date_from: dateFrom,
    date_to: dateTo,
  })

  if (isLoading) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height }}>
        <CircularProgress />
      </Box>
    )
  }

  if (error) {
    return (
      <Alert severity="error">
        Failed to load daily P&L data: {error.message}
      </Alert>
    )
  }

  if (!data || data.length === 0) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height }}>
        <Typography variant="body2" color="text.secondary">
          No daily P&L data available
        </Typography>
      </Box>
    )
  }

  // Format data for chart
  const chartData = data.map((point) => ({
    date: format(new Date(point.date), 'MMM dd'),
    fullDate: point.date,
    pnl: Number(point.pnl),
    tradeCount: point.trade_count,
  }))

  // Custom tooltip formatter
  const formatTooltipValue = (value: number) => {
    return `$${value.toFixed(2)}`
  }

  const formatTooltipLabel = (label: string, payload: any[]) => {
    if (payload && payload[0] && payload[0].payload) {
      const tradeCount = payload[0].payload.tradeCount
      return `${format(new Date(payload[0].payload.fullDate), 'MMM dd, yyyy')} (${tradeCount} trade${tradeCount !== 1 ? 's' : ''})`
    }
    return label
  }

  // Custom bar color based on P&L value
  const getBarColor = (entry: any) => {
    return entry.pnl >= 0 ? '#10b981' : '#ef4444'
  }

  return (
    <Paper sx={{ p: 2 }}>
      <Typography variant="h6" gutterBottom>
        Daily P&L
      </Typography>
      <ResponsiveContainer width="100%" height={height}>
        <BarChart data={chartData} margin={{ top: 5, right: 20, left: 10, bottom: 5 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#2a2a2a" />
          <XAxis
            dataKey="date"
            stroke="#d1d5db"
            style={{ fontSize: '12px' }}
            tick={{ fill: '#d1d5db' }}
          />
          <YAxis
            stroke="#d1d5db"
            style={{ fontSize: '12px' }}
            tick={{ fill: '#d1d5db' }}
            tickFormatter={(value) => `$${value.toFixed(0)}`}
          />
          <Tooltip
            contentStyle={{
              backgroundColor: '#1e1e1e',
              border: '1px solid #2a2a2a',
              borderRadius: '4px',
              color: '#d1d5db',
            }}
            labelFormatter={formatTooltipLabel}
            formatter={(value: number) => [formatTooltipValue(value), 'Daily P&L']}
          />
          <Legend
            wrapperStyle={{ color: '#d1d5db' }}
          />
          <Bar
            dataKey="pnl"
            name="Daily P&L"
            radius={[4, 4, 0, 0]}
          >
            {chartData.map((entry, index) => (
              <Cell key={`cell-${index}`} fill={getBarColor(entry)} />
            ))}
          </Bar>
        </BarChart>
      </ResponsiveContainer>
    </Paper>
  )
}

