# Claude Harness Monorepo Migration Plan

> Extracting claude-harness from homelab-ai into its own repository with profile-based configuration.

## Executive Summary

**Goal**: Create a standalone `claude-harness` repository that supports multiple deployment contexts (server, Mac Mini, local dev) through a profile system, while maintaining backwards compatibility during migration.

**Timeline**: ~2-3 sessions of focused work

---

## Current State

### Repository Structure
```
homelab-ai/
├── .gitea/workflows/build.yml    # Builds all homelab-ai components
├── claude-harness/               # ← Extract this
│   ├── main.py
│   ├── ralph-wiggum.sh
│   ├── Dockerfile
│   ├── entrypoint.sh
│   ├── clawd/                    # Avery profile source
│   └── ...
└── [other components]
```

### Deployment
- **Image**: `harbor.server.unarmedpuppy.com/library/claude-harness:latest`
- **Compose**: `home-server/apps/homelab-ai/docker-compose.yml`
- **Trigger**: Tag push to homelab-ai → Gitea Actions builds → Harbor → Watchtower deploys
- **Volumes**: claude-credentials, claude-workspace, claude-ssh, claude-ssh-host-keys

### Dependencies
| Dependency | Current Location | Notes |
|------------|------------------|-------|
| OAuth tokens | `claude-credentials` volume | `.claude.json`, `.claude/` |
| Git repos | `claude-workspace` volume | Shared with llm-router |
| SSH keys | `claude-ssh` volume | For git operations |
| Host keys | `claude-ssh-host-keys` volume | Persist across rebuilds |
| GPG key | `.gpg-key.asc` mounted | For commit signing |
| Authorized keys | Host file mounted | SSH access control |

---

## Target State

### New Repository Structure
```
claude-harness/                   # New standalone repo
├── .gitea/
│   └── workflows/
│       └── build.yml             # Single image, tag-triggered
├── profiles/
│   ├── ralph/                    # Server (Docker) - task processor
│   │   ├── profile.yaml
│   │   ├── SOUL.md
│   │   ├── IDENTITY.md
│   │   └── CLAUDE.md
│   ├── avery/                    # Mac Mini - family coordinator
│   │   ├── profile.yaml
│   │   ├── SOUL.md
│   │   ├── IDENTITY.md
│   │   ├── USER.md
│   │   ├── TOOLS.md
│   │   ├── HEARTBEAT.md
│   │   └── MEMORY.md
│   └── dev/                      # Local laptop - development
│       ├── profile.yaml
│       ├── SOUL.md
│       └── IDENTITY.md
├── skills/                       # Shared skills library
│   ├── task-management/
│   ├── git-operations/
│   └── ...
├── platform/                     # Platform-specific code
│   ├── macos/
│   │   ├── imsg.py               # iMessage wrapper
│   │   └── gog.py                # Google CLI wrapper
│   ├── docker/
│   │   └── entrypoint.sh
│   └── common/
│       └── tools.py
├── core/
│   ├── main.py                   # FastAPI service
│   ├── profile.py                # Profile loader
│   ├── ralph.py                  # Task loop (refactored)
│   └── cli.py                    # Direct CLI mode
├── deploy/
│   ├── Dockerfile
│   ├── docker-compose.yml        # Reference compose file
│   ├── systemd/                  # Linux service files
│   ├── launchd/                  # macOS service files
│   └── install.sh                # Mac/Linux installer
├── secrets/
│   └── .gitkeep                  # Mount point for secrets
├── AGENTS.md                     # Cross-profile instructions
├── CLAUDE.md                     # Default Claude instructions
├── README.md
└── requirements.txt
```

### Deployment Model
```
┌─────────────────────────────────────────────────────────────────┐
│                       Home Server                                │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │  claude-harness container                                  │  │
│  │  HARNESS_PROFILE=ralph                                     │  │
│  │  - Ralph Wiggum task processor                             │  │
│  │  - SSH deploy access                                       │  │
│  │  - Git operations                                          │  │
│  └───────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│                       Mac Mini                                   │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │  claude-harness (native)                                   │  │
│  │  HARNESS_PROFILE=avery                                     │  │
│  │  - Avery family coordinator                                │  │
│  │  - imsg, gog, twilio tools                                 │  │
│  │  - Heartbeat system                                        │  │
│  └───────────────────────────────────────────────────────────┘  │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │  n8n (docker)                                              │  │
│  │  - Schedules (morning briefing, etc.)                      │  │
│  │  - Triggers harness API                                    │  │
│  └───────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│                       Laptop (Local Dev)                         │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │  claude-harness (native)                                   │  │
│  │  HARNESS_PROFILE=dev                                       │  │
│  │  - Development & testing                                   │  │
│  │  - Local repos                                             │  │
│  └───────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

---

## Migration Phases

### Phase 1: Repository Setup (Foundation)

**1.1 Create new repo in Gitea**
```bash
# Via Gitea UI or API
# Org: homelab
# Name: claude-harness
# Visibility: Private
# Initialize: Empty (we'll push content)
```

**1.2 Extract and restructure files**
```bash
# Clone fresh
cd /tmp
git clone gitea:homelab/homelab-ai.git homelab-ai-temp
cd homelab-ai-temp

# Create new repo structure
mkdir -p claude-harness-new/{profiles,skills,platform,core,deploy}

# Copy core files
cp claude-harness/main.py claude-harness-new/core/
cp claude-harness/ralph-wiggum.sh claude-harness-new/core/ralph.sh
cp claude-harness/entrypoint.sh claude-harness-new/deploy/docker/
cp claude-harness/Dockerfile claude-harness-new/deploy/
cp claude-harness/requirements.txt claude-harness-new/
cp claude-harness/mcp-puppeteer.sh claude-harness-new/platform/docker/
cp claude-harness/CLAUDE.md claude-harness-new/
cp claude-harness/README.md claude-harness-new/

# Create ralph profile from existing
mkdir -p claude-harness-new/profiles/ralph
# Create profile.yaml (new file)
# Create SOUL.md, IDENTITY.md (new files for Ralph)

# Create avery profile from clawd
mkdir -p claude-harness-new/profiles/avery
cp claude-harness/clawd/SOUL.md claude-harness-new/profiles/avery/
cp claude-harness/clawd/IDENTITY.md claude-harness-new/profiles/avery/
cp claude-harness/clawd/USER.md claude-harness-new/profiles/avery/
cp claude-harness/clawd/TOOLS.md claude-harness-new/profiles/avery/
cp claude-harness/clawd/HEARTBEAT.md claude-harness-new/profiles/avery/
cp claude-harness/clawd/MEMORY.md claude-harness-new/profiles/avery/
# Create profile.yaml (new file)

# Create dev profile skeleton
mkdir -p claude-harness-new/profiles/dev
# Create profile.yaml, SOUL.md, IDENTITY.md

# Skills (copy from home-server or create new)
cp -r /workspace/home-server/agents/skills/task-management claude-harness-new/skills/
# ... other relevant skills
```

**1.3 Create profile.yaml files**

See [Profile Configuration](#profile-configuration) section below.

**1.4 Initialize git and push**
```bash
cd claude-harness-new
git init
git add .
git commit -m "feat: initial extraction from homelab-ai

- Profile-based configuration (ralph, avery, dev)
- Shared skills library
- Platform adapters for macos/docker"

git remote add origin gitea:homelab/claude-harness.git
git push -u origin main
```

---

### Phase 2: CI/CD Setup

**2.1 Create Gitea Actions workflow**

`.gitea/workflows/build.yml`:
```yaml
name: Build and Deploy

on:
  push:
    tags: ['v*']
  workflow_dispatch:

jobs:
  build:
    uses: unarmedpuppy/workflows/.gitea/workflows/docker-build.yml@main
    with:
      image_name: library/claude-harness
      app_path: apps/claude-harness
      dockerfile: deploy/Dockerfile
      context: .
    secrets: inherit

  deploy:
    needs: [build]
    runs-on: ubuntu-latest
    steps:
      - name: Setup SSH
        run: |
          mkdir -p ~/.ssh
          chmod 700 ~/.ssh
          printf '%s\n' "${{ secrets.DEPLOY_SSH_KEY }}" > ~/.ssh/deploy_key
          chmod 600 ~/.ssh/deploy_key
          ssh-keyscan -p ${{ secrets.DEPLOY_PORT }} ${{ secrets.DEPLOY_HOST }} >> ~/.ssh/known_hosts 2>/dev/null || true

      - name: Deploy claude-harness
        env:
          SSH_KEY: ~/.ssh/deploy_key
          SSH_USER: ${{ secrets.DEPLOY_USER }}
          SSH_HOST: ${{ secrets.DEPLOY_HOST }}
          SSH_PORT: ${{ secrets.DEPLOY_PORT }}
        run: |
          APP_PATH="/home/unarmedpuppy/server/apps/claude-harness"
          ssh -i $SSH_KEY -p $SSH_PORT -o StrictHostKeyChecking=no $SSH_USER@$SSH_HOST \
            "cd $APP_PATH && sudo docker compose pull && sudo docker compose up -d"
          echo 'Deployment complete!'
```

**2.2 Update shared workflow (if needed)**

The existing `docker-build.yml` workflow should work, but verify it handles the new context path correctly.

**2.3 Set up Gitea secrets**

Ensure the new repo has access to:
- `DEPLOY_SSH_KEY`
- `DEPLOY_HOST`
- `DEPLOY_PORT`
- `DEPLOY_USER`
- `HARBOR_USERNAME`
- `HARBOR_PASSWORD`

(These may already be org-level secrets)

---

### Phase 3: Code Refactoring

**3.1 Profile loader (`core/profile.py`)**

```python
"""Profile loading and environment detection."""

import os
import platform
import yaml
from pathlib import Path
from dataclasses import dataclass
from typing import Optional

@dataclass
class Profile:
    name: str
    display_name: str
    role: str
    capabilities: list[str]
    tools: dict
    claude_config: dict
    paths: dict
    # Loaded content
    soul: Optional[str] = None
    identity: Optional[str] = None
    user: Optional[str] = None
    tools_doc: Optional[str] = None
    heartbeat: Optional[str] = None

def detect_profile() -> str:
    """Auto-detect profile based on environment."""
    # Explicit override
    if profile := os.environ.get("HARNESS_PROFILE"):
        return profile

    # Platform-based detection
    if platform.system() == "Darwin":
        hostname = platform.node().lower()
        if "mac-mini" in hostname or "avery" in hostname:
            return "avery"
        return "dev"

    # Docker detection
    if Path("/.dockerenv").exists():
        return "ralph"

    return "dev"

def get_profiles_dir() -> Path:
    """Get profiles directory."""
    # Check for HARNESS_PROFILES_DIR override
    if profiles_dir := os.environ.get("HARNESS_PROFILES_DIR"):
        return Path(profiles_dir)

    # Default: relative to this file
    return Path(__file__).parent.parent / "profiles"

def load_profile(profile_name: str) -> Profile:
    """Load profile configuration and content."""
    profiles_dir = get_profiles_dir()
    profile_dir = profiles_dir / profile_name

    if not profile_dir.exists():
        raise ValueError(f"Profile not found: {profile_name} (looked in {profiles_dir})")

    # Load profile.yaml
    config_path = profile_dir / "profile.yaml"
    if not config_path.exists():
        raise ValueError(f"Missing profile.yaml in {profile_dir}")

    with open(config_path) as f:
        config = yaml.safe_load(f)

    # Load markdown content files
    content = {}
    for fname in ["SOUL.md", "IDENTITY.md", "USER.md", "TOOLS.md", "HEARTBEAT.md"]:
        fpath = profile_dir / fname
        if fpath.exists():
            key = fname.replace(".md", "").lower()
            content[key] = fpath.read_text()

    return Profile(
        name=config["name"],
        display_name=config.get("display_name", config["name"]),
        role=config.get("role", "Agent"),
        capabilities=config.get("capabilities", []),
        tools=config.get("tools", {}),
        claude_config=config.get("claude", {}),
        paths=config.get("paths", {}),
        soul=content.get("soul"),
        identity=content.get("identity"),
        user=content.get("user"),
        tools_doc=content.get("tools"),
        heartbeat=content.get("heartbeat"),
    )

def validate_profile(profile: Profile) -> list[str]:
    """Validate profile requirements are met. Returns list of errors."""
    errors = []

    # Check required binaries
    if requires := profile.tools:
        for tool_name, tool_config in requires.items():
            if binary := tool_config.get("binary"):
                if not Path(binary).exists() and not shutil.which(tool_name):
                    errors.append(f"Required binary not found: {tool_name} ({binary})")

    # Check platform
    if platform_req := profile.claude_config.get("requires", {}).get("platform"):
        current = platform.system().lower()
        if platform_req == "darwin" and current != "darwin":
            errors.append(f"Profile requires macOS, running on {current}")

    return errors
```

**3.2 System prompt builder (`core/prompt.py`)**

```python
"""System prompt construction from profile."""

from datetime import datetime
from pathlib import Path
from .profile import Profile

def load_memory(profile: Profile) -> str:
    """Load memory content for profile."""
    memory_path = Path(profile.paths.get("memory", "")).expanduser()

    if not memory_path.exists():
        return ""

    content = []

    # Long-term memory
    long_term = memory_path / "MEMORY.md"
    if long_term.exists():
        content.append(f"## Long-term Memory\n\n{long_term.read_text()}")

    # Recent daily logs (last 2 days)
    from datetime import timedelta
    for i in range(2):
        date = (datetime.now() - timedelta(days=i)).strftime("%Y-%m-%d")
        log_path = memory_path / f"{date}.md"
        if log_path.exists():
            content.append(f"## Log: {date}\n\n{log_path.read_text()}")

    return "\n\n---\n\n".join(content)

def build_system_prompt(profile: Profile) -> str:
    """Build complete system prompt from profile."""
    parts = []

    # Soul - core identity
    if profile.soul:
        parts.append(f"# SOUL\n\n{profile.soul}")

    # Identity - public persona
    if profile.identity:
        parts.append(f"# IDENTITY\n\n{profile.identity}")

    # User context
    if profile.user:
        parts.append(f"# USER CONTEXT\n\n{profile.user}")

    # Tools documentation
    if profile.tools_doc:
        parts.append(f"# TOOLS\n\n{profile.tools_doc}")

    # Memory (loaded dynamically)
    if memory := load_memory(profile):
        parts.append(f"# MEMORY\n\n{memory}")

    # Current time
    now = datetime.now().strftime("%Y-%m-%d %H:%M %Z")
    parts.append(f"# CURRENT TIME\n\n{now}")

    # Capabilities summary
    if profile.capabilities:
        caps = ", ".join(profile.capabilities)
        parts.append(f"# CAPABILITIES\n\nYou have access to: {caps}")

    return "\n\n---\n\n".join(parts)
```

**3.3 Update main.py**

Key changes to `core/main.py`:
- Import and use profile loader at startup
- Build system prompt from profile
- Validate profile requirements
- Use profile paths for workspace, memory
- Log profile info on startup

```python
# At startup
from core.profile import detect_profile, load_profile, validate_profile
from core.prompt import build_system_prompt

# Load profile
profile_name = detect_profile()
profile = load_profile(profile_name)

# Validate
errors = validate_profile(profile)
if errors:
    logger.warning(f"Profile validation warnings: {errors}")

# Log startup
logger.info(f"Starting claude-harness with profile: {profile.display_name} ({profile.name})")
logger.info(f"Role: {profile.role}")
logger.info(f"Capabilities: {profile.capabilities}")

# Use profile in API calls
@app.post("/v1/chat/completions")
async def chat_completions(...):
    system_prompt = build_system_prompt(profile)
    # ... rest of implementation
```

**3.4 Refactor Ralph as module**

Move Ralph Wiggum from shell script to Python module that can be invoked by any profile:

```python
# core/ralph.py
"""Ralph Wiggum - Autonomous task processor."""

class TaskLoop:
    def __init__(self, tasks_file: str, labels: list[str] = None):
        self.tasks_file = Path(tasks_file)
        self.labels = labels or []

    async def find_next_task(self) -> Optional[dict]:
        """Find next available task matching labels."""
        # Parse tasks.md
        # Return first OPEN task matching labels
        pass

    async def claim_task(self, task_id: str) -> bool:
        """Mark task as IN_PROGRESS."""
        pass

    async def complete_task(self, task_id: str, status: str = "CLOSED") -> bool:
        """Mark task as completed."""
        pass

    async def process_task(self, task: dict) -> dict:
        """Execute a task using Claude."""
        pass

    async def run_loop(self, max_tasks: int = None):
        """Main task processing loop."""
        pass
```

---

### Phase 4: Docker & Deployment Updates

**4.1 Update Dockerfile**

`deploy/Dockerfile`:
```dockerfile
FROM harbor.server.unarmedpuppy.com/docker-hub/library/python:3.11-slim

# ... existing setup ...

# Copy application
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY core/ ./core/
COPY profiles/ ./profiles/
COPY skills/ ./skills/
COPY platform/ ./platform/
COPY deploy/docker/entrypoint.sh /entrypoint.sh
COPY CLAUDE.md ./

# Default profile (can be overridden)
ENV HARNESS_PROFILE=ralph

ENTRYPOINT ["/entrypoint.sh"]
CMD ["python", "-m", "core.main"]
```

**4.2 Create new docker-compose in home-server**

`home-server/apps/claude-harness/docker-compose.yml`:
```yaml
# Claude Harness - Standalone deployment
#
# Profile: ralph (server task processor)
# Source: https://gitea.server.unarmedpuppy.com/homelab/claude-harness

services:
  claude-harness:
    image: harbor.server.unarmedpuppy.com/library/claude-harness:latest
    container_name: claude-harness
    restart: unless-stopped
    ports:
      - "8013:8013"
      - "2222:22"
      - "8016:8443"
    environment:
      - TZ=America/Chicago
      - HARNESS_PROFILE=ralph
      - GITEA_TOKEN=${GITEA_TOKEN:-}
      - GITHUB_TOKEN=${GITHUB_TOKEN:-}
      - GIT_AUTHOR_NAME=Joshua Jenquist
      - GIT_AUTHOR_EMAIL=github@jenquist.com
      - GIT_COMMITTER_NAME=Joshua Jenquist
      - GIT_COMMITTER_EMAIL=github@jenquist.com
      - GPG_KEY_ID=3B4E44601D30F05F
      - DEPLOY_HOST=192.168.86.47
      - DEPLOY_USER=claude-deploy
      - DEPLOY_PORT=4242
    volumes:
      - claude-credentials:/home/appuser/.claude
      - claude-workspace:/workspace
      - claude-ssh:/home/appuser/.ssh
      - claude-ssh-host-keys:/etc/ssh/host_keys
      - /home/unarmedpuppy/.ssh/authorized_keys:/etc/ssh/user_authorized_keys:ro
      - ./.gpg-key.asc:/etc/gpg-key.asc:ro
      - ./secrets.env:/app/secrets/secrets.env:ro  # NEW: unified secrets
    networks:
      - my-network
    extra_hosts:
      - "host.docker.internal:host-gateway"
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8013/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 60s
    labels:
      - "com.centurylinklabs.watchtower.enable=true"
      # ... existing traefik labels ...

networks:
  my-network:
    external: true

volumes:
  claude-credentials:
    external: true
  claude-workspace:
    external: true
  claude-ssh:
    external: true
  claude-ssh-host-keys:
    external: true
```

**4.3 Update homelab-ai docker-compose**

Remove claude-harness from `home-server/apps/homelab-ai/docker-compose.yml`:
- Remove the `claude-harness` service block
- Keep the volume definitions that are shared with other services
- Add comment pointing to new location

**4.4 Update homelab-ai CI/CD**

Remove claude-harness build job from `homelab-ai/.gitea/workflows/build.yml`:
- Remove `build-claude-harness` job
- Remove from `deploy.needs` array

---

### Phase 5: Secrets Management

**5.1 Create unified secrets file format**

`home-server/apps/claude-harness/secrets.env.example`:
```bash
# Claude Harness Secrets
# Copy to secrets.env and fill in values

# API Keys
ANTHROPIC_API_KEY=
GITEA_TOKEN=
GITHUB_TOKEN=

# Google (for avery profile)
GOOGLE_ACCOUNT=
GOOGLE_CALENDAR_ID=

# Twilio (for avery profile)
TWILIO_SID=
TWILIO_TOKEN=
TWILIO_FROM_NUMBER=

# Deploy access
DEPLOY_HOST=
DEPLOY_USER=
DEPLOY_PORT=
```

**5.2 Secrets loader**

```python
# core/secrets.py
"""Unified secrets management."""

import os
from pathlib import Path
from dotenv import load_dotenv

def load_secrets():
    """Load secrets from mounted file or environment."""
    # Check for mounted secrets file
    secrets_file = Path("/app/secrets/secrets.env")
    if secrets_file.exists():
        load_dotenv(secrets_file)

    # Also check home directory (for native installs)
    home_secrets = Path.home() / ".claude-harness" / "secrets.env"
    if home_secrets.exists():
        load_dotenv(home_secrets)
```

---

### Phase 6: Testing & Cutover

**6.1 Parallel testing**

1. Build and push new image from claude-harness repo
2. Deploy to test container (different name/ports)
3. Verify:
   - API responds correctly
   - Profile loads (check /health endpoint)
   - Ralph task loop works
   - Skills are available

**6.2 Cutover checklist**

```markdown
## Pre-Cutover
- [ ] New repo created in Gitea
- [ ] CI/CD workflow working (test build)
- [ ] Profile system implemented and tested
- [ ] New docker-compose created in home-server/apps/claude-harness/
- [ ] Secrets file created and populated
- [ ] Volumes verified (same external volumes)

## Cutover
- [ ] Stop old container: `docker stop claude-harness`
- [ ] Update homelab-ai compose (remove claude-harness service)
- [ ] Deploy new compose: `cd apps/claude-harness && docker compose up -d`
- [ ] Verify health: `curl http://localhost:8013/health`
- [ ] Verify Ralph: `curl http://localhost:8013/v1/ralph/status`
- [ ] Test job submission

## Post-Cutover
- [ ] Monitor logs for 24h
- [ ] Remove claude-harness from homelab-ai build.yml
- [ ] Update documentation references
- [ ] Archive clawd directory (or delete after stable)
```

**6.3 Rollback plan**

If issues occur:
1. Stop new container
2. Re-enable old service in homelab-ai compose
3. `docker compose up -d` in apps/homelab-ai
4. Investigate and fix before retrying

---

## Profile Configuration

### Ralph Profile (Server)

`profiles/ralph/profile.yaml`:
```yaml
name: ralph
display_name: "Ralph Wiggum"
role: "Autonomous Task Processor"

capabilities:
  - git
  - ssh
  - docker
  - filesystem
  - task-management

requires:
  binaries:
    - git
    - ssh

tools:
  ssh:
    enabled: true
    host: host.docker.internal
    port: 4242
    user: claude-deploy
  git:
    enabled: true
    author: "Claude Agent"
    email: "claude@homelab"

task_loop:
  enabled: true
  tasks_file: /workspace/home-server/tasks.md

claude:
  permissions: yolo
  timeout_sync: 1800
  timeout_async: 7200

paths:
  workspace: /workspace
  memory: /workspace/.claude-memory
```

`profiles/ralph/SOUL.md`:
```markdown
# SOUL - Ralph Wiggum

I am Ralph Wiggum, the autonomous task processor for the homelab infrastructure.

## Purpose

Execute tasks from tasks.md efficiently and correctly. Complete complex multi-step work without supervision.

## Operating Principles

- Read the task carefully before starting
- Verify completion criteria are met before marking done
- Commit and push all changes
- If blocked, mark task as BLOCKED with clear explanation
- Never assume - check the actual state

## Capabilities

- Git operations (clone, commit, push, branch)
- SSH to server for troubleshooting (read-only)
- Docker operations via SSH
- File editing and creation
- Code review and refactoring

## Boundaries

I can:
- Modify code in /workspace repos
- Commit and push changes
- Read server logs via SSH
- Restart services via SSH

I cannot:
- Delete containers/volumes/images
- Modify production data directly
- Make architectural decisions without task approval
- Access external systems beyond configured tools
```

`profiles/ralph/IDENTITY.md`:
```markdown
# IDENTITY - Ralph Wiggum

**Name:** Ralph Wiggum
**Role:** Autonomous Task Processor
**System:** claude-harness (Docker)

## Behavior

- Process tasks from tasks.md
- Work methodically through verification steps
- Provide clear commit messages
- Log progress in task updates

## Communication

When updating tasks:
- Be specific about what was done
- Include relevant file paths and line numbers
- Note any issues or follow-up work needed

## Quirk

"Me fail English? That's unpossible!" - I embrace the name but take the work seriously.
```

### Avery Profile (Mac Mini)

`profiles/avery/profile.yaml`:
```yaml
name: avery
display_name: "Avery Iris Jenquist"
role: "Family Coordinator"

capabilities:
  - imessage
  - google
  - twilio
  - filesystem
  - web

requires:
  platform: darwin
  binaries:
    - imsg
    - gog

tools:
  imsg:
    enabled: true
    default_chat_id: 4
    chats:
      family: 4
      joshua: 5
      abby: 6
  google:
    enabled: true
    account: aijenquist@gmail.com
    calendar_id: "0etal2q0us3nkegput87mbag80@group.calendar.google.com"
  twilio:
    enabled: true
    from_number: "+16122606660"

heartbeat:
  enabled: true
  interval: 30m
  checks:
    - email
    - calendar

claude:
  permissions: yolo
  timeout_sync: 1800
  timeout_async: 7200

paths:
  workspace: ~/clawd
  memory: ~/clawd/memory
```

(SOUL.md, IDENTITY.md, USER.md, TOOLS.md, HEARTBEAT.md already exist in clawd/)

### Dev Profile (Laptop)

`profiles/dev/profile.yaml`:
```yaml
name: dev
display_name: "Dev Agent"
role: "Local Development Assistant"

capabilities:
  - git
  - filesystem
  - web

tools:
  git:
    enabled: true
    author: "Joshua Jenquist"
    email: "github@jenquist.com"

claude:
  permissions: yolo
  timeout_sync: 1800
  timeout_async: 7200

paths:
  workspace: ~/Developer/homelab
  memory: ~/.claude-harness/memory
```

`profiles/dev/SOUL.md`:
```markdown
# SOUL - Dev Agent

I assist with local development on the homelab projects.

## Purpose

Help with coding, debugging, and local testing of homelab services.

## Operating Principles

- Work within the local development environment
- Don't deploy to production (that's Ralph's job)
- Help iterate quickly on changes
- Run tests before suggesting commits

## Capabilities

- Read and modify local code
- Run local tests
- Git operations (local branches)
- Web searches for documentation
```

---

## Timeline

| Phase | Tasks | Estimate |
|-------|-------|----------|
| **1. Repository Setup** | Create repo, extract files, structure profiles | 1-2 hours |
| **2. CI/CD Setup** | Workflow, secrets, test build | 30 min |
| **3. Code Refactoring** | Profile loader, prompt builder, main.py updates | 2-3 hours |
| **4. Docker Updates** | Dockerfile, compose files, homelab-ai cleanup | 1 hour |
| **5. Secrets Management** | Unified secrets, loader | 30 min |
| **6. Testing & Cutover** | Parallel test, cutover, monitoring | 1-2 hours |

**Total: ~6-8 hours across 2-3 sessions**

---

## Post-Migration

### Mac Mini Setup

After server migration is stable:

1. Clone claude-harness to Mac Mini
2. Install dependencies (Python, Node, Claude CLI)
3. Configure `HARNESS_PROFILE=avery`
4. Set up launchd service
5. Configure n8n to call harness API
6. Test imsg/gog/twilio integrations

### Laptop Setup

1. Clone claude-harness
2. Install dependencies
3. Configure `HARNESS_PROFILE=dev`
4. Optionally run as service or on-demand

---

## Questions to Resolve

1. **Git history**: Start fresh or preserve history via `git filter-branch`?
   - Recommendation: Fresh start (cleaner, history lives in homelab-ai)

2. **Shared volumes**: Keep using external volumes or create new ones?
   - Recommendation: Keep existing (claude-credentials, claude-workspace) for continuity

3. **Skills location**: Copy to new repo or symlink from home-server?
   - Recommendation: Copy core skills, maintain separately going forward

4. **Clawdbot**: Keep running or deprecate after Avery is stable?
   - Recommendation: Keep until Avery is proven, then deprecate

---

## Appendix: File Inventory

### Files to Extract
```
claude-harness/
├── main.py              → core/main.py
├── ralph-wiggum.sh      → core/ralph.sh (or Python rewrite)
├── entrypoint.sh        → deploy/docker/entrypoint.sh
├── Dockerfile           → deploy/Dockerfile
├── mcp-puppeteer.sh     → platform/docker/mcp-puppeteer.sh
├── requirements.txt     → requirements.txt
├── CLAUDE.md            → CLAUDE.md
├── README.md            → README.md
├── .claude/skills/      → skills/ (merge with others)
└── clawd/               → profiles/avery/ (selective copy)
```

### Files to Create
```
.gitea/workflows/build.yml
profiles/ralph/profile.yaml
profiles/ralph/SOUL.md
profiles/ralph/IDENTITY.md
profiles/dev/profile.yaml
profiles/dev/SOUL.md
profiles/dev/IDENTITY.md
core/profile.py
core/prompt.py
core/secrets.py
deploy/systemd/claude-harness.service
deploy/launchd/com.homelab.claude-harness.plist
deploy/install.sh
AGENTS.md
```

### Files in home-server to Update
```
apps/homelab-ai/docker-compose.yml  # Remove claude-harness service
apps/claude-harness/docker-compose.yml  # NEW
apps/claude-harness/secrets.env  # NEW
```
