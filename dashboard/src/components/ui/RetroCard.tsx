import type { ReactNode } from 'react';

export interface RetroCardProps {
  children: ReactNode;
  title?: string;
  variant?: 'default' | 'highlight' | 'warning' | 'success';
  className?: string;
  onClick?: () => void;
  selected?: boolean;
  size?: 'sm' | 'md' | 'lg' | 'responsive';
  stackOnMobile?: boolean;
}

export function RetroCard({
  children,
  title,
  variant = 'default',
  className = '',
  onClick,
  selected = false,
  size = 'md',
  stackOnMobile = false,
}: RetroCardProps) {
  const variantClasses = {
    default: '',
    highlight: 'retro-card--highlight',
    warning: 'retro-card--warning',
    success: 'retro-card--success',
  };

  const sizeClasses = {
    sm: 'p-2',
    md: 'p-4',
    lg: 'p-6',
    responsive: 'p-3 sm:p-4 lg:p-6',
  };

  const baseClasses = [
    'retro-card',
    selected ? 'retro-card--selected' : '',
    variantClasses[variant],
    onClick ? 'cursor-pointer' : '',
    stackOnMobile ? 'retro-card--stack-mobile' : '',
    className,
  ].filter(Boolean).join(' ');

  return (
    <div
      className={baseClasses}
      onClick={onClick}
      role={onClick ? 'button' : undefined}
      tabIndex={onClick ? 0 : undefined}
      onKeyDown={onClick ? (e) => {
        if (e.key === 'Enter' || e.key === ' ') {
          e.preventDefault();
          onClick();
        }
      } : undefined}
    >
      {title && (
        <div className="retro-card__header">
          <span className="retro-card__title">{title}</span>
        </div>
      )}
      <div className={`retro-card__content ${title ? '' : sizeClasses[size]}`}>
        {children}
      </div>
    </div>
  );
}

export default RetroCard;
