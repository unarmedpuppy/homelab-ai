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

    const container = chartContainerRef.current
    let resizeHandler: (() => void) | null = null
    let timeoutId: ReturnType<typeof setTimeout> | null = null
    
    // Wait for container to have a width
    const initChart = () => {
      const width = container.clientWidth
      if (width === 0) {
        // Retry after a short delay (max 10 attempts)
        timeoutId = setTimeout(initChart, 100)
        return
      }

      // Create chart
      const chart = createChart(container, {
        layout: {
          background: { type: ColorType.Solid, color: '#1e1e1e' },
          textColor: '#d1d5db',
        },
        grid: {
          vertLines: { color: '#2a2a2a' },
          horzLines: { color: '#2a2a2a' },
        },
        width: width,
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
      resizeHandler = () => {
        if (container && chart) {
          const newWidth = container.clientWidth || width
          chart.applyOptions({ width: newWidth })
        }
      }

      window.addEventListener('resize', resizeHandler)
      setChartReady(true)
    }

    // Start initialization
    initChart()

    return () => {
      if (timeoutId) {
        clearTimeout(timeoutId)
      }
      if (resizeHandler) {
        window.removeEventListener('resize', resizeHandler)
      }
      if (chartRef.current) {
        chartRef.current.remove()
        chartRef.current = null
        seriesRef.current = null
      }
    }
  }, [height])

  useEffect(() => {
    console.log('PriceChart useEffect triggered:', {
      hasChartRef: !!chartRef.current,
      chartReady,
      hasData: !!data,
      dataLength: data?.data?.length || 0
    })

    if (!chartRef.current || !chartReady || !data) {
      console.log('PriceChart: Early return - missing requirements')
      return
    }

    // Remove existing series
    if (seriesRef.current) {
      chartRef.current.removeSeries(seriesRef.current)
      seriesRef.current = null
    }

    // Check if we have data
    if (!data.data || data.data.length === 0) {
      console.warn('No chart data available - data.data is empty or missing')
      return
    }

    // Prepare data - convert timestamps to unix time (seconds since epoch)
    const chartData = data.data.map((point) => {
      const timestamp = new Date(point.timestamp)
      if (isNaN(timestamp.getTime())) {
        console.error('Invalid timestamp:', point.timestamp)
        return null
      }
      const unixTime = Math.floor(timestamp.getTime() / 1000)
      return {
        time: unixTime as any, // lightweight-charts expects Time type
        open: Number(point.open),
        high: Number(point.high),
        low: Number(point.low),
        close: Number(point.close),
        volume: point.volume ? Number(point.volume) : 0,
      }
    }).filter((item): item is NonNullable<typeof item> => item !== null)

    if (chartData.length === 0) {
      console.warn('No valid chart data after processing')
      return
    }

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
    
    try {
      series.setData(chartData)
      console.log(`Chart data set: ${chartData.length} points`)
    } catch (error) {
      console.error('Error setting chart data:', error)
      return
    }

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
    try {
      chartRef.current.timeScale().fitContent()
    } catch (error) {
      console.error('Error fitting content:', error)
    }
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

  if (!data) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height, minHeight: height }}>
        <Typography variant="body2" color="text.secondary">
          No price data available
        </Typography>
      </Box>
    )
  }

  if (data.data && data.data.length === 0) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height, minHeight: height }}>
        <Typography variant="body2" color="text.secondary">
          No price data available for this ticker/timeframe. The data may still be loading, or the ticker may not be available.
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
        display: 'block', // Ensure it's a block element
      }}
    />
  )
}

