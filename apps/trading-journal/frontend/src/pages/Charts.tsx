/**
 * Charts page component.
 */

import { useState, useEffect } from 'react'
import { Box, Typography, Paper, TextField, Button, Alert } from '@mui/material'
import { useParams, useNavigate } from 'react-router-dom'
import { usePriceDataRange } from '../hooks/useCharts'
import PriceChart from '../components/charts/PriceChart'
import ChartControls from '../components/charts/ChartControls'
import { Timeframe, ChartMode } from '../types/charts'

export default function Charts() {
  const { ticker: urlTicker } = useParams()
  const navigate = useNavigate()
  const [ticker, setTicker] = useState<string>(urlTicker || '')
  const [timeframe, setTimeframe] = useState<Timeframe>('1h')
  const [chartMode, setChartMode] = useState<ChartMode>('candlestick')
  const [days, setDays] = useState<number>(365)

  // Sync ticker with URL parameter
  useEffect(() => {
    if (urlTicker) {
      setTicker(urlTicker.toUpperCase())
    }
  }, [urlTicker])

  const { data: priceData, isLoading, error } = usePriceDataRange(
    ticker || undefined,
    days,
    timeframe
  )

  const handleTickerSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    if (ticker.trim()) {
      navigate(`/charts/${ticker.trim().toUpperCase()}`)
    }
  }

  return (
    <Box sx={{ p: 3 }}>
      <Typography variant="h4" gutterBottom>
        Price Charts
      </Typography>

      {/* Ticker input */}
      <Paper sx={{ p: 2, mb: 3 }}>
        <form onSubmit={handleTickerSubmit}>
          <Box sx={{ display: 'flex', gap: 2, alignItems: 'center' }}>
            <TextField
              label="Ticker Symbol"
              value={ticker}
              onChange={(e) => setTicker(e.target.value.toUpperCase())}
              placeholder="e.g., TSLA, AAPL"
              size="small"
              sx={{ flexGrow: 1, maxWidth: 200 }}
            />
            <Button type="submit" variant="contained" disabled={!ticker.trim()}>
              Load Chart
            </Button>
          </Box>
        </form>
      </Paper>

      {/* Chart controls */}
      {ticker && (
        <Paper sx={{ p: 2, mb: 3 }}>
          <ChartControls
            timeframe={timeframe}
            chartMode={chartMode}
            days={days}
            onTimeframeChange={setTimeframe}
            onChartModeChange={setChartMode}
            onDaysChange={setDays}
          />
        </Paper>
      )}

      {/* Chart */}
      {ticker && (
        <Paper sx={{ p: 2 }}>
          <Typography variant="h6" gutterBottom>
            {ticker.toUpperCase()} - {timeframe} Chart
          </Typography>
          <PriceChart
            data={priceData}
            isLoading={isLoading}
            error={error as Error | null}
            chartMode={chartMode}
            height={600}
          />
        </Paper>
      )}

      {!ticker && (
        <Alert severity="info" sx={{ mt: 2 }}>
          Enter a ticker symbol above to view price charts
        </Alert>
      )}
    </Box>
  )
}

