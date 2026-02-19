import type { InputHTMLAttributes } from 'react';
import { forwardRef } from 'react';

export interface RetroInputProps extends InputHTMLAttributes<HTMLInputElement> {
  label?: string;
  error?: string;
}

export const RetroInput = forwardRef<HTMLInputElement, RetroInputProps>(
  ({ label, error, className = '', id, ...props }, ref) => {
    const inputId = id || label?.toLowerCase().replace(/\s+/g, '-');

    return (
      <div className="space-y-1">
        {label && (
          <label
            htmlFor={inputId}
            className="block text-xs font-semibold text-[var(--retro-text-secondary)]"
          >
            {label}
          </label>
        )}
        <input
          ref={ref}
          id={inputId}
          className={`retro-input ${error ? 'border-[var(--retro-accent-red)]' : ''} ${className}`.trim()}
          {...props}
        />
        {error && (
          <p className="text-xs text-[var(--retro-accent-red)]">{error}</p>
        )}
      </div>
    );
  }
);

RetroInput.displayName = 'RetroInput';

export default RetroInput;
