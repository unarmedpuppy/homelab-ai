# Local AI Provider/Model Architecture Overhaul

## Overview

Restructure the Local AI ecosystem to properly separate providers from models, with health checking, proper capability tracking, and a clean UI for provider/model selection.

## Current Problems

1. **Conflated Concepts**: "Model" selection mixes providers (3070, 3090, gaming-pc) with actual models (GLM, Claude)
2. **No Provider Abstraction**: No clear data structure for providers and their capabilities
3. **Hardcoded Options**: Model list is hardcoded in dashboard with no dynamic discovery
4. **No Health Tracking**: Can't tell which providers are online/healthy
5. **Unclear Routing**: Auto routing logic is implicit, not explicit with fallback chain
6. **No Capability Metadata**: Missing context limits, rate limits, special capabilities

## Goals

1. **Clear Separation**: Providers are distinct from the models they can run
2. **Health Awareness**: Know which providers are online and healthy
3. **Capability Tracking**: Context window, rate limits, features per model
4. **Explicit Routing**: Clear auto-routing logic with fallback chain
5. **Clean UI**: Two-step selection (pick provider → pick model)
6. **Dynamic Discovery**: Providers can report their available models and health

## Data Structures

### Provider

```typescript
interface Provider {
  id: string;                    // e.g., "server-3070", "gaming-pc-3090", "zai", "anthropic"
  name: string;                  // Display name: "Server (RTX 3070)"
  type: 'local' | 'cloud';       // Provider type
  description?: string;          // Optional description
  endpoint: string;              // Base URL for this provider
  priority: number;              // For auto-routing (lower = higher priority)
  enabled: boolean;              // Can be manually disabled

  // Health/Status
  status: 'online' | 'offline' | 'degraded' | 'unknown';
  lastHealthCheck?: string;      // ISO timestamp

  // Metadata
  gpu?: string;                  // e.g., "RTX 3070", "RTX 3090"
  location?: string;             // e.g., "home-server", "gaming-pc", "cloud"
}
```

### Model

```typescript
interface Model {
  id: string;                    // e.g., "qwen2.5-14b", "glm-4-9b", "claude-3-5-sonnet"
  name: string;                  // Display name
  providerId: string;            // Which provider offers this

  // Capabilities
  contextWindow: number;         // Max tokens in context
  maxTokens?: number;            // Max output tokens
  tokensPerMinute?: number;      // Rate limit

  // Features
  capabilities: {
    vision?: boolean;
    functionCalling?: boolean;
    jsonMode?: boolean;
    streaming?: boolean;
  };

  // Status
  isDefault?: boolean;           // Default model for this provider
  status: 'available' | 'loading' | 'unavailable';
  warmStatus?: 'warm' | 'cold';  // For local models

  // Metadata
  description?: string;
  tags?: string[];               // e.g., ["coding", "chat", "fast"]
}
```

### ProviderHealth

```typescript
interface ProviderHealth {
  providerId: string;
  status: 'healthy' | 'unhealthy' | 'degraded';
  timestamp: string;             // ISO timestamp
  responseTime?: number;         // ms

  // Model-specific health
  models: {
    modelId: string;
    status: 'available' | 'loading' | 'unavailable';
    warmStatus?: 'warm' | 'cold';
    loadTime?: number;           // Time to load if cold
  }[];

  // Error info if unhealthy
  error?: string;
}
```

### Conversation Metadata

Enhanced conversation tracking with user identity, source, and naming.

```typescript
interface Conversation {
  id: string;                      // Unique conversation ID
  session_id?: string;             // Session identifier
  created_at: string;              // ISO timestamp
  updated_at: string;              // ISO timestamp

  // User tracking
  user_id?: string;                // User ID (e.g., "12345", "josh")
  username?: string;               // Display name (e.g., "Joshua")

  // Source tracking
  source?: string;                 // Origin: "ui-dashboard", "api", "cli", etc.

  // Organization
  project?: string;                // Project categorization
  display_name?: string;           // Optional user-provided name (e.g., "Cooking ideas")

  // Message metadata
  message_count?: number;          // Total messages in conversation
  messages?: Message[];            // Conversation messages
}
```

**Usage Examples:**

```json
// From dashboard
{
  "conversationId": "conv-abc123",
  "user_id": "josh",
  "username": "Joshua",
  "source": "ui-dashboard",
  "display_name": "Cooking ideas"
}

// From API
{
  "conversationId": "conv-def456",
  "user_id": "system",
  "source": "api",
  "project": "automation"
}
```

**Notes:**
- `display_name` replaces the `name` field from the conversation renaming plan
- All user/source fields are optional but should be populated when available
- `source` helps track which interface initiated the conversation
- `username` is for display purposes, `user_id` is the canonical identifier

## Configuration

### Static Provider Config

**File**: `apps/local-ai-router/config/providers.yaml`

```yaml
providers:
  - id: server-3070
    name: "Server (RTX 3070)"
    type: local
    description: "Home server with RTX 3070"
    endpoint: "http://192.168.86.47:8000"
    priority: 1
    enabled: true
    gpu: "RTX 3070"
    location: "home-server"

  - id: gaming-pc-3090
    name: "Gaming PC (RTX 3090)"
    type: local
    description: "Gaming PC with RTX 3090"
    endpoint: "http://192.168.86.48:8000"
    priority: 2
    enabled: true
    gpu: "RTX 3090"
    location: "gaming-pc"

  - id: zai
    name: "ZAI"
    type: cloud
    description: "ZAI API service"
    endpoint: "https://zai.unarmedpuppy.com"
    priority: 3
    enabled: true
    location: "cloud"

  - id: anthropic
    name: "Anthropic (Claude)"
    type: cloud
    description: "Anthropic API"
    endpoint: "https://api.anthropic.com"
    priority: 4
    enabled: true
    location: "cloud"

models:
  # Server (3070) models
  - id: qwen2.5-14b
    name: "Qwen 2.5 14B"
    providerId: server-3070
    contextWindow: 32768
    maxTokens: 8192
    isDefault: true
    capabilities:
      functionCalling: true
      streaming: true
    tags: ["chat", "coding", "fast"]

  - id: qwen2.5-7b
    name: "Qwen 2.5 7B (Fast)"
    providerId: server-3070
    contextWindow: 32768
    maxTokens: 8192
    capabilities:
      functionCalling: true
      streaming: true
    tags: ["chat", "fast", "lightweight"]

  # Gaming PC (3090) models
  - id: qwen2.5-32b
    name: "Qwen 2.5 32B"
    providerId: gaming-pc-3090
    contextWindow: 32768
    maxTokens: 8192
    isDefault: true
    capabilities:
      functionCalling: true
      streaming: true
    tags: ["chat", "coding", "large"]

  - id: deepseek-coder-33b
    name: "DeepSeek Coder 33B"
    providerId: gaming-pc-3090
    contextWindow: 16384
    maxTokens: 4096
    capabilities:
      functionCalling: true
      streaming: true
    tags: ["coding", "specialized"]

  # ZAI models
  - id: glm-4-9b
    name: "GLM-4 9B"
    providerId: zai
    contextWindow: 128000
    maxTokens: 8192
    isDefault: true
    capabilities:
      functionCalling: true
      streaming: true
    tags: ["chat", "large-context"]

  # Anthropic models
  - id: claude-3-5-sonnet-20241022
    name: "Claude 3.5 Sonnet"
    providerId: anthropic
    contextWindow: 200000
    maxTokens: 8192
    isDefault: true
    capabilities:
      vision: true
      functionCalling: true
      streaming: true
    tags: ["chat", "coding", "vision", "premium"]

  - id: claude-3-5-haiku-20241022
    name: "Claude 3.5 Haiku"
    providerId: anthropic
    contextWindow: 200000
    maxTokens: 8192
    capabilities:
      vision: true
      functionCalling: true
      streaming: true
    tags: ["chat", "fast", "premium"]
```

## Auto-Routing Logic

### Fallback Chain

Default priority order (configurable via `priority` field):

1. **server-3070** (priority: 1) - Default for most requests
2. **gaming-pc-3090** (priority: 2) - Fallback + larger models
3. **zai** (priority: 3) - GLM-4 fallback
4. **anthropic** (priority: 4) - Final fallback

### Selection Algorithm

```python
def select_provider_and_model(request, providers, models):
    """
    Select the best provider/model for a request.

    Considers:
    - Provider health
    - Model capabilities
    - Context window requirements
    - Provider priority
    """

    # Calculate required context window
    required_context = sum(len(msg.content) for msg in request.messages) * 1.5

    # Filter to healthy providers only
    healthy_providers = [p for p in providers if p.status == 'online']

    # Sort by priority
    healthy_providers.sort(key=lambda p: p.priority)

    for provider in healthy_providers:
        # Get available models for this provider
        provider_models = [m for m in models
                          if m.providerId == provider.id
                          and m.status == 'available']

        # Filter models by context window requirement
        suitable_models = [m for m in provider_models
                          if m.contextWindow >= required_context]

        if suitable_models:
            # Prefer warm models for local providers
            if provider.type == 'local':
                warm_models = [m for m in suitable_models if m.warmStatus == 'warm']
                if warm_models:
                    return provider, warm_models[0]

            # Use default or first suitable model
            default_model = next((m for m in suitable_models if m.isDefault), None)
            return provider, default_model or suitable_models[0]

    # No suitable provider/model found
    raise NoProviderAvailableError(f"No provider can handle context of {required_context} tokens")
```

## API Changes

### New Endpoints

#### GET /providers

List all configured providers with current health status.

**Response:**
```json
{
  "providers": [
    {
      "id": "server-3070",
      "name": "Server (RTX 3070)",
      "type": "local",
      "status": "online",
      "priority": 1,
      "gpu": "RTX 3070",
      "location": "home-server",
      "lastHealthCheck": "2025-12-29T18:30:00Z"
    },
    ...
  ]
}
```

#### GET /models

List all available models, optionally filtered by provider.

**Query Params:**
- `provider`: Filter by provider ID

**Response:**
```json
{
  "models": [
    {
      "id": "qwen2.5-14b",
      "name": "Qwen 2.5 14B",
      "providerId": "server-3070",
      "contextWindow": 32768,
      "maxTokens": 8192,
      "status": "available",
      "warmStatus": "warm",
      "isDefault": true,
      "capabilities": {
        "functionCalling": true,
        "streaming": true
      },
      "tags": ["chat", "coding", "fast"]
    },
    ...
  ]
}
```

#### GET /providers/{providerId}/health

Get detailed health status for a specific provider.

**Response:**
```json
{
  "providerId": "server-3070",
  "status": "healthy",
  "timestamp": "2025-12-29T18:30:00Z",
  "responseTime": 45,
  "models": [
    {
      "modelId": "qwen2.5-14b",
      "status": "available",
      "warmStatus": "warm"
    },
    {
      "modelId": "qwen2.5-7b",
      "status": "available",
      "warmStatus": "cold",
      "loadTime": 8500
    }
  ]
}
```

#### POST /health/check

Trigger health check for all providers.

**Response:**
```json
{
  "results": [
    {
      "providerId": "server-3070",
      "status": "healthy",
      "responseTime": 45
    },
    ...
  ]
}
```

### Updated Chat Completion Endpoint

#### POST /v1/chat/completions

**Updated Request:**
```json
{
  "model": "auto",  // Can be "auto", a provider ID, or "providerId/modelId"
  "provider": "server-3070",  // Optional: explicitly select provider
  "messages": [...],

  // Optional: model selection within provider
  "modelId": "qwen2.5-14b",

  // Existing parameters
  "temperature": 1.0,
  ...
}
```

**Examples:**

1. **Auto routing** (default behavior):
   ```json
   { "model": "auto", "messages": [...] }
   ```

2. **Explicit provider, default model**:
   ```json
   { "provider": "gaming-pc-3090", "messages": [...] }
   ```

3. **Explicit provider + model**:
   ```json
   { "provider": "server-3070", "modelId": "qwen2.5-7b", "messages": [...] }
   ```

4. **Shorthand notation**:
   ```json
   { "model": "server-3070/qwen2.5-14b", "messages": [...] }
   ```

**Response** (adds provider info):
```json
{
  "id": "chatcmpl-...",
  "model": "qwen2.5-14b",
  "provider": "server-3070",  // NEW: Which provider was used
  "choices": [...],
  "usage": {...}
}
```

## Router Implementation

### File Structure

```
apps/local-ai-router/
├── config/
│   ├── providers.yaml           # Static provider/model config
│   └── providers.example.yaml   # Example config
├── providers/
│   ├── __init__.py
│   ├── manager.py               # ProviderManager class
│   ├── health.py                # Health checking
│   ├── registry.py              # Provider/model registry
│   └── selection.py             # Auto-routing logic
├── models/
│   ├── provider.py              # Provider data model
│   ├── model.py                 # Model data model
│   └── health.py                # Health data model
└── main.py                      # FastAPI app
```

### Key Classes

```python
# providers/manager.py
class ProviderManager:
    """Manages providers, models, and health checks."""

    def __init__(self, config_path: str):
        self.providers: Dict[str, Provider] = {}
        self.models: Dict[str, Model] = {}
        self.health_checker = HealthChecker(self)
        self._load_config(config_path)

    def get_provider(self, provider_id: str) -> Provider:
        """Get provider by ID."""

    def get_model(self, model_id: str) -> Model:
        """Get model by ID."""

    def get_models_for_provider(self, provider_id: str) -> List[Model]:
        """Get all models for a provider."""

    def select_provider_model(
        self,
        request: ChatRequest,
        provider_hint: Optional[str] = None,
        model_hint: Optional[str] = None
    ) -> Tuple[Provider, Model]:
        """Auto-select best provider/model for request."""
```

```python
# providers/health.py
class HealthChecker:
    """Periodic health checking for all providers."""

    def __init__(self, manager: ProviderManager):
        self.manager = manager
        self.check_interval = 30  # seconds

    async def start(self):
        """Start periodic health checks."""

    async def check_provider(self, provider: Provider) -> ProviderHealth:
        """Check health of a single provider."""

    async def check_all(self) -> List[ProviderHealth]:
        """Check health of all providers."""
```

## Dashboard UI Changes

### Model Selection Component

Replace the current single dropdown with a two-step selection UI.

**File**: `apps/local-ai-dashboard/src/components/ModelSelector.tsx`

```typescript
interface ModelSelectorProps {
  selectedProvider?: string;
  selectedModel?: string;
  onSelect: (provider: string, model: string) => void;
}

export function ModelSelector({ selectedProvider, selectedModel, onSelect }: ModelSelectorProps) {
  const { data: providers } = useQuery({
    queryKey: ['providers'],
    queryFn: () => api.getProviders(),
    refetchInterval: 30000, // Refresh every 30s for health updates
  });

  const { data: models } = useQuery({
    queryKey: ['models', selectedProvider],
    queryFn: () => api.getModels(selectedProvider),
    enabled: !!selectedProvider,
  });

  return (
    <div className="flex gap-4">
      {/* Provider Selection */}
      <div className="flex-1">
        <label className="text-xs uppercase tracking-wider text-gray-500">
          Provider:
        </label>
        <select
          value={selectedProvider}
          onChange={(e) => {
            const provider = e.target.value;
            // Auto-select default model for this provider
            const defaultModel = models?.find(m => m.isDefault);
            onSelect(provider, defaultModel?.id || '');
          }}
          className="w-full px-3 py-2 bg-gray-800 border border-gray-700 rounded text-white"
        >
          <option value="">Auto (Best Available)</option>
          {providers?.map(p => (
            <option key={p.id} value={p.id} disabled={p.status !== 'online'}>
              {p.name} {p.status !== 'online' && '(Offline)'}
            </option>
          ))}
        </select>
      </div>

      {/* Model Selection (only if provider selected) */}
      {selectedProvider && (
        <div className="flex-1">
          <label className="text-xs uppercase tracking-wider text-gray-500">
            Model:
          </label>
          <select
            value={selectedModel}
            onChange={(e) => onSelect(selectedProvider, e.target.value)}
            className="w-full px-3 py-2 bg-gray-800 border border-gray-700 rounded text-white"
          >
            {models?.map(m => (
              <option
                key={m.id}
                value={m.id}
                disabled={m.status !== 'available'}
              >
                {m.name}
                {m.warmStatus === 'cold' && '❄️'}
                {m.status !== 'available' && '(Unavailable)'}
              </option>
            ))}
          </select>

          {/* Model details */}
          {selectedModel && (
            <div className="mt-2 text-xs text-gray-500">
              {models?.find(m => m.id === selectedModel)?.description}
            </div>
          )}
        </div>
      )}
    </div>
  );
}
```

### Provider Status Indicator

Show provider health in the UI.

```typescript
function ProviderStatus({ provider }: { provider: Provider }) {
  const statusColors = {
    online: 'text-green-400',
    offline: 'text-red-400',
    degraded: 'text-yellow-400',
    unknown: 'text-gray-400',
  };

  const statusIcons = {
    online: '●',
    offline: '●',
    degraded: '◐',
    unknown: '○',
  };

  return (
    <span className={statusColors[provider.status]}>
      {statusIcons[provider.status]} {provider.status}
    </span>
  );
}
```

## Migration Plan

### Phase 1: Backend Foundation

1. **Create provider configuration**
   - [ ] Create `apps/local-ai-router/config/providers.yaml`
   - [ ] Define all providers (server-3070, gaming-pc-3090, zai, anthropic)
   - [ ] Define all models per provider

2. **Implement data models**
   - [ ] Create `models/provider.py`
   - [ ] Create `models/model.py`
   - [ ] Create `models/health.py`

3. **Build provider system**
   - [ ] Implement `ProviderManager` class
   - [ ] Implement config loading from YAML
   - [ ] Implement provider/model lookup

### Phase 2: Health Checking

4. **Health check system**
   - [ ] Implement `HealthChecker` class
   - [ ] Add health check endpoints to each provider
   - [ ] Implement periodic background checks
   - [ ] Add `/providers/{id}/health` endpoint

### Phase 3: API Updates

5. **New API endpoints**
   - [ ] Add `GET /providers`
   - [ ] Add `GET /models`
   - [ ] Add `GET /providers/{id}/health`
   - [ ] Add `POST /health/check`

6. **Update chat completion endpoint**
   - [ ] Support `provider` parameter
   - [ ] Support `modelId` parameter
   - [ ] Support `model: "provider/model"` shorthand
   - [ ] Add `provider` to response
   - [ ] Implement auto-routing with new selection logic

### Phase 4: Frontend Updates

7. **Dashboard API client**
   - [ ] Add `getProviders()` method
   - [ ] Add `getModels(providerId?)` method
   - [ ] Add `getProviderHealth(providerId)` method
   - [ ] Update types for new API responses

8. **UI components**
   - [ ] Create `ModelSelector` component
   - [ ] Create `ProviderStatus` indicator
   - [ ] Update `ChatInterface` to use new selector
   - [ ] Add provider/model info to message metadata display

### Phase 5: Testing & Deployment

9. **Testing**
   - [ ] Test auto-routing with all providers healthy
   - [ ] Test fallback chain (disable providers one by one)
   - [ ] Test manual provider/model selection
   - [ ] Test health checks and status updates
   - [ ] Test context window enforcement

10. **Deployment**
    - [ ] Deploy router with new endpoints
    - [ ] Deploy updated dashboard
    - [ ] Verify all providers are discovered
    - [ ] Monitor health checks
    - [ ] Test end-to-end flow

## Success Criteria

- ✅ Providers and models are clearly separated in config
- ✅ Health status is visible in UI and updated regularly
- ✅ Auto-routing follows priority chain and respects health
- ✅ Manual provider/model selection works correctly
- ✅ Context window limits are enforced
- ✅ Provider fallback works when primary is unhealthy
- ✅ UI shows which provider/model was used for each message
- ✅ All existing functionality still works

## Future Enhancements (Out of Scope)

- Provider load balancing
- Model warmup on-demand
- Cost tracking per provider
- Usage statistics per model
- Provider-specific retry logic
- Model recommendation based on query type
- Automatic model selection based on message content
