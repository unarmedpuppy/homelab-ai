/**
 * TypeScript types for playbook-related data structures.
 * 
 * These types match the Pydantic schemas from the backend.
 */

export interface PlaybookPerformance {
  total_trades: number
  missed_trades: number
  net_pnl: number
  gross_pnl: number
  win_rate?: number
  profit_factor?: number
  avg_win?: number
  avg_loss?: number
  winners: number
  losers: number
}

export interface PlaybookBase {
  name: string
  description?: string
  template_id?: number
  is_active: boolean
  is_shared: boolean
}

export interface PlaybookCreate extends PlaybookBase {}

export interface PlaybookUpdate extends Partial<PlaybookBase> {}

export interface PlaybookResponse extends PlaybookBase {
  id: number
  created_at: string // ISO datetime string
  updated_at: string // ISO datetime string
  user_id: number
  performance?: PlaybookPerformance
}

export interface PlaybookListResponse {
  playbooks: PlaybookResponse[]
  total: number
}

export interface PlaybookTemplateBase {
  name: string
  description?: string
  category?: string
}

export interface PlaybookTemplateCreate extends PlaybookTemplateBase {}

export interface PlaybookTemplateResponse extends PlaybookTemplateBase {
  id: number
  is_system: boolean
  created_at: string // ISO datetime string
  user_id: number
}

