/**
 * Playbooks page component.
 */

import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import {
  Box,
  Typography,
  Paper,
  Grid,
  Card,
  CardContent,
  Button,
  TextField,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  IconButton,
  Chip,
  Switch,
  FormControlLabel,
  MenuItem,
  Select,
  FormControl,
  InputLabel,
  Tooltip,
} from '@mui/material'
import {
  Add,
  Edit,
  Delete,
  Visibility,
  Search,
} from '@mui/icons-material'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import {
  getPlaybooks,
  createPlaybook,
  updatePlaybook,
  deletePlaybook,
  getPlaybookTemplates,
} from '../api/playbooks'
import type { PlaybookResponse, PlaybookCreate, PlaybookUpdate } from '../types/playbook'
import LoadingSpinner from '../components/common/LoadingSpinner'
import ErrorAlert from '../components/common/ErrorAlert'
import { formatCurrency, formatPercent } from '../utils/formatting'

export default function Playbooks() {
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  const [searchTerm, setSearchTerm] = useState('')
  const [isActiveFilter, setIsActiveFilter] = useState<boolean | undefined>(undefined)
  const [createDialogOpen, setCreateDialogOpen] = useState(false)
  const [editDialogOpen, setEditDialogOpen] = useState(false)
  const [selectedPlaybook, setSelectedPlaybook] = useState<PlaybookResponse | null>(null)
  const [formData, setFormData] = useState<PlaybookCreate>({
    name: '',
    description: '',
    template_id: undefined,
    is_active: true,
    is_shared: false,
  })

  // Fetch playbooks
  const {
    data: playbooksData,
    isLoading,
    error,
  } = useQuery({
    queryKey: ['playbooks', searchTerm, isActiveFilter],
    queryFn: () =>
      getPlaybooks({
        search: searchTerm || undefined,
        is_active: isActiveFilter,
        limit: 100,
      }),
  })

  // Fetch templates
  const { data: templates } = useQuery({
    queryKey: ['playbook-templates'],
    queryFn: getPlaybookTemplates,
  })

  // Create mutation
  const createMutation = useMutation({
    mutationFn: createPlaybook,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['playbooks'] })
      setCreateDialogOpen(false)
      setFormData({
        name: '',
        description: '',
        template_id: undefined,
        is_active: true,
        is_shared: false,
      })
    },
  })

  // Update mutation
  const updateMutation = useMutation({
    mutationFn: ({ id, data }: { id: number; data: PlaybookUpdate }) => updatePlaybook(id, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['playbooks'] })
      setEditDialogOpen(false)
      setSelectedPlaybook(null)
    },
  })

  // Delete mutation
  const deleteMutation = useMutation({
    mutationFn: deletePlaybook,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['playbooks'] })
    },
  })

  const handleCreate = () => {
    createMutation.mutate(formData)
  }

  const handleEdit = (playbook: PlaybookResponse) => {
    setSelectedPlaybook(playbook)
    setFormData({
      name: playbook.name,
      description: playbook.description || '',
      template_id: playbook.template_id,
      is_active: playbook.is_active,
      is_shared: playbook.is_shared,
    })
    setEditDialogOpen(true)
  }

  const handleUpdate = () => {
    if (selectedPlaybook) {
      updateMutation.mutate({ id: selectedPlaybook.id, data: formData })
    }
  }

  const handleDelete = (id: number) => {
    if (window.confirm('Are you sure you want to delete this playbook? Trades using this playbook will have their playbook assignment removed.')) {
      deleteMutation.mutate(id)
    }
  }

  const handleViewDetails = (playbook: PlaybookResponse) => {
    navigate(`/playbooks/${playbook.id}`)
  }

  if (isLoading) {
    return <LoadingSpinner />
  }

  if (error) {
    return <ErrorAlert message="Failed to load playbooks" />
  }

  const playbooks = playbooksData?.playbooks || []

  return (
    <Box>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Typography variant="h4" component="h1">
          Playbooks
        </Typography>
        <Button
          variant="contained"
          startIcon={<Add />}
          onClick={() => setCreateDialogOpen(true)}
        >
          New Playbook
        </Button>
      </Box>

      {/* Filters */}
      <Paper sx={{ p: 2, mb: 3 }}>
        <Grid container spacing={2} alignItems="center">
          <Grid item xs={12} sm={6} md={4}>
            <TextField
              fullWidth
              label="Search"
              variant="outlined"
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              InputProps={{
                startAdornment: <Search sx={{ mr: 1, color: 'text.secondary' }} />,
              }}
            />
          </Grid>
          <Grid item xs={12} sm={6} md={4}>
            <FormControl fullWidth>
              <InputLabel>Status</InputLabel>
              <Select
                value={isActiveFilter === undefined ? 'all' : isActiveFilter ? 'active' : 'inactive'}
                label="Status"
                onChange={(e) => {
                  const value = e.target.value
                  setIsActiveFilter(
                    value === 'all' ? undefined : value === 'active' ? true : false
                  )
                }}
              >
                <MenuItem value="all">All</MenuItem>
                <MenuItem value="active">Active</MenuItem>
                <MenuItem value="inactive">Inactive</MenuItem>
              </Select>
            </FormControl>
          </Grid>
        </Grid>
      </Paper>

      {/* Playbooks Grid */}
      {playbooks.length === 0 ? (
        <Paper sx={{ p: 4, textAlign: 'center' }}>
          <Typography variant="h6" color="text.secondary">
            No playbooks found
          </Typography>
          <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
            Create your first playbook to start tracking trading strategies
          </Typography>
        </Paper>
      ) : (
        <Grid container spacing={3}>
          {playbooks.map((playbook) => (
            <Grid item xs={12} sm={6} md={4} key={playbook.id}>
              <Card>
                <CardContent>
                  <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'start', mb: 2 }}>
                    <Box>
                      <Typography variant="h6" component="h2">
                        {playbook.name}
                      </Typography>
                      {playbook.description && (
                        <Typography variant="body2" color="text.secondary" sx={{ mt: 0.5 }}>
                          {playbook.description}
                        </Typography>
                      )}
                    </Box>
                    <Box sx={{ display: 'flex', gap: 0.5 }}>
                      <Tooltip title="View Details">
                        <IconButton size="small" onClick={() => handleViewDetails(playbook)}>
                          <Visibility fontSize="small" />
                        </IconButton>
                      </Tooltip>
                      <Tooltip title="Edit">
                        <IconButton size="small" onClick={() => handleEdit(playbook)}>
                          <Edit fontSize="small" />
                        </IconButton>
                      </Tooltip>
                      <Tooltip title="Delete">
                        <IconButton
                          size="small"
                          onClick={() => handleDelete(playbook.id)}
                          color="error"
                        >
                          <Delete fontSize="small" />
                        </IconButton>
                      </Tooltip>
                    </Box>
                  </Box>

                  <Box sx={{ display: 'flex', gap: 1, mb: 2, flexWrap: 'wrap' }}>
                    <Chip
                      label={playbook.is_active ? 'Active' : 'Inactive'}
                      color={playbook.is_active ? 'success' : 'default'}
                      size="small"
                    />
                    {playbook.is_shared && (
                      <Chip label="Shared" color="info" size="small" />
                    )}
                  </Box>

                  {playbook.performance && (
                    <Box>
                      <Typography variant="subtitle2" sx={{ mb: 1 }}>
                        Performance
                      </Typography>
                      <Grid container spacing={1}>
                        <Grid item xs={6}>
                          <Typography variant="caption" color="text.secondary">
                            Trades
                          </Typography>
                          <Typography variant="body2" fontWeight="bold">
                            {playbook.performance.total_trades}
                          </Typography>
                        </Grid>
                        <Grid item xs={6}>
                          <Typography variant="caption" color="text.secondary">
                            Net P&L
                          </Typography>
                          <Typography
                            variant="body2"
                            fontWeight="bold"
                            color={
                              playbook.performance.net_pnl >= 0
                                ? 'success.main'
                                : 'error.main'
                            }
                          >
                            {formatCurrency(playbook.performance.net_pnl)}
                          </Typography>
                        </Grid>
                        {playbook.performance.win_rate !== undefined && (
                          <Grid item xs={6}>
                            <Typography variant="caption" color="text.secondary">
                              Win Rate
                            </Typography>
                            <Typography variant="body2" fontWeight="bold">
                              {formatPercent(playbook.performance.win_rate)}
                            </Typography>
                          </Grid>
                        )}
                        {playbook.performance.profit_factor !== undefined && (
                          <Grid item xs={6}>
                            <Typography variant="caption" color="text.secondary">
                              Profit Factor
                            </Typography>
                            <Typography variant="body2" fontWeight="bold">
                              {playbook.performance.profit_factor.toFixed(2)}
                            </Typography>
                          </Grid>
                        )}
                      </Grid>
                    </Box>
                  )}
                </CardContent>
              </Card>
            </Grid>
          ))}
        </Grid>
      )}

      {/* Create Dialog */}
      <Dialog open={createDialogOpen} onClose={() => setCreateDialogOpen(false)} maxWidth="sm" fullWidth>
        <DialogTitle>Create Playbook</DialogTitle>
        <DialogContent>
          <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2, pt: 1 }}>
            <TextField
              label="Name"
              fullWidth
              required
              value={formData.name}
              onChange={(e) => setFormData({ ...formData, name: e.target.value })}
            />
            <TextField
              label="Description"
              fullWidth
              multiline
              rows={3}
              value={formData.description}
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
          <Button onClick={() => setCreateDialogOpen(false)}>Cancel</Button>
          <Button
            variant="contained"
            onClick={handleCreate}
            disabled={!formData.name || createMutation.isPending}
          >
            Create
          </Button>
        </DialogActions>
      </Dialog>

      {/* Edit Dialog */}
      <Dialog open={editDialogOpen} onClose={() => setEditDialogOpen(false)} maxWidth="sm" fullWidth>
        <DialogTitle>Edit Playbook</DialogTitle>
        <DialogContent>
          <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2, pt: 1 }}>
            <TextField
              label="Name"
              fullWidth
              required
              value={formData.name}
              onChange={(e) => setFormData({ ...formData, name: e.target.value })}
            />
            <TextField
              label="Description"
              fullWidth
              multiline
              rows={3}
              value={formData.description}
              onChange={(e) => setFormData({ ...formData, description: e.target.value })}
            />
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

