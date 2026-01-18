import type { ReactNode } from 'react';

interface RetroCardProps {
  children: ReactNode;
  title?: string;
  variant?: 'default' | 'highlight' | 'warning' | 'success' | 'danger';
  className?: string;
  onClick?: () => void;
  selected?: boolean;
  size?: 'sm' | 'md' | 'lg';
}

export function RetroCard({
  children,
  title,
  variant = 'default',
  className = '',
  onClick,
  selected = false,
  size = 'md',
}: RetroCardProps) {
  const variantClasses = {
    default: '',
    highlight: 'border-[var(--retro-border-highlight)]',
    warning: 'border-[var(--retro-accent-orange)]',
    success: 'border-[var(--retro-accent-green)]',
    danger: 'border-[var(--retro-accent-red)]',
  };

  const sizeClasses = {
    sm: 'p-2',
    md: 'p-4',
    lg: 'p-6',
  };

  const baseClasses = `
    retro-card
    ${selected ? 'retro-card-selected' : ''}
    ${variantClasses[variant]}
    ${onClick ? 'cursor-pointer' : ''}
    ${className}
  `.trim();

  return (
    <div className={baseClasses} onClick={onClick}>
      {title && (
        <div className="retro-panel-header -m-[2px] mb-3 rounded-t">
          <span>{title}</span>
        </div>
      )}
      <div className={title ? '' : sizeClasses[size]}>
        {children}
      </div>
    </div>
  );
}

export default RetroCard;
