/**
 * Price chart component using TradingView Lightweight Charts.
 */

import { useEffect, useRef, useState } from 'react'
import { createChart, IChartApi, ISeriesApi, ColorType, LineStyle, LineWidth } from 'lightweight-charts'
import { Box, CircularProgress, Alert, Typography } from '@mui/material'
import { PriceDataResponse, TradeOverlayData, ChartMode } from '../../types/charts'

interface PriceChartProps {
  data: PriceDataResponse | undefined
  isLoading: boolean
  error: Error | null
  chartMode?: ChartMode
  tradeOverlay?: TradeOverlayData | null
  height?: number
}

export default function PriceChart({
  data,
  isLoading,
  error,
  chartMode = 'candlestick',
  tradeOverlay,
  height = 500,
}: PriceChartProps) {
  const chartContainerRef = useRef<HTMLDivElement>(null)
  const chartRef = useRef<IChartApi | null>(null)
  const seriesRef = useRef<ISeriesApi<'Candlestick' | 'Line'> | null>(null)
  const [chartReady, setChartReady] = useState(false)

  useEffect(() => {
    if (!chartContainerRef.current) return

    // Create chart
    const chart = createChart(chartContainerRef.current, {
      layout: {
        background: { type: ColorType.Solid, color: '#1e1e1e' },
        textColor: '#d1d5db',
      },
      grid: {
        vertLines: { color: '#2a2a2a' },
        horzLines: { color: '#2a2a2a' },
      },
      width: chartContainerRef.current.clientWidth,
      height: height,
      timeScale: {
        timeVisible: true,
        secondsVisible: false,
      },
      rightPriceScale: {
        borderColor: '#2a2a2a',
      },
    })

    chartRef.current = chart

    // Handle resize
    const handleResize = () => {
      if (chartContainerRef.current && chart) {
        chart.applyOptions({ width: chartContainerRef.current.clientWidth })
      }
    }

    window.addEventListener('resize', handleResize)
    setChartReady(true)

    return () => {
      window.removeEventListener('resize', handleResize)
      chart.remove()
      chartRef.current = null
      seriesRef.current = null
    }
  }, [height])

  useEffect(() => {
    if (!chartRef.current || !chartReady || !data) return

    // Remove existing series
    if (seriesRef.current) {
      chartRef.current.removeSeries(seriesRef.current)
      seriesRef.current = null
    }

    // Prepare data - convert timestamps to unix time (seconds since epoch)
    const chartData = data.data.map((point) => {
      const unixTime = Math.floor(new Date(point.timestamp).getTime() / 1000)
      return {
        time: unixTime as any, // lightweight-charts expects Time type
        open: point.open,
        high: point.high,
        low: point.low,
        close: point.close,
        volume: point.volume || 0,
      }
    })

    // Create series based on chart mode
    let series: ISeriesApi<'Candlestick' | 'Line'>
    if (chartMode === 'candlestick') {
      series = chartRef.current.addCandlestickSeries({
        upColor: '#10b981',
        downColor: '#ef4444',
        borderVisible: false,
        wickUpColor: '#10b981',
        wickDownColor: '#ef4444',
      })
    } else {
      series = chartRef.current.addLineSeries({
        color: '#9c27b0',
        lineWidth: 2 as LineWidth,
        lineStyle: LineStyle.Solid,
        priceFormat: {
          type: 'price',
          precision: 2,
          minMove: 0.01,
        },
      })
    }

    seriesRef.current = series
    series.setData(chartData)

    // Add trade overlay markers if provided
    if (tradeOverlay) {
      const entryTime = Math.floor(new Date(tradeOverlay.entry_time).getTime() / 1000)
      const exitTime = tradeOverlay.exit_time
        ? Math.floor(new Date(tradeOverlay.exit_time).getTime() / 1000)
        : null

      // Build marker text with trade details
      const entryText = `Entry: ${tradeOverlay.side} @ $${tradeOverlay.entry_price.toFixed(2)}`
      const exitText = exitTime
        ? `Exit @ $${tradeOverlay.exit_price?.toFixed(2) || 'N/A'}${
            tradeOverlay.net_pnl !== null && tradeOverlay.net_pnl !== undefined
              ? ` (P&L: $${tradeOverlay.net_pnl >= 0 ? '+' : ''}${tradeOverlay.net_pnl.toFixed(2)})`
              : ''
          }`
        : ''

      // Entry marker
      const markers: any[] = [
        {
          time: entryTime,
          position: 'belowBar',
          color: tradeOverlay.side === 'LONG' ? '#10b981' : '#ef4444',
          shape: 'arrowUp',
          text: entryText,
        },
      ]

      if (exitTime) {
        markers.push({
          time: exitTime,
          position: 'aboveBar',
          color: tradeOverlay.side === 'LONG' ? '#ef4444' : '#10b981',
          shape: 'arrowDown',
          text: exitText,
        })
      }

      series.setMarkers(markers)
    }

    // Fit content
    chartRef.current.timeScale().fitContent()
  }, [data, chartMode, tradeOverlay, chartReady])

  if (isLoading) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height, minHeight: height }}>
        <CircularProgress />
      </Box>
    )
  }

  if (error) {
    return (
      <Alert severity="error" sx={{ m: 2 }}>
        Failed to load chart data: {error.message}
      </Alert>
    )
  }

  if (!data || data.data.length === 0) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height, minHeight: height }}>
        <Typography variant="body2" color="text.secondary">
          No price data available
        </Typography>
      </Box>
    )
  }

  return (
    <Box
      ref={chartContainerRef}
      sx={{
        width: '100%',
        height: height,
        minHeight: height,
        position: 'relative',
      }}
    />
  )
}

