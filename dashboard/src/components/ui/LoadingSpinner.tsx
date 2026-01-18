import type { ReactNode } from 'react';

export interface LoadingSpinnerProps {
  /** Size of the spinner */
  size?: 'sm' | 'md' | 'lg';
  /** Loading message to display */
  message?: string;
  /** Whether to center the spinner in its container */
  centered?: boolean;
  /** Custom class name */
  className?: string;
}

/**
 * Retro-styled loading spinner for Suspense fallbacks and loading states.
 */
export function LoadingSpinner({
  size = 'md',
  message,
  centered = true,
  className = '',
}: LoadingSpinnerProps) {
  const sizeClasses = {
    sm: 'w-4 h-4',
    md: 'w-8 h-8',
    lg: 'w-12 h-12',
  };

  const textSizeClasses = {
    sm: 'text-xs',
    md: 'text-sm',
    lg: 'text-base',
  };

  const content = (
    <div className={`flex flex-col items-center gap-3 ${className}`}>
      <div
        className={`
          ${sizeClasses[size]}
          border-2 border-[var(--retro-border)]
          border-t-[var(--retro-accent-cyan)]
          rounded-full
          animate-spin
        `}
        role="status"
        aria-label="Loading"
      />
      {message && (
        <span
          className={`
            ${textSizeClasses[size]}
            text-[var(--retro-text-muted)]
            uppercase tracking-wider
            retro-animate-pulse
          `}
        >
          {message}
        </span>
      )}
    </div>
  );

  if (centered) {
    return (
      <div className="flex items-center justify-center min-h-[200px] h-full">
        {content}
      </div>
    );
  }

  return content;
}

/**
 * Full-page loading component for route-level Suspense fallbacks.
 */
export interface PageLoadingProps {
  /** The section being loaded */
  section?: string;
}

export function PageLoading({ section }: PageLoadingProps) {
  return (
    <div className="h-full w-full flex flex-col items-center justify-center bg-[var(--retro-bg-dark)]">
      <LoadingSpinner
        size="lg"
        message={section ? `Loading ${section}...` : 'Loading...'}
        centered={false}
      />
    </div>
  );
}

/**
 * Skeleton loader for content placeholders.
 */
export interface SkeletonProps {
  /** Width of skeleton (CSS value) */
  width?: string;
  /** Height of skeleton (CSS value) */
  height?: string;
  /** Whether skeleton is circular */
  rounded?: boolean;
  /** Custom class name */
  className?: string;
}

export function Skeleton({
  width = '100%',
  height = '1rem',
  rounded = false,
  className = '',
}: SkeletonProps) {
  return (
    <div
      className={`
        bg-[var(--retro-bg-light)]
        retro-animate-pulse
        ${rounded ? 'rounded-full' : 'rounded'}
        ${className}
      `}
      style={{ width, height }}
      aria-hidden="true"
    />
  );
}

/**
 * Card skeleton for loading states.
 */
export function CardSkeleton() {
  return (
    <div className="bg-[var(--retro-bg-card)] border border-[var(--retro-border)] rounded p-4 space-y-3">
      <Skeleton width="60%" height="1rem" />
      <Skeleton width="100%" height="0.75rem" />
      <Skeleton width="80%" height="0.75rem" />
      <div className="flex gap-2 pt-2">
        <Skeleton width="4rem" height="1.5rem" rounded />
        <Skeleton width="4rem" height="1.5rem" rounded />
      </div>
    </div>
  );
}

/**
 * Wraps content with error boundary for lazy-loaded components.
 */
export interface ErrorFallbackProps {
  error?: Error;
  resetErrorBoundary?: () => void;
  children?: ReactNode;
}

export function ErrorFallback({ error, resetErrorBoundary }: ErrorFallbackProps) {
  return (
    <div className="h-full w-full flex flex-col items-center justify-center bg-[var(--retro-bg-dark)] p-4">
      <div className="max-w-md text-center space-y-4">
        <h2 className="text-lg font-bold text-[var(--retro-accent-red)] uppercase tracking-wider">
          Failed to Load
        </h2>
        <p className="text-sm text-[var(--retro-text-muted)]">
          {error?.message || 'An error occurred while loading this section.'}
        </p>
        {resetErrorBoundary && (
          <button
            onClick={resetErrorBoundary}
            className="
              px-4 py-2
              bg-[var(--retro-bg-medium)]
              border border-[var(--retro-border)]
              text-[var(--retro-text-primary)]
              text-sm uppercase tracking-wider
              rounded
              hover:border-[var(--retro-accent-cyan)]
              transition-colors
            "
          >
            Try Again
          </button>
        )}
      </div>
    </div>
  );
}

export default LoadingSpinner;
