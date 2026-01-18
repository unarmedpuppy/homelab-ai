import type { ReactNode, ButtonHTMLAttributes } from 'react';

interface RetroButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  children: ReactNode;
  variant?: 'default' | 'primary' | 'success' | 'danger' | 'warning' | 'ghost';
  size?: 'sm' | 'md' | 'lg';
  loading?: boolean;
}

export function RetroButton({
  children,
  variant = 'default',
  size = 'md',
  loading = false,
  disabled,
  className = '',
  ...props
}: RetroButtonProps) {
  const variantClasses = {
    default: '',
    primary: 'retro-btn-primary',
    success: 'retro-btn-success',
    danger: 'retro-btn-danger',
    warning: 'retro-btn-warning',
    ghost: 'retro-btn-ghost',
  };

  const sizeClasses = {
    sm: 'text-xs px-2 py-1 min-h-8',
    md: 'text-sm px-4 py-2',
    lg: 'text-base px-6 py-3',
  };

  return (
    <button
      className={`retro-btn ${variantClasses[variant]} ${sizeClasses[size]} ${className}`.trim()}
      disabled={disabled || loading}
      {...props}
    >
      {loading ? (
        <>
          <span className="retro-animate-pulse">...</span>
        </>
      ) : (
        children
      )}
    </button>
  );
}

export default RetroButton;
