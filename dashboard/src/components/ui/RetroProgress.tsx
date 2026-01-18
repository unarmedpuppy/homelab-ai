export interface RetroProgressProps {
  value: number; // 0-100
  showLabel?: boolean;
  variant?: 'default' | 'success' | 'warning' | 'danger';
  size?: 'sm' | 'md';
  segments?: number; // Number of segments (default 10)
  className?: string;
}

export function RetroProgress({
  value,
  showLabel = false,
  variant = 'default',
  size = 'md',
  segments = 10,
  className = '',
}: RetroProgressProps) {
  const clampedValue = Math.min(100, Math.max(0, value));

  // Calculate how many segments should be filled
  const filledSegments = Math.round((clampedValue / 100) * segments);

  const variantColors = {
    default: 'var(--retro-accent-cyan)',
    success: 'var(--retro-accent-green)',
    warning: 'var(--retro-accent-yellow)',
    danger: 'var(--retro-accent-red)',
  };

  const sizeHeights = {
    sm: '6px',
    md: '8px',
  };

  const segmentHeight = sizeHeights[size];
  const fillColor = variantColors[variant];

  return (
    <div className={`flex items-center gap-2 ${className}`.trim()}>
      <div
        className="retro-progress-segmented"
        style={{
          display: 'flex',
          gap: '2px',
          background: 'var(--retro-bg-dark)',
          border: '1px solid var(--retro-border)',
          padding: '2px',
          flex: 1,
          borderRadius: 'var(--retro-radius-sm)',
        }}
      >
        {Array.from({ length: segments }, (_, index) => {
          const isFilled = index < filledSegments;
          return (
            <div
              key={index}
              className="retro-progress__segment"
              style={{
                flex: 1,
                height: segmentHeight,
                background: isFilled ? fillColor : 'var(--retro-bg-medium)',
                transition: 'background 0.2s ease',
                borderRadius: '1px',
              }}
            />
          );
        })}
      </div>
      {showLabel && (
        <span className="text-xs font-bold text-[var(--retro-text-secondary)] min-w-[3ch] text-right">
          {Math.round(clampedValue)}%
        </span>
      )}
    </div>
  );
}

export default RetroProgress;
