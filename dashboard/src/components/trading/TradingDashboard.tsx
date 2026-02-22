import { useState, useCallback } from 'react';
import type {
  MercuryStatus,
  PortfolioSummary,
  Position,
  Trade,
  RiskStatus,
  RiskLimitUpdate,
  WalletBalance,
  ActiveMarket,
} from '../../types/trading';
import { mercuryAPI } from '../../api/client';
import { RetroPanel, RetroStatCard, RetroBadge, RetroProgress, RetroButton, RetroToggle } from '../ui';
import { useVisibilityPolling } from '../../hooks/useDocumentVisibility';
import { useMercurySSE } from '../../hooks/useMercurySSE';

const POLL_INTERVAL = 30000;
const WALLET_POLL_INTERVAL = 60000;

function formatUSD(value: number | null | undefined): string {
  if (value == null) return '--';
  const sign = value >= 0 ? '+' : '';
  return `${sign}$${value.toFixed(2)}`;
}

function formatTime(seconds: number): string {
  const h = Math.floor(seconds / 3600);
  const m = Math.floor((seconds % 3600) / 60);
  if (h > 0) return `${h}h ${m}m`;
  return `${m}m`;
}

function pnlColor(value: number | null | undefined): 'green' | 'red' | 'default' {
  if (value == null || value === 0) return 'default';
  return value > 0 ? 'green' : 'red';
}

function cbBadgeVariant(state: string): 'status-done' | 'status-progress' | 'status-blocked' | 'status-open' {
  switch (state) {
    case 'NORMAL': return 'status-done';
    case 'WARNING': return 'status-progress';
    case 'CAUTION': return 'status-blocked';
    case 'HALT': return 'status-blocked';
    default: return 'status-open';
  }
}

function StatusBar({ status }: { status: MercuryStatus }) {
  const cbState = status.components?.circuit_breaker ?? 'UNKNOWN';
  const strategies = status.active_strategies ?? [];

  return (
    <div className="flex flex-wrap items-center gap-3 p-3 bg-[var(--retro-bg-medium)] border border-[var(--retro-border)] rounded">
      <RetroBadge variant={status.status === 'healthy' ? 'status-done' : status.status === 'degraded' ? 'status-progress' : 'status-blocked'}>
        {(status.status ?? 'unknown').toUpperCase()}
      </RetroBadge>
      {status.dry_run && (
        <RetroBadge variant="status-progress">DRY RUN</RetroBadge>
      )}
      <RetroBadge variant={cbBadgeVariant(cbState)}>
        CB: {cbState}
      </RetroBadge>
      <span className="text-xs text-[var(--retro-text-secondary)]">
        v{status.version ?? '?'}
      </span>
      <span className="text-xs text-[var(--retro-text-secondary)]">
        Up {formatTime(status.uptime_seconds ?? 0)}
      </span>
      <span className="text-xs text-[var(--retro-text-secondary)]">
        Strategies: {strategies.join(', ') || 'none'}
      </span>
    </div>
  );
}

function PortfolioCards({ portfolio, wallet }: { portfolio: PortfolioSummary; wallet: WalletBalance | null }) {
  return (
    <div className="grid grid-cols-2 lg:grid-cols-5 gap-3">
      <RetroStatCard
        label="Total P&L"
        value={formatUSD(portfolio.total_realized_pnl)}
        color={pnlColor(portfolio.total_realized_pnl)}
      />
      <RetroStatCard
        label="Today P&L"
        value={formatUSD(portfolio.today_realized_pnl)}
        color={pnlColor(portfolio.today_realized_pnl)}
      />
      <RetroStatCard
        label="Open Positions"
        value={portfolio.open_positions}
        color="blue"
      />
      <RetroStatCard
        label="Exposure"
        value={`$${portfolio.total_exposure.toFixed(2)}`}
        color="default"
      />
      <RetroStatCard
        label="Wallet Balance"
        value={wallet ? `$${wallet.balance.toFixed(2)}` : '--'}
        color="blue"
      />
    </div>
  );
}

function PositionsTable({ positions }: { positions: Position[] }) {
  if (positions.length === 0) {
    return (
      <p className="text-sm text-[var(--retro-text-secondary)] py-4 text-center">
        No open positions
      </p>
    );
  }

  return (
    <div className="overflow-x-auto">
      <table className="w-full text-sm">
        <thead>
          <tr className="text-left text-[var(--retro-text-secondary)] border-b border-[var(--retro-border)]">
            <th className="py-2 pr-4">Market</th>
            <th className="py-2 pr-4">Side</th>
            <th className="py-2 pr-4">Size</th>
            <th className="py-2 pr-4">Entry</th>
            <th className="py-2 pr-4">Current</th>
            <th className="py-2 pr-4">P&L</th>
          </tr>
        </thead>
        <tbody>
          {positions.map((p) => (
            <tr key={p.position_id} className="border-b border-[var(--retro-border)] border-opacity-30">
              <td className="py-2 pr-4 text-[var(--retro-text-primary)] font-mono text-xs truncate max-w-[200px]">
                {p.market_id}
              </td>
              <td className="py-2 pr-4">
                <RetroBadge variant={p.side === 'YES' ? 'status-done' : 'status-blocked'}>
                  {p.side}
                </RetroBadge>
              </td>
              <td className="py-2 pr-4 font-mono">{p.size.toFixed(1)}</td>
              <td className="py-2 pr-4 font-mono">${p.entry_price.toFixed(3)}</td>
              <td className="py-2 pr-4 font-mono">
                {p.current_price != null ? `$${p.current_price.toFixed(3)}` : '--'}
              </td>
              <td className={`py-2 pr-4 font-mono ${
                (p.unrealized_pnl ?? 0) > 0 ? 'text-[var(--retro-accent-green)]' :
                (p.unrealized_pnl ?? 0) < 0 ? 'text-[var(--retro-accent-red)]' :
                'text-[var(--retro-text-secondary)]'
              }`}>
                {formatUSD(p.unrealized_pnl)}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function TradesTable({ trades }: { trades: Trade[] }) {
  if (trades.length === 0) {
    return (
      <p className="text-sm text-[var(--retro-text-secondary)] py-4 text-center">
        No recent trades
      </p>
    );
  }

  return (
    <div className="overflow-x-auto">
      <table className="w-full text-sm">
        <thead>
          <tr className="text-left text-[var(--retro-text-secondary)] border-b border-[var(--retro-border)]">
            <th className="py-2 pr-4">Time</th>
            <th className="py-2 pr-4">Strategy</th>
            <th className="py-2 pr-4">Market</th>
            <th className="py-2 pr-4">Side</th>
            <th className="py-2 pr-4">Size</th>
            <th className="py-2 pr-4">Price</th>
            <th className="py-2 pr-4">Profit</th>
          </tr>
        </thead>
        <tbody>
          {trades.map((t) => (
            <tr key={t.trade_id} className="border-b border-[var(--retro-border)] border-opacity-30">
              <td className="py-2 pr-4 text-xs text-[var(--retro-text-secondary)]">
                {new Date(t.timestamp).toLocaleString(undefined, {
                  month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit',
                })}
              </td>
              <td className="py-2 pr-4 text-xs font-mono">{t.strategy}</td>
              <td className="py-2 pr-4 font-mono text-xs truncate max-w-[150px]">
                {t.market_id}
              </td>
              <td className="py-2 pr-4">
                <RetroBadge variant={t.side === 'YES' ? 'status-done' : 'status-blocked'}>
                  {t.side}
                </RetroBadge>
              </td>
              <td className="py-2 pr-4 font-mono">{t.size.toFixed(1)}</td>
              <td className="py-2 pr-4 font-mono">${t.price.toFixed(3)}</td>
              <td className={`py-2 pr-4 font-mono ${
                (t.actual_profit ?? 0) > 0 ? 'text-[var(--retro-accent-green)]' :
                (t.actual_profit ?? 0) < 0 ? 'text-[var(--retro-accent-red)]' :
                'text-[var(--retro-text-secondary)]'
              }`}>
                {t.actual_profit != null ? formatUSD(t.actual_profit) : '--'}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function formatRelativeTime(isoString: string): string {
  const end = new Date(isoString).getTime();
  const now = Date.now();
  const diffMs = end - now;
  if (diffMs <= 0) return 'ended';
  const mins = Math.floor(diffMs / 60000);
  if (mins < 60) return `in ${mins}m`;
  const hrs = Math.floor(mins / 60);
  return `in ${hrs}h ${mins % 60}m`;
}

function priceColor(price: number): string {
  if (price > 0.5) return 'text-[var(--retro-accent-green)]';
  if (price < 0.5) return 'text-[var(--retro-accent-red)]';
  return 'text-[var(--retro-text-primary)]';
}

function ActiveMarketsTable({ markets }: { markets: ActiveMarket[] }) {
  if (markets.length === 0) {
    return (
      <p className="text-sm text-[var(--retro-text-secondary)] py-4 text-center">
        No active markets being tracked
      </p>
    );
  }

  return (
    <div className="overflow-x-auto">
      <table className="w-full text-sm">
        <thead>
          <tr className="text-left text-[var(--retro-text-secondary)] border-b border-[var(--retro-border)]">
            <th className="py-2 pr-4">Asset</th>
            <th className="py-2 pr-4">YES</th>
            <th className="py-2 pr-4">NO</th>
            <th className="py-2 pr-4">Spread</th>
            <th className="py-2 pr-4">Ends</th>
            <th className="py-2 pr-4">Strategy</th>
            <th className="py-2 pr-4">Link</th>
          </tr>
        </thead>
        <tbody>
          {markets.map((m) => (
            <tr key={m.condition_id} className="border-b border-[var(--retro-border)] border-opacity-30">
              <td className="py-2 pr-4">
                <RetroBadge variant="status-progress">{m.asset}</RetroBadge>
              </td>
              <td className={`py-2 pr-4 font-mono ${priceColor(m.yes_price)}`}>
                {m.yes_price.toFixed(2)}
              </td>
              <td className={`py-2 pr-4 font-mono ${priceColor(m.no_price)}`}>
                {m.no_price.toFixed(2)}
              </td>
              <td className="py-2 pr-4 font-mono">
                {m.spread_cents.toFixed(1)}c
              </td>
              <td className="py-2 pr-4 text-xs text-[var(--retro-text-secondary)]">
                {formatRelativeTime(m.end_time)}
              </td>
              <td className="py-2 pr-4">
                {m.strategies.map((s) => (
                  <RetroBadge key={s} variant="status-open">{s}</RetroBadge>
                ))}
              </td>
              <td className="py-2 pr-4">
                <a
                  href={m.url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-[var(--retro-accent-blue)] hover:underline text-xs"
                >
                  Polymarket
                </a>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function RiskPanel({ risk }: { risk: RiskStatus }) {
  const dailyLossUsed = risk.limits.max_daily_loss > 0
    ? Math.min(100, Math.abs(risk.daily.pnl < 0 ? risk.daily.pnl : 0) / risk.limits.max_daily_loss * 100)
    : 0;

  const exposurePct = risk.limits.max_unhedged_exposure > 0
    ? Math.min(100, risk.exposure.unhedged / risk.limits.max_unhedged_exposure * 100)
    : 0;

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap items-center gap-3">
        <RetroBadge variant={cbBadgeVariant(risk.circuit_breaker.state)}>
          {risk.circuit_breaker.state}
        </RetroBadge>
        {risk.circuit_breaker.can_trade ? (
          <span className="text-xs text-[var(--retro-accent-green)]">Trading enabled</span>
        ) : (
          <span className="text-xs text-[var(--retro-accent-red)]">Trading disabled</span>
        )}
        {risk.circuit_breaker.is_in_cooldown && (
          <span className="text-xs text-[var(--retro-accent-yellow)]">Cooldown active</span>
        )}
        <span className="text-xs text-[var(--retro-text-secondary)]">
          Size mult: {risk.size_multiplier}x
        </span>
      </div>

      <div className="space-y-2">
        <div>
          <div className="flex justify-between text-xs mb-1">
            <span className="text-[var(--retro-text-secondary)]">Daily Loss</span>
            <span className="font-mono">
              {formatUSD(risk.daily.pnl)} / -${risk.limits.max_daily_loss.toFixed(0)}
            </span>
          </div>
          <RetroProgress
            value={dailyLossUsed}
            variant={dailyLossUsed > 80 ? 'danger' : dailyLossUsed > 50 ? 'warning' : 'default'}
            size="sm"
          />
        </div>

        <div>
          <div className="flex justify-between text-xs mb-1">
            <span className="text-[var(--retro-text-secondary)]">Unhedged Exposure</span>
            <span className="font-mono">
              ${risk.exposure.unhedged.toFixed(0)} / ${risk.limits.max_unhedged_exposure.toFixed(0)}
            </span>
          </div>
          <RetroProgress
            value={exposurePct}
            variant={exposurePct > 80 ? 'danger' : exposurePct > 50 ? 'warning' : 'default'}
            size="sm"
          />
        </div>
      </div>

      <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 text-xs">
        <div>
          <span className="text-[var(--retro-text-secondary)]">Peak P&L</span>
          <div className="font-mono">{formatUSD(risk.daily.peak_pnl)}</div>
        </div>
        <div>
          <span className="text-[var(--retro-text-secondary)]">Max Drawdown</span>
          <div className="font-mono text-[var(--retro-accent-red)]">{formatUSD(-risk.daily.max_drawdown)}</div>
        </div>
        <div>
          <span className="text-[var(--retro-text-secondary)]">Consec. Failures</span>
          <div className="font-mono">{risk.daily.consecutive_failures}</div>
        </div>
        <div>
          <span className="text-[var(--retro-text-secondary)]">Total Exposure</span>
          <div className="font-mono">${risk.exposure.current.toFixed(2)}</div>
        </div>
      </div>
    </div>
  );
}

function ControlsPanel({
  status,
  risk,
  onRefresh,
}: {
  status: MercuryStatus;
  risk: RiskStatus;
  onRefresh: () => void;
}) {
  const [acting, setActing] = useState(false);
  const [confirmHalt, setConfirmHalt] = useState(false);
  const [riskForm, setRiskForm] = useState<RiskLimitUpdate>({
    max_daily_loss: risk.limits.max_daily_loss,
    max_position_size: risk.limits.max_position_size,
    max_unhedged_exposure: risk.limits.max_unhedged_exposure,
  });

  const isHalted = risk.circuit_breaker.state === 'HALT';
  const allStrategies = status.all_strategies ?? status.active_strategies ?? [];

  const doAction = async (action: () => Promise<unknown>) => {
    setActing(true);
    try {
      await action();
      onRefresh();
    } catch {
      // Error handling via parent refresh
    } finally {
      setActing(false);
      setConfirmHalt(false);
    }
  };

  return (
    <div className="space-y-4">
      {/* Master toggle */}
      <div className="flex items-center gap-3">
        {isHalted ? (
          <RetroButton
            variant="primary"
            onClick={() => doAction(() => mercuryAPI.resume())}
            disabled={acting}
          >
            RESUME TRADING
          </RetroButton>
        ) : confirmHalt ? (
          <div className="flex items-center gap-2">
            <span className="text-xs text-[var(--retro-accent-red)]">Confirm halt?</span>
            <RetroButton
              variant="danger"
              onClick={() => doAction(() => mercuryAPI.halt())}
              disabled={acting}
            >
              YES, HALT
            </RetroButton>
            <RetroButton
              variant="secondary"
              onClick={() => setConfirmHalt(false)}
              disabled={acting}
            >
              Cancel
            </RetroButton>
          </div>
        ) : (
          <RetroButton
            variant="danger"
            onClick={() => setConfirmHalt(true)}
            disabled={acting}
          >
            HALT TRADING
          </RetroButton>
        )}
        <RetroBadge variant={isHalted ? 'status-blocked' : 'status-done'}>
          {isHalted ? 'HALTED' : 'ACTIVE'}
        </RetroBadge>
      </div>

      {/* Strategy toggles */}
      <div>
        <div className="text-xs text-[var(--retro-text-secondary)] mb-2">Strategies</div>
        <div className="flex flex-wrap gap-4">
          {allStrategies.map((name) => {
            const isOn = status.active_strategies.includes(name);
            return (
              <RetroToggle
                key={name}
                label={name}
                checked={isOn}
                disabled={acting}
                onChange={() => doAction(() =>
                  isOn ? mercuryAPI.disableStrategy(name) : mercuryAPI.enableStrategy(name)
                )}
              />
            );
          })}
          {allStrategies.length === 0 && (
            <span className="text-xs text-[var(--retro-text-secondary)]">No strategies configured</span>
          )}
        </div>
      </div>

      {/* Risk limit editor */}
      <div>
        <div className="text-xs text-[var(--retro-text-secondary)] mb-2">Risk Limits</div>
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-2">
          <label className="text-xs">
            <span className="text-[var(--retro-text-secondary)]">Max Daily Loss ($)</span>
            <input
              type="number"
              className="w-full mt-1 px-2 py-1 bg-[var(--retro-bg-dark)] border border-[var(--retro-border)] rounded text-[var(--retro-text-primary)] font-mono text-sm"
              value={riskForm.max_daily_loss ?? ''}
              onChange={(e) => setRiskForm({ ...riskForm, max_daily_loss: Number(e.target.value) })}
            />
          </label>
          <label className="text-xs">
            <span className="text-[var(--retro-text-secondary)]">Max Position Size ($)</span>
            <input
              type="number"
              className="w-full mt-1 px-2 py-1 bg-[var(--retro-bg-dark)] border border-[var(--retro-border)] rounded text-[var(--retro-text-primary)] font-mono text-sm"
              value={riskForm.max_position_size ?? ''}
              onChange={(e) => setRiskForm({ ...riskForm, max_position_size: Number(e.target.value) })}
            />
          </label>
          <label className="text-xs">
            <span className="text-[var(--retro-text-secondary)]">Max Unhedged Exp ($)</span>
            <input
              type="number"
              className="w-full mt-1 px-2 py-1 bg-[var(--retro-bg-dark)] border border-[var(--retro-border)] rounded text-[var(--retro-text-primary)] font-mono text-sm"
              value={riskForm.max_unhedged_exposure ?? ''}
              onChange={(e) => setRiskForm({ ...riskForm, max_unhedged_exposure: Number(e.target.value) })}
            />
          </label>
        </div>
        <div className="mt-2">
          <RetroButton
            variant="secondary"
            onClick={() => doAction(() => mercuryAPI.updateRiskLimits(riskForm))}
            disabled={acting}
          >
            Save Limits
          </RetroButton>
        </div>
      </div>
    </div>
  );
}

function formatLastUpdated(ts: number | null): string {
  if (!ts) return '';
  const ago = Math.round((Date.now() - ts) / 1000);
  if (ago < 2) return 'just now';
  if (ago < 60) return `${ago}s ago`;
  return `${Math.floor(ago / 60)}m ago`;
}

export default function TradingDashboard() {
  const live = useMercurySSE(true);

  // Fallback state for when SSE is disconnected
  const [fallbackStatus, setFallbackStatus] = useState<MercuryStatus | null>(null);
  const [fallbackPortfolio, setFallbackPortfolio] = useState<PortfolioSummary | null>(null);
  const [fallbackPositions, setFallbackPositions] = useState<Position[]>([]);
  const [fallbackTrades, setFallbackTrades] = useState<Trade[]>([]);
  const [fallbackRisk, setFallbackRisk] = useState<RiskStatus | null>(null);
  const [fallbackMarkets, setFallbackMarkets] = useState<ActiveMarket[]>([]);
  const [wallet, setWallet] = useState<WalletBalance | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Use SSE data when connected, fallback state when not
  const status = live.connected ? live.status : fallbackStatus;
  const portfolio = live.connected ? live.portfolio : fallbackPortfolio;
  const positions = live.connected ? live.positions : fallbackPositions;
  const trades = live.connected ? live.trades : fallbackTrades;
  const risk = live.connected ? live.risk : fallbackRisk;
  const markets = live.connected ? live.markets : fallbackMarkets;

  const fetchData = useCallback(async () => {
    try {
      const [statusData, portfolioData, positionsData, tradesData, riskData, marketsData] = await Promise.all([
        mercuryAPI.getStatus(),
        mercuryAPI.getPortfolio(),
        mercuryAPI.getPositions(),
        mercuryAPI.getTrades({ limit: 20 }),
        mercuryAPI.getRisk(),
        mercuryAPI.getMarkets().catch(() => ({ markets: [], total: 0 })),
      ]);
      setFallbackStatus(statusData);
      setFallbackPortfolio(portfolioData);
      setFallbackPositions(positionsData?.positions ?? []);
      setFallbackTrades(tradesData?.trades ?? []);
      setFallbackRisk(riskData);
      setFallbackMarkets(marketsData?.markets ?? []);
      setError(null);
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Failed to connect to Mercury');
    } finally {
      setLoading(false);
    }
  }, []);

  // Wallet: always poll (expensive CLOB call, rarely changes)
  useVisibilityPolling({
    callback: () => mercuryAPI.getWallet().catch(() => null).then(setWallet),
    interval: WALLET_POLL_INTERVAL,
    enabled: true,
    immediate: true,
  });

  // Fallback: poll everything only when SSE is disconnected
  useVisibilityPolling({
    callback: fetchData,
    interval: POLL_INTERVAL,
    enabled: !live.connected,
    immediate: true,
  });

  // Mark loading complete once SSE delivers first snapshot or fallback loads
  if (loading && (live.status || fallbackStatus)) {
    setLoading(false);
  }

  if (loading && !status) {
    return (
      <div className="p-6">
        <div className="text-[var(--retro-text-secondary)] text-center py-12">
          Connecting to Mercury...
        </div>
      </div>
    );
  }

  if (error && !status && !live.connected) {
    return (
      <div className="p-6">
        <div className="text-center py-12">
          <p className="text-[var(--retro-accent-red)] mb-4">{error}</p>
          <RetroButton variant="secondary" onClick={() => { setLoading(true); fetchData(); }}>
            Retry
          </RetroButton>
        </div>
      </div>
    );
  }

  return (
    <div className="p-4 sm:p-6 space-y-4 overflow-auto h-full">
      <div className="flex items-center justify-between mb-2">
        <div className="flex items-center gap-3">
          <h2 className="text-xl font-bold text-[var(--retro-text-primary)]">Trading</h2>
          {live.connected ? (
            <RetroBadge variant="status-done">LIVE</RetroBadge>
          ) : (
            <RetroBadge variant="status-progress">POLLING</RetroBadge>
          )}
        </div>
        <div className="flex items-center gap-3">
          {live.lastUpdated && (
            <span className="text-xs text-[var(--retro-text-secondary)]">
              Updated {formatLastUpdated(live.lastUpdated)}
            </span>
          )}
          {error && !live.connected && (
            <span className="text-xs text-[var(--retro-accent-yellow)]">
              Update failed - showing stale data
            </span>
          )}
        </div>
      </div>

      {status && <StatusBar status={status} />}

      {portfolio && <PortfolioCards portfolio={portfolio} wallet={wallet} />}

      <RetroPanel title="Active Markets" collapsible defaultCollapsed={false}>
        <ActiveMarketsTable markets={markets} />
      </RetroPanel>

      {status && risk && (
        <RetroPanel title="Controls" collapsible defaultCollapsed={true}>
          <ControlsPanel status={status} risk={risk} onRefresh={fetchData} />
        </RetroPanel>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        <RetroPanel title="Open Positions" collapsible defaultCollapsed={false}>
          <PositionsTable positions={positions} />
        </RetroPanel>

        {risk && (
          <RetroPanel title="Risk" collapsible defaultCollapsed={false}>
            <RiskPanel risk={risk} />
          </RetroPanel>
        )}
      </div>

      <RetroPanel title="Recent Trades" collapsible defaultCollapsed={false}>
        <TradesTable trades={trades} />
      </RetroPanel>
    </div>
  );
}
