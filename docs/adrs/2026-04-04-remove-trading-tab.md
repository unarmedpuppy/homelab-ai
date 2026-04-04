# ADR: Remove Trading Tab from Homelab AI Dashboard

**Date**: 2026-04-04
**Status**: Accepted

## Context

The homelab AI dashboard included a Trading tab (`/trading`) backed by `TradingDashboard.tsx` and `BinancePriceWidget.tsx`. This tab provided a lightweight view into market prices and related data.

A dedicated trading dashboard is now being built in the `jenquist-investments` repo for Jenquist Investments. That project is purpose-built for trading workflows — charting, position tracking, strategy monitoring — with far greater depth than the generic tab here could ever provide.

## Decision

Remove the Trading tab entirely from the homelab AI dashboard:

- Delete the `/trading` route and `TradingView` component from `App.tsx`
- Remove the lazy import for `TradingDashboard`
- Remove the `trading` nav item and its icon from `AppNavigation`
- Remove `'trading'` from the `ViewName` union type
- Leave `src/components/trading/` in place (not deleted) in case components are useful for reference, but they are no longer wired into the app

## Consequences

- The homelab dashboard nav is cleaner and more focused on AI infrastructure concerns
- Trading functionality lives exclusively in `jenquist-investments`, the appropriate home for it
- No data loss — the trading components were read-only market data views
