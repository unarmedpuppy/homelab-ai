/**
 * Daily Journal page component.
 */

import { useState, useEffect } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import {
  Box,
  Typography,
  Paper,
  Grid,
  Card,
  CardContent,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  TextField,
  Button,
  IconButton,
  Chip,
  useTheme,
  Tooltip,
  MenuItem,
} from '@mui/material'
import {
  ArrowBack,
  Save,
  Delete,
  TrendingUp,
  TrendingDown,
  Assessment,
  ShowChart,
} from '@mui/icons-material'
import { format, parseISO, startOfDay } from 'date-fns'
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from 'recharts'
import {
  useDailyJournal,
  useCreateOrUpdateDailyNotes,
  useDeleteDailyNotes,
} from '../hooks/useDaily'
import LoadingSpinner from '../components/common/LoadingSpinner'
import ErrorAlert from '../components/common/ErrorAlert'

export default function DailyJournal() {
  const theme = useTheme()
  const navigate = useNavigate()
  const { date } = useParams<{ date: string }>()
  
  const [notes, setNotes] = useState('')
  const [isEditing, setIsEditing] = useState(false)
  const [tickerFilter, setTickerFilter] = useState('')
  const [playbookFilter, setPlaybookFilter] = useState('')
  const [typeFilter, setTypeFilter] = useState('')

  const { data: journal, isLoading, error } = useDailyJournal(date || '')
  const createOrUpdateNotes = useCreateOrUpdateDailyNotes()
  const deleteNotes = useDeleteDailyNotes()

  // Update notes when journal data loads
  useEffect(() => {
    if (journal?.notes !== undefined && !isEditing) {
      setNotes(journal.notes || '')
    }
  }, [journal?.notes, isEditing])

  const handleSaveNotes = async () => {
    if (!date) return
    
    try {
      await createOrUpdateNotes.mutateAsync({
        date,
        noteData: { notes },
      })
      setIsEditing(false)
    } catch (error) {
      console.error('Failed to save notes:', error)
    }
  }

  const handleDeleteNotes = async () => {
    if (!date) return
    
    if (window.confirm('Are you sure you want to delete these notes?')) {
      try {
        await deleteNotes.mutateAsync(date)
        setNotes('')
        setIsEditing(false)
      } catch (error) {
        console.error('Failed to delete notes:', error)
      }
    }
  }

  const formatCurrency = (value: number): string => {
    if (value === 0) return '$0'
    if (Math.abs(value) >= 1000000) {
      return `$${(value / 1000000).toFixed(2)}M`
    } else if (Math.abs(value) >= 1000) {
      return `$${(value / 1000).toFixed(2)}K`
    }
    return `$${value.toFixed(2)}`
  }

  const formatPnl = (pnl: number | null | undefined): string => {
    if (pnl === null || pnl === undefined) return 'N/A'
    return formatCurrency(pnl)
  }

  const getPnlColor = (pnl: number | null | undefined): 'success' | 'error' | 'default' => {
    if (pnl === null || pnl === undefined) return 'default'
    return pnl >= 0 ? 'success' : 'error'
  }

  if (isLoading) {
    return <LoadingSpinner message="Loading daily journal..." />
  }

  if (error) {
    return (
      <ErrorAlert
        title="Failed to load daily journal"
        message={error.message || 'Failed to load daily journal data. Please try again.'}
        showRetry
        onRetry={() => window.location.reload()}
      />
    )
  }

  if (!journal || !date) {
    return (
      <ErrorAlert
        title="No data found"
        message="No data found for this date. Please select a different date."
        severity="warning"
      />
    )
  }

  const journalDate = parseISO(date)

  return (
    <Box>
      {/* Header */}
      <Box
        sx={{
          display: 'flex',
          alignItems: 'center',
          gap: { xs: 1, sm: 2 },
          mb: { xs: 2, sm: 3 },
          flexWrap: 'wrap',
        }}
      >
        <IconButton onClick={() => navigate('/calendar')} color="primary">
          <ArrowBack />
        </IconButton>
        <Typography variant="h4" component="h1">
          {format(journalDate, 'MMMM d, yyyy')}
        </Typography>
        <Chip
          label={formatCurrency(journal.net_pnl)}
          color={getPnlColor(journal.net_pnl)}
          sx={{ fontWeight: 'bold', fontSize: '1rem' }}
        />
      </Box>

      {/* Summary Cards */}
      <Grid container spacing={{ xs: 1.5, sm: 2 }} sx={{ mb: { xs: 2, sm: 3 } }}>
        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                <Assessment color="primary" />
                <Typography variant="body2" color="text.secondary">
                  Total Trades
                </Typography>
              </Box>
              <Typography variant="h5" sx={{ mt: 1, fontWeight: 'bold' }}>
                {journal.summary.total_trades}
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                <TrendingUp color="success" />
                <Typography variant="body2" color="text.secondary">
                  Winners
                </Typography>
              </Box>
              <Typography
                variant="h5"
                sx={{ mt: 1, fontWeight: 'bold', color: theme.palette.success.main }}
              >
                {journal.summary.winners}
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                <TrendingDown color="error" />
                <Typography variant="body2" color="text.secondary">
                  Losers
                </Typography>
              </Box>
              <Typography
                variant="h5"
                sx={{ mt: 1, fontWeight: 'bold', color: theme.palette.error.main }}
              >
                {journal.summary.losers}
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                <Assessment color="primary" />
                <Typography variant="body2" color="text.secondary">
                  Win Rate
                </Typography>
              </Box>
              <Typography variant="h5" sx={{ mt: 1, fontWeight: 'bold' }}>
                {journal.summary.winrate !== null
                  ? `${journal.summary.winrate.toFixed(1)}%`
                  : 'N/A'}
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Typography variant="body2" color="text.secondary">
                Gross P&L
              </Typography>
              <Typography
                variant="h6"
                sx={{
                  mt: 1,
                  fontWeight: 'bold',
                  color:
                    journal.summary.gross_pnl >= 0
                      ? theme.palette.success.main
                      : theme.palette.error.main,
                }}
              >
                {formatCurrency(journal.summary.gross_pnl)}
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Typography variant="body2" color="text.secondary">
                Commissions
              </Typography>
              <Typography variant="h6" sx={{ mt: 1, fontWeight: 'bold' }}>
                {formatCurrency(journal.summary.commissions)}
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Typography variant="body2" color="text.secondary">
                Profit Factor
              </Typography>
              <Typography
                variant="h6"
                sx={{
                  mt: 1,
                  fontWeight: 'bold',
                  color:
                    journal.summary.profit_factor && journal.summary.profit_factor >= 1
                      ? theme.palette.success.main
                      : theme.palette.error.main,
                }}
              >
                {journal.summary.profit_factor !== null
                  ? journal.summary.profit_factor.toFixed(2)
                  : 'N/A'}
              </Typography>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* P&L Progression Chart */}
      {journal.trades.length > 0 && (
        <Paper sx={{ p: { xs: 1.5, sm: 2 }, mb: { xs: 2, sm: 3 } }}>
          <Typography variant="h6" gutterBottom>
            P&L Progression
          </Typography>
          {(() => {
            // Calculate cumulative P&L throughout the day
            const dayStart = startOfDay(parseISO(date || ''))
            const chartData: Array<{ time: string; cumulativePnl: number }> = []
            let cumulativePnl = 0

            // Sort trades by entry time
            const sortedTrades = [...journal.trades].sort((a, b) => {
              const aTime = a.entry_time ? parseISO(a.entry_time).getTime() : 0
              const bTime = b.entry_time ? parseISO(b.entry_time).getTime() : 0
              return aTime - bTime
            })

            // Add initial point at start of day
            chartData.push({
              time: format(dayStart, 'HH:mm'),
              cumulativePnl: 0,
            })

            // Process each trade
            sortedTrades.forEach((trade) => {
              if (trade.entry_time) {
                const entryTime = parseISO(trade.entry_time)
                // Add point at entry (P&L doesn't change yet)
                chartData.push({
                  time: format(entryTime, 'HH:mm'),
                  cumulativePnl: cumulativePnl,
                })
              }

              // If trade is closed, add P&L at exit time
              if (trade.exit_time && trade.net_pnl !== null && trade.net_pnl !== undefined) {
                const exitTime = parseISO(trade.exit_time)
                cumulativePnl += trade.net_pnl
                chartData.push({
                  time: format(exitTime, 'HH:mm'),
                  cumulativePnl: cumulativePnl,
                })
              }
            })

            // If no trades have exited yet, show current cumulative
            if (chartData.length === 1 && sortedTrades.length > 0) {
              chartData.push({
                time: format(new Date(), 'HH:mm'),
                cumulativePnl: cumulativePnl,
              })
            }

            return (
              <ResponsiveContainer width="100%" height={250}>
                <LineChart data={chartData} margin={{ top: 5, right: 20, left: 10, bottom: 5 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#2a2a2a" />
                  <XAxis
                    dataKey="time"
                    stroke="#d1d5db"
                    style={{ fontSize: '12px' }}
                    tick={{ fill: '#d1d5db' }}
                  />
                  <YAxis
                    stroke="#d1d5db"
                    style={{ fontSize: '12px' }}
                    tick={{ fill: '#d1d5db' }}
                    tickFormatter={(value) => `$${value.toFixed(0)}`}
                  />
                  <Tooltip
                    contentStyle={{
                      backgroundColor: '#1e1e1e',
                      border: '1px solid #2a2a2a',
                      borderRadius: '4px',
                      color: '#d1d5db',
                    }}
                    formatter={(value: number) => [formatCurrency(value), 'Cumulative P&L']}
                  />
                  <Line
                    type="monotone"
                    dataKey="cumulativePnl"
                    stroke={cumulativePnl >= 0 ? theme.palette.success.main : theme.palette.error.main}
                    strokeWidth={2}
                    dot={{ fill: cumulativePnl >= 0 ? theme.palette.success.main : theme.palette.error.main, r: 4 }}
                    activeDot={{ r: 6 }}
                  />
                </LineChart>
              </ResponsiveContainer>
            )
          })()}
        </Paper>
      )}

      {/* Trades Table */}
      <Paper sx={{ p: { xs: 1.5, sm: 2 }, mb: { xs: 2, sm: 3 } }}>
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
          <Typography variant="h6">Trades</Typography>
          <Box sx={{ display: 'flex', gap: 1, flexWrap: 'wrap' }}>
            <TextField
              size="small"
              label="Filter by ticker"
              value={tickerFilter}
              onChange={(e) => setTickerFilter(e.target.value)}
              sx={{ minWidth: 150 }}
            />
            <TextField
              size="small"
              select
              label="Filter by playbook"
              value={playbookFilter}
              onChange={(e) => setPlaybookFilter(e.target.value)}
              sx={{ minWidth: 150 }}
            >
              <MenuItem value="">All</MenuItem>
              {Array.from(new Set(journal.trades.map((t) => t.playbook).filter(Boolean))).map(
                (pb) => (
                  <MenuItem key={pb} value={pb}>
                    {pb}
                  </MenuItem>
                )
              )}
            </TextField>
            <TextField
              size="small"
              select
              label="Filter by type"
              value={typeFilter}
              onChange={(e) => setTypeFilter(e.target.value)}
              sx={{ minWidth: 150 }}
            >
              <MenuItem value="">All</MenuItem>
              <MenuItem value="STOCK">Stock</MenuItem>
              <MenuItem value="OPTION">Option</MenuItem>
              <MenuItem value="CRYPTO_SPOT">Crypto Spot</MenuItem>
              <MenuItem value="CRYPTO_PERP">Crypto Perp</MenuItem>
              <MenuItem value="PREDICTION_MARKET">Prediction Market</MenuItem>
            </TextField>
          </Box>
        </Box>
        {(() => {
          // Filter trades
          const filteredTrades = journal.trades.filter((trade) => {
            if (tickerFilter && !trade.ticker.toLowerCase().includes(tickerFilter.toLowerCase())) {
              return false
            }
            if (playbookFilter && trade.playbook !== playbookFilter) {
              return false
            }
            if (typeFilter && trade.trade_type !== typeFilter) {
              return false
            }
            return true
          })

          return filteredTrades.length === 0 ? (
            <Typography variant="body2" color="text.secondary" sx={{ py: 2 }}>
              {journal.trades.length === 0
                ? 'No trades for this day'
                : 'No trades match the selected filters'}
            </Typography>
          ) : (
            <TableContainer sx={{ maxWidth: '100%', overflowX: 'auto' }}>
              <Table size="small" sx={{ minWidth: 800 }}>
                <TableHead>
                  <TableRow>
                    <TableCell>Ticker</TableCell>
                    <TableCell>Type</TableCell>
                    <TableCell>Side</TableCell>
                    <TableCell>Entry Time</TableCell>
                    <TableCell>Exit Time</TableCell>
                    <TableCell>Playbook</TableCell>
                    <TableCell align="right">P&L</TableCell>
                    <TableCell align="right">ROI</TableCell>
                    <TableCell align="right">R-Multiple</TableCell>
                    <TableCell align="center">Chart</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {filteredTrades.map((trade) => (
                    <TableRow
                      key={trade.id}
                      hover
                      sx={{ cursor: 'pointer' }}
                      onClick={() => {
                        // TODO: Navigate to trade edit/view page
                        console.log('View/edit trade:', trade.id)
                      }}
                    >
                    <TableCell>
                      <Typography variant="body2" fontWeight="bold">
                        {trade.ticker}
                      </Typography>
                    </TableCell>
                    <TableCell>
                      <Chip label={trade.trade_type} size="small" variant="outlined" />
                    </TableCell>
                    <TableCell>
                      <Chip
                        label={trade.side}
                        size="small"
                        color={trade.side === 'LONG' ? 'primary' : 'secondary'}
                      />
                    </TableCell>
                    <TableCell>
                      <Typography variant="body2">
                        {trade.entry_time
                          ? format(parseISO(trade.entry_time), 'HH:mm:ss')
                          : 'N/A'}
                      </Typography>
                    </TableCell>
                    <TableCell>
                      <Typography variant="body2">
                        {trade.exit_time
                          ? format(parseISO(trade.exit_time), 'HH:mm:ss')
                          : 'N/A'}
                      </Typography>
                    </TableCell>
                    <TableCell>
                      {trade.playbook ? (
                        <Chip label={trade.playbook} size="small" variant="outlined" />
                      ) : (
                        <Typography variant="body2" color="text.secondary">
                          -
                        </Typography>
                      )}
                    </TableCell>
                    <TableCell align="right">
                      <Typography
                        variant="body2"
                        fontWeight="bold"
                        color={
                          getPnlColor(trade.net_pnl) === 'success'
                            ? 'success.main'
                            : 'error.main'
                        }
                      >
                        {formatPnl(trade.net_pnl)}
                      </Typography>
                    </TableCell>
                    <TableCell align="right">
                      <Typography variant="body2">
                        {trade.net_roi !== null && trade.net_roi !== undefined
                          ? `${trade.net_roi.toFixed(2)}%`
                          : 'N/A'}
                      </Typography>
                    </TableCell>
                    <TableCell align="right">
                      <Typography variant="body2">
                        {trade.realized_r_multiple !== null && trade.realized_r_multiple !== undefined
                          ? trade.realized_r_multiple.toFixed(2)
                          : 'N/A'}
                      </Typography>
                    </TableCell>
                    <TableCell align="center">
                      <Tooltip title="View trade on chart">
                        <IconButton
                          size="small"
                          onClick={() => navigate(`/charts/trade/${trade.id}`)}
                          color="primary"
                        >
                          <ShowChart fontSize="small" />
                        </IconButton>
                      </Tooltip>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </TableContainer>
          )
        })()}
      </Paper>

      {/* Notes Section */}
      <Paper sx={{ p: { xs: 1.5, sm: 2 } }}>
        <Box
          sx={{
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            mb: 2,
            flexWrap: 'wrap',
            gap: 1,
          }}
        >
          <Typography variant="h6">Daily Notes</Typography>
          <Box sx={{ display: 'flex', gap: 1, flexWrap: 'wrap' }}>
            {isEditing ? (
              <>
                <Button
                  variant="contained"
                  startIcon={<Save />}
                  onClick={handleSaveNotes}
                  disabled={createOrUpdateNotes.isPending}
                >
                  Save
                </Button>
                <Button
                  variant="outlined"
                  onClick={() => {
                    setNotes(journal.notes || '')
                    setIsEditing(false)
                  }}
                >
                  Cancel
                </Button>
                {journal.notes && (
                  <Button
                    variant="outlined"
                    color="error"
                    startIcon={<Delete />}
                    onClick={handleDeleteNotes}
                    disabled={deleteNotes.isPending}
                  >
                    Delete
                  </Button>
                )}
              </>
            ) : (
              <Button variant="outlined" onClick={() => setIsEditing(true)}>
                {journal.notes ? 'Edit' : 'Add Notes'}
              </Button>
            )}
          </Box>
        </Box>
        {isEditing ? (
          <TextField
            fullWidth
            multiline
            rows={6}
            value={notes}
            onChange={(e) => setNotes(e.target.value)}
            placeholder="Enter your daily notes here..."
            variant="outlined"
          />
        ) : (
          <Typography
            variant="body1"
            color={journal.notes ? 'text.primary' : 'text.secondary'}
            sx={{
              whiteSpace: 'pre-wrap',
              minHeight: '100px',
              p: 2,
              backgroundColor: 'rgba(255, 255, 255, 0.05)',
              borderRadius: 1,
            }}
          >
            {journal.notes || 'No notes for this day. Click "Add Notes" to add some.'}
          </Typography>
        )}
      </Paper>
    </Box>
  )
}
