'use client';

import ErrorBoundary from './ErrorBoundary';

interface DashboardWrapperProps {
  children: React.ReactNode;
}

export default function DashboardWrapper({ children }: DashboardWrapperProps) {
  return <ErrorBoundary>{children}</ErrorBoundary>;
}

