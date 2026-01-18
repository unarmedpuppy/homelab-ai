import { useState, useEffect, useRef } from 'react';

/**
 * Custom hook that returns the current document visibility state.
 * Uses the Page Visibility API to detect when the tab is hidden/visible.
 *
 * @returns 'visible' | 'hidden' - The current visibility state
 */
export function useDocumentVisibility(): DocumentVisibilityState {
  const [visibility, setVisibility] = useState<DocumentVisibilityState>(
    typeof document !== 'undefined' ? document.visibilityState : 'visible'
  );

  useEffect(() => {
    if (typeof document === 'undefined') return;

    const handleVisibilityChange = () => {
      setVisibility(document.visibilityState);
    };

    document.addEventListener('visibilitychange', handleVisibilityChange);
    return () => {
      document.removeEventListener('visibilitychange', handleVisibilityChange);
    };
  }, []);

  return visibility;
}

/**
 * Returns true when the document is visible, false when hidden.
 */
export function useIsDocumentVisible(): boolean {
  return useDocumentVisibility() === 'visible';
}

/**
 * Configuration for visibility-aware polling.
 */
interface UseVisibilityPollingOptions {
  /** Callback to execute on each poll */
  callback: () => void | Promise<void>;
  /** Polling interval in milliseconds when document is visible */
  interval: number;
  /** Whether polling is enabled at all (can be used to pause polling) */
  enabled?: boolean;
  /** Whether to execute callback immediately on mount */
  immediate?: boolean;
}

/**
 * Custom hook for polling that automatically pauses when the tab is hidden.
 * This prevents unnecessary network requests and CPU usage when the user
 * isn't looking at the page.
 *
 * Features:
 * - Pauses polling when tab is hidden
 * - Resumes polling when tab becomes visible
 * - Executes callback immediately on visibility change (to refresh stale data)
 * - Proper cleanup on unmount
 *
 * @param options - Polling configuration
 *
 * @example
 * ```tsx
 * useVisibilityPolling({
 *   callback: fetchData,
 *   interval: 5000,
 *   enabled: isRunning,
 *   immediate: true,
 * });
 * ```
 */
export function useVisibilityPolling({
  callback,
  interval,
  enabled = true,
  immediate = false,
}: UseVisibilityPollingOptions): void {
  const isVisible = useIsDocumentVisible();
  const savedCallback = useRef(callback);
  const wasHidden = useRef(false);

  // Update saved callback ref when callback changes
  useEffect(() => {
    savedCallback.current = callback;
  }, [callback]);

  useEffect(() => {
    // Don't start polling if disabled
    if (!enabled) {
      return;
    }

    // Track visibility transitions to refresh on tab return
    if (!isVisible) {
      wasHidden.current = true;
      return; // Don't poll while hidden
    }

    // If we just became visible after being hidden, fetch immediately to refresh stale data
    if (wasHidden.current) {
      wasHidden.current = false;
      savedCallback.current();
    }

    // Initial fetch if immediate is set
    if (immediate) {
      savedCallback.current();
    }

    // Set up polling interval
    const id = setInterval(() => {
      savedCallback.current();
    }, interval);

    return () => {
      clearInterval(id);
    };
  }, [isVisible, interval, enabled, immediate]);
}

/**
 * Hook for conditional polling based on application state.
 * Supports different intervals for different states (e.g., faster polling when running).
 */
interface UseConditionalPollingOptions {
  callback: () => void | Promise<void>;
  /** Interval when in active state */
  activeInterval: number;
  /** Interval when in idle state */
  idleInterval: number;
  /** Whether the application is in active state */
  isActive: boolean;
  /** Whether to execute callback immediately */
  immediate?: boolean;
}

export function useConditionalPolling({
  callback,
  activeInterval,
  idleInterval,
  isActive,
  immediate = false,
}: UseConditionalPollingOptions): void {
  const interval = isActive ? activeInterval : idleInterval;

  useVisibilityPolling({
    callback,
    interval,
    enabled: true,
    immediate,
  });
}

export default useDocumentVisibility;
