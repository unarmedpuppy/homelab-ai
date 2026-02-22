import { useState, useEffect, useRef, useCallback } from 'react';
import { useIsDocumentVisible } from './useDocumentVisibility';
import type {
  MercuryStatus,
  PortfolioSummary,
  Position,
  Trade,
  RiskStatus,
  ActiveMarket,
  MercurySSEState,
} from '../types/trading';

const MERCURY_API_URL = import.meta.env.VITE_MERCURY_API_URL || '/mercury-api';

export function useMercurySSE(enabled: boolean): MercurySSEState {
  const [connected, setConnected] = useState(false);
  const [status, setStatus] = useState<MercuryStatus | null>(null);
  const [portfolio, setPortfolio] = useState<PortfolioSummary | null>(null);
  const [positions, setPositions] = useState<Position[]>([]);
  const [trades, setTrades] = useState<Trade[]>([]);
  const [risk, setRisk] = useState<RiskStatus | null>(null);
  const [markets, setMarkets] = useState<ActiveMarket[]>([]);
  const [lastUpdated, setLastUpdated] = useState<number | null>(null);

  const esRef = useRef<EventSource | null>(null);
  const isVisible = useIsDocumentVisible();

  const connect = useCallback(() => {
    if (esRef.current) {
      esRef.current.close();
      esRef.current = null;
    }

    const es = new EventSource(`${MERCURY_API_URL}/api/v1/stream`);
    esRef.current = es;

    es.onopen = () => {
      setConnected(true);
    };

    es.onerror = () => {
      setConnected(false);
      // EventSource auto-reconnects; no manual logic needed
    };

    es.addEventListener('status', (e: MessageEvent) => {
      try {
        setStatus(JSON.parse(e.data) as MercuryStatus);
        setLastUpdated(Date.now());
      } catch { /* ignore parse errors */ }
    });

    es.addEventListener('portfolio', (e: MessageEvent) => {
      try {
        setPortfolio(JSON.parse(e.data) as PortfolioSummary);
        setLastUpdated(Date.now());
      } catch { /* ignore */ }
    });

    es.addEventListener('positions', (e: MessageEvent) => {
      try {
        const data = JSON.parse(e.data);
        setPositions(data.positions ?? []);
        setLastUpdated(Date.now());
      } catch { /* ignore */ }
    });

    es.addEventListener('trades', (e: MessageEvent) => {
      try {
        const data = JSON.parse(e.data);
        setTrades(data.trades ?? []);
        setLastUpdated(Date.now());
      } catch { /* ignore */ }
    });

    es.addEventListener('trade', (e: MessageEvent) => {
      try {
        const trade = JSON.parse(e.data) as Trade;
        setTrades(prev => [trade, ...prev].slice(0, 20));
        setLastUpdated(Date.now());
      } catch { /* ignore */ }
    });

    es.addEventListener('risk', (e: MessageEvent) => {
      try {
        setRisk(JSON.parse(e.data) as RiskStatus);
        setLastUpdated(Date.now());
      } catch { /* ignore */ }
    });

    es.addEventListener('markets', (e: MessageEvent) => {
      try {
        const data = JSON.parse(e.data);
        setMarkets(data.markets ?? []);
        setLastUpdated(Date.now());
      } catch { /* ignore */ }
    });

    es.addEventListener('heartbeat', () => {
      setConnected(true);
      setLastUpdated(Date.now());
    });
  }, []);

  const disconnect = useCallback(() => {
    if (esRef.current) {
      esRef.current.close();
      esRef.current = null;
    }
    setConnected(false);
  }, []);

  useEffect(() => {
    if (!enabled) {
      disconnect();
      return;
    }

    if (isVisible) {
      connect();
    } else {
      disconnect();
    }

    return () => {
      disconnect();
    };
  }, [enabled, isVisible, connect, disconnect]);

  return { connected, status, portfolio, positions, trades, risk, markets, lastUpdated };
}
