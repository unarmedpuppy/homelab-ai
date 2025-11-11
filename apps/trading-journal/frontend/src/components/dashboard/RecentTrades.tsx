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
  IconButton,
  Tooltip,
} from '@mui/material'
import LoadingSpinner from '../common/LoadingSpinner'
import ErrorAlert from '../common/ErrorAlert'
import { format } from 'date-fns'
import { useNavigate } from 'react-router-dom'
import { ShowChart } from '@mui/icons-material'
import { RecentTrade } from '../../types/dashboard'

interface RecentTradesProps {
  trades: RecentTrade[] | undefined
  isLoading: boolean
  error: Error | null
}

export default function RecentTrades({ trades, isLoading, error }: RecentTradesProps) {
  const navigate = useNavigate()
  if (isLoading) {
    return <LoadingSpinner message="Loading recent trades..." minHeight={200} />
  }

  if (error) {
    return (
      <ErrorAlert
        title="Failed to load recent trades"
        message={error.message || 'Failed to load recent trades. Please try again.'}
        showRetry
        onRetry={() => window.location.reload()}
      />
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
    <TableContainer component={Paper} sx={{ maxWidth: '100%', overflowX: 'auto' }}>
      <Table size="small" sx={{ minWidth: 600 }}>
        <TableHead>
          <TableRow>
            <TableCell>Ticker</TableCell>
            <TableCell>Type</TableCell>
            <TableCell>Side</TableCell>
            <TableCell>Entry</TableCell>
            <TableCell>Exit</TableCell>
            <TableCell align="right">P&L</TableCell>
            <TableCell align="center">Chart</TableCell>
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
}

