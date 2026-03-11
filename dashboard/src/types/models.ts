export type ModelType = 'text' | 'image' | 'tts' | 'embedding';
export type ModelStatus = 'running' | 'stopped' | 'unavailable';
export type ModelSource = 'huggingface' | 'harbor' | 'custom';

export interface ModelCard {
  id: string;
  name: string;
  provider_id: string;
  provider_name: string;
  description?: string;
  type: ModelType;
  quantization: string | null;
  vram_gb: number | null;
  context_window: number | null;
  max_tokens: number | null;
  capabilities: {
    streaming: boolean;
    function_calling: boolean;
    vision: boolean;
    json_mode: boolean;
  };
  tags: string[];
  is_default: boolean;
  status: ModelStatus;
  cached: boolean | null;
  cache_size_gb: number | null;
  idle_seconds: number | null;
  source: ModelSource;
  is_local: boolean;
  architecture?: string;
  license?: string;
  hf_model?: string;
  harbor_ref?: string;
}

export interface ModelGardenResponse {
  models: ModelCard[];
  summary: {
    total: number;
    running: number;
    cached: number;
    available: number;
  };
}

export interface PrefetchStatus {
  status: 'idle' | 'downloading' | 'completed' | 'failed' | 'already_downloading';
  progress?: string;
  model?: string;
}

export interface CustomModelCreate {
  id: string;
  name: string;
  type: ModelType;
  provider_id?: string;
  description?: string;
  quantization?: string;
  vram_gb?: number;
  context_window?: number;
  max_tokens?: number;
  architecture?: string;
  license?: string;
  harbor_ref?: string;
  hf_model?: string;
  tags?: string[];
}

export interface ModelFilters {
  search: string;
  type: ModelType | 'all';
  status: ModelStatus | 'cached' | 'all';
  provider: string | 'all';
}
