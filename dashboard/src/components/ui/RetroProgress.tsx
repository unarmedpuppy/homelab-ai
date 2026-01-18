interface RetroProgressProps {
  value: number; // 0-100
  showLabel?: boolean;
  variant?: 'default' | 'success' | 'warning' | 'danger';
  size?: 'sm' | 'md' | 'lg';
  className?: string;
}

export function RetroProgress({
  value,
  showLabel = false,
  variant = 'default',
  size = 'md',
  className = '',
}: RetroProgressProps) {
  const clampedValue = Math.min(100, Math.max(0, value));

  const variantClasses = {
    default: '',
    success: 'retro-progress-bar-success',
    warning: 'retro-progress-bar-warning',
    danger: 'retro-progress-bar-danger',
  };

  const sizeClasses = {
    sm: 'h-1',
    md: 'h-2',
    lg: 'h-3',
  };

  // Auto-determine variant based on value if not specified
  const autoVariant = variant === 'default'
    ? clampedValue >= 100
      ? 'success'
      : clampedValue >= 75
        ? 'warning'
        : 'default'
    : variant;

  return (
    <div className={`flex items-center gap-2 ${className}`.trim()}>
      <div className={`retro-progress flex-1 ${sizeClasses[size]}`}>
        <div
          className={`retro-progress-bar ${variantClasses[autoVariant]} ${sizeClasses[size]}`}
          style={{ width: `${clampedValue}%` }}
        />
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
