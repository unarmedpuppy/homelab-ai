/**
 * Playbook Details page component.
 */

import { useState, useMemo } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import {
  Box,
  Typography,
  Paper,
  Grid,
  Button,
  Chip,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  FormControlLabel,
  Switch,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
} from '@mui/material'
import {
  Edit,
  Delete,
  ArrowBack,
} from '@mui/icons-material'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import {
  getPlaybook,
  getPlaybookTrades,
  updatePlaybook,
  deletePlaybook,
  getPlaybookTemplates,
} from '../api/playbooks'
import type { PlaybookUpdate } from '../types/playbook'
import LoadingSpinner from '../components/common/LoadingSpinner'
import ErrorAlert from '../components/common/ErrorAlert'
import KPICard from '../components/dashboard/KPICard'
import RecentTrades from '../components/dashboard/RecentTrades'
import { formatCurrency, formatPercent } from '../utils/formatting'
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Legend,
} from 'recharts'
import { format } from 'date-fns'

export default function PlaybookDetails() {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  const playbookId = Number(id)

  const [editDialogOpen, setEditDialogOpen] = useState(false)
  const [formData, setFormData] = useState<PlaybookUpdate>({})

  // Fetch playbook details
  const {
    data: playbook,
    isLoading: isPlaybookLoading,
    error: playbookError,
  } = useQuery({
    queryKey: ['playbook', playbookId],
    queryFn: () => getPlaybook(playbookId),
    enabled: !!playbookId,
  })

  // Fetch playbook trades
  const {
    data: trades,
    isLoading: isTradesLoading,
    error: tradesError,
  } = useQuery({
    queryKey: ['playbook-trades', playbookId],
    queryFn: () => getPlaybookTrades(playbookId),
    enabled: !!playbookId,
  })

  // Fetch templates for edit dialog
  const { data: templates } = useQuery({
    queryKey: ['playbook-templates'],
    queryFn: getPlaybookTemplates,
    enabled: editDialogOpen,
  })

  // Update mutation
  const updateMutation = useMutation({
    mutationFn: (data: PlaybookUpdate) => updatePlaybook(playbookId, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['playbook', playbookId] })
      queryClient.invalidateQueries({ queryKey: ['playbooks'] })
      setEditDialogOpen(false)
    },
  })

  // Delete mutation
  const deleteMutation = useMutation({
    mutationFn: deletePlaybook,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['playbooks'] })
      navigate('/playbooks')
    },
  })

  const handleEdit = () => {
    if (playbook) {
      setFormData({
        name: playbook.name,
        description: playbook.description,
        template_id: playbook.template_id,
        is_active: playbook.is_active,
        is_shared: playbook.is_shared,
      })
      setEditDialogOpen(true)
    }
  }

  const handleUpdate = () => {
    updateMutation.mutate(formData)
  }

  const handleDelete = () => {
    if (window.confirm('Are you sure you want to delete this playbook? Trades using this playbook will have their playbook assignment removed.')) {
      deleteMutation.mutate(playbookId)
    }
  }

  // Calculate cumulative P&L for chart
  const chartData = useMemo(() => {
    if (!trades || trades.length === 0) return []

    // Sort trades by exit time
    const sortedTrades = [...trades]
      .filter(t => t.exit_time && t.net_pnl !== null)
      .sort((a, b) => new Date(a.exit_time!).getTime() - new Date(b.exit_time!).getTime())

    let cumulativePnl = 0
    return sortedTrades.map(trade => {
      cumulativePnl += trade.net_pnl || 0
      return {
        date: format(new Date(trade.exit_time!), 'MMM dd'),
        fullDate: trade.exit_time!,
        cumulativePnl,
        tradePnl: trade.net_pnl,
      }
    })
  }, [trades])

  if (isPlaybookLoading || isTradesLoading) {
    return <LoadingSpinner />
  }

  if (playbookError || tradesError) {
    return <ErrorAlert message="Failed to load playbook details" />
  }

  if (!playbook) {
    return <ErrorAlert message="Playbook not found" />
  }

  // Format trades for RecentTrades component
  const recentTrades = trades?.map(trade => ({
    id: trade.id,
    ticker: trade.ticker,
    trade_type: trade.trade_type,
    side: trade.side,
    entry_time: trade.entry_time,
    exit_time: trade.exit_time,
    net_pnl: trade.net_pnl,
  })) || []

  return (
    <Box>
      {/* Header */}
      <Box sx={{ mb: 3 }}>
        <Button
          startIcon={<ArrowBack />}
          onClick={() => navigate('/playbooks')}
          sx={{ mb: 2 }}
        >
          Back to Playbooks
        </Button>
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'start' }}>
          <Box>
            <Typography variant="h4" component="h1" gutterBottom>
              {playbook.name}
            </Typography>
            <Typography variant="body1" color="text.secondary" sx={{ mb: 1 }}>
              {playbook.description || 'No description'}
            </Typography>
            <Box sx={{ display: 'flex', gap: 1 }}>
              <Chip
                label={playbook.is_active ? 'Active' : 'Inactive'}
                color={playbook.is_active ? 'success' : 'default'}
                size="small"
              />
              {playbook.is_shared && (
                <Chip label="Shared" color="info" size="small" />
              )}
            </Box>
          </Box>
          <Box sx={{ display: 'flex', gap: 1 }}>
            <Button
              variant="outlined"
              startIcon={<Edit />}
              onClick={handleEdit}
            >
              Edit
            </Button>
            <Button
              variant="outlined"
              color="error"
              startIcon={<Delete />}
              onClick={handleDelete}
            >
              Delete
            </Button>
          </Box>
        </Box>
      </Box>

      {/* Performance KPIs */}
      {playbook.performance && (
        <Grid container spacing={3} sx={{ mb: 3 }}>
          <Grid item xs={12} sm={6} md={3}>
            <KPICard
              title="Net P&L"
              value={playbook.performance.net_pnl}
              format="currency"
              color={playbook.performance.net_pnl >= 0 ? 'success' : 'error'}
            />
          </Grid>
          <Grid item xs={12} sm={6} md={3}>
            <KPICard
              title="Win Rate"
              value={playbook.performance.win_rate || 0}
              format="percent"
              color="primary"
            />
          </Grid>
          <Grid item xs={12} sm={6} md={3}>
            <KPICard
              title="Profit Factor"
              value={playbook.performance.profit_factor || 0}
              format="number"
              color="info"
            />
          </Grid>
          <Grid item xs={12} sm={6} md={3}>
            <KPICard
              title="Total Trades"
              value={playbook.performance.total_trades}
              format="number"
              color="default"
            />
          </Grid>
        </Grid>
      )}

      {/* Cumulative P&L Chart */}
      <Paper sx={{ p: 2, mb: 3 }}>
        <Typography variant="h6" gutterBottom>
          Cumulative Performance
        </Typography>
        {chartData.length > 0 ? (
          <ResponsiveContainer width="100%" height={300}>
            <LineChart data={chartData} margin={{ top: 5, right: 20, left: 10, bottom: 5 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#2a2a2a" />
              <XAxis
                dataKey="date"
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
                labelFormatter={(label, payload) => {
                  if (payload && payload[0] && payload[0].payload) {
                    return format(new Date(payload[0].payload.fullDate), 'MMM dd, yyyy')
                  }
                  return label
                }}
              />
              <Legend wrapperStyle={{ color: '#d1d5db' }} />
              <Line
                type="monotone"
                dataKey="cumulativePnl"
                stroke="#9c27b0"
                strokeWidth={2}
                dot={false}
                name="Cumulative P&L"
              />
            </LineChart>
          </ResponsiveContainer>
        ) : (
          <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: 300 }}>
            <Typography variant="body2" color="text.secondary">
              No performance data available
            </Typography>
          </Box>
        )}
      </Paper>

      {/* Trades List */}
      <Box sx={{ mb: 3 }}>
        <Typography variant="h6" gutterBottom>
          Trade History
        </Typography>
        <RecentTrades
          trades={recentTrades}
          isLoading={isTradesLoading}
          error={tradesError}
        />
      </Box>

      {/* Edit Dialog */}
      <Dialog open={editDialogOpen} onClose={() => setEditDialogOpen(false)} maxWidth="sm" fullWidth>
        <DialogTitle>Edit Playbook</DialogTitle>
        <DialogContent>
          <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2, pt: 1 }}>
            <TextField
              label="Name"
              fullWidth
              required
              value={formData.name || ''}
              onChange={(e) => setFormData({ ...formData, name: e.target.value })}
            />
            <TextField
              label="Description"
              fullWidth
              multiline
              rows={3}
              value={formData.description || ''}
              onChange={(e) => setFormData({ ...formData, description: e.target.value })}
            />
            {templates && templates.length > 0 && (
              <FormControl fullWidth>
                <InputLabel>Template (Optional)</InputLabel>
                <Select
                  value={formData.template_id || ''}
                  label="Template (Optional)"
                  onChange={(e) =>
                    setFormData({
                      ...formData,
                      template_id: e.target.value ? Number(e.target.value) : undefined,
                    })
                  }
                >
                  <MenuItem value="">None</MenuItem>
                  {templates.map((template) => (
                    <MenuItem key={template.id} value={template.id}>
                      {template.name}
                    </MenuItem>
                  ))}
                </Select>
              </FormControl>
            )}
            <FormControlLabel
              control={
                <Switch
                  checked={formData.is_active}
                  onChange={(e) => setFormData({ ...formData, is_active: e.target.checked })}
                />
              }
              label="Active"
            />
            <FormControlLabel
              control={
                <Switch
                  checked={formData.is_shared}
                  onChange={(e) => setFormData({ ...formData, is_shared: e.target.checked })}
                />
              }
              label="Shared"
            />
          </Box>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setEditDialogOpen(false)}>Cancel</Button>
          <Button
            variant="contained"
            onClick={handleUpdate}
            disabled={!formData.name || updateMutation.isPending}
          >
            Update
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  )
}

