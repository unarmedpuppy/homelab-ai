import { useState, useEffect, useCallback } from 'react';
import type { BeadTask, BeadsStats } from '../../types/beads';
import { beadsAPI } from '../../api/client';
import { BeadsTaskCard } from './BeadsTaskCard';
import { BeadsTaskDetail } from './BeadsTaskDetail';
import { BeadsStatsHeader } from './BeadsStatsHeader';
import { BeadsLabelFilter } from './BeadsLabelFilter';
import { CreateTaskModal } from './CreateTaskModal';
import { useIsMobile } from '../../hooks/useMediaQuery';

const POLL_INTERVAL = 5000; // 5 seconds

interface Column {
  id: 'backlog' | 'in_progress' | 'done';
  title: string;
  filter: (task: BeadTask) => boolean;
}

const columns: Column[] = [
  {
    id: 'backlog',
    title: 'Backlog',
    filter: (task) => task.status === 'open',
  },
  {
    id: 'in_progress',
    title: 'In Progress',
    filter: (task) => task.status === 'in_progress',
  },
  {
    id: 'done',
    title: 'Done',
    filter: (task) => task.status === 'closed',
  },
];

export function BeadsBoard() {
  const [tasks, setTasks] = useState<BeadTask[]>([]);
  const [stats, setStats] = useState<BeadsStats | null>(null);
  const [labels, setLabels] = useState<string[]>([]);
  const [selectedLabels, setSelectedLabels] = useState<string[]>([]);
  const [selectedTask, setSelectedTask] = useState<BeadTask | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [activeColumn, setActiveColumn] = useState<'backlog' | 'in_progress' | 'done'>('backlog');
  const [showFilterDrawer, setShowFilterDrawer] = useState(false);
  const isMobile = useIsMobile();

  const fetchData = useCallback(async () => {
    try {
      const [tasksRes, statsRes, labelsRes] = await Promise.all([
        beadsAPI.listTasks(
          selectedLabels.length > 0
            ? { label: selectedLabels[0] } // API only supports one label filter
            : undefined
        ),
        beadsAPI.getStats(),
        beadsAPI.getLabels(),
      ]);

      // If multiple labels selected, filter client-side
      let filteredTasks = tasksRes.tasks;
      if (selectedLabels.length > 1) {
        filteredTasks = tasksRes.tasks.filter(task =>
          selectedLabels.every(label => task.labels.includes(label))
        );
      }

      setTasks(filteredTasks);
      setStats(statsRes);
      setLabels(labelsRes.labels);
      setError(null);
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Failed to fetch tasks');
    } finally {
      setLoading(false);
    }
  }, [selectedLabels]);

  // Initial fetch and polling
  useEffect(() => {
    fetchData();
    const interval = setInterval(fetchData, POLL_INTERVAL);
    return () => clearInterval(interval);
  }, [fetchData]);

  const handleToggleLabel = (label: string) => {
    setSelectedLabels(prev =>
      prev.includes(label)
        ? prev.filter(l => l !== label)
        : [...prev, label]
    );
  };

  const handleClearFilters = () => {
    setSelectedLabels([]);
  };

  const handleRefresh = () => {
    setLoading(true);
    fetchData();
  };

  const handleTaskUpdate = () => {
    fetchData();
    // Keep detail panel open but refresh data
    if (selectedTask) {
      beadsAPI.getTask(selectedTask.id).then(task => {
        setSelectedTask(task);
      }).catch(() => {
        setSelectedTask(null);
      });
    }
  };

  // Handle selecting a task by ID (used for blocked-by links)
  const handleSelectTaskById = async (taskId: string) => {
    try {
      const task = await beadsAPI.getTask(taskId);
      setSelectedTask(task);
    } catch {
      // Task not found, do nothing
      console.warn(`Task ${taskId} not found`);
    }
  };

  const getColumnTasks = (column: Column) => {
    return tasks.filter(column.filter);
  };

  // Convert labels to format with counts for BeadsLabelFilter
  const labelsWithCounts = labels.map(label => ({
    name: label,
    count: stats?.by_label[label] ?? 0,
  }));

  // Mobile column selector
  const mobileColumnSelector = (
    <div className="sm:hidden flex gap-1 p-2 bg-[var(--retro-bg-medium)] border-b border-[var(--retro-border)]">
      {/* Filter button */}
      <button
        onClick={() => setShowFilterDrawer(true)}
        className={`
          py-2 px-3 text-xs font-bold uppercase rounded transition-colors
          ${selectedLabels.length > 0
            ? 'bg-[var(--retro-accent-cyan)] text-[var(--retro-bg-dark)]'
            : 'text-[var(--retro-text-muted)] hover:text-[var(--retro-text-primary)] border border-[var(--retro-border)]'
          }
        `}
        aria-label="Open filters"
      >
        <svg width="16" height="16" viewBox="0 0 16 16" fill="none" xmlns="http://www.w3.org/2000/svg" className="inline-block">
          <path d="M2 4h12M4 8h8M6 12h4" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round"/>
        </svg>
        {selectedLabels.length > 0 && (
          <span className="ml-1">({selectedLabels.length})</span>
        )}
      </button>
      {/* Column tabs */}
      {columns.map(col => (
        <button
          key={col.id}
          onClick={() => setActiveColumn(col.id)}
          className={`
            flex-1 py-2 px-3 text-xs font-bold uppercase rounded transition-colors
            ${activeColumn === col.id
              ? 'bg-[var(--retro-accent-cyan)] text-[var(--retro-bg-dark)]'
              : 'text-[var(--retro-text-muted)] hover:text-[var(--retro-text-primary)]'
            }
          `}
        >
          {col.title}
          <span className="ml-1 text-[0.625rem]">
            ({getColumnTasks(col).length})
          </span>
        </button>
      ))}
    </div>
  );

  return (
    <div className="h-full flex flex-col bg-[var(--retro-bg-dark)]">
      {/* Stats Header */}
      <BeadsStatsHeader
        stats={stats}
        loading={loading}
        onCreateTask={() => setShowCreateModal(true)}
        onRefresh={handleRefresh}
      />

      {/* Mobile column selector */}
      {mobileColumnSelector}

      {/* Error */}
      {error && (
        <div className="p-3 m-4 bg-[rgba(255,68,68,0.1)] border border-[var(--retro-accent-red)] rounded text-sm text-[var(--retro-accent-red)]">
          {error}
        </div>
      )}

      {/* Main Content */}
      <div className="flex-1 flex overflow-hidden">
        {/* Sidebar - Label Filters (desktop only) */}
        <div className={`
          w-64 flex-shrink-0 border-r border-[var(--retro-border)] bg-[var(--retro-bg-medium)]
          overflow-hidden
          hidden lg:block
        `}>
          <BeadsLabelFilter
            labels={labelsWithCounts}
            activeLabels={selectedLabels}
            onToggleLabel={handleToggleLabel}
            onClearFilters={handleClearFilters}
          />
        </div>

        {/* Mobile Filter Drawer */}
        {isMobile && (
          <BeadsLabelFilter
            labels={labelsWithCounts}
            activeLabels={selectedLabels}
            onToggleLabel={handleToggleLabel}
            onClearFilters={handleClearFilters}
            isOpen={showFilterDrawer}
            onClose={() => setShowFilterDrawer(false)}
          />
        )}

        {/* Kanban Columns */}
        <div className="flex-1 flex overflow-hidden">
          {/* Desktop: All columns */}
          <div className="hidden sm:flex flex-1 gap-4 p-4 overflow-x-auto">
            {columns.map(column => (
              <div key={column.id} className="retro-kanban-column">
                <div className="retro-kanban-column-header">
                  <span>{column.title}</span>
                  <span className="retro-kanban-column-count">
                    {getColumnTasks(column).length}
                  </span>
                </div>
                <div className="retro-kanban-column-body">
                  {getColumnTasks(column).length === 0 ? (
                    <div className="text-xs text-[var(--retro-text-muted)] text-center py-4">
                      No tasks
                    </div>
                  ) : (
                    getColumnTasks(column).map(task => (
                      <BeadsTaskCard
                        key={task.id}
                        task={task}
                        selected={selectedTask?.id === task.id}
                        onClick={() => setSelectedTask(task)}
                      />
                    ))
                  )}
                </div>
              </div>
            ))}
          </div>

          {/* Mobile: Single column */}
          <div className="sm:hidden flex-1 overflow-y-auto p-4">
            <div className="space-y-3">
              {getColumnTasks(columns.find(c => c.id === activeColumn)!).map(task => (
                <BeadsTaskCard
                  key={task.id}
                  task={task}
                  selected={selectedTask?.id === task.id}
                  onClick={() => setSelectedTask(task)}
                />
              ))}
              {getColumnTasks(columns.find(c => c.id === activeColumn)!).length === 0 && (
                <div className="text-sm text-[var(--retro-text-muted)] text-center py-8">
                  No tasks in {activeColumn.replace('_', ' ')}
                </div>
              )}
            </div>
          </div>
        </div>

        {/* Task Detail Panel (desktop) */}
        {selectedTask && (
          <div className="hidden lg:block w-80 flex-shrink-0 border-l border-[var(--retro-border)] overflow-hidden">
            <BeadsTaskDetail
              task={selectedTask}
              onClose={() => setSelectedTask(null)}
              onUpdate={handleTaskUpdate}
              onSelectTask={handleSelectTaskById}
            />
          </div>
        )}
      </div>

      {/* Task Detail Modal (mobile) */}
      {selectedTask && (
        <div className="lg:hidden fixed inset-0 z-50 bg-[var(--retro-bg-dark)]">
          <BeadsTaskDetail
            task={selectedTask}
            onClose={() => setSelectedTask(null)}
            onUpdate={handleTaskUpdate}
            onSelectTask={handleSelectTaskById}
          />
        </div>
      )}

      {/* Create Task Modal */}
      <CreateTaskModal
        isOpen={showCreateModal}
        onClose={() => setShowCreateModal(false)}
        onCreated={handleRefresh}
      />
    </div>
  );
}

export default BeadsBoard;
