/**
 * Drawdown chart component.
 */

import { Box, Paper, Typography } from '@mui/material'
import LoadingSpinner from '../common/LoadingSpinner'
import ErrorAlert from '../common/ErrorAlert'
import {
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Legend,
} from 'recharts'
import { useDrawdownData } from '../../hooks/useDashboard'
import { format } from 'date-fns'

interface DrawdownChartProps {
  dateFrom?: string
  dateTo?: string
  height?: number
}

export default function DrawdownChart({
  dateFrom,
  dateTo,
  height = 300,
}: DrawdownChartProps) {
  const { data, isLoading, error } = useDrawdownData({
    date_from: dateFrom,
    date_to: dateTo,
  })

  if (isLoading) {
    return <LoadingSpinner message="Loading chart data..." minHeight={height} />
  }

  if (error) {
    return (
      <ErrorAlert
        title="Failed to load chart"
        message={error.message || 'Failed to load drawdown data. Please try again.'}
        showRetry
        onRetry={() => window.location.reload()}
      />
    )
  }

  if (!data || data.length === 0) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height }}>
        <Typography variant="body2" color="text.secondary">
          No drawdown data available
        </Typography>
      </Box>
    )
  }

  // Format data for chart
  const chartData = data.map((point) => ({
    date: format(new Date(point.date), 'MMM dd'),
    fullDate: point.date,
    peak: Number(point.peak),
    trough: Number(point.trough),
    drawdown: Number(point.drawdown),
    drawdownPct: Number(point.drawdown_pct),
    recoveryDate: point.recovery_date,
  }))

  // Custom tooltip formatter
  const formatTooltipValue = (value: number, name: string) => {
    if (name === 'Drawdown %') {
      return `${value.toFixed(2)}%`
    }
    return `$${value.toFixed(2)}`
  }

  const formatTooltipLabel = (label: string, payload: any[]) => {
    if (payload && payload[0] && payload[0].payload) {
      const recoveryDate = payload[0].payload.recoveryDate
      const recoveryText = recoveryDate
        ? ` (Recovered: ${format(new Date(recoveryDate), 'MMM dd, yyyy')})`
        : ' (Not recovered)'
      return `${format(new Date(payload[0].payload.fullDate), 'MMM dd, yyyy')}${recoveryText}`
    }
    return label
  }

  return (
    <Paper sx={{ p: 2 }}>
      <Typography variant="h6" gutterBottom>
        Drawdown
      </Typography>
      <ResponsiveContainer width="100%" height={height}>
        <AreaChart data={chartData} margin={{ top: 5, right: 20, left: 10, bottom: 5 }}>
          <defs>
            <linearGradient id="colorDrawdown" x1="0" y1="0" x2="0" y2="1">
              <stop offset="5%" stopColor="#ef4444" stopOpacity={0.8} />
              <stop offset="95%" stopColor="#ef4444" stopOpacity={0.1} />
            </linearGradient>
          </defs>
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
            tickFormatter={(value) => `${value.toFixed(0)}%`}
          />
          <Tooltip
            contentStyle={{
              backgroundColor: '#1e1e1e',
              border: '1px solid #2a2a2a',
              borderRadius: '4px',
              color: '#d1d5db',
            }}
            labelFormatter={formatTooltipLabel}
            formatter={formatTooltipValue}
          />
          <Legend
            wrapperStyle={{ color: '#d1d5db' }}
          />
          <Area
            type="monotone"
            dataKey="drawdownPct"
            stroke="#ef4444"
            strokeWidth={2}
            fill="url(#colorDrawdown)"
            name="Drawdown %"
          />
        </AreaChart>
      </ResponsiveContainer>
    </Paper>
  )
}

