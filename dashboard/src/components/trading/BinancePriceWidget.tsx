import { useState, useMemo } from 'react';
import { AreaChart, Area, Tooltip, ResponsiveContainer, YAxis } from 'recharts';
import type { BinanceData, BinancePricePoint } from '../../types/trading';
import { RetroPanel, RetroBadge } from '../ui';

const ASSET_COLORS: Record<string, string> = {
  BTC: 'var(--retro-accent-yellow)',
  ETH: 'var(--retro-accent-blue)',
  SOL: 'var(--retro-accent-green)',
};

const ASSET_ORDER = ['BTC', 'ETH', 'SOL'];

function formatPrice(price: number | null): string {
  if (price == null) return '--';
  if (price >= 1000) return `$${price.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
  return `$${price.toFixed(4)}`;
}

function formatMomentum(pct: number | null): { text: string; color: string } {
  if (pct == null) return { text: '--', color: 'var(--retro-text-secondary)' };
  const sign = pct >= 0 ? '+' : '';
  const color = pct > 0 ? 'var(--retro-accent-green)' : pct < 0 ? 'var(--retro-accent-red)' : 'var(--retro-text-secondary)';
  return { text: `${sign}${(pct * 100).toFixed(3)}% /60s`, color };
}

function PriceChart({ history, color }: { history: BinancePricePoint[]; color: string }) {
  const data = useMemo(() => history.map(pt => ({ t: pt.t, price: pt.p })), [history]);

  if (data.length < 2) {
    return (
      <div className="h-[128px] flex items-center justify-center text-xs text-[var(--retro-text-secondary)]">
        Waiting for data...
      </div>
    );
  }

  const prices = data.map(d => d.price);
  const min = Math.min(...prices);
  const max = Math.max(...prices);
  const padding = (max - min) * 0.1 || max * 0.001;

  return (
    <ResponsiveContainer width="100%" height={128}>
      <AreaChart data={data} margin={{ top: 4, right: 0, bottom: 0, left: 0 }}>
        <defs>
          <linearGradient id={`gradient-${color}`} x1="0" y1="0" x2="0" y2="1">
            <stop offset="5%" stopColor={color} stopOpacity={0.3} />
            <stop offset="95%" stopColor={color} stopOpacity={0} />
          </linearGradient>
        </defs>
        <YAxis domain={[min - padding, max + padding]} hide />
        <Tooltip
          contentStyle={{
            background: 'var(--retro-bg-dark)',
            border: '1px solid var(--retro-border)',
            borderRadius: '4px',
            fontSize: '11px',
            color: 'var(--retro-text-primary)',
          }}
          formatter={(value: number | undefined) => [formatPrice(value ?? null), 'Price']}
          labelFormatter={(label: number) => new Date(label * 1000).toLocaleTimeString()}
        />
        <Area
          type="monotone"
          dataKey="price"
          stroke={color}
          strokeWidth={1.5}
          fill={`url(#gradient-${color})`}
          dot={false}
          isAnimationActive={false}
        />
      </AreaChart>
    </ResponsiveContainer>
  );
}

export default function BinancePriceWidget({ data }: { data: BinanceData | null }) {
  const assets = useMemo(() => {
    if (!data?.tickers) return ASSET_ORDER;
    const available = Object.keys(data.tickers);
    return ASSET_ORDER.filter(a => available.includes(a)).concat(
      available.filter(a => !ASSET_ORDER.includes(a))
    );
  }, [data?.tickers]);

  const [selectedAsset, setSelectedAsset] = useState<string>('BTC');

  const ticker = data?.tickers?.[selectedAsset];
  const history = data?.history?.[selectedAsset] ?? [];
  const color = ASSET_COLORS[selectedAsset] ?? 'var(--retro-accent-blue)';
  const momentum = formatMomentum(ticker?.momentum_pct ?? null);

  const connectionBadge = (
    <RetroBadge variant={data?.connected ? 'status-done' : 'status-blocked'}>
      {data?.connected ? 'CONNECTED' : 'DISCONNECTED'}
    </RetroBadge>
  );

  return (
    <RetroPanel title="Binance Prices" actions={connectionBadge}>
      {/* Ticker tabs */}
      <div className="flex gap-1 mb-3">
        {assets.map((asset) => {
          const t = data?.tickers?.[asset];
          const isActive = asset === selectedAsset;
          return (
            <button
              key={asset}
              onClick={() => setSelectedAsset(asset)}
              className={`px-3 py-1.5 text-xs font-mono rounded transition-colors ${
                isActive
                  ? 'bg-[var(--retro-bg-light)] border border-[var(--retro-border)] text-[var(--retro-text-primary)]'
                  : 'text-[var(--retro-text-secondary)] hover:text-[var(--retro-text-primary)] border border-transparent'
              }`}
            >
              <span className="font-bold">{asset}</span>
              {t?.price != null && (
                <span className="ml-2 opacity-80">{formatPrice(t.price)}</span>
              )}
            </button>
          );
        })}
      </div>

      {!data ? (
        <div className="text-sm text-[var(--retro-text-secondary)] py-8 text-center">
          Waiting for Binance data...
        </div>
      ) : (
        <>
          {/* Main price display */}
          <div className="mb-3">
            <div className="text-2xl font-mono font-bold text-[var(--retro-text-primary)]" style={{ color }}>
              {formatPrice(ticker?.price ?? null)}
            </div>
            <div className="flex items-center gap-4 mt-1 text-xs">
              <span className="font-mono" style={{ color: momentum.color }}>
                {momentum.text}
              </span>
              {ticker && (
                <>
                  <span className="text-[var(--retro-text-secondary)]">
                    Window: {ticker.window_size} ticks
                  </span>
                  <span className="text-[var(--retro-text-secondary)]">
                    Chart: {history.length} pts
                  </span>
                </>
              )}
            </div>
          </div>

          {/* Sparkline chart */}
          <PriceChart history={history} color={color} />
        </>
      )}
    </RetroPanel>
  );
}
