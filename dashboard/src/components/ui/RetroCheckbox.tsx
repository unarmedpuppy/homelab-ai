import type { InputHTMLAttributes } from 'react';
import { forwardRef } from 'react';

interface RetroCheckboxProps extends Omit<InputHTMLAttributes<HTMLInputElement>, 'type'> {
  label: string;
}

export const RetroCheckbox = forwardRef<HTMLInputElement, RetroCheckboxProps>(
  ({ label, className = '', id, ...props }, ref) => {
    const checkboxId = id || label.toLowerCase().replace(/\s+/g, '-');

    return (
      <label htmlFor={checkboxId} className={`retro-checkbox ${className}`.trim()}>
        <input
          ref={ref}
          type="checkbox"
          id={checkboxId}
          {...props}
        />
        <span className="text-sm text-[var(--retro-text-primary)]">{label}</span>
      </label>
    );
  }
);

RetroCheckbox.displayName = 'RetroCheckbox';

export default RetroCheckbox;
