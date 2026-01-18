import type { ButtonHTMLAttributes } from 'react';

export interface RetroButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  children: React.ReactNode;
  variant?: 'primary' | 'secondary' | 'danger' | 'ghost' | 'success' | 'warning';
  size?: 'sm' | 'md' | 'lg';
  disabled?: boolean;
  loading?: boolean;
  type?: 'button' | 'submit';
  fullWidth?: boolean;
  icon?: React.ReactNode;
}

function LoadingSpinner() {
  return (
    <svg
      className="retro-btn-spinner"
      width="16"
      height="16"
      viewBox="0 0 16 16"
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
    >
      <circle
        cx="8"
        cy="8"
        r="6"
        stroke="currentColor"
        strokeWidth="2"
        strokeLinecap="round"
        strokeDasharray="32"
        strokeDashoffset="12"
      />
    </svg>
  );
}

export function RetroButton({
  children,
  variant = 'secondary',
  size = 'md',
  loading = false,
  disabled,
  fullWidth = false,
  icon,
  className = '',
  type = 'button',
  ...props
}: RetroButtonProps) {
  const variantClasses: Record<NonNullable<RetroButtonProps['variant']>, string> = {
    primary: 'retro-btn-primary',
    secondary: 'retro-btn-secondary',
    danger: 'retro-btn-danger',
    ghost: 'retro-btn-ghost',
    success: 'retro-btn-success',
    warning: 'retro-btn-warning',
  };

  const sizeClasses: Record<NonNullable<RetroButtonProps['size']>, string> = {
    sm: 'retro-btn-sm',
    md: 'retro-btn-md',
    lg: 'retro-btn-lg',
  };

  const classes = [
    'retro-btn',
    variantClasses[variant],
    sizeClasses[size],
    fullWidth ? 'retro-btn-full-width' : '',
    loading ? 'retro-btn-loading' : '',
    className,
  ].filter(Boolean).join(' ');

  return (
    <button
      className={classes}
      disabled={disabled || loading}
      type={type}
      {...props}
    >
      {loading ? (
        <LoadingSpinner />
      ) : icon ? (
        <span className="retro-btn-icon">{icon}</span>
      ) : null}
      <span className={loading ? 'retro-btn-text-loading' : ''}>{children}</span>
    </button>
  );
}

export default RetroButton;
