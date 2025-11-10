/**
 * KPI Card component for displaying dashboard metrics.
 */

import { Card, CardContent, Typography, Box } from '@mui/material'
import { TrendingUp, TrendingDown } from '@mui/icons-material'

interface KPICardProps {
  title: string
  value: string | number | null
  subtitle?: string
  trend?: 'up' | 'down' | 'neutral'
  color?: 'primary' | 'success' | 'error' | 'warning' | 'info'
}

export default function KPICard({
  title,
  value,
  subtitle,
  trend,
  color = 'primary',
}: KPICardProps) {
  const formatValue = (val: string | number | null): string => {
    if (val === null || val === undefined) return 'N/A'
    if (typeof val === 'number') {
      // Format numbers with appropriate precision
      if (Math.abs(val) >= 1000000) {
        return `$${(val / 1000000).toFixed(2)}M`
      } else if (Math.abs(val) >= 1000) {
        return `$${(val / 1000).toFixed(2)}K`
      } else if (val % 1 === 0) {
        return `$${val.toFixed(0)}`
      } else {
        return `$${val.toFixed(2)}`
      }
    }
    return String(val)
  }

  const getColor = () => {
    switch (color) {
      case 'success':
        return '#10b981'
      case 'error':
        return '#ef4444'
      case 'warning':
        return '#f59e0b'
      case 'info':
        return '#3b82f6'
      default:
        return '#9c27b0'
    }
  }

  return (
    <Card sx={{ height: '100%' }}>
      <CardContent>
        <Typography variant="body2" color="text.secondary" gutterBottom>
          {title}
        </Typography>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mt: 1 }}>
          <Typography
            variant="h4"
            component="div"
            sx={{
              color: getColor(),
              fontWeight: 'bold',
            }}
          >
            {formatValue(value)}
          </Typography>
          {trend === 'up' && (
            <TrendingUp sx={{ color: '#10b981', fontSize: 24 }} />
          )}
          {trend === 'down' && (
            <TrendingDown sx={{ color: '#ef4444', fontSize: 24 }} />
          )}
        </Box>
        {subtitle && (
          <Typography variant="caption" color="text.secondary" sx={{ mt: 1, display: 'block' }}>
            {subtitle}
          </Typography>
        )}
      </CardContent>
    </Card>
  )
}

