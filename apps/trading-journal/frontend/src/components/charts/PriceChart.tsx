/**
 * Price chart component using TradingView Lightweight Charts.
 */

import { useEffect, useRef, useState } from 'react'
import { createChart, IChartApi, ISeriesApi, ColorType, LineStyle, LineWidth } from 'lightweight-charts'
import { Box, CircularProgress, Alert, Typography } from '@mui/material'
import { PriceDataResponse, TradeOverlayData, ChartMode, ChartColorConfig, ChartIndicatorConfig } from '../../types/charts'

interface PriceChartProps {
  data: PriceDataResponse | undefined
  isLoading: boolean
  error: Error | null
  chartMode?: ChartMode
  tradeOverlay?: TradeOverlayData | null
  height?: number
  colors?: ChartColorConfig
  indicators?: ChartIndicatorConfig
}

// Default color scheme (dark theme)
const DEFAULT_COLORS: ChartColorConfig = {
  background: '#1e1e1e',
  textColor: '#d1d5db',
  gridLines: '#2a2a2a',
  borderColor: '#2a2a2a',
  upColor: '#10b981',      // Green for up candles
  downColor: '#ef4444',    // Red for down candles
  wickUpColor: '#10b981',
  wickDownColor: '#ef4444',
  lineColor: '#9c27b0',    // Purple for line chart
  volumeColor: '#3b82f6',  // Blue for volume
  movingAverageColor: '#f59e0b',  // Amber for MA
  movingAverageColor2: '#8b5cf6', // Purple for MA2
}

// Default indicators
const DEFAULT_INDICATORS: ChartIndicatorConfig = {
  showSMA: false,
  smaPeriod: 20,
  showEMA: false,
  emaPeriod: 20,
  showVolume: false,
}

export default function PriceChart({
  data,
  isLoading,
  error,
  chartMode = 'candlestick',
  tradeOverlay,
  height = 500,
  colors = DEFAULT_COLORS,
  indicators = DEFAULT_INDICATORS,
}: PriceChartProps) {
  const chartContainerRef = useRef<HTMLDivElement>(null)
  const chartRef = useRef<IChartApi | null>(null)
  const seriesRef = useRef<ISeriesApi<'Candlestick' | 'Line'> | null>(null)
  const volumeSeriesRef = useRef<ISeriesApi<'Histogram'> | null>(null)
  const smaSeriesRef = useRef<ISeriesApi<'Line'> | null>(null)
  const emaSeriesRef = useRef<ISeriesApi<'Line'> | null>(null)
  const [chartReady, setChartReady] = useState(false)
  
  // Merge with defaults
  const chartColors = { ...DEFAULT_COLORS, ...colors }
  const chartIndicators = { ...DEFAULT_INDICATORS, ...indicators }

  useEffect(() => {
    // Wait for container ref to be attached
    const initChart = () => {
      if (!chartContainerRef.current) {
        // Retry after a short delay if ref not attached yet
        setTimeout(initChart, 50)
        return
      }

      const container = chartContainerRef.current
      let resizeHandler: (() => void) | null = null
      let timeoutId: ReturnType<typeof setTimeout> | null = null
      
      // Wait for container to have a width
      const createChartInstance = () => {
        const width = container.clientWidth
        if (width === 0) {
          // Retry after a short delay (max 20 attempts)
          timeoutId = setTimeout(createChartInstance, 100)
          return
        }

        console.log('Creating chart with dimensions:', { width, height })

        // Create chart with custom colors
        const chart = createChart(container, {
          layout: {
            background: { type: ColorType.Solid, color: chartColors.background || '#1e1e1e' },
            textColor: chartColors.textColor || '#d1d5db',
          },
          grid: {
            vertLines: { color: chartColors.gridLines || '#2a2a2a' },
            horzLines: { color: chartColors.gridLines || '#2a2a2a' },
          },
          width: width,
          height: height,
          timeScale: {
            timeVisible: true,
            secondsVisible: false,
          },
          rightPriceScale: {
            borderColor: chartColors.borderColor || '#2a2a2a',
          },
        })

        chartRef.current = chart
        console.log('Chart created successfully')

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

      // Start chart creation
      createChartInstance()

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
    }

    // Start initialization
    const cleanup = initChart()

    return () => {
      if (cleanup) cleanup()
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

    // Remove existing indicator series
    if (volumeSeriesRef.current) {
      chartRef.current.removeSeries(volumeSeriesRef.current)
      volumeSeriesRef.current = null
    }
    if (smaSeriesRef.current) {
      chartRef.current.removeSeries(smaSeriesRef.current)
      smaSeriesRef.current = null
    }
    if (emaSeriesRef.current) {
      chartRef.current.removeSeries(emaSeriesRef.current)
      emaSeriesRef.current = null
    }

    // Create series based on chart mode with custom colors
    let series: ISeriesApi<'Candlestick' | 'Line'>
    if (chartMode === 'candlestick') {
      series = chartRef.current.addCandlestickSeries({
        upColor: chartColors.upColor || '#10b981',
        downColor: chartColors.downColor || '#ef4444',
        borderVisible: false,
        wickUpColor: chartColors.wickUpColor || chartColors.upColor || '#10b981',
        wickDownColor: chartColors.wickDownColor || chartColors.downColor || '#ef4444',
      })
    } else {
      series = chartRef.current.addLineSeries({
        color: chartColors.lineColor || '#9c27b0',
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

    // Add volume indicator if enabled
    if (chartIndicators.showVolume && chartData.length > 0) {
      const volumeData = chartData.map(point => ({
        time: point.time,
        value: point.volume || 0,
        color: point.close >= (chartData.find(d => d.time === point.time)?.open || point.close)
          ? (chartColors.upColor || '#10b981') + '80' // Add transparency
          : (chartColors.downColor || '#ef4444') + '80',
      }))

      volumeSeriesRef.current = chartRef.current.addHistogramSeries({
        color: chartColors.volumeColor || '#3b82f6',
        priceFormat: {
          type: 'volume',
        },
        priceScaleId: 'volume',
        scaleMargins: {
          top: 0.8,
          bottom: 0,
        },
      })

      chartRef.current.priceScale('volume').applyOptions({
        scaleMargins: {
          top: 0.8,
          bottom: 0,
        },
      })

      volumeSeriesRef.current.setData(volumeData)
    }

    // Calculate and add Simple Moving Average (SMA) if enabled
    if (chartIndicators.showSMA && chartData.length >= (chartIndicators.smaPeriod || 20)) {
      const smaPeriod = chartIndicators.smaPeriod || 20
      const smaData: { time: any; value: number }[] = []

      for (let i = smaPeriod - 1; i < chartData.length; i++) {
        const sum = chartData.slice(i - smaPeriod + 1, i + 1).reduce((acc, point) => acc + point.close, 0)
        const sma = sum / smaPeriod
        smaData.push({
          time: chartData[i].time,
          value: sma,
        })
      }

      smaSeriesRef.current = chartRef.current.addLineSeries({
        color: chartColors.movingAverageColor || '#f59e0b',
        lineWidth: 2 as LineWidth,
        lineStyle: LineStyle.Solid,
        title: `SMA(${smaPeriod})`,
        priceFormat: {
          type: 'price',
          precision: 2,
          minMove: 0.01,
        },
      })

      smaSeriesRef.current.setData(smaData)
    }

    // Calculate and add Exponential Moving Average (EMA) if enabled
    if (chartIndicators.showEMA && chartData.length >= (chartIndicators.emaPeriod || 20)) {
      const emaPeriod = chartIndicators.emaPeriod || 20
      const multiplier = 2 / (emaPeriod + 1)
      const emaData: { time: any; value: number }[] = []

      // Start with SMA for first value
      let ema = chartData.slice(0, emaPeriod).reduce((acc, point) => acc + point.close, 0) / emaPeriod
      emaData.push({
        time: chartData[emaPeriod - 1].time,
        value: ema,
      })

      // Calculate EMA for remaining points
      for (let i = emaPeriod; i < chartData.length; i++) {
        ema = (chartData[i].close - ema) * multiplier + ema
        emaData.push({
          time: chartData[i].time,
          value: ema,
        })
      }

      emaSeriesRef.current = chartRef.current.addLineSeries({
        color: chartColors.movingAverageColor2 || '#8b5cf6',
        lineWidth: 2 as LineWidth,
        lineStyle: LineStyle.Solid,
        title: `EMA(${emaPeriod})`,
        priceFormat: {
          type: 'price',
          precision: 2,
          minMove: 0.01,
        },
      })

      emaSeriesRef.current.setData(emaData)
    }

    // Fit content
    try {
      chartRef.current.timeScale().fitContent()
    } catch (error) {
      console.error('Error fitting content:', error)
    }
  }, [data, chartMode, tradeOverlay, chartReady, colors, indicators])

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

