import type { ReactNode } from 'react';
import { CleanNav } from './CleanNav';

interface CleanLayoutProps {
  children: ReactNode;
}

export function CleanLayout({ children }: CleanLayoutProps) {
  return (
    <div className="theme-clean">
      <CleanNav />
      <main className="clean-container">
        {children}
      </main>
    </div>
  );
}
