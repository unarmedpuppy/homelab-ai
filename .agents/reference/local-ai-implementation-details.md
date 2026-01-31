# Local AI System - Implementation Details & Decisions

**Purpose**: Document specific implementation decisions for features across all phases of the provider/model architecture rollout.

**Related Documentation**:
- [Architecture Audit](local-ai-architecture-audit.md) - Overall system review
- [Provider/Model Architecture Plan](../plans/local-ai-provider-model-architecture.md) - Core architectural plan

---

## Phase 0: Repository Structure & Deployment

### 0.1 Current State (Embedded in home-server)

**Current Structure**:
```
home-server/
├── apps/
│   ├── local-ai-router/          # FastAPI backend
│   │   ├── router.py
│   │   ├── models.py
│   │   ├── database.py
│   │   └── docker-compose.yml
│   └── local-ai-dashboard/        # React frontend
│       ├── src/
│       ├── vite.config.ts
│       └── docker-compose.yml
```

**Current Deployment**:
1. Build Docker images locally on server
2. Restart containers via `docker compose up -d --build`
3. Images are not published to registry
4. No versioning or tagging

**Limitations**:
- No artifact reuse across environments
- Slow deployments (rebuild every time)
- No version tracking
- Tight coupling to home-server repo

---

### 0.2 Future State (Extracted Repository)

**Decision**: Monorepo with published Docker images

**Rationale**:
- **Monorepo vs Multi-repo**: Monorepo is simpler for this use case
  - Router and dashboard are tightly coupled (shared data models, API contracts)
  - Single CI/CD pipeline for both services
  - Easier to coordinate changes across frontend and backend
  - Fewer repositories to manage

**Target Repository Structure**:
```
local-ai/                           # New standalone repo
├── router/                         # Backend service
│   ├── src/
│   │   ├── router.py
│   │   ├── models.py
│   │   ├── database.py
│   │   └── providers/
│   ├── Dockerfile
│   ├── requirements.txt
│   └── pyproject.toml
│
├── dashboard/                      # Frontend service
│   ├── src/
│   ├── Dockerfile
│   ├── package.json
│   └── vite.config.ts
│
├── .github/
│   └── workflows/
│       ├── build-router.yml        # Router CI/CD
│       └── build-dashboard.yml     # Dashboard CI/CD
│
├── docker-compose.yml              # Local development
├── docker-compose.prod.yml         # Production reference
└── README.md
```

**Home Server Integration**:
```
home-server/
├── apps/
│   └── local-ai/                   # Minimal wrapper
│       ├── docker-compose.yml      # Pulls published images
│       ├── .env                    # Environment config
│       └── README.md               # Deployment docs
```

---

### 0.3 Docker Image Publishing Strategy

**Decision**: GitHub Container Registry (GHCR) with semantic versioning

**Registry**: `ghcr.io/joshuajenquist/local-ai-router` and `ghcr.io/joshuajenquist/local-ai-dashboard`

**Why GHCR over Docker Hub**:
- Free for public and private repositories
- Native GitHub integration
- Automatic authentication via GitHub tokens
- Unlimited pulls
- Better security scanning

**Image Tagging Strategy**:
```
ghcr.io/joshuajenquist/local-ai-router:latest       # Latest stable
ghcr.io/joshuajenquist/local-ai-router:main         # Main branch (auto-deploy)
ghcr.io/joshuajenquist/local-ai-router:v1.2.3       # Semantic version
ghcr.io/joshuajenquist/local-ai-router:sha-abc1234  # Git SHA (for rollback)
```

**Versioning Approach**:
- **Semantic Versioning** (MAJOR.MINOR.PATCH)
  - **MAJOR**: Breaking API changes (v1.x.x → v2.0.0)
  - **MINOR**: New features, backward compatible (v1.1.x → v1.2.0)
  - **PATCH**: Bug fixes (v1.2.1 → v1.2.2)
- **Automated**: Use git tags to trigger releases
- **Manual**: Create tags via GitHub UI or `git tag v1.2.3 && git push --tags`

**GitHub Actions Workflow**:

**File**: `.github/workflows/build-router.yml`
```yaml
name: Build & Publish Router

on:
  push:
    branches:
      - main
    tags:
      - 'v*.*.*'
  pull_request:

env:
  REGISTRY: ghcr.io
  IMAGE_NAME: joshuajenquist/local-ai-router

jobs:
  build:
    runs-on: ubuntu-latest
    permissions:
      contents: read
      packages: write

    steps:
      - uses: actions/checkout@v4

      - name: Log in to GHCR
        uses: docker/login-action@v3
        with:
          registry: ${{ env.REGISTRY }}
          username: ${{ github.actor }}
          password: ${{ secrets.GITHUB_TOKEN }}

      - name: Extract metadata
        id: meta
        uses: docker/metadata-action@v5
        with:
          images: ${{ env.REGISTRY }}/${{ env.IMAGE_NAME }}
          tags: |
            type=ref,event=branch
            type=ref,event=pr
            type=semver,pattern={{version}}
            type=semver,pattern={{major}}.{{minor}}
            type=sha,prefix=sha-

      - name: Build and push
        uses: docker/build-push-action@v5
        with:
          context: ./router
          push: ${{ github.event_name != 'pull_request' }}
          tags: ${{ steps.meta.outputs.tags }}
          labels: ${{ steps.meta.outputs.labels }}
          cache-from: type=gha
          cache-to: type=gha,mode=max
```

**Similar workflow for dashboard** (`.github/workflows/build-dashboard.yml`)

**Trigger Behavior**:
- **Push to main**: Builds `main` and `latest` tags
- **Create tag v1.2.3**: Builds `v1.2.3`, `1.2`, and updates `latest`
- **Pull request**: Builds but doesn't push (for testing)

---

### 0.4 Migration Path

**Decision**: Gradual migration in 3 phases

#### Phase A: Prepare for Extraction (In home-server repo)

**Goal**: Make code portable without breaking current deployment

**Tasks**:
1. **Containerize properly**:
   - Ensure Dockerfiles don't rely on home-server context
   - Use environment variables for all config
   - Test building images standalone

2. **Documentation**:
   - Document all environment variables
   - Document volume mounts and data persistence
   - Document network requirements

3. **Configuration externalization**:
   - Move hardcoded values to environment variables
   - Create `.env.example` files

**No changes to deployment yet** - still building locally

---

#### Phase B: Extract to New Repository (Breaking change)

**Goal**: Create standalone repository with CI/CD

**Tasks**:
1. **Create new repo**: `github.com/joshuajenquist/local-ai`

2. **Copy code**:
   ```bash
   # In local-ai repo
   cp -r ../home-server/apps/local-ai-router ./router
   cp -r ../home-server/apps/local-ai-dashboard ./dashboard
   ```

3. **Set up GitHub Actions**:
   - Add build workflows for both services
   - Configure GHCR authentication
   - Test builds on main branch

4. **First release**:
   ```bash
   git tag v0.1.0
   git push --tags
   ```

5. **Verify published images**:
   ```bash
   docker pull ghcr.io/joshuajenquist/local-ai-router:v0.1.0
   docker pull ghcr.io/joshuajenquist/local-ai-dashboard:v0.1.0
   ```

**Home server still using local builds** - new repo is a mirror

---

#### Phase C: Switch to Published Images (In home-server repo)

**Goal**: Consume published images from home-server

**Tasks**:
1. **Update docker-compose.yml in home-server**:
   ```yaml
   # apps/local-ai/docker-compose.yml
   version: '3.8'

   services:
     local-ai-router:
       image: ghcr.io/joshuajenquist/local-ai-router:v0.1.0  # Was: build: ./local-ai-router
       container_name: local-ai-router
       environment:
         - DATABASE_PATH=/data/local-ai-router.db
         - GAMING_PC_URL=${GAMING_PC_URL}
       volumes:
         - /mnt/data/local-ai:/data
       ports:
         - "8012:8000"
       restart: unless-stopped

     local-ai-dashboard:
       image: ghcr.io/joshuajenquist/local-ai-dashboard:v0.1.0  # Was: build: ./local-ai-dashboard
       container_name: local-ai-dashboard
       environment:
         - VITE_API_URL=https://local-ai-api.server.unarmedpuppy.com
       ports:
         - "5173:80"
       restart: unless-stopped
   ```

2. **Delete source code from home-server**:
   ```bash
   # In home-server repo
   git rm -r apps/local-ai-router/
   git rm -r apps/local-ai-dashboard/

   # Keep only:
   # apps/local-ai/
   # ├── docker-compose.yml
   # ├── .env
   # └── README.md
   ```

3. **Deploy**:
   ```bash
   cd apps/local-ai
   docker compose pull  # Pull published images
   docker compose up -d  # Start services
   ```

**Now home-server only contains configuration**, not code

---

### 0.5 Harbor Integration (Optional)

**Decision**: Proxy GHCR through Harbor for offline capability

**Current Harbor Setup**: Already proxies Docker Hub, GHCR, etc.

**Configuration**:
```yaml
# In home-server/apps/local-ai/docker-compose.yml
services:
  local-ai-router:
    image: harbor.server.unarmedpuppy.com/ghcr/joshuajenquist/local-ai-router:v0.1.0
    # Instead of: ghcr.io/joshuajenquist/local-ai-router:v0.1.0
```

**Benefits**:
- Offline availability (Harbor caches images)
- Faster pulls (local network)
- Avoids GHCR rate limits
- Consistent with other home-server services

**Setup** (one-time):
1. Add GHCR as proxy in Harbor UI
2. Test pull: `docker pull harbor.server.unarmedpuppy.com/ghcr/joshuajenquist/local-ai-router:v0.1.0`

---

### 0.6 Deployment Workflow (After Migration)

**Development Workflow**:
```bash
# In local-ai repo
cd local-ai/

# Make changes
vim router/src/router.py

# Test locally
docker compose up --build

# Commit and push
git add .
git commit -m "feat: add provider health caching"
git push origin main

# Wait for CI/CD (~2-3 minutes)
# Check: https://github.com/joshuajenquist/local-ai/actions

# Verify published image
docker pull ghcr.io/joshuajenquist/local-ai-router:main
```

**Production Deployment**:
```bash
# In home-server repo (on server)
cd apps/local-ai

# Update image tag in docker-compose.yml
sed -i 's/:v0.1.0/:v0.2.0/g' docker-compose.yml

# Pull and restart
docker compose pull
docker compose up -d

# Verify
docker compose logs -f local-ai-router
```

**Rollback** (if needed):
```bash
# In docker-compose.yml, change tag back to previous version
sed -i 's/:v0.2.0/:v0.1.0/g' docker-compose.yml

# Pull old version and restart
docker compose pull
docker compose up -d
```

---

### 0.7 Version Management

**Release Process**:
1. **Feature complete**: All PRs merged to main
2. **Test main**: Verify `main` tag works in staging
3. **Create release**:
   ```bash
   git tag -a v1.2.0 -m "Release v1.2.0: Add provider/model architecture"
   git push --tags
   ```
4. **GitHub Actions automatically**:
   - Builds Docker images
   - Tags as `v1.2.0`, `1.2`, `latest`
   - Pushes to GHCR
5. **Update home-server**:
   - Change docker-compose.yml to use `v1.2.0`
   - Deploy to server

**Version Pinning Strategy**:
```yaml
# Option 1: Pin to exact version (safest)
image: ghcr.io/joshuajenquist/local-ai-router:v1.2.3

# Option 2: Pin to minor version (get patches automatically)
image: ghcr.io/joshuajenquist/local-ai-router:1.2

# Option 3: Always latest (risky for production)
image: ghcr.io/joshuajenquist/local-ai-router:latest

# Recommended: Pin to minor version
```

---

### 0.8 Timeline

**Immediate (Phase 1-4 implementation)**:
- Stay in home-server repo
- Build images locally
- Focus on features, not infrastructure

**After Phase 4 complete**:
- Execute Phase A (prepare for extraction)
- Execute Phase B (create standalone repo)
- Execute Phase C (switch to published images)

**Estimated Effort**:
- **Phase A**: 2-4 hours (configuration externalization, docs)
- **Phase B**: 1-2 hours (repo setup, CI/CD)
- **Phase C**: 1 hour (update home-server, test deployment)

**Total**: ~4-7 hours for complete migration

---

## Phase 1: Critical Foundation

### 1.1 Provider Configuration Format

**Decision**: YAML-based configuration with environment variable overrides

**File**: `apps/local-ai-router/config/providers.yaml`

**Format**:
```yaml
providers:
  - id: gaming-pc-3090
    name: "Gaming PC (RTX 3090)"
    type: local
    endpoint: "http://192.168.86.63:8000"
    priority: 1
    enabled: true
    maxConcurrent: 1
    gpu: "RTX 3090"
    location: "gaming-pc"

    # Health check config
    healthCheckInterval: 30  # seconds
    healthCheckTimeout: 5    # seconds
    healthCheckPath: "/health"

    # Auth (if needed for provider)
    authType: null  # null, "api_key", "bearer"
    authSecret: null  # env var name or direct value

models:
  - id: qwen2.5-14b
    name: "Qwen 2.5 14B"
    providerId: gaming-pc-3090
    contextWindow: 32768
    maxTokens: 8192
    isDefault: true

    # Cost tracking (optional)
    costPer1kTokens: 0.0  # Local models are free

    capabilities:
      streaming: true
      functionCalling: true
      vision: false
      jsonMode: false

    tags: ["chat", "coding", "fast"]
```

**Environment Variable Overrides**:
- `PROVIDER_{ID}_ENDPOINT` → Override endpoint URL
- `PROVIDER_{ID}_ENABLED` → Override enabled flag
- `PROVIDER_{ID}_API_KEY` → Set API key for cloud providers

**Validation**:
- Schema validation on startup (using Pydantic)
- Error if required fields missing
- Warning if optional fields have unusual values

---

### 1.2 Database Schema Updates

**Decision**: Use Alembic for migrations, add metadata fields incrementally

#### Install Alembic

```bash
cd apps/local-ai-router
pip install alembic
alembic init alembic
```

#### Migration 1: Add Conversation Metadata

**File**: `alembic/versions/001_add_conversation_metadata.py`

```python
"""Add conversation metadata fields

Revision ID: 001
Revises:
Create Date: 2025-12-29
"""
from alembic import op
import sqlalchemy as sa

def upgrade():
    # Add new columns to conversations table
    op.add_column('conversations', sa.Column('username', sa.String, nullable=True))
    op.add_column('conversations', sa.Column('source', sa.String, nullable=True))
    op.add_column('conversations', sa.Column('display_name', sa.String, nullable=True))

def downgrade():
    op.drop_column('conversations', 'display_name')
    op.drop_column('conversations', 'source')
    op.drop_column('conversations', 'username')
```

#### Migration 2: Add API Keys Table

**File**: `alembic/versions/002_add_api_keys.py`

```python
"""Add API keys table

Revision ID: 002
Revises: 001
Create Date: 2025-12-29
"""
from alembic import op
import sqlalchemy as sa

def upgrade():
    op.create_table(
        'api_keys',
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('key_hash', sa.String(64), nullable=False, unique=True),
        sa.Column('key_prefix', sa.String(8), nullable=False),  # First 8 chars for display
        sa.Column('name', sa.String, nullable=False),  # e.g., "agent-1", "opencode"
        sa.Column('created_at', sa.DateTime, nullable=False),
        sa.Column('last_used_at', sa.DateTime, nullable=True),
        sa.Column('expires_at', sa.DateTime, nullable=True),
        sa.Column('enabled', sa.Boolean, default=True),
        sa.Column('scopes', sa.String, nullable=True),  # JSON string, future use
        sa.Column('metadata', sa.String, nullable=True),  # JSON string
    )

    op.create_index('idx_api_keys_hash', 'api_keys', ['key_hash'])
    op.create_index('idx_api_keys_enabled', 'api_keys', ['enabled'])

def downgrade():
    op.drop_table('api_keys')
```

**Migration Commands**:
```bash
# Generate migration
alembic revision --autogenerate -m "description"

# Apply migrations
alembic upgrade head

# Rollback one migration
alembic downgrade -1
```

---

### 1.3 Provider Manager Implementation

**Decision**: Single `ProviderManager` class with dependency injection

**File**: `apps/local-ai-router/providers/manager.py`

**Key Design Decisions**:

1. **In-Memory State**: Active request tracking in memory (future: Redis for multi-instance)
2. **Async Locks**: Per-provider `asyncio.Lock` for thread safety
3. **Config Hot-Reload**: Phase 1 requires restart, Phase 4 adds hot-reload
4. **Health Caching**: Cache health status for 30s, avoid thundering herd

**Pseudocode**:
```python
class ProviderManager:
    def __init__(self, config_path: str):
        self.providers: Dict[str, Provider] = {}
        self.models: Dict[str, Model] = {}
        self.active_requests: Dict[str, int] = {}
        self.locks: Dict[str, asyncio.Lock] = {}
        self.health_cache: Dict[str, Tuple[ProviderHealth, float]] = {}

        self._load_config(config_path)
        self._init_locks()

    async def select_provider_and_model(
        self,
        request: ChatRequest,
        priority: int = 1
    ) -> Tuple[Provider, Model]:
        # Implementation from architecture plan
        pass

    async def increment_active_requests(self, provider_id: str):
        async with self.locks[provider_id]:
            self.active_requests[provider_id] = self.active_requests.get(provider_id, 0) + 1

    async def decrement_active_requests(self, provider_id: str):
        async with self.locks[provider_id]:
            self.active_requests[provider_id] = max(0, self.active_requests.get(provider_id, 0) - 1)
```

---

### 1.4 Health Checking Implementation

**Decision**: Background task with periodic checks, cached results

**File**: `apps/local-ai-router/providers/health.py`

**Design**:
- **Interval**: 30 seconds (configurable)
- **Timeout**: 5 seconds per provider
- **Concurrent Checks**: Check all providers in parallel
- **Degradation**: Mark as degraded if latency >5s, offline if failed 3 consecutive checks

**Health Check Endpoints**:
- Local providers (vLLM): `GET /health` → 200 OK
- Z.ai: `GET /health` or `POST /v1/models` → 200 OK
- Anthropic: `GET /v1/models` with API key → 200 OK

**Implementation**:
```python
class HealthChecker:
    def __init__(self, provider_manager: ProviderManager):
        self.manager = provider_manager
        self.interval = 30
        self.timeout = 5
        self.consecutive_failures: Dict[str, int] = {}

    async def start(self):
        """Start background health checking task"""
        while True:
            await self.check_all()
            await asyncio.sleep(self.interval)

    async def check_provider(self, provider: Provider) -> ProviderHealth:
        """Check health of single provider"""
        start_time = time.time()

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(f"{provider.endpoint}/health")

                if response.status_code == 200:
                    response_time = int((time.time() - start_time) * 1000)

                    # Determine status based on latency
                    if response_time > 5000:
                        status = "degraded"
                    else:
                        status = "healthy"

                    self.consecutive_failures[provider.id] = 0

                    return ProviderHealth(
                        providerId=provider.id,
                        status=status,
                        responseTime=response_time,
                        timestamp=datetime.utcnow().isoformat()
                    )
        except Exception as e:
            self.consecutive_failures[provider.id] = self.consecutive_failures.get(provider.id, 0) + 1

            # Mark offline after 3 consecutive failures
            status = "unhealthy" if self.consecutive_failures[provider.id] >= 3 else "degraded"

            return ProviderHealth(
                providerId=provider.id,
                status=status,
                error=str(e),
                timestamp=datetime.utcnow().isoformat()
            )
```

---

## Phase 2: Agent Support

### 2.1 API Key Management

**Decision**: SHA-256 hashed keys, prefix storage for display

**Key Format**: `lai_` + 32 random chars (e.g., `lai_5f4d3c2b1a9e8d7c6b5a4e3d2c1b0a9f`)

**Generation**:
```python
import secrets
import hashlib

def generate_api_key() -> Tuple[str, str, str]:
    """
    Generate API key.

    Returns:
        Tuple of (full_key, key_hash, key_prefix)
    """
    random_part = secrets.token_hex(16)
    full_key = f"lai_{random_part}"
    key_hash = hashlib.sha256(full_key.encode()).hexdigest()
    key_prefix = full_key[:8]  # "lai_5f4d"

    return full_key, key_hash, key_prefix
```

**Storage** (in database):
- `key_hash`: SHA-256 hash (for validation)
- `key_prefix`: First 8 chars (for display in UI)
- Never store the full key after initial generation

**Validation**:
```python
async def validate_api_key(key: str) -> Optional[ApiKey]:
    """Validate API key and return key metadata"""
    key_hash = hashlib.sha256(key.encode()).hexdigest()

    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, name, enabled, scopes, last_used_at
            FROM api_keys
            WHERE key_hash = ? AND enabled = 1
        """, (key_hash,))

        row = cursor.fetchone()
        if not row:
            return None

        # Update last_used_at
        cursor.execute("""
            UPDATE api_keys
            SET last_used_at = ?
            WHERE id = ?
        """, (datetime.utcnow(), row['id']))
        conn.commit()

        return ApiKey(
            id=row['id'],
            name=row['name'],
            enabled=row['enabled'],
            scopes=json.loads(row['scopes']) if row['scopes'] else None
        )
```

**CLI Tool**: `scripts/manage-api-keys.py`
```python
#!/usr/bin/env python3
"""Manage API keys for Local AI Router"""

import sys
import argparse
from datetime import datetime
from router.auth import generate_api_key
from router.database import get_db_connection

def create_key(name: str):
    """Create new API key"""
    full_key, key_hash, key_prefix = generate_api_key()

    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO api_keys (key_hash, key_prefix, name, created_at, enabled)
            VALUES (?, ?, ?, ?, 1)
        """, (key_hash, key_prefix, name, datetime.utcnow()))
        conn.commit()

    print(f"Created API key for '{name}':")
    print(f"  Key: {full_key}")
    print(f"  ⚠️  Save this key now - it won't be shown again!")

def list_keys():
    """List all API keys"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT key_prefix, name, created_at, last_used_at, enabled
            FROM api_keys
            ORDER BY created_at DESC
        """)

        print(f"{'Prefix':<12} {'Name':<20} {'Created':<20} {'Last Used':<20} {'Status':<10}")
        print("-" * 90)

        for row in cursor.fetchall():
            status = "Enabled" if row['enabled'] else "Disabled"
            last_used = row['last_used_at'] or "Never"
            print(f"{row['key_prefix']:<12} {row['name']:<20} {row['created_at']:<20} {last_used:<20} {status:<10}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Manage API keys")
    subparsers = parser.add_subparsers(dest='command')

    create_parser = subparsers.add_parser('create', help='Create new API key')
    create_parser.add_argument('name', help='Key name (e.g., agent-1, opencode)')

    list_parser = subparsers.add_parser('list', help='List all API keys')

    args = parser.parse_args()

    if args.command == 'create':
        create_key(args.name)
    elif args.command == 'list':
        list_keys()
    else:
        parser.print_help()
```

**Usage**:
```bash
# Create key for agent
python3 scripts/manage-api-keys.py create agent-1

# List all keys
python3 scripts/manage-api-keys.py list
```

---

### 2.2 Authentication Middleware

**Decision**: FastAPI dependency for API key validation

**File**: `apps/local-ai-router/auth.py`

```python
from fastapi import Header, HTTPException, Depends
from typing import Optional

async def validate_api_key_header(
    authorization: Optional[str] = Header(None)
) -> ApiKey:
    """
    Validate API key from Authorization header.

    Accepts:
      - Authorization: Bearer lai_...
      - Authorization: lai_...
    """
    if not authorization:
        raise HTTPException(status_code=401, detail="Missing API key")

    # Extract key from header
    if authorization.startswith("Bearer "):
        key = authorization[7:]
    else:
        key = authorization

    # Validate
    api_key = await validate_api_key(key)
    if not api_key:
        raise HTTPException(status_code=401, detail="Invalid API key")

    return api_key

# Use in endpoints
@app.post("/v1/chat/completions")
async def chat_completions(
    request: ChatRequest,
    api_key: ApiKey = Depends(validate_api_key_header)
):
    # api_key.name tells us which agent is calling
    priority = 0 if api_key.name.startswith("agent-") else 1
    ...
```

---

### 2.3 Streaming Implementation

**Decision**: Use FastAPI's `StreamingResponse` with OpenAI SSE format

**OpenAI SSE Format**:
```
data: {"id":"chatcmpl-123","object":"chat.completion.chunk","choices":[{"delta":{"content":"Hello"}}]}

data: {"id":"chatcmpl-123","object":"chat.completion.chunk","choices":[{"delta":{"content":" world"}}]}

data: [DONE]
```

**Implementation**:
```python
from fastapi.responses import StreamingResponse
import json

async def stream_chat_completion(
    provider: Provider,
    model: Model,
    request: ChatRequest
) -> StreamingResponse:
    """Stream chat completion from provider"""

    async def generate():
        completion_id = f"chatcmpl-{secrets.token_hex(12)}"

        async with httpx.AsyncClient(timeout=120.0) as client:
            async with client.stream(
                "POST",
                f"{provider.endpoint}/v1/chat/completions",
                json=request.dict(),
                headers={"Content-Type": "application/json"}
            ) as response:
                async for line in response.aiter_lines():
                    if line.startswith("data: "):
                        data = line[6:]  # Remove "data: " prefix

                        if data == "[DONE]":
                            yield f"data: [DONE]\n\n"
                            break

                        # Parse and re-emit chunk
                        try:
                            chunk = json.loads(data)
                            # Add provider info to chunk
                            chunk["provider"] = provider.id
                            yield f"data: {json.dumps(chunk)}\n\n"
                        except json.JSONDecodeError:
                            continue

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        }
    )
```

---

### 2.4 Error Handling & Retry Logic

**Decision**: Single retry with exponential backoff, OpenAI-compatible errors

**Retry Strategy**:
- **Transient errors**: Retry once after 1s delay
- **Provider unavailable**: Immediate failover to next provider
- **Timeout**: No retry, return error

**Error Format** (OpenAI-compatible):
```python
class ErrorResponse(BaseModel):
    error: dict

def create_error_response(
    message: str,
    type: str,
    code: str,
    status_code: int = 500
) -> HTTPException:
    """Create OpenAI-compatible error response"""
    return HTTPException(
        status_code=status_code,
        detail={
            "error": {
                "message": message,
                "type": type,
                "code": code
            }
        }
    )

# Usage
raise create_error_response(
    message="All providers are currently busy. Please retry in a few seconds.",
    type="service_unavailable",
    code="provider_capacity_exceeded",
    status_code=503
)
```

**Timeout Values**:
```python
TIMEOUTS = {
    "local": {
        "connect": 5,
        "read": 60,
        "write": 60,
        "pool": 60
    },
    "cloud": {
        "connect": 10,
        "read": 120,
        "write": 120,
        "pool": 120
    }
}
```

---

## Phase 3: Dashboard Enhancement

### 3.1 Image Upload Implementation

**Decision**: Persistent storage in `data/images/`, file references in DB

**Storage Structure**:
```
data/images/
├── {conversation_id}/
│   ├── {message_id}/
│   │   ├── 001_original_filename.png
│   │   ├── 002_another_image.jpg
│   │   └── ...
```

**Database Schema**:
```python
# Add to messages table
op.add_column('messages', sa.Column('image_refs', sa.String, nullable=True))  # JSON array
```

**Image Reference Format** (stored as JSON in `image_refs`):
```json
[
  {
    "filename": "001_screenshot.png",
    "path": "data/images/conv-123/msg-456/001_screenshot.png",
    "size": 1024000,
    "mimeType": "image/png",
    "width": 1920,
    "height": 1080
  }
]
```

**Upload Endpoint**:
```python
from fastapi import UploadFile, File
from PIL import Image
import os

@app.post("/v1/images/upload")
async def upload_image(
    conversation_id: str,
    message_id: str,
    file: UploadFile = File(...)
) -> dict:
    """Upload image for message"""

    # Validate
    if file.size > 10 * 1024 * 1024:  # 10MB
        raise HTTPException(400, "Image too large (max 10MB)")

    if not file.content_type.startswith("image/"):
        raise HTTPException(400, "Invalid file type")

    # Create directory
    image_dir = f"data/images/{conversation_id}/{message_id}"
    os.makedirs(image_dir, exist_ok=True)

    # Count existing images
    existing = len([f for f in os.listdir(image_dir) if f.endswith(('.png', '.jpg', '.jpeg', '.gif'))])
    if existing >= 5:
        raise HTTPException(400, "Maximum 5 images per message")

    # Save file
    sequence = f"{existing + 1:03d}"
    filename = f"{sequence}_{file.filename}"
    filepath = os.path.join(image_dir, filename)

    with open(filepath, "wb") as f:
        content = await file.read()
        f.write(content)

    # Get image dimensions
    with Image.open(filepath) as img:
        width, height = img.size

    return {
        "filename": filename,
        "path": filepath,
        "size": len(content),
        "mimeType": file.content_type,
        "width": width,
        "height": height
    }
```

**Dashboard Component**:
```typescript
// apps/local-ai-dashboard/src/components/ImageUpload.tsx
async function uploadImage(file: File, conversationId: string, messageId: string) {
  const formData = new FormData();
  formData.append('file', file);

  const response = await fetch(
    `/v1/images/upload?conversation_id=${conversationId}&message_id=${messageId}`,
    {
      method: 'POST',
      body: formData,
      headers: {
        'Authorization': `Bearer ${apiKey}`
      }
    }
  );

  return response.json();
}
```

**Cleanup Policy**:
- Delete images when conversation is deleted
- Keep images indefinitely otherwise
- Future: Add retention policy (e.g., delete after 90 days)

---

### 3.2 Provider Visibility in Dashboard

**Decision**: Two-step dropdown with provider status indicators

**UI Component**: `ModelSelector.tsx`
```typescript
interface ModelSelectorProps {
  onSelect: (provider: string, model: string) => void;
}

function ModelSelector({ onSelect }: ModelSelectorProps) {
  const [selectedProvider, setSelectedProvider] = useState<string>('auto');

  const { data: providers } = useQuery({
    queryKey: ['providers'],
    queryFn: () => api.getProviders(),
    refetchInterval: 30000  // Refresh every 30s
  });

  const { data: models } = useQuery({
    queryKey: ['models', selectedProvider],
    queryFn: () => api.getModels({ provider: selectedProvider }),
    enabled: selectedProvider !== 'auto'
  });

  return (
    <div className="space-y-4">
      {/* Provider Selection */}
      <div>
        <label>Provider</label>
        <select value={selectedProvider} onChange={(e) => setSelectedProvider(e.target.value)}>
          <option value="auto">Auto (Best Available)</option>
          {providers?.map(p => (
            <option key={p.id} value={p.id} disabled={p.status !== 'online'}>
              <StatusIcon status={p.status} /> {p.name}
              {p.status !== 'online' && ' (Offline)'}
              {p.activeRequests > 0 && ` (${p.activeRequests}/${p.maxConcurrent})`}
            </option>
          ))}
        </select>
      </div>

      {/* Model Selection (if provider selected) */}
      {selectedProvider !== 'auto' && (
        <div>
          <label>Model</label>
          <select onChange={(e) => onSelect(selectedProvider, e.target.value)}>
            {models?.map(m => (
              <option key={m.id} value={m.id}>
                {m.name}
                {m.warmStatus === 'cold' && ' ❄️'}
                {m.warmStatus === 'warm' && ' 🔥'}
              </option>
            ))}
          </select>
        </div>
      )}
    </div>
  );
}
```

---

## Phase 4: Operational Excellence

### 4.1 Prometheus Metrics

**Decision**: Use `prometheus_client` library, standard metric naming

**Installation**:
```bash
pip install prometheus-client
```

**Metrics Definition**:
```python
from prometheus_client import Counter, Histogram, Gauge, generate_latest

# Request metrics
requests_total = Counter(
    'local_ai_requests_total',
    'Total requests',
    ['endpoint', 'model', 'provider', 'status']
)

request_duration = Histogram(
    'local_ai_request_duration_seconds',
    'Request duration in seconds',
    ['endpoint', 'provider']
)

# Provider metrics
provider_active_requests = Gauge(
    'local_ai_provider_active_requests',
    'Currently active requests per provider',
    ['provider']
)

provider_health = Gauge(
    'local_ai_provider_health',
    'Provider health status (1=healthy, 0=unhealthy)',
    ['provider']
)

# Failover metrics
provider_failover_total = Counter(
    'local_ai_provider_failover_total',
    'Provider failover events',
    ['from_provider', 'to_provider']
)
```

**Metrics Endpoint**:
```python
@app.get("/metrics")
async def metrics():
    """Prometheus metrics endpoint"""
    return Response(
        content=generate_latest(),
        media_type="text/plain"
    )
```

**Update Metrics in Code**:
```python
# In router endpoint
start_time = time.time()

try:
    provider, model = await provider_manager.select_provider_and_model(request)

    # Update active requests gauge
    provider_active_requests.labels(provider=provider.id).inc()

    result = await call_provider(provider, model, request)

    # Record success
    requests_total.labels(
        endpoint="/v1/chat/completions",
        model=model.id,
        provider=provider.id,
        status="success"
    ).inc()

    return result

except Exception as e:
    # Record failure
    requests_total.labels(
        endpoint="/v1/chat/completions",
        model="unknown",
        provider="unknown",
        status="error"
    ).inc()
    raise

finally:
    # Decrement active requests
    provider_active_requests.labels(provider=provider.id).dec()

    # Record duration
    request_duration.labels(
        endpoint="/v1/chat/completions",
        provider=provider.id
    ).observe(time.time() - start_time)
```

---

### 4.2 Cost Tracking

**Decision**: Calculate cost from token counts using model config

**Cost Calculation**:
```python
def calculate_cost(model: Model, usage: dict) -> float:
    """
    Calculate cost for request.

    Args:
        model: Model config with costPer1kTokens
        usage: {"prompt_tokens": 100, "completion_tokens": 50}

    Returns:
        Cost in USD
    """
    if model.costPer1kTokens == 0.0:
        return 0.0  # Local models are free

    total_tokens = usage.get("prompt_tokens", 0) + usage.get("completion_tokens", 0)
    cost = (total_tokens / 1000.0) * model.costPer1kTokens

    return round(cost, 6)
```

**Add to Metrics Table**:
```python
# Migration 003: Add cost tracking
op.add_column('metrics', sa.Column('cost_usd', sa.Float, default=0.0))
```

**Daily Cost Rollup**:
```sql
SELECT
    date,
    SUM(cost_usd) as total_cost,
    COUNT(*) as total_requests,
    SUM(cost_usd) / COUNT(*) as avg_cost_per_request
FROM metrics
WHERE date >= DATE('now', '-30 days')
GROUP BY date
ORDER BY date DESC;
```

---

### 4.3 OpenCode Integration

**Decision**: Document configuration in separate guide

**File**: `agents/reference/opencode-integration.md`

**Configuration Example**:
```json
{
  "providers": [
    {
      "name": "local-ai",
      "type": "openai",
      "baseURL": "https://local-ai-api.server.unarmedpuppy.com/v1",
      "apiKey": "lai_your_key_here",
      "models": ["auto", "gaming-pc-3090", "server-3070"]
    }
  ]
}
```

**Testing**:
```python
# Test script: scripts/test-opencode-integration.py
import openai

client = openai.OpenAI(
    base_url="https://local-ai-api.server.unarmedpuppy.com/v1",
    api_key="lai_test_key"
)

# Test streaming
for chunk in client.chat.completions.create(
    model="auto",
    messages=[{"role": "user", "content": "Hello!"}],
    stream=True
):
    print(chunk.choices[0].delta.content, end="", flush=True)
```

---

## Implementation Checklist

### Phase 1: Critical Foundation
- [ ] Create `providers.yaml` config file
- [ ] Implement ProviderManager class
- [ ] Add Alembic migrations (conversation metadata)
- [ ] Implement HealthChecker background task
- [ ] Test concurrency tracking

### Phase 2: Agent Support
- [ ] Create API keys database table (migration)
- [ ] Implement API key generation CLI tool
- [ ] Add authentication middleware
- [ ] Validate streaming with OpenAI SDK
- [ ] Test error handling and failover

### Phase 3: Dashboard Enhancement
- [x] Implement image upload endpoint (POST /v1/images/upload)
- [x] Add image storage directory structure (data/images/{conv_id}/{msg_id}/)
- [x] Create ImageUpload component in dashboard (drag-and-drop, file validation)
- [x] Persist image_refs in messages table (JSON column via Alembic migration 004)
- [x] Convert images to base64 for vision models in router (format_messages_for_vision)
- [x] Upload images from ChatInterface before sending messages
- [ ] Implement two-step ModelSelector
- [ ] Show provider/model in message metadata
- [x] Sunset local-ai-app (completed 2025-12-30, moved to `inactive/`)

### Phase 4: Operational Excellence
- [ ] Add Prometheus metrics endpoint
- [ ] Implement cost calculation
- [ ] Create Grafana dashboard JSON
- [ ] Document OpenCode integration
- [ ] Write agent integration guide

---

**Last Updated**: 2025-12-29
**Next Review**: After Phase 1 completion
