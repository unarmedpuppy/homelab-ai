/**
 * Chart controls component for timeframe and date range selection.
 */

import { Box, FormControl, InputLabel, Select, MenuItem, TextField, SelectChangeEvent } from '@mui/material'
import { Timeframe, ChartMode } from '../../types/charts'
import { format, subDays } from 'date-fns'

interface ChartControlsProps {
  timeframe: Timeframe
  chartMode: ChartMode
  days: number
  onTimeframeChange: (timeframe: Timeframe) => void
  onChartModeChange: (mode: ChartMode) => void
  onDaysChange: (days: number) => void
}

const TIMEFRAMES: { value: Timeframe; label: string }[] = [
  { value: '1m', label: '1 Minute' },
  { value: '5m', label: '5 Minutes' },
  { value: '15m', label: '15 Minutes' },
  { value: '1h', label: '1 Hour' },
  { value: '1d', label: '1 Day' },
]

const CHART_MODES: { value: ChartMode; label: string }[] = [
  { value: 'candlestick', label: 'Candlestick' },
  { value: 'line', label: 'Line' },
]

export default function ChartControls({
  timeframe,
  chartMode,
  days,
  onTimeframeChange,
  onChartModeChange,
  onDaysChange,
}: ChartControlsProps) {
  const handleTimeframeChange = (event: SelectChangeEvent<Timeframe>) => {
    onTimeframeChange(event.target.value as Timeframe)
  }

  const handleChartModeChange = (event: SelectChangeEvent<ChartMode>) => {
    onChartModeChange(event.target.value as ChartMode)
  }

  const handleDaysChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    const value = parseInt(event.target.value, 10)
    if (!isNaN(value) && value > 0 && value <= 365) {
      onDaysChange(value)
    }
  }

  return (
    <Box sx={{ display: 'flex', gap: 2, mb: 2, flexWrap: 'wrap' }}>
      <FormControl size="small" sx={{ minWidth: 150 }}>
        <InputLabel>Timeframe</InputLabel>
        <Select value={timeframe} label="Timeframe" onChange={handleTimeframeChange}>
          {TIMEFRAMES.map((tf) => (
            <MenuItem key={tf.value} value={tf.value}>
              {tf.label}
            </MenuItem>
          ))}
        </Select>
      </FormControl>

      <FormControl size="small" sx={{ minWidth: 150 }}>
        <InputLabel>Chart Type</InputLabel>
        <Select value={chartMode} label="Chart Type" onChange={handleChartModeChange}>
          {CHART_MODES.map((mode) => (
            <MenuItem key={mode.value} value={mode.value}>
              {mode.label}
            </MenuItem>
          ))}
        </Select>
      </FormControl>

      <TextField
        label="Days"
        type="number"
        size="small"
        value={days}
        onChange={handleDaysChange}
        inputProps={{ min: 1, max: 365 }}
        sx={{ width: 100 }}
      />
    </Box>
  )
}

