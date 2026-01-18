import type { SelectHTMLAttributes } from 'react';
import { forwardRef } from 'react';

export interface RetroSelectOption {
  value: string;
  label: string;
  disabled?: boolean;
}

export interface RetroSelectProps extends Omit<SelectHTMLAttributes<HTMLSelectElement>, 'children' | 'size'> {
  label?: string;
  error?: string;
  options: RetroSelectOption[];
  placeholder?: string;
  size?: 'sm' | 'md';
}

export const RetroSelect = forwardRef<HTMLSelectElement, RetroSelectProps>(
  ({ label, error, options, placeholder, size = 'md', className = '', id, ...props }, ref) => {
    const selectId = id || label?.toLowerCase().replace(/\s+/g, '-');

    const sizeClasses = {
      sm: 'retro-select-sm',
      md: '',
    };

    return (
      <div className="space-y-1">
        {label && (
          <label
            htmlFor={selectId}
            className="block text-xs font-semibold uppercase tracking-wider text-[var(--retro-text-secondary)]"
          >
            {label}
          </label>
        )}
        <select
          ref={ref}
          id={selectId}
          className={`retro-select ${sizeClasses[size]} ${error ? 'border-[var(--retro-accent-red)]' : ''} ${className}`.trim()}
          {...props}
        >
          {placeholder && (
            <option value="" disabled>
              {placeholder}
            </option>
          )}
          {options.map((option) => (
            <option
              key={option.value}
              value={option.value}
              disabled={option.disabled}
            >
              {option.label}
            </option>
          ))}
        </select>
        {error && (
          <p className="text-xs text-[var(--retro-accent-red)]">{error}</p>
        )}
      </div>
    );
  }
);

RetroSelect.displayName = 'RetroSelect';

export default RetroSelect;
