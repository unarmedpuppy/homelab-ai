import { useState, useEffect, useCallback } from 'react';
import { tasksAPI } from '../../api/client';
import type { Task, TaskStats, TaskFilters, TaskStatus, TaskPriority, TaskType, BuildingType } from '../../types/tasks';

const BUILDING_TYPE_LABELS: Record<BuildingType, string> = {
  'town-center': 'Town Center',
  'barracks':    'Barracks',
  'market':      'Market',
  'university':  'University',
  'castle':      'Castle',
};

const STATUS_ORDER: TaskStatus[] = ['OPEN', 'IN_PROGRESS', 'BLOCKED', 'CLOSED'];
const PRIORITY_COLORS: Record<TaskPriority, string> = {
  P0: 'bg-red-600',
  P1: 'bg-orange-500',
  P2: 'bg-yellow-500',
  P3: 'bg-green-600',
};

const STATUS_COLORS: Record<TaskStatus, string> = {
  OPEN: 'border-blue-500',
  IN_PROGRESS: 'border-yellow-500',
  BLOCKED: 'border-red-500',
  CLOSED: 'border-green-500',
};

interface TaskCardProps {
  task: Task;
  onStatusChange: (taskId: string, newStatus: TaskStatus) => void;
}

function TaskCard({ task, onStatusChange }: TaskCardProps) {
  const [expanded, setExpanded] = useState(false);

  return (
    <div
      className={`
        bg-[var(--retro-bg-light)] border-l-4 ${STATUS_COLORS[task.status]}
        rounded p-3 mb-2 cursor-pointer hover:bg-[var(--retro-bg-medium)] transition-colors
      `}
      onClick={() => setExpanded(!expanded)}
    >
      <div className="flex items-start justify-between gap-2">
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 mb-1">
            <span className={`text-xs px-1.5 py-0.5 rounded ${PRIORITY_COLORS[task.priority]} text-white font-bold`}>
              {task.priority}
            </span>
            <span className="text-xs text-[var(--retro-text-secondary)] font-mono">
              {task.id}
            </span>
          </div>
          <h4 className="text-sm font-medium text-[var(--retro-text-primary)] truncate">
            {task.title}
          </h4>
          <div className="flex flex-wrap gap-1 mt-1">
            <span className="text-xs px-1.5 py-0.5 bg-[var(--retro-bg-dark)] rounded text-[var(--retro-text-secondary)]">
              {task.repo}
            </span>
            {task.labels.slice(0, 2).map((label) => (
              <span
                key={label}
                className="text-xs px-1.5 py-0.5 bg-[var(--retro-accent-purple)]/20 rounded text-[var(--retro-accent-purple)]"
              >
                {label}
              </span>
            ))}
            {task.labels.length > 2 && (
              <span className="text-xs text-[var(--retro-text-secondary)]">
                +{task.labels.length - 2}
              </span>
            )}
          </div>
        </div>
      </div>

      {expanded && (
        <div className="mt-3 pt-3 border-t border-[var(--retro-border)]" onClick={(e) => e.stopPropagation()}>
          {task.description && (
            <p className="text-xs text-[var(--retro-text-secondary)] mb-2 whitespace-pre-wrap">
              {task.description}
            </p>
          )}
          {task.epic && (
            <p className="text-xs text-[var(--retro-accent-green)] mb-2">
              Epic: {task.epic}
            </p>
          )}
          <div className="flex flex-wrap gap-1 mt-2">
            {STATUS_ORDER.filter((s) => s !== task.status).map((status) => (
              <button
                key={status}
                onClick={() => onStatusChange(task.id, status)}
                className="text-xs px-2 py-1 rounded bg-[var(--retro-bg-dark)] hover:bg-[var(--retro-border)] text-[var(--retro-text-secondary)] transition-colors"
              >
                → {status.replace('_', ' ')}
              </button>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

interface TaskColumnProps {
  status: TaskStatus;
  tasks: Task[];
  onStatusChange: (taskId: string, newStatus: TaskStatus) => void;
}

function TaskColumn({ status, tasks, onStatusChange }: TaskColumnProps) {
  return (
    <div className="flex-1 min-w-[280px] max-w-[350px] flex flex-col">
      <div className={`border-t-4 ${STATUS_COLORS[status]} bg-[var(--retro-bg-medium)] rounded-t p-3 flex-shrink-0`}>
        <div className="flex items-center justify-between">
          <h3 className="text-sm font-bold text-[var(--retro-text-primary)]">
            {status.replace('_', ' ')}
          </h3>
          <span className="text-xs px-2 py-0.5 bg-[var(--retro-bg-dark)] rounded-full text-[var(--retro-text-secondary)]">
            {tasks.length}
          </span>
        </div>
      </div>
      <div className="bg-[var(--retro-bg-dark)] rounded-b p-2 min-h-[200px] flex-1 overflow-y-auto">
        {tasks.map((task) => (
          <TaskCard key={task.id} task={task} onStatusChange={onStatusChange} />
        ))}
        {tasks.length === 0 && (
          <div className="text-center py-8 text-[var(--retro-text-secondary)] text-sm">
            No tasks
          </div>
        )}
      </div>
    </div>
  );
}

interface StatsBarProps {
  stats: TaskStats | null;
}

function StatsBar({ stats }: StatsBarProps) {
  if (!stats) return null;

  return (
    <div className="flex flex-wrap gap-4 mb-6 p-4 bg-[var(--retro-bg-medium)] rounded border border-[var(--retro-border)]">
      <div className="text-center">
        <div className="text-2xl font-bold text-[var(--retro-accent-green)]">{stats.total}</div>
        <div className="text-xs text-[var(--retro-text-secondary)] uppercase">Total</div>
      </div>
      <div className="border-l border-[var(--retro-border)] pl-4">
        <div className="flex gap-3">
          {Object.entries(stats.by_status).map(([status, count]) => (
            <div key={status} className="text-center">
              <div className="text-lg font-bold text-[var(--retro-text-primary)]">{count}</div>
              <div className="text-xs text-[var(--retro-text-secondary)]">{status.replace('_', ' ')}</div>
            </div>
          ))}
        </div>
      </div>
      <div className="border-l border-[var(--retro-border)] pl-4">
        <div className="flex gap-3">
          {Object.entries(stats.by_priority)
            .sort(([a], [b]) => a.localeCompare(b))
            .map(([priority, count]) => (
              <div key={priority} className="text-center">
                <div className={`text-lg font-bold ${PRIORITY_COLORS[priority as TaskPriority]} bg-clip-text text-transparent bg-gradient-to-r from-current to-current`}>
                  {count}
                </div>
                <div className="text-xs text-[var(--retro-text-secondary)]">{priority}</div>
              </div>
            ))}
        </div>
      </div>
    </div>
  );
}

interface FilterBarProps {
  filters: TaskFilters | null;
  selectedRepo: string;
  selectedLabel: string;
  selectedPriority: string;
  selectedType: string;
  selectedBuildingType: string;
  onRepoChange: (repo: string) => void;
  onLabelChange: (label: string) => void;
  onPriorityChange: (priority: string) => void;
  onTypeChange: (type: string) => void;
  onBuildingTypeChange: (buildingType: string) => void;
}

function FilterBar({
  filters,
  selectedRepo,
  selectedLabel,
  selectedPriority,
  selectedType,
  selectedBuildingType,
  onRepoChange,
  onLabelChange,
  onPriorityChange,
  onTypeChange,
  onBuildingTypeChange,
}: FilterBarProps) {
  if (!filters) return null;

  const selectClass = "px-3 py-1.5 bg-[var(--retro-bg-light)] border border-[var(--retro-border)] rounded text-sm text-[var(--retro-text-primary)] focus:border-[var(--retro-border-active)] focus:outline-none";

  return (
    <div className="flex flex-wrap gap-3 mb-4">
      <select value={selectedType} onChange={(e) => onTypeChange(e.target.value)} className={selectClass}>
        <option value="">All Types</option>
        {filters.types.map((t) => (
          <option key={t} value={t}>{t.charAt(0).toUpperCase() + t.slice(1)}</option>
        ))}
      </select>

      <select value={selectedBuildingType} onChange={(e) => onBuildingTypeChange(e.target.value)} className={selectClass}>
        <option value="">All Buildings</option>
        {filters.building_types.map((bt) => (
          <option key={bt} value={bt}>{BUILDING_TYPE_LABELS[bt as BuildingType] ?? bt}</option>
        ))}
      </select>

      <select value={selectedRepo} onChange={(e) => onRepoChange(e.target.value)} className={selectClass}>
        <option value="">All Repos</option>
        {filters.repos.map((repo) => (
          <option key={repo} value={repo}>{repo}</option>
        ))}
      </select>

      <select value={selectedLabel} onChange={(e) => onLabelChange(e.target.value)} className={selectClass}>
        <option value="">All Labels</option>
        {filters.labels.map((label) => (
          <option key={label} value={label}>{label}</option>
        ))}
      </select>

      <select value={selectedPriority} onChange={(e) => onPriorityChange(e.target.value)} className={selectClass}>
        <option value="">All Priorities</option>
        {filters.priorities.map((p) => (
          <option key={p} value={p}>{p}</option>
        ))}
      </select>
    </div>
  );
}

export default function TasksDashboard() {
  const [tasks, setTasks] = useState<Task[]>([]);
  const [stats, setStats] = useState<TaskStats | null>(null);
  const [filters, setFilters] = useState<TaskFilters | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Filter state
  const [selectedRepo, setSelectedRepo] = useState('');
  const [selectedLabel, setSelectedLabel] = useState('');
  const [selectedPriority, setSelectedPriority] = useState('');
  const [selectedType, setSelectedType] = useState('');
  const [selectedBuildingType, setSelectedBuildingType] = useState('');

  const loadData = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);

      const params = {
        ...(selectedRepo && { repo: selectedRepo }),
        ...(selectedLabel && { label: selectedLabel }),
        ...(selectedPriority && { priority: selectedPriority as TaskPriority }),
        ...(selectedType && { type: selectedType as TaskType }),
        ...(selectedBuildingType && { building_type: selectedBuildingType as BuildingType }),
      };

      const [tasksRes, statsRes, filtersRes] = await Promise.all([
        tasksAPI.list(params),
        tasksAPI.getStats(),
        tasksAPI.getFilters(),
      ]);

      setTasks(tasksRes.tasks);
      setStats(statsRes);
      setFilters(filtersRes);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load tasks');
    } finally {
      setLoading(false);
    }
  }, [selectedRepo, selectedLabel, selectedPriority, selectedType, selectedBuildingType]);

  useEffect(() => {
    loadData();
  }, [loadData]);

  const handleStatusChange = async (taskId: string, newStatus: TaskStatus) => {
    try {
      await tasksAPI.update(taskId, { status: newStatus });
      await loadData();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to update task');
    }
  };

  const tasksByStatus = STATUS_ORDER.reduce(
    (acc, status) => {
      acc[status] = tasks.filter((t) => t.status === status);
      return acc;
    },
    {} as Record<TaskStatus, Task[]>
  );

  if (loading && tasks.length === 0) {
    return (
      <div className="flex items-center justify-center h-full">
        <div className="text-[var(--retro-text-secondary)]">Loading tasks...</div>
      </div>
    );
  }

  return (
    <div className="h-full flex flex-col p-4 overflow-hidden">
      <div className="flex-shrink-0">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-xl font-bold text-[var(--retro-text-primary)]">
            Tasks
          </h2>
          <button
            onClick={loadData}
            disabled={loading}
            className="px-3 py-1.5 bg-[var(--retro-bg-light)] border border-[var(--retro-border)] rounded text-sm text-[var(--retro-text-primary)] hover:border-[var(--retro-border-active)] transition-colors disabled:opacity-50"
          >
            {loading ? 'Loading...' : 'Refresh'}
          </button>
        </div>

        {error && (
          <div className="mb-4 p-3 bg-red-900/20 border border-red-500 rounded text-red-400 text-sm">
            {error}
          </div>
        )}

        <StatsBar stats={stats} />

        <FilterBar
          filters={filters}
          selectedRepo={selectedRepo}
          selectedLabel={selectedLabel}
          selectedPriority={selectedPriority}
          selectedType={selectedType}
          selectedBuildingType={selectedBuildingType}
          onRepoChange={setSelectedRepo}
          onLabelChange={setSelectedLabel}
          onPriorityChange={setSelectedPriority}
          onTypeChange={setSelectedType}
          onBuildingTypeChange={setSelectedBuildingType}
        />
      </div>

      <div className="flex-1 overflow-x-auto">
        <div className="flex gap-4 min-w-max pb-4">
          {STATUS_ORDER.map((status) => (
            <TaskColumn
              key={status}
              status={status}
              tasks={tasksByStatus[status]}
              onStatusChange={handleStatusChange}
            />
          ))}
        </div>
      </div>
    </div>
  );
}
