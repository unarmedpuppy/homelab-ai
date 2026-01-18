import React, { useState, useCallback, useEffect } from 'react';
import { useIsMobile, useIsTablet } from '../../hooks/useMediaQuery';
import { MobileNav, type MobileNavView } from './MobileNav';

export interface ResponsiveLayoutProps {
  /** Main content area */
  children: React.ReactNode;
  /** Sidebar content (typically navigation + filters) */
  sidebar?: React.ReactNode;
  /** Header content for sidebar (shown above navigation) */
  sidebarHeader?: React.ReactNode;
  /** Control sidebar collapse state externally */
  sidebarCollapsed?: boolean;
  /** Callback when sidebar toggle is clicked */
  onToggleSidebar?: () => void;
  /** Width of the sidebar (default: 320px / w-80) */
  sidebarWidth?: number | string;
  /** Current view for mobile nav highlighting */
  currentView?: MobileNavView;
  /** Whether to show mobile bottom navigation (default: true) */
  showMobileNav?: boolean;
  /** Additional CSS classes for main container */
  className?: string;
  /** Additional CSS classes for main content area */
  contentClassName?: string;
}

/**
 * ResponsiveLayout provides a mobile-first responsive container.
 *
 * Desktop (>= 1024px): Persistent sidebar (w-80)
 * Tablet (640-1023px): Collapsible sidebar (slide-out)
 * Mobile (< 640px): Hamburger menu + MobileNav bottom bar
 *
 * The layout handles:
 * - Automatic sidebar visibility based on viewport
 * - Slide-out animation for tablet sidebar
 * - Mobile hamburger menu toggle
 * - Bottom padding for mobile nav clearance
 * - Safe area insets for mobile devices
 */
export function ResponsiveLayout({
  children,
  sidebar,
  sidebarHeader,
  sidebarCollapsed: externalCollapsed,
  onToggleSidebar,
  sidebarWidth = 320,
  currentView,
  showMobileNav = true,
  className = '',
  contentClassName = '',
}: ResponsiveLayoutProps) {
  const isMobile = useIsMobile();
  const isTablet = useIsTablet();
  const isDesktop = !isMobile && !isTablet;

  // Internal collapse state (used when external control not provided)
  const [internalCollapsed, setInternalCollapsed] = useState(true);

  // Use external state if provided, otherwise use internal
  const isCollapsed = externalCollapsed ?? internalCollapsed;

  const handleToggle = useCallback(() => {
    if (onToggleSidebar) {
      onToggleSidebar();
    } else {
      setInternalCollapsed((prev) => !prev);
    }
  }, [onToggleSidebar]);

  // Auto-collapse sidebar when switching to mobile/tablet
  useEffect(() => {
    if ((isMobile || isTablet) && !externalCollapsed) {
      setInternalCollapsed(true);
    }
  }, [isMobile, isTablet, externalCollapsed]);

  // Close sidebar when clicking overlay
  const handleOverlayClick = useCallback(() => {
    if (!isCollapsed && (isMobile || isTablet)) {
      handleToggle();
    }
  }, [isCollapsed, isMobile, isTablet, handleToggle]);

  // Calculate sidebar width value for CSS
  const sidebarWidthValue = typeof sidebarWidth === 'number' ? `${sidebarWidth}px` : sidebarWidth;

  return (
    <div
      className={`retro-responsive-layout ${className}`.trim()}
      style={{
        '--sidebar-width': sidebarWidthValue,
      } as React.CSSProperties}
    >
      {/* Mobile hamburger button */}
      {sidebar && !isDesktop && (
        <button
          type="button"
          className="retro-hamburger-btn retro-hide-desktop"
          onClick={handleToggle}
          aria-label={isCollapsed ? 'Open menu' : 'Close menu'}
          aria-expanded={!isCollapsed}
        >
          <span className="retro-hamburger-icon">
            {isCollapsed ? '☰' : '✕'}
          </span>
        </button>
      )}

      {/* Overlay for mobile/tablet when sidebar is open */}
      {!isDesktop && !isCollapsed && (
        <div
          className="retro-sidebar-overlay"
          onClick={handleOverlayClick}
          aria-hidden="true"
        />
      )}

      {/* Sidebar */}
      {sidebar && (
        <aside
          className={`
            retro-sidebar
            ${isDesktop ? 'retro-sidebar-desktop' : ''}
            ${isTablet ? 'retro-sidebar-tablet' : ''}
            ${isMobile ? 'retro-sidebar-mobile' : ''}
            ${isCollapsed && !isDesktop ? 'retro-sidebar-collapsed' : ''}
          `.trim()}
          style={{ width: sidebarWidthValue }}
        >
          {/* Optional sidebar header */}
          {sidebarHeader && (
            <div className="retro-sidebar-header">
              {sidebarHeader}
            </div>
          )}

          {/* Sidebar content */}
          <div className="retro-sidebar-content">
            {sidebar}
          </div>

          {/* Close button inside sidebar for mobile/tablet */}
          {!isDesktop && (
            <button
              type="button"
              className="retro-sidebar-close-btn"
              onClick={handleToggle}
              aria-label="Close sidebar"
            >
              ✕
            </button>
          )}
        </aside>
      )}

      {/* Main content */}
      <main
        className={`
          retro-main-content
          ${sidebar && isDesktop ? 'retro-main-content-with-sidebar' : ''}
          ${showMobileNav && isMobile ? 'retro-with-mobile-nav' : ''}
          ${contentClassName}
        `.trim()}
      >
        {children}
      </main>

      {/* Mobile navigation */}
      {showMobileNav && <MobileNav currentView={currentView} />}
    </div>
  );
}

export default ResponsiveLayout;
