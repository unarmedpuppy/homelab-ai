/**
 * Dashboard page component.
 */

import { useState, useRef } from 'react'
import {
  Box,
  Grid,
  Typography,
  Button,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Alert,
  CircularProgress,
} from '@mui/material'
import { FileUpload, FileDownload } from '@mui/icons-material'
import { useDashboardStats, useRecentTrades } from '../hooks/useDashboard'
import { exportTrades, importTrades } from '../api/trades'
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

  const [importDialogOpen, setImportDialogOpen] = useState(false)
  const [importFile, setImportFile] = useState<File | null>(null)
  const [importing, setImporting] = useState(false)
  const [importResult, setImportResult] = useState<{ success: number; errors: string[] } | null>(null)
  const fileInputRef = useRef<HTMLInputElement>(null)

  const handleExport = async () => {
    try {
      const blob = await exportTrades()
      const url = window.URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = `trades_export_${new Date().toISOString().split('T')[0]}.csv`
      document.body.appendChild(a)
      a.click()
      window.URL.revokeObjectURL(url)
      document.body.removeChild(a)
    } catch (error) {
      console.error('Failed to export trades:', error)
      alert('Failed to export trades. Please try again.')
    }
  }

  const handleImportClick = () => {
    setImportDialogOpen(true)
    setImportResult(null)
    setImportFile(null)
  }

  const handleFileChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    if (event.target.files && event.target.files[0]) {
      setImportFile(event.target.files[0])
    }
  }

  const handleImportSubmit = async () => {
    if (!importFile) return

    setImporting(true)
    try {
      const result = await importTrades(importFile)
      setImportResult({
        success: result.success_count,
        errors: result.errors,
      })
      if (result.success_count > 0) {
        // Reload page to show new data after short delay
        setTimeout(() => window.location.reload(), 2000)
      }
    } catch (error) {
      console.error('Failed to import trades:', error)
      setImportResult({
        success: 0,
        errors: ['Failed to upload file. Please check the format and try again.'],
      })
    } finally {
      setImporting(false)
    }
  }

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
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: { xs: 2, sm: 3 } }}>
        <Typography variant="h4" component="h1">
          Dashboard
        </Typography>
        <Box sx={{ display: 'flex', gap: 1 }}>
          <Button
            variant="outlined"
            startIcon={<FileUpload />}
            onClick={handleImportClick}
          >
            Import
          </Button>
          <Button
            variant="outlined"
            startIcon={<FileDownload />}
            onClick={handleExport}
          >
            Export
          </Button>
        </Box>
      </Box>

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

      {/* Import Dialog */}
      <Dialog open={importDialogOpen} onClose={() => setImportDialogOpen(false)} maxWidth="sm" fullWidth>
        <DialogTitle>Import Trades</DialogTitle>
        <DialogContent>
          <Box sx={{ pt: 1, display: 'flex', flexDirection: 'column', gap: 2 }}>
            <Typography variant="body2" color="text.secondary">
              Upload a CSV file to import trades. The CSV should match the export format.
            </Typography>
            
            <Button
              variant="outlined"
              component="label"
              startIcon={<FileUpload />}
            >
              Select File
              <input
                type="file"
                hidden
                accept=".csv"
                onChange={handleFileChange}
                ref={fileInputRef}
              />
            </Button>
            
            {importFile && (
              <Typography variant="body2">
                Selected: {importFile.name}
              </Typography>
            )}

            {importResult && (
              <Box sx={{ mt: 2 }}>
                {importResult.success > 0 && (
                  <Alert severity="success" sx={{ mb: 1 }}>
                    Successfully imported {importResult.success} trades.
                  </Alert>
                )}
                {importResult.errors.length > 0 && (
                  <Alert severity="warning">
                    {importResult.errors.length} errors occurred:
                    <ul style={{ margin: '8px 0', paddingLeft: '20px' }}>
                      {importResult.errors.slice(0, 5).map((err, i) => (
                        <li key={i}>{err}</li>
                      ))}
                      {importResult.errors.length > 5 && (
                        <li>...and {importResult.errors.length - 5} more</li>
                      )}
                    </ul>
                  </Alert>
                )}
              </Box>
            )}
          </Box>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setImportDialogOpen(false)}>Close</Button>
          <Button
            variant="contained"
            onClick={handleImportSubmit}
            disabled={!importFile || importing}
            startIcon={importing ? <CircularProgress size={20} /> : null}
          >
            {importing ? 'Importing...' : 'Import'}
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  )
}
