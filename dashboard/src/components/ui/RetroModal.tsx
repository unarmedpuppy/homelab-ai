import type { ReactNode } from 'react';
import { useEffect } from 'react';
import { RetroButton } from './RetroButton';

interface RetroModalProps {
  isOpen: boolean;
  onClose: () => void;
  title: string;
  children: ReactNode;
  footer?: ReactNode;
  fullscreenOnMobile?: boolean;
  size?: 'sm' | 'md' | 'lg';
}

export function RetroModal({
  isOpen,
  onClose,
  title,
  children,
  footer,
  fullscreenOnMobile = true,
  size = 'md',
}: RetroModalProps) {
  // Handle escape key
  useEffect(() => {
    const handleEscape = (e: KeyboardEvent) => {
      if (e.key === 'Escape' && isOpen) {
        onClose();
      }
    };

    document.addEventListener('keydown', handleEscape);
    return () => document.removeEventListener('keydown', handleEscape);
  }, [isOpen, onClose]);

  // Prevent body scroll when modal is open
  useEffect(() => {
    if (isOpen) {
      document.body.style.overflow = 'hidden';
    } else {
      document.body.style.overflow = '';
    }
    return () => {
      document.body.style.overflow = '';
    };
  }, [isOpen]);

  if (!isOpen) return null;

  const sizeClasses = {
    sm: 'max-w-sm',
    md: 'max-w-md',
    lg: 'max-w-2xl',
  };

  return (
    <>
      {/* Overlay */}
      <div className="retro-overlay" onClick={onClose} />

      {/* Modal */}
      <div
        className={`retro-modal ${fullscreenOnMobile ? 'retro-modal-fullscreen sm:top-1/2 sm:left-1/2 sm:transform sm:-translate-x-1/2 sm:-translate-y-1/2 sm:w-[calc(100%-2rem)] sm:max-h-[calc(100vh-4rem)] sm:rounded' : ''} ${sizeClasses[size]}`}
        role="dialog"
        aria-modal="true"
        aria-labelledby="modal-title"
      >
        {/* Header */}
        <div className="retro-modal-header">
          <h2 id="modal-title" className="retro-modal-title">
            {title}
          </h2>
          <RetroButton
            variant="ghost"
            size="sm"
            onClick={onClose}
            aria-label="Close modal"
          >
            ✕
          </RetroButton>
        </div>

        {/* Body */}
        <div className="retro-modal-body">
          {children}
        </div>

        {/* Footer */}
        {footer && (
          <div className="retro-modal-footer">
            {footer}
          </div>
        )}
      </div>
    </>
  );
}

export default RetroModal;
