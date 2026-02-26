import { useQuery } from '@tanstack/react-query';
import { fetchTasks } from '../api/tasksApi';
import { Task, BuildingType } from '../types/game';

// Fallback building_type from task.type when building_type is null
const TYPE_TO_BUILDING: Record<string, BuildingType> = {
  engineering: 'barracks',
  research:    'university',
  personal:    'town-center',
  home:        'town-center',
  family:      'town-center',
};

function normalize(task: Task): Task {
  if (task.building_type) return task;
  const fallback = TYPE_TO_BUILDING[task.type] ?? 'barracks';
  return { ...task, building_type: fallback };
}

export function useTasks() {
  return useQuery<Task[]>({
    queryKey: ['tasks'],
    queryFn: async () => {
      const tasks = await fetchTasks({ status: 'OPEN' });
      return tasks.map(normalize);
    },
    refetchInterval: 30000,
    staleTime: 15000,
  });
}

// Group open tasks by building_type (after normalization)
export function useTasksByBuilding() {
  const { data: tasks = [] } = useTasks();
  const grouped = new Map<BuildingType, Task[]>();
  for (const task of tasks) {
    if (!grouped.has(task.building_type)) grouped.set(task.building_type, []);
    grouped.get(task.building_type)!.push(task);
  }
  return grouped;
}
