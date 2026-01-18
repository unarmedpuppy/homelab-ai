import { useState, useEffect, useCallback } from 'react';

/**
 * Custom hook that returns true if the given media query matches.
 * Uses window.matchMedia API with proper cleanup and SSR safety.
 *
 * @param query - CSS media query string (e.g., "(min-width: 640px)")
 * @returns boolean indicating if the query matches
 */
export function useMediaQuery(query: string): boolean {
  const getMatches = useCallback(() => {
    // SSR safety check
    if (typeof window === 'undefined') {
      return false;
    }
    return window.matchMedia(query).matches;
  }, [query]);

  const [matches, setMatches] = useState(getMatches);

  useEffect(() => {
    // SSR safety check
    if (typeof window === 'undefined') {
      return;
    }

    const mediaQueryList = window.matchMedia(query);

    // Update state on initial render
    setMatches(mediaQueryList.matches);

    // Handler for changes
    const handleChange = (event: MediaQueryListEvent) => {
      setMatches(event.matches);
    };

    // Modern browsers
    if (mediaQueryList.addEventListener) {
      mediaQueryList.addEventListener('change', handleChange);
      return () => mediaQueryList.removeEventListener('change', handleChange);
    } else {
      // Fallback for older browsers
      mediaQueryList.addListener(handleChange);
      return () => mediaQueryList.removeListener(handleChange);
    }
  }, [query]);

  return matches;
}

// Breakpoints matching CSS variables in retro-theme.css
const BREAKPOINTS = {
  sm: 640,
  md: 768,
  lg: 1024,
  xl: 1280,
} as const;

/**
 * Returns true if viewport width is less than 640px (mobile devices).
 */
export function useIsMobile(): boolean {
  return useMediaQuery(`(max-width: ${BREAKPOINTS.sm - 1}px)`);
}

/**
 * Returns true if viewport width is between 640px and 1023px (tablets).
 */
export function useIsTablet(): boolean {
  return useMediaQuery(`(min-width: ${BREAKPOINTS.sm}px) and (max-width: ${BREAKPOINTS.lg - 1}px)`);
}

/**
 * Returns true if viewport width is 1024px or greater (desktop).
 */
export function useIsDesktop(): boolean {
  return useMediaQuery(`(min-width: ${BREAKPOINTS.lg}px)`);
}

/**
 * Returns the current breakpoint name based on viewport width.
 */
export function useBreakpoint(): 'mobile' | 'tablet' | 'desktop' {
  const isMobile = useIsMobile();
  const isDesktop = useIsDesktop();

  if (isMobile) return 'mobile';
  if (isDesktop) return 'desktop';
  return 'tablet';
}

/**
 * Returns true if the user prefers reduced motion.
 * Useful for disabling animations for accessibility.
 */
export function usePrefersReducedMotion(): boolean {
  return useMediaQuery('(prefers-reduced-motion: reduce)');
}

export default useMediaQuery;
