/**
 * TypeScript types for trade-related data structures.
 * 
 * These types match the Pydantic schemas from the backend.
 */

export type TradeType = 'STOCK' | 'OPTION' | 'CRYPTO_SPOT' | 'CRYPTO_PERP' | 'PREDICTION_MARKET'
export type TradeSide = 'LONG' | 'SHORT'
export type TradeStatus = 'open' | 'closed' | 'partial'
export type OptionType = 'CALL' | 'PUT'

export interface TradeBase {
  ticker: string
  trade_type: TradeType
  side: TradeSide
  entry_price: number
  entry_quantity: number
  entry_time: string // ISO datetime string
  entry_commission: number
  exit_price?: number
  exit_quantity?: number
  exit_time?: string // ISO datetime string
  exit_commission: number
  // Options fields
  strike_price?: number
  expiration_date?: string // ISO date string
  option_type?: OptionType
  delta?: number
  gamma?: number
  theta?: number
  vega?: number
  rho?: number
  implied_volatility?: number
  volume?: number
  open_interest?: number
  bid_price?: number
  ask_price?: number
  bid_ask_spread?: number
  // Crypto fields
  crypto_exchange?: string
  crypto_pair?: string
  // Prediction market fields
  prediction_market_platform?: string
  prediction_outcome?: string
  // Risk management
  stop_loss?: number
  take_profit?: number
  // Metadata
  status: TradeStatus
  playbook?: string
  notes?: string
  tags?: string[]
}

export interface TradeCreate extends TradeBase {}

export interface TradeUpdate extends Partial<TradeBase> {}

export interface TradeResponse extends TradeBase {
  id: number
  user_id: number
  net_pnl?: number
  net_roi?: number
  realized_r_multiple?: number
  created_at: string // ISO datetime string
  updated_at: string // ISO datetime string
}

export interface TradeListResponse {
  trades: TradeResponse[]
  total: number
  limit: number
  offset: number
  has_more: boolean
}

