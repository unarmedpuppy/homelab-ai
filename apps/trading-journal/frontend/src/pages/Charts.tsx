/**
 * Charts page component.
 */

import { useState, useEffect } from 'react'
import { Box, Typography, Paper, TextField, Button, Alert, Chip } from '@mui/material'
import { useParams, useNavigate } from 'react-router-dom'
import { usePriceDataRange, useTradeChart, useTradeOverlay } from '../hooks/useCharts'
import { useTrade } from '../hooks/useTrades'
import PriceChart from '../components/charts/PriceChart'
import ChartControls from '../components/charts/ChartControls'
import { Timeframe, ChartMode } from '../types/charts'

export default function Charts() {
  const { ticker: urlTicker, tradeId: urlTradeId } = useParams()
  const navigate = useNavigate()
  const [ticker, setTicker] = useState<string>(urlTicker || '')
  const [timeframe, setTimeframe] = useState<Timeframe>('1h')
  const [chartMode, setChartMode] = useState<ChartMode>('candlestick')
  const [days, setDays] = useState<number>(365)
  const [daysBefore, setDaysBefore] = useState<number>(30)
  const [daysAfter, setDaysAfter] = useState<number>(30)

  const tradeId = urlTradeId ? parseInt(urlTradeId, 10) : undefined
  const isTradeView = !!tradeId

  // Fetch trade data if viewing a specific trade
  const { data: trade } = useTrade(tradeId || 0)
  const { data: tradeOverlay } = useTradeOverlay(tradeId)

  // Fetch price data - use trade chart endpoint if viewing a trade, otherwise use ticker
  const {
    data: priceDataFromTicker,
    isLoading: isLoadingTicker,
    error: errorTicker,
  } = usePriceDataRange(ticker && !isTradeView ? ticker : undefined, days, timeframe)

  const {
    data: priceDataFromTrade,
    isLoading: isLoadingTrade,
    error: errorTrade,
  } = useTradeChart(tradeId, daysBefore, daysAfter, timeframe)

  const priceData = isTradeView ? priceDataFromTrade : priceDataFromTicker
  const isLoading = isTradeView ? isLoadingTrade : isLoadingTicker
  const error = isTradeView ? errorTrade : errorTicker

  // Sync ticker with URL parameter
  useEffect(() => {
    if (urlTicker && !isTradeView) {
      setTicker(urlTicker.toUpperCase())
    }
  }, [urlTicker, isTradeView])

  // Sync ticker from trade data
  useEffect(() => {
    if (trade && isTradeView) {
      setTicker(trade.ticker)
    }
  }, [trade, isTradeView])

  const handleTickerSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    if (ticker.trim()) {
      navigate(`/charts/${ticker.trim().toUpperCase()}`)
    }
  }

  return (
    <Box sx={{ p: 3 }}>
      <Typography variant="h4" gutterBottom>
        {isTradeView ? 'Trade Chart View' : 'Price Charts'}
      </Typography>

      {/* Trade info banner */}
      {isTradeView && trade && (
        <Paper sx={{ p: 2, mb: 3, bgcolor: 'background.paper' }}>
          <Box sx={{ display: 'flex', gap: 2, alignItems: 'center', flexWrap: 'wrap' }}>
            <Typography variant="h6">
              Trade #{trade.id}: {trade.ticker}
            </Typography>
            <Chip label={trade.trade_type} size="small" variant="outlined" />
            <Chip
              label={trade.side}
              size="small"
              color={trade.side === 'LONG' ? 'primary' : 'secondary'}
            />
            {trade.net_pnl !== null && (
              <Chip
                label={`P&L: $${trade.net_pnl.toFixed(2)}`}
                size="small"
                color={trade.net_pnl >= 0 ? 'success' : 'error'}
              />
            )}
            <Button
              variant="outlined"
              size="small"
              onClick={() => navigate(`/charts/${trade.ticker}`)}
            >
              View Ticker Chart
            </Button>
          </Box>
        </Paper>
      )}

      {/* Ticker input (only show if not viewing a trade) */}
      {!isTradeView && (
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
      )}

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
          {isTradeView && (
            <Box sx={{ display: 'flex', gap: 2, mt: 2, flexWrap: 'wrap' }}>
              <TextField
                label="Days Before Entry"
                type="number"
                size="small"
                value={daysBefore}
                onChange={(e) => {
                  const val = parseInt(e.target.value, 10)
                  if (!isNaN(val) && val > 0 && val <= 365) {
                    setDaysBefore(val)
                  }
                }}
                inputProps={{ min: 1, max: 365 }}
                sx={{ width: 150 }}
              />
              <TextField
                label="Days After Exit"
                type="number"
                size="small"
                value={daysAfter}
                onChange={(e) => {
                  const val = parseInt(e.target.value, 10)
                  if (!isNaN(val) && val > 0 && val <= 365) {
                    setDaysAfter(val)
                  }
                }}
                inputProps={{ min: 1, max: 365 }}
                sx={{ width: 150 }}
              />
            </Box>
          )}
        </Paper>
      )}

      {/* Chart */}
      {ticker && (
        <Paper sx={{ p: 2 }}>
          <Typography variant="h6" gutterBottom>
            {ticker.toUpperCase()} - {timeframe} Chart
            {isTradeView && trade && (
              <Typography variant="body2" color="text.secondary" component="span" sx={{ ml: 2 }}>
                (Trade #{trade.id})
              </Typography>
            )}
          </Typography>
          <PriceChart
            data={priceData}
            isLoading={isLoading}
            error={error as Error | null}
            chartMode={chartMode}
            tradeOverlay={tradeOverlay || undefined}
            height={600}
          />
        </Paper>
      )}

      {!ticker && !isTradeView && (
        <Alert severity="info" sx={{ mt: 2 }}>
          Enter a ticker symbol above to view price charts, or click on a trade to view it on a chart
        </Alert>
      )}
    </Box>
  )
}

