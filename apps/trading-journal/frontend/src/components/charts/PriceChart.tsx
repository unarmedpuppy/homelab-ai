/**
 * Price chart component using TradingView Lightweight Charts.
 */

import { useEffect, useRef, useState } from 'react'
import { createChart, IChartApi, ISeriesApi, ColorType, LineStyle, LineWidth } from 'lightweight-charts'
import { Box, Typography } from '@mui/material'
import LoadingSpinner from '../common/LoadingSpinner'
import ErrorAlert from '../common/ErrorAlert'
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
  showSMA20: false,
  showSMA200: false,
  showEMA9: false,
  showEMA21: false,
  showVolume: false,
  showRSI: false,
  rsiPeriod: 14,
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
  const sma20SeriesRef = useRef<ISeriesApi<'Line'> | null>(null)
  const sma200SeriesRef = useRef<ISeriesApi<'Line'> | null>(null)
  const ema9SeriesRef = useRef<ISeriesApi<'Line'> | null>(null)
  const ema21SeriesRef = useRef<ISeriesApi<'Line'> | null>(null)
  const rsiSeriesRef = useRef<ISeriesApi<'Line'> | null>(null)
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
                  horzLines: { 
                    color: chartColors.gridLines || '#2a2a2a',
                    style: LineStyle.Solid, // Solid grid lines, not dashed
                  },
                },
                width: width,
                height: height,
                timeScale: {
                  timeVisible: true,
                  secondsVisible: false,
                },
                rightPriceScale: {
                  borderColor: chartColors.borderColor || '#2a2a2a',
                  // Remove any horizontal price lines that might appear dashed
                  entireTextOnly: false,
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
    const dataLength = data?.data?.length || 0
    console.log('PriceChart useEffect triggered:', {
      hasChartRef: !!chartRef.current,
      chartReady,
      hasData: !!data,
      dataLength: dataLength,
      sma20Enabled: chartIndicators.showSMA20,
      sma200Enabled: chartIndicators.showSMA200,
      canShowSMA20: dataLength >= 20,
      canShowSMA200: dataLength >= 200,
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
    if (sma20SeriesRef.current) {
      chartRef.current.removeSeries(sma20SeriesRef.current)
      sma20SeriesRef.current = null
    }
    if (sma200SeriesRef.current) {
      chartRef.current.removeSeries(sma200SeriesRef.current)
      sma200SeriesRef.current = null
    }
    if (ema9SeriesRef.current) {
      chartRef.current.removeSeries(ema9SeriesRef.current)
      ema9SeriesRef.current = null
    }
    if (ema21SeriesRef.current) {
      chartRef.current.removeSeries(ema21SeriesRef.current)
      ema21SeriesRef.current = null
    }
    if (rsiSeriesRef.current) {
      chartRef.current.removeSeries(rsiSeriesRef.current)
      rsiSeriesRef.current = null
    }

    // Create series based on chart mode with custom colors (white/gray theme)
    let series: ISeriesApi<'Candlestick' | 'Line'>
    if (chartMode === 'candlestick') {
      series = chartRef.current.addCandlestickSeries({
        upColor: '#ffffff', // White for up candles
        downColor: '#808080', // Gray for down candles
        borderVisible: false,
        wickUpColor: '#ffffff', // White wicks for up candles
        wickDownColor: '#808080', // Gray wicks for down candles
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

    // Add volume indicator if enabled (white/gray theme)
    if (chartIndicators.showVolume && chartData.length > 0) {
      const volumeData = chartData.map((point, index) => {
        // Determine if volume is up or down based on price movement
        const prevPoint = index > 0 ? chartData[index - 1] : point
        const isUp = point.close >= prevPoint.close
        
        return {
          time: point.time,
          value: point.volume || 0,
          color: isUp ? '#ffffff' : '#808080', // White for up, gray for down
        }
      })

      volumeSeriesRef.current = chartRef.current.addHistogramSeries({
        priceFormat: {
          type: 'volume',
        },
        priceScaleId: 'volume',
      })

      // Set scale margins on the price scale
      chartRef.current.priceScale('volume').applyOptions({
        scaleMargins: {
          top: 0.8,
          bottom: 0,
        },
      })

      volumeSeriesRef.current.setData(volumeData)
    }

    // Calculate and add SMA 20 if enabled
    // Indicators are calculated based on the number of candles, which aligns with the chart timeframe
    // SMA 20 on 1h chart = 20 hours, SMA 20 on 1d chart = 20 days, etc.
    if (chartIndicators.showSMA20) {
      const sma20Period = 20
      // Use adaptive period if we don't have enough data
      const actualPeriod = Math.min(sma20Period, Math.max(2, Math.floor(chartData.length / 2)))
      
      if (chartData.length >= actualPeriod) {
        const sma20Data: { time: any; value: number }[] = []

        for (let i = actualPeriod - 1; i < chartData.length; i++) {
          const sum = chartData.slice(i - actualPeriod + 1, i + 1).reduce((acc, point) => acc + point.close, 0)
          const sma = sum / actualPeriod
          sma20Data.push({
            time: chartData[i].time,
            value: sma,
          })
        }

        if (sma20Data.length > 0) {
          sma20SeriesRef.current = chartRef.current.addLineSeries({
            color: '#ffffff', // White
            lineWidth: 1 as LineWidth,
            lineStyle: LineStyle.Solid,
            // No title to avoid blocking view
            priceFormat: {
              type: 'price',
              precision: 2,
              minMove: 0.01,
            },
            // Ensure it's just a line path, no other visual elements
            lastValueVisible: false,
            priceLineVisible: false,
          })

          sma20SeriesRef.current.setData(sma20Data)
          console.log(`SMA 20 added with period ${actualPeriod}, ${sma20Data.length} points`)
        }
      }
    }

    // Calculate and add SMA 200 if enabled
    // Only show if we have enough data for the full 200 period
    if (chartIndicators.showSMA200 && chartData.length >= 200) {
      const sma200Period = 200
      const sma200Data: { time: any; value: number }[] = []

      for (let i = 199; i < chartData.length; i++) {
        const sum = chartData.slice(i - 199, i + 1).reduce((acc, point) => acc + point.close, 0)
        const sma = sum / sma200Period
        sma200Data.push({
          time: chartData[i].time,
          value: sma,
        })
      }

      if (sma200Data.length > 0) {
        sma200SeriesRef.current = chartRef.current.addLineSeries({
          color: '#808080', // Gray
          lineWidth: 1 as LineWidth,
          lineStyle: LineStyle.Dashed, // Dashed line for SMA 200
          // No title to avoid blocking view
          priceFormat: {
            type: 'price',
            precision: 2,
            minMove: 0.01,
          },
          // Ensure it's just a line path, no other visual elements
          lastValueVisible: false,
          priceLineVisible: false,
        })

        sma200SeriesRef.current.setData(sma200Data)
        console.log(`SMA 200 added with period ${sma200Period}, ${sma200Data.length} points`)
      }
    }

    // Calculate and add EMA 9 if enabled
    if (chartIndicators.showEMA9) {
      const ema9Period = 9
      // Use adaptive period if we don't have enough data
      const actualPeriod = Math.min(ema9Period, Math.max(2, Math.floor(chartData.length / 2)))
      
      if (chartData.length >= actualPeriod) {
        const multiplier = 2 / (actualPeriod + 1)
        const ema9Data: { time: any; value: number }[] = []

        // Start with SMA for first value
        let ema = chartData.slice(0, actualPeriod).reduce((acc, point) => acc + point.close, 0) / actualPeriod
        ema9Data.push({
          time: chartData[actualPeriod - 1].time,
          value: ema,
        })

        // Calculate EMA for remaining points
        for (let i = actualPeriod; i < chartData.length; i++) {
          ema = (chartData[i].close - ema) * multiplier + ema
          ema9Data.push({
            time: chartData[i].time,
            value: ema,
          })
        }

        if (ema9Data.length > 0) {
          ema9SeriesRef.current = chartRef.current.addLineSeries({
            color: '#ffffff', // White
            lineWidth: 1 as LineWidth,
            lineStyle: LineStyle.Solid,
            // No title to avoid blocking view
            priceFormat: {
              type: 'price',
              precision: 2,
              minMove: 0.01,
            },
            // Ensure it's just a line path, no other visual elements
            lastValueVisible: false,
            priceLineVisible: false,
          })

          ema9SeriesRef.current.setData(ema9Data)
          console.log(`EMA 9 added with period ${actualPeriod}, ${ema9Data.length} points`)
        }
      }
    }

    // Calculate and add EMA 21 if enabled
    if (chartIndicators.showEMA21) {
      const ema21Period = 21
      // Use adaptive period if we don't have enough data
      const actualPeriod = Math.min(ema21Period, Math.max(2, Math.floor(chartData.length / 2)))
      
      if (chartData.length >= actualPeriod) {
        const multiplier = 2 / (actualPeriod + 1)
        const ema21Data: { time: any; value: number }[] = []

        // Start with SMA for first value
        let ema = chartData.slice(0, actualPeriod).reduce((acc, point) => acc + point.close, 0) / actualPeriod
        ema21Data.push({
          time: chartData[actualPeriod - 1].time,
          value: ema,
        })

        // Calculate EMA for remaining points
        for (let i = actualPeriod; i < chartData.length; i++) {
          ema = (chartData[i].close - ema) * multiplier + ema
          ema21Data.push({
            time: chartData[i].time,
            value: ema,
          })
        }

        if (ema21Data.length > 0) {
          ema21SeriesRef.current = chartRef.current.addLineSeries({
            color: '#808080', // Gray
            lineWidth: 1 as LineWidth,
            lineStyle: LineStyle.Solid,
            // No title to avoid blocking view
            priceFormat: {
              type: 'price',
              precision: 2,
              minMove: 0.01,
            },
            // Ensure it's just a line path, no other visual elements
            lastValueVisible: false,
            priceLineVisible: false,
          })

          ema21SeriesRef.current.setData(ema21Data)
          console.log(`EMA 21 added with period ${actualPeriod}, ${ema21Data.length} points`)
        }
      }
    }

    // Calculate and add RSI if enabled
    if (chartIndicators.showRSI && chartData.length >= (chartIndicators.rsiPeriod || 14) + 1) {
      const rsiPeriod = chartIndicators.rsiPeriod || 14
      const rsiData: { time: any; value: number }[] = []

      // Calculate RSI
      for (let i = rsiPeriod; i < chartData.length; i++) {
        let gains = 0
        let losses = 0

        // Calculate average gain and loss over the period
        for (let j = i - rsiPeriod + 1; j <= i; j++) {
          const change = chartData[j].close - chartData[j - 1].close
          if (change > 0) {
            gains += change
          } else {
            losses += Math.abs(change)
          }
        }

        const avgGain = gains / rsiPeriod
        const avgLoss = losses / rsiPeriod

        if (avgLoss === 0) {
          rsiData.push({ time: chartData[i].time, value: 100 })
        } else {
          const rs = avgGain / avgLoss
          const rsi = 100 - (100 / (1 + rs))
          rsiData.push({ time: chartData[i].time, value: rsi })
        }
      }

      rsiSeriesRef.current = chartRef.current.addLineSeries({
        color: '#ffffff', // White
        lineWidth: 1 as LineWidth,
        lineStyle: LineStyle.Solid,
        // No title to avoid blocking view
        priceFormat: {
          type: 'price',
          precision: 2,
          minMove: 0.01,
        },
        priceScaleId: 'rsi',
      })

      // Set RSI scale to 0-100 range
      chartRef.current.priceScale('rsi').applyOptions({
        scaleMargins: {
          top: 0.1,
          bottom: 0.1,
        },
      })

      rsiSeriesRef.current.setData(rsiData)
    }

    // Fit content
    try {
      chartRef.current.timeScale().fitContent()
    } catch (error) {
      console.error('Error fitting content:', error)
    }
  }, [data, chartMode, tradeOverlay, chartReady, colors, indicators])

  if (isLoading) {
    return <LoadingSpinner message="Loading chart data..." minHeight={height} />
  }

  if (error) {
    return (
      <ErrorAlert
        title="Failed to load chart"
        message={error.message || 'Failed to load chart data. Please try again.'}
        showRetry
        onRetry={() => window.location.reload()}
      />
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
        '& canvas': {
          touchAction: 'pan-x pan-y', // Enable touch scrolling on charts
        },
      }}
    />
  )
}

