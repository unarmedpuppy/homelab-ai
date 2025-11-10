/**
 * Recent Trades table component for dashboard.
 */

import {
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  Typography,
  Chip,
  Box,
  CircularProgress,
  Alert,
} from '@mui/material'
import { format } from 'date-fns'
import { RecentTrade } from '../../types/dashboard'

interface RecentTradesProps {
  trades: RecentTrade[] | undefined
  isLoading: boolean
  error: Error | null
}

export default function RecentTrades({ trades, isLoading, error }: RecentTradesProps) {
  if (isLoading) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', p: 3 }}>
        <CircularProgress />
      </Box>
    )
  }

  if (error) {
    return (
      <Alert severity="error" sx={{ m: 2 }}>
        Failed to load recent trades: {error.message}
      </Alert>
    )
  }

  if (!trades || trades.length === 0) {
    return (
      <Box sx={{ p: 3, textAlign: 'center' }}>
        <Typography variant="body2" color="text.secondary">
          No recent trades
        </Typography>
      </Box>
    )
  }

  const formatPnl = (pnl: number | null): string => {
    if (pnl === null) return 'N/A'
    return `$${pnl.toFixed(2)}`
  }

  const getPnlColor = (pnl: number | null): 'success' | 'error' | 'default' => {
    if (pnl === null) return 'default'
    return pnl >= 0 ? 'success' : 'error'
  }

  return (
    <TableContainer component={Paper}>
      <Table size="small">
        <TableHead>
          <TableRow>
            <TableCell>Ticker</TableCell>
            <TableCell>Type</TableCell>
            <TableCell>Side</TableCell>
            <TableCell>Entry</TableCell>
            <TableCell>Exit</TableCell>
            <TableCell align="right">P&L</TableCell>
          </TableRow>
        </TableHead>
        <TableBody>
          {trades.map((trade) => (
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
                  {format(new Date(trade.entry_time), 'MMM d, yyyy')}
                </Typography>
              </TableCell>
              <TableCell>
                <Typography variant="body2">
                  {trade.exit_time
                    ? format(new Date(trade.exit_time), 'MMM d, yyyy')
                    : 'N/A'}
                </Typography>
              </TableCell>
              <TableCell align="right">
                <Typography
                  variant="body2"
                  fontWeight="bold"
                  color={getPnlColor(trade.net_pnl) === 'success' ? 'success.main' : 'error.main'}
                >
                  {formatPnl(trade.net_pnl)}
                </Typography>
              </TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>
    </TableContainer>
  )
}

