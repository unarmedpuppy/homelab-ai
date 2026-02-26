// Agent profiles
export type UnitProfile = 'avery' | 'gilfoyle' | 'ralph' | 'jobin' | 'colin' | 'villager';

export const UNIT_COLORS: Record<UnitProfile, number> = {
  avery: 0x4a90e2,      // blue
  gilfoyle: 0xe24a4a,   // crimson
  ralph: 0xe2844a,      // orange
  jobin: 0x9b4ae2,      // purple
  colin: 0x2eb87a,      // green (finance/money)
  villager: 0xc8a84b,   // tan/gold
};

export const UNIT_LABELS: Record<UnitProfile, string> = {
  avery: 'A',
  gilfoyle: 'G',
  ralph: 'R',
  jobin: 'J',
  colin: 'C',
  villager: 'V',
};

export type UnitStatus = 'idle' | 'moving' | 'working' | 'done' | 'error';

export type BuildingType = 'town-center' | 'barracks' | 'market' | 'university' | 'castle';

export const BUILDING_COLORS: Record<BuildingType, number> = {
  'town-center': 0xd4a017,
  'barracks': 0x8b4513,
  'market': 0x2e8b57,
  'university': 0x4169e1,
  'castle': 0x708090,
};

export const BUILDING_LABELS: Record<BuildingType, string> = {
  'town-center': 'TC',
  'barracks': 'BK',
  'market': 'MK',
  'university': 'UN',
  'castle': 'CS',
};

export type BuildingStatus = 'foundation' | 'idle' | 'active' | 'complete';

export interface TilePos {
  col: number;
  row: number;
}

export interface WorldPos {
  x: number;
  y: number;
}

export interface UnitData {
  id: string;
  profile: UnitProfile;
  status: UnitStatus;
  currentJobId?: string;
  homeCol: number;
  homeRow: number;
  col: number;
  row: number;
}

export interface BuildingData {
  id: string;
  type: BuildingType;
  status: BuildingStatus;
  projectId?: string;
  col: number;
  row: number;
  name: string;
}

export interface MapState {
  buildings: BuildingData[];
  terrain: TerrainOverride[];
}

export interface TerrainOverride {
  col: number;
  row: number;
  type: 'water' | 'dirt' | 'grass';
}

// From agent-harness API
export interface Job {
  id: string;
  status: 'pending' | 'running' | 'completed' | 'failed' | 'timeout' | 'cancelled';
  prompt: string;
  model: string;
  created_at: string;
  started_at?: string;
  completed_at?: string;
  result?: string;
  error?: string;
  duration_seconds?: number;
  session_id?: string;
  cost_usd?: number;
  input_tokens?: number;
  output_tokens?: number;
  num_turns?: number;
  agent?: string;
  working_directory?: string;
}

export interface Project {
  id: string;
  name: string;
  type: string;
  building_type: BuildingType;
  description?: string;
  created_at: string;
  updated_at: string;
}

export interface AgentUnitState {
  profile: UnitProfile;
  status: UnitStatus;
  currentJobId?: string;
  displayName: string;
}

// Events emitted on the EventBus
export type GameEvent =
  | { type: 'unit-selected'; unitId: string; profile: UnitProfile; status: UnitStatus }
  | { type: 'building-selected'; buildingId: string; buildingData: BuildingData }
  | { type: 'selection-cleared' }
  | { type: 'job-dispatch'; prompt: string; targetProfile?: UnitProfile; buildingId?: string }
  | { type: 'unit-moved'; unitId: string; col: number; row: number }
  | { type: 'building-placed'; buildingData: BuildingData }
  | { type: 'right-click-empty'; col: number; row: number };

export interface HarnessHealth {
  status: string;
  profile: {
    name: string;
    display_name: string;
    role: string;
  };
  jobs: Record<string, number>;
}

export interface RouterHealth {
  status: string;
  providers?: Record<string, unknown>;
}
