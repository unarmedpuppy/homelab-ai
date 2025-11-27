/**
 * Analytics Dashboard page component.
 */

import { useState } from 'react'
import {
  Box,
  Typography,
  Paper,
  Grid,
  Tabs,
  Tab,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  TextField,
} from '@mui/material'
import { useQuery } from '@tanstack/react-query'
import {
  getPerformanceMetrics,
  getPerformanceByTicker,
  getPerformanceByType,
  getPerformanceByPlaybook,
} from '../api/analytics'
import LoadingSpinner from '../components/common/LoadingSpinner'
import ErrorAlert from '../components/common/ErrorAlert'
import KPICard from '../components/dashboard/KPICard'
import { formatCurrency, formatPercent } from '../utils/formatting'

interface TabPanelProps {
  children?: React.ReactNode
  index: number
  value: number
}

function TabPanel(props: TabPanelProps) {
  const { children, value, index, ...other } = props

  return (
    <div
      role="tabpanel"
      hidden={value !== index}
      id={`analytics-tabpanel-${index}`}
      aria-labelledby={`analytics-tab-${index}`}
      {...other}
    >
      {value === index && <Box sx={{ py: 3 }}>{children}</Box>}
    </div>
  )
}

export default function Analytics() {
  const [tabValue, setTabValue] = useState(0)
  const [dateFrom, setDateFrom] = useState('')
  const [dateTo, setDateTo] = useState('')

  const handleTabChange = (_event: React.SyntheticEvent, newValue: number) => {
    setTabValue(newValue)
  }

  const params = {
    date_from: dateFrom || undefined,
    date_to: dateTo || undefined,
  }

  // Fetch data
  const {
    data: metrics,
    isLoading: isMetricsLoading,
    error: metricsError,
  } = useQuery({
    queryKey: ['analytics-metrics', params],
    queryFn: () => getPerformanceMetrics(params),
  })

  const {
    data: tickerData,
    isLoading: isTickerLoading,
    error: tickerError,
  } = useQuery({
    queryKey: ['analytics-ticker', params],
    queryFn: () => getPerformanceByTicker(params),
    enabled: tabValue === 1,
  })

  const {
    data: typeData,
    isLoading: isTypeLoading,
    error: typeError,
  } = useQuery({
    queryKey: ['analytics-type', params],
    queryFn: () => getPerformanceByType(params),
    enabled: tabValue === 2,
  })

  const {
    data: playbookData,
    isLoading: isPlaybookLoading,
    error: playbookError,
  } = useQuery({
    queryKey: ['analytics-playbook', params],
    queryFn: () => getPerformanceByPlaybook(params),
    enabled: tabValue === 3,
  })

  const renderPerformanceTable = (data: any[], nameKey: string) => (
    <TableContainer component={Paper}>
      <Table size="small">
        <TableHead>
          <TableRow>
            <TableCell>{nameKey === 'ticker' ? 'Ticker' : nameKey === 'trade_type' ? 'Type' : 'Playbook'}</TableCell>
            <TableCell align="right">Trades</TableCell>
            <TableCell align="right">Net P&L</TableCell>
            <TableCell align="right">Win Rate</TableCell>
            <TableCell align="right">Profit Factor</TableCell>
            <TableCell align="right">Avg Win</TableCell>
            <TableCell align="right">Avg Loss</TableCell>
          </TableRow>
        </TableHead>
        <TableBody>
          {data.map((row, index) => (
            <TableRow key={index} hover>
              <TableCell component="th" scope="row">
                {row[nameKey]}
              </TableCell>
              <TableCell align="right">{row.total_trades}</TableCell>
              <TableCell
                align="right"
                sx={{ color: row.net_pnl >= 0 ? 'success.main' : 'error.main', fontWeight: 'bold' }}
              >
                {formatCurrency(row.net_pnl)}
              </TableCell>
              <TableCell align="right">{formatPercent(row.win_rate)}</TableCell>
              <TableCell align="right">{row.profit_factor?.toFixed(2) || 'N/A'}</TableCell>
              <TableCell align="right" sx={{ color: 'success.main' }}>
                {formatCurrency(row.avg_win)}
              </TableCell>
              <TableCell align="right" sx={{ color: 'error.main' }}>
                {formatCurrency(row.avg_loss)}
              </TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>
    </TableContainer>
  )

  return (
    <Box>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Typography variant="h4" component="h1">
          Analytics
        </Typography>
        <Box sx={{ display: 'flex', gap: 2 }}>
          <TextField
            label="From Date"
            type="date"
            size="small"
            InputLabelProps={{ shrink: true }}
            value={dateFrom}
            onChange={(e) => setDateFrom(e.target.value)}
          />
          <TextField
            label="To Date"
            type="date"
            size="small"
            InputLabelProps={{ shrink: true }}
            value={dateTo}
            onChange={(e) => setDateTo(e.target.value)}
          />
        </Box>
      </Box>

      <Box sx={{ borderBottom: 1, borderColor: 'divider' }}>
        <Tabs value={tabValue} onChange={handleTabChange} aria-label="analytics tabs">
          <Tab label="Overview" />
          <Tab label="By Ticker" />
          <Tab label="By Type" />
          <Tab label="By Playbook" />
        </Tabs>
      </Box>

      {/* Overview Tab */}
      <TabPanel value={tabValue} index={0}>
        {isMetricsLoading ? (
          <LoadingSpinner />
        ) : metricsError ? (
          <ErrorAlert message="Failed to load metrics" />
        ) : metrics ? (
          <Grid container spacing={3}>
            <Grid item xs={12} sm={6} md={3}>
              <KPICard
                title="Sharpe Ratio"
                value={metrics.sharpe_ratio || 0}
                format="number"
                color="primary"
              />
            </Grid>
            <Grid item xs={12} sm={6} md={3}>
              <KPICard
                title="Sortino Ratio"
                value={metrics.sortino_ratio || 0}
                format="number"
                color="primary"
              />
            </Grid>
            <Grid item xs={12} sm={6} md={3}>
              <KPICard
                title="Max Drawdown"
                value={metrics.max_drawdown || 0}
                format="percent"
                color="error"
              />
            </Grid>
            <Grid item xs={12} sm={6} md={3}>
              <KPICard
                title="Avg Drawdown"
                value={metrics.avg_drawdown || 0}
                format="percent"
                color="warning"
              />
            </Grid>
            <Grid item xs={12} sm={6} md={3}>
              <KPICard
                title="Best Trade"
                value={metrics.best_trade || 0}
                format="currency"
                color="success"
              />
            </Grid>
            <Grid item xs={12} sm={6} md={3}>
              <KPICard
                title="Worst Trade"
                value={metrics.worst_trade || 0}
                format="currency"
                color="error"
              />
            </Grid>
            <Grid item xs={12} sm={6} md={3}>
              <KPICard
                title="Win Rate"
                value={metrics.win_rate || 0}
                format="percent"
                color="info"
              />
            </Grid>
            <Grid item xs={12} sm={6} md={3}>
              <KPICard
                title="Profit Factor"
                value={metrics.profit_factor || 0}
                format="number"
                color="info"
              />
            </Grid>
          </Grid>
        ) : null}
      </TabPanel>

      {/* Ticker Tab */}
      <TabPanel value={tabValue} index={1}>
        {isTickerLoading ? (
          <LoadingSpinner />
        ) : tickerError ? (
          <ErrorAlert message="Failed to load ticker data" />
        ) : tickerData ? (
          renderPerformanceTable(tickerData.tickers, 'ticker')
        ) : null}
      </TabPanel>

      {/* Type Tab */}
      <TabPanel value={tabValue} index={2}>
        {isTypeLoading ? (
          <LoadingSpinner />
        ) : typeError ? (
          <ErrorAlert message="Failed to load type data" />
        ) : typeData ? (
          renderPerformanceTable(typeData.types, 'trade_type')
        ) : null}
      </TabPanel>

      {/* Playbook Tab */}
      <TabPanel value={tabValue} index={3}>
        {isPlaybookLoading ? (
          <LoadingSpinner />
        ) : playbookError ? (
          <ErrorAlert message="Failed to load playbook data" />
        ) : playbookData ? (
          renderPerformanceTable(playbookData.playbooks, 'playbook')
        ) : null}
      </TabPanel>
    </Box>
  )
}

