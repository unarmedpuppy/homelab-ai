/**
 * Dashboard page component.
 */

import { Box, Grid, Typography } from '@mui/material'
import { useDashboardStats, useRecentTrades } from '../hooks/useDashboard'
import KPICard from '../components/dashboard/KPICard'
import RecentTrades from '../components/dashboard/RecentTrades'
import CumulativePnLChart from '../components/dashboard/CumulativePnLChart'
import DailyPnLChart from '../components/dashboard/DailyPnLChart'
import DrawdownChart from '../components/dashboard/DrawdownChart'
import LoadingSpinner from '../components/common/LoadingSpinner'
import ErrorAlert from '../components/common/ErrorAlert'

export default function Dashboard() {
  const { data: stats, isLoading: statsLoading, error: statsError } = useDashboardStats()
  const {
    data: recentTrades,
    isLoading: tradesLoading,
    error: tradesError,
  } = useRecentTrades(10)

  if (statsLoading) {
    return <LoadingSpinner message="Loading dashboard statistics..." />
  }

  if (statsError) {
    return (
      <ErrorAlert
        title="Failed to load dashboard"
        message={statsError.message || 'Failed to load dashboard statistics. Please try again.'}
        showRetry
        onRetry={() => window.location.reload()}
      />
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
    <Box>
      <Typography variant="h4" gutterBottom sx={{ mb: { xs: 2, sm: 3 } }}>
        Dashboard
      </Typography>

      {/* KPI Cards */}
      {stats && (
        <Grid container spacing={{ xs: 2, sm: 3 }} sx={{ mb: { xs: 3, sm: 4 } }}>
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
      <Box sx={{ mt: { xs: 3, sm: 4 } }}>
        <Typography variant="h5" gutterBottom sx={{ mb: { xs: 2, sm: 3 } }}>
          Performance Charts
        </Typography>
        <Grid container spacing={{ xs: 2, sm: 3 }}>
          <Grid item xs={12} md={6}>
            <CumulativePnLChart height={300} />
          </Grid>
          <Grid item xs={12} md={6}>
            <DailyPnLChart height={300} />
          </Grid>
          <Grid item xs={12}>
            <DrawdownChart height={300} />
          </Grid>
        </Grid>
      </Box>

      {/* Recent Trades */}
      <Box sx={{ mt: { xs: 3, sm: 4 } }}>
        <Typography variant="h5" gutterBottom sx={{ mb: { xs: 1.5, sm: 2 } }}>
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
