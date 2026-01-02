import type { ActivityDay } from '../types/api';

interface Props {
  data: ActivityDay[];
}

export default function ActivityHeatmap({ data }: Props) {
  if (!data || data.length === 0) {
    return (
      <div className="text-gray-500 dark:text-gray-400 text-sm">
        No activity data available
      </div>
    );
  }

  // Group by week (7 days) for display
  const weeks: ActivityDay[][] = [];
  for (let i = 0; i < data.length; i += 7) {
    weeks.push(data.slice(i, i + 7));
  }

  // Calculate max count for color scaling
  const maxCount = Math.max(...data.map(d => d.count), 1);

  const getColor = (count: number): string => {
    if (count === 0) return 'bg-gray-100 dark:bg-gray-700';
    const intensity = count / maxCount;
    if (intensity < 0.25) return 'bg-green-200 dark:bg-green-900';
    if (intensity < 0.5) return 'bg-green-400 dark:bg-green-700';
    if (intensity < 0.75) return 'bg-green-600 dark:bg-green-500';
    return 'bg-green-800 dark:bg-green-300';
  };

  return (
    <div className="space-y-2">
      <div className="flex gap-1 overflow-x-auto pb-2">
        {weeks.map((week, weekIdx) => (
          <div key={weekIdx} className="flex flex-col gap-1">
            {week.map((day, dayIdx) => (
              <div
                key={dayIdx}
                className={`w-3 h-3 rounded-sm ${getColor(day.count)} hover:ring-2 hover:ring-blue-500 transition-all cursor-pointer`}
                title={`${day.date}: ${day.count} requests`}
              />
            ))}
          </div>
        ))}
      </div>
      <div className="flex items-center gap-2 text-xs text-gray-600 dark:text-gray-400">
        <span>Less</span>
        <div className="flex gap-1">
          <div className="w-3 h-3 bg-gray-100 dark:bg-gray-700 rounded-sm" />
          <div className="w-3 h-3 bg-green-200 dark:bg-green-900 rounded-sm" />
          <div className="w-3 h-3 bg-green-400 dark:bg-green-700 rounded-sm" />
          <div className="w-3 h-3 bg-green-600 dark:bg-green-500 rounded-sm" />
          <div className="w-3 h-3 bg-green-800 dark:bg-green-300 rounded-sm" />
        </div>
        <span>More</span>
      </div>
    </div>
  );
}
