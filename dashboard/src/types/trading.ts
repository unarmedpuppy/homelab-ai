export interface MercuryStatus {
  status: 'healthy' | 'degraded' | 'unhealthy' | 'unknown';
  uptime_seconds: number;
  dry_run: boolean;
  version: string;
  components: {
    redis: boolean;
    websocket: boolean;
    circuit_breaker: string;
  };
  active_strategies: string[];
  open_positions_count: number;
}

export interface PortfolioSummary {
  total_realized_pnl: number;
  today_realized_pnl: number;
  unrealized_pnl: number;
  open_positions: number;
  total_exposure: number;
  today: {
    trade_count: number;
    volume: number;
    wins: number;
    losses: number;
    win_rate: number;
  };
}

export interface Position {
  position_id: string;
  market_id: string;
  strategy: string;
  side: string;
  size: number;
  entry_price: number;
  current_price: number | null;
  cost_basis: number;
  unrealized_pnl: number | null;
  realized_pnl: number | null;
  status: string;
  opened_at: string;
  closed_at: string | null;
}

export interface PositionsResponse {
  positions: Position[];
  total: number;
}

export interface Trade {
  trade_id: string;
  market_id: string;
  strategy: string;
  side: string;
  size: number;
  price: number;
  cost: number;
  fee: number;
  status: string;
  actual_profit: number | null;
  dry_run: boolean;
  timestamp: string;
}

export interface TradesResponse {
  trades: Trade[];
  total: number;
}

export interface RiskStatus {
  circuit_breaker: {
    state: string;
    reasons: string[];
    can_trade: boolean;
    can_open_positions: boolean;
    cooldown_until: string | null;
    is_in_cooldown: boolean;
  };
  daily: {
    pnl: number;
    trades: number;
    volume: number;
    peak_pnl: number;
    max_drawdown: number;
    consecutive_failures: number;
  };
  exposure: {
    current: number;
    unhedged: number;
    by_market: Record<string, number>;
  };
  limits: {
    max_daily_loss: number;
    max_position_size: number;
    max_unhedged_exposure: number;
    max_per_market_exposure: number;
    max_concurrent_positions: number;
  };
  size_multiplier: number;
}

export interface DailyPnL {
  date: string;
  realized_pnl: number;
  trade_count: number;
  volume: number;
  wins: number;
  losses: number;
  win_rate: number;
  max_drawdown: number;
}

export interface DailyPnLResponse {
  daily: DailyPnL[];
  days: number;
}
