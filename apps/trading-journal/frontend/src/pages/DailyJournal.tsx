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
  CircularProgress,
  Alert,
  useTheme,
} from '@mui/material'
import {
  ArrowBack,
  Save,
  Delete,
  TrendingUp,
  TrendingDown,
  Assessment,
} from '@mui/icons-material'
import { format, parseISO } from 'date-fns'
import {
  useDailyJournal,
  useCreateOrUpdateDailyNotes,
  useDeleteDailyNotes,
} from '../hooks/useDaily'

export default function DailyJournal() {
  const theme = useTheme()
  const navigate = useNavigate()
  const { date } = useParams<{ date: string }>()
  
  const [notes, setNotes] = useState('')
  const [isEditing, setIsEditing] = useState(false)

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
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', minHeight: '400px' }}>
        <CircularProgress />
      </Box>
    )
  }

  if (error) {
    return (
      <Alert severity="error" sx={{ m: 2 }}>
        Failed to load daily journal: {error.message}
      </Alert>
    )
  }

  if (!journal || !date) {
    return (
      <Alert severity="warning" sx={{ m: 2 }}>
        No data found for this date
      </Alert>
    )
  }

  const journalDate = parseISO(date)

  return (
    <Box sx={{ p: 3 }}>
      {/* Header */}
      <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, mb: 3 }}>
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
      <Grid container spacing={2} sx={{ mb: 3 }}>
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

      {/* Trades Table */}
      <Paper sx={{ p: 2, mb: 3 }}>
        <Typography variant="h6" gutterBottom>
          Trades
        </Typography>
        {journal.trades.length === 0 ? (
          <Typography variant="body2" color="text.secondary" sx={{ py: 2 }}>
            No trades for this day
          </Typography>
        ) : (
          <TableContainer>
            <Table size="small">
              <TableHead>
                <TableRow>
                  <TableCell>Ticker</TableCell>
                  <TableCell>Type</TableCell>
                  <TableCell>Side</TableCell>
                  <TableCell>Entry Time</TableCell>
                  <TableCell>Exit Time</TableCell>
                  <TableCell align="right">P&L</TableCell>
                  <TableCell align="right">ROI</TableCell>
                  <TableCell align="right">R-Multiple</TableCell>
                  <TableCell align="center">Chart</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {journal.trades.map((trade) => (
                  <TableRow key={trade.id} hover>
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
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </TableContainer>
        )}
      </Paper>

      {/* Notes Section */}
      <Paper sx={{ p: 2 }}>
        <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', mb: 2 }}>
          <Typography variant="h6">Daily Notes</Typography>
          <Box sx={{ display: 'flex', gap: 1 }}>
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
