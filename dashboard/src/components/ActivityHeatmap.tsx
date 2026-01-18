import type { ActivityDay } from '../types/api';

interface Props {
  data: ActivityDay[];
}

// Retro color palette for activity heatmap
const HEATMAP_COLORS = {
  empty: 'var(--retro-bg-dark)',
  level1: 'rgba(0, 255, 65, 0.2)',  // --retro-accent-green at 20%
  level2: 'rgba(0, 255, 65, 0.4)',  // --retro-accent-green at 40%
  level3: 'rgba(0, 255, 65, 0.6)',  // --retro-accent-green at 60%
  level4: 'var(--retro-accent-green)',  // Full green
};

export default function ActivityHeatmap({ data }: Props) {
  if (!data || data.length === 0) {
    return (
      <div className="text-[var(--retro-text-muted)] text-sm uppercase tracking-wider">
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
    if (count === 0) return HEATMAP_COLORS.empty;
    const intensity = count / maxCount;
    if (intensity < 0.25) return HEATMAP_COLORS.level1;
    if (intensity < 0.5) return HEATMAP_COLORS.level2;
    if (intensity < 0.75) return HEATMAP_COLORS.level3;
    return HEATMAP_COLORS.level4;
  };

  return (
    <div className="space-y-3">
      <div className="flex gap-1 overflow-x-auto pb-2 scrollbar-thin">
        {weeks.map((week, weekIdx) => (
          <div key={weekIdx} className="flex flex-col gap-1 flex-shrink-0">
            {week.map((day, dayIdx) => (
              <div
                key={dayIdx}
                className="w-3 h-3 sm:w-4 sm:h-4 rounded-sm transition-all cursor-pointer hover:ring-2 hover:ring-[var(--retro-accent-cyan)] border border-[var(--retro-border)]"
                style={{ backgroundColor: getColor(day.count) }}
                title={`${day.date}: ${day.count} requests`}
              />
            ))}
          </div>
        ))}
      </div>
      {/* Legend */}
      <div className="flex items-center gap-2 text-xs text-[var(--retro-text-muted)]">
        <span className="uppercase tracking-wider">Less</span>
        <div className="flex gap-1">
          <div
            className="w-3 h-3 rounded-sm border border-[var(--retro-border)]"
            style={{ backgroundColor: HEATMAP_COLORS.empty }}
          />
          <div
            className="w-3 h-3 rounded-sm border border-[var(--retro-border)]"
            style={{ backgroundColor: HEATMAP_COLORS.level1 }}
          />
          <div
            className="w-3 h-3 rounded-sm border border-[var(--retro-border)]"
            style={{ backgroundColor: HEATMAP_COLORS.level2 }}
          />
          <div
            className="w-3 h-3 rounded-sm border border-[var(--retro-border)]"
            style={{ backgroundColor: HEATMAP_COLORS.level3 }}
          />
          <div
            className="w-3 h-3 rounded-sm border border-[var(--retro-border)]"
            style={{ backgroundColor: HEATMAP_COLORS.level4 }}
          />
        </div>
        <span className="uppercase tracking-wider">More</span>
      </div>
    </div>
  );
}
