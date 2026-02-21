import { type InputHTMLAttributes, forwardRef } from 'react';

export interface RetroToggleProps extends Omit<InputHTMLAttributes<HTMLInputElement>, 'type' | 'size'> {
  label?: string;
  size?: 'sm' | 'md';
}

export const RetroToggle = forwardRef<HTMLInputElement, RetroToggleProps>(
  ({ label, size = 'md', className = '', disabled, checked, ...props }, ref) => {
    const trackW = size === 'sm' ? 'w-9' : 'w-11';
    const trackH = size === 'sm' ? 'h-5' : 'h-6';
    const thumbSize = size === 'sm' ? 'h-3.5 w-3.5' : 'h-4.5 w-4.5';
    const translateOn = size === 'sm' ? 'translate-x-4' : 'translate-x-5';

    return (
      <label
        className={`inline-flex items-center gap-2 ${disabled ? 'opacity-50 cursor-not-allowed' : 'cursor-pointer'} ${className}`}
      >
        <input
          ref={ref}
          type="checkbox"
          className="sr-only"
          checked={checked}
          disabled={disabled}
          {...props}
        />
        <span
          className={`
            relative inline-flex ${trackW} ${trackH} shrink-0 items-center rounded-full
            border transition-colors duration-200
            ${checked
              ? 'bg-[var(--retro-accent-green)] border-[var(--retro-accent-green)]'
              : 'bg-[var(--retro-bg-dark)] border-[var(--retro-border)]'
            }
          `}
        >
          <span
            className={`
              inline-block ${thumbSize} rounded-full bg-white shadow-sm
              transition-transform duration-200 ml-0.5
              ${checked ? translateOn : 'translate-x-0'}
            `}
          />
        </span>
        {label && (
          <span className="text-sm text-[var(--retro-text-primary)]">{label}</span>
        )}
      </label>
    );
  }
);

RetroToggle.displayName = 'RetroToggle';

export default RetroToggle;
