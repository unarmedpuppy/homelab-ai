/**
 * Dashboard page component.
 */

import { Box, Grid, Typography, CircularProgress, Alert } from '@mui/material'
import { useDashboardStats, useRecentTrades } from '../hooks/useDashboard'
import KPICard from '../components/dashboard/KPICard'
import RecentTrades from '../components/dashboard/RecentTrades'
import CumulativePnLChart from '../components/dashboard/CumulativePnLChart'
import DailyPnLChart from '../components/dashboard/DailyPnLChart'
import DrawdownChart from '../components/dashboard/DrawdownChart'

export default function Dashboard() {
  const { data: stats, isLoading: statsLoading, error: statsError } = useDashboardStats()
  const {
    data: recentTrades,
    isLoading: tradesLoading,
    error: tradesError,
  } = useRecentTrades(10)

  if (statsLoading) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', minHeight: '400px' }}>
        <CircularProgress />
      </Box>
    )
  }

  if (statsError) {
    return (
      <Alert severity="error" sx={{ m: 2 }}>
        Failed to load dashboard statistics: {statsError.message}
      </Alert>
    )
  }

  const formatPercentage = (value: number | null): string => {
    if (value === null) return 'N/A'
    return `${value.toFixed(2)}%`
  }

  const getPnlTrend = (pnl: number | null): 'up' | 'down' | 'neutral' => {
    if (pnl === null) return 'neutral'
    if (pnl > 0) return 'up'
    if (pnl < 0) return 'down'
    return 'neutral'
  }

  return (
    <Box sx={{ p: 3 }}>
      <Typography variant="h4" gutterBottom sx={{ mb: 3 }}>
        Dashboard
      </Typography>

      {/* KPI Cards */}
      {stats && (
        <Grid container spacing={3} sx={{ mb: 4 }}>
          <Grid item xs={12} sm={6} md={3}>
            <KPICard
              title="Net P&L"
              value={stats.net_pnl}
              trend={getPnlTrend(stats.net_pnl)}
              color={stats.net_pnl >= 0 ? 'success' : 'error'}
            />
          </Grid>
          <Grid item xs={12} sm={6} md={3}>
            <KPICard
              title="Gross P&L"
              value={stats.gross_pnl}
              trend={getPnlTrend(stats.gross_pnl)}
              color={stats.gross_pnl >= 0 ? 'success' : 'error'}
            />
          </Grid>
          <Grid item xs={12} sm={6} md={3}>
            <KPICard
              title="Win Rate"
              value={stats.win_rate !== null ? formatPercentage(stats.win_rate) : null}
              subtitle={`${stats.winners}W / ${stats.losers}L`}
              color="info"
            />
          </Grid>
          <Grid item xs={12} sm={6} md={3}>
            <KPICard
              title="Total Trades"
              value={stats.total_trades}
              color="primary"
            />
          </Grid>
          <Grid item xs={12} sm={6} md={3}>
            <KPICard
              title="Profit Factor"
              value={stats.profit_factor !== null ? stats.profit_factor.toFixed(2) : null}
              color={stats.profit_factor && stats.profit_factor >= 1 ? 'success' : 'error'}
            />
          </Grid>
          <Grid item xs={12} sm={6} md={3}>
            <KPICard
              title="Day Win Rate"
              value={stats.day_win_rate !== null ? formatPercentage(stats.day_win_rate) : null}
              color="info"
            />
          </Grid>
          <Grid item xs={12} sm={6} md={3}>
            <KPICard
              title="Avg Win"
              value={stats.avg_win ?? null}
              color="success"
            />
          </Grid>
          <Grid item xs={12} sm={6} md={3}>
            <KPICard
              title="Avg Loss"
              value={stats.avg_loss ?? null}
              color="error"
            />
          </Grid>
          <Grid item xs={12} sm={6} md={3}>
            <KPICard
              title="Max Drawdown"
              value={stats.max_drawdown !== null ? formatPercentage(stats.max_drawdown) : null}
              color="error"
            />
          </Grid>
          <Grid item xs={12} sm={6} md={3}>
            <KPICard
              title="Zella Score"
              value={stats.zella_score !== null ? stats.zella_score.toFixed(1) : null}
              subtitle="Composite metric (0-100)"
              color="primary"
            />
          </Grid>
        </Grid>
      )}

      {/* Charts Section */}
      <Box sx={{ mt: 4 }}>
        <Typography variant="h5" gutterBottom sx={{ mb: 3 }}>
          Performance Charts
        </Typography>
        <Grid container spacing={3}>
          <Grid item xs={12} md={6}>
            <CumulativePnLChart height={350} />
          </Grid>
          <Grid item xs={12} md={6}>
            <DailyPnLChart height={350} />
          </Grid>
          <Grid item xs={12}>
            <DrawdownChart height={350} />
          </Grid>
        </Grid>
      </Box>

      {/* Recent Trades */}
      <Box sx={{ mt: 4 }}>
        <Typography variant="h5" gutterBottom sx={{ mb: 2 }}>
          Recent Trades
        </Typography>
        <RecentTrades
          trades={recentTrades}
          isLoading={tradesLoading}
          error={tradesError as Error | null}
        />
      </Box>
    </Box>
  )
}
