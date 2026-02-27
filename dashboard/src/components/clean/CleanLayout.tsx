import type { ReactNode } from 'react';
import { CleanNav } from './CleanNav';

interface CleanLayoutProps {
  children: ReactNode;
  noNav?: boolean;
}

export function CleanLayout({ children, noNav = false }: CleanLayoutProps) {
  return (
    <div className="theme-clean">
      {!noNav && <CleanNav />}
      <main className="clean-container">
        {children}
      </main>
    </div>
  );
}
