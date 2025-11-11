/**
 * Cumulative P&L line chart component.
 */

import { Box, Paper, Typography } from '@mui/material'
import LoadingSpinner from '../common/LoadingSpinner'
import ErrorAlert from '../common/ErrorAlert'
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Legend,
} from 'recharts'
import { useCumulativePnL } from '../../hooks/useDashboard'
import { format } from 'date-fns'

interface CumulativePnLChartProps {
  dateFrom?: string
  dateTo?: string
  groupBy?: 'day' | 'week' | 'month'
  height?: number
}

export default function CumulativePnLChart({
  dateFrom,
  dateTo,
  groupBy = 'day',
  height = 300,
}: CumulativePnLChartProps) {
  const { data, isLoading, error } = useCumulativePnL({
    date_from: dateFrom,
    date_to: dateTo,
    group_by: groupBy,
  })

  if (isLoading) {
    return <LoadingSpinner message="Loading chart data..." minHeight={height} />
  }

  if (error) {
    return (
      <ErrorAlert
        title="Failed to load chart"
        message={error.message || 'Failed to load cumulative P&L data. Please try again.'}
        showRetry
        onRetry={() => window.location.reload()}
      />
    )
  }

  if (!data || data.length === 0) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height }}>
        <Typography variant="body2" color="text.secondary">
          No cumulative P&L data available
        </Typography>
      </Box>
    )
  }

  // Format data for chart
  const chartData = data.map((point) => ({
    date: format(new Date(point.date), 'MMM dd'),
    fullDate: point.date,
    cumulativePnl: Number(point.cumulative_pnl),
  }))

  // Custom tooltip formatter
  const formatTooltipValue = (value: number) => {
    return `$${value.toFixed(2)}`
  }

  const formatTooltipLabel = (label: string, payload: any[]) => {
    if (payload && payload[0] && payload[0].payload) {
      return format(new Date(payload[0].payload.fullDate), 'MMM dd, yyyy')
    }
    return label
  }

  return (
    <Paper sx={{ p: 2 }}>
      <Typography variant="h6" gutterBottom>
        Cumulative P&L
      </Typography>
      <ResponsiveContainer width="100%" height={height}>
        <LineChart data={chartData} margin={{ top: 5, right: 20, left: 10, bottom: 5 }}>
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
            formatter={(value: number) => [formatTooltipValue(value), 'Cumulative P&L']}
          />
          <Legend
            wrapperStyle={{ color: '#d1d5db' }}
            iconType="line"
          />
          <Line
            type="monotone"
            dataKey="cumulativePnl"
            stroke="#9c27b0"
            strokeWidth={2}
            dot={false}
            name="Cumulative P&L"
          />
        </LineChart>
      </ResponsiveContainer>
    </Paper>
  )
}

