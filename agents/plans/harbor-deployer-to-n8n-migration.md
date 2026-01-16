# Harbor Deployer Migration: Systemd → n8n

## Overview

Migrate the Harbor auto-deployer from a custom Python systemd service to an n8n workflow for better observability, debugging, and consistency with existing automation patterns.

## Current State

**Location**: `scripts/harbor-deployer.py`
**Service**: `systemctl status harbor-deployer`
**Config**: `scripts/harbor-deployer.json`
**Logs**: `journalctl -u harbor-deployer -f` or `/home/unarmedpuppy/server/logs/harbor-deployer.log`

**How it works:**
1. Polls every 60s
2. Lists containers with label `com.centurylinklabs.watchtower.enable=true`
3. For each container:
   - Get local image digest from `docker inspect`
   - Get remote digest from Harbor API (`/v2/{repo}/manifests/{tag}`)
   - If different → pull image → stop container → `docker compose up -d`
4. Send Mattermost notification on deploy

**Container-to-App mapping** (for finding compose files):
```
llm-router, llm-manager, homelab-ai-dashboard, claude-harness → homelab-ai
agent-core, agent-gateway → agent-gateway
polymarket-bot → polyjuiced
bird-api, bird-viewer → bird-viewer
```

## Target State

Two implementation options - recommend **Option A** for simplicity.

### Option A: Polling-Based (Recommended)

n8n workflow that polls Harbor on a schedule, similar to current approach but with n8n's observability.

**Pros:**
- Simpler to implement
- No Harbor configuration needed
- Matches existing n8n patterns

**Cons:**
- Slight latency (1-5 min depending on poll interval)
- More API calls than webhook approach

### Option B: Webhook-Based

Harbor sends webhook on image push → n8n receives → deploys immediately.

**Pros:**
- Instant deploys
- No wasted API calls
- More efficient

**Cons:**
- Requires Harbor webhook configuration per project
- Requires n8n webhook endpoint exposed
- More complex error handling

## Implementation Plan (Option A - Polling)

### Phase 1: Create n8n Workflow

#### Step 1.1: Create workflow file

Create `apps/n8n/workflows/harbor-auto-deploy.json` with this structure:

```
[Schedule Trigger] → [Get Watched Containers] → [Code: Parse] → [Loop: For Each Container]
                                                                         ↓
                                                      [Get Local Digest] → [Get Remote Digest]
                                                                         ↓
                                                              [Code: Compare Digests]
                                                                         ↓
                                                              [Filter: Needs Update?]
                                                                         ↓
                                                              [Deploy Container]
                                                                         ↓
                                                         [Mattermost Notification]
```

#### Step 1.2: Node Definitions

**1. Schedule Trigger**
```json
{
  "type": "n8n-nodes-base.scheduleTrigger",
  "parameters": {
    "rule": {
      "interval": [{ "field": "minutes", "minutesInterval": 2 }]
    }
  }
}
```

**2. Get Watched Containers (SSH)**
```bash
docker ps --filter 'label=com.centurylinklabs.watchtower.enable=true' \
  --format '{{.Names}}|{{.Image}}|{{.ID}}'
```

**3. Parse Containers (Code Node)**
```javascript
const output = $input.first().json.stdout || '';
const lines = output.split('\n').filter(l => l.trim());

// Container to app mapping for compose paths
const containerToApp = {
  'llm-router': 'homelab-ai',
  'llm-manager': 'homelab-ai',
  'homelab-ai-dashboard': 'homelab-ai',
  'claude-harness': 'homelab-ai',
  'agent-core': 'agent-gateway',
  'agent-gateway': 'agent-gateway',
  'polymarket-bot': 'polyjuiced',
  'bird-api': 'bird-viewer',
  'bird-viewer': 'bird-viewer',
};

return lines.map(line => {
  const [name, image, id] = line.split('|');
  const appName = containerToApp[name] || name;
  return {
    json: {
      container_name: name,
      image: image,
      container_id: id,
      app_name: appName,
      compose_path: `/home/unarmedpuppy/server/apps/${appName}/docker-compose.yml`
    }
  };
});
```

**4. Get Local Digest (SSH - in loop)**
```bash
docker image inspect {{ $json.image }} --format '{{index .RepoDigests 0}}' 2>/dev/null | cut -d'@' -f2
```

**5. Get Remote Digest (HTTP Request)**
- URL: `https://harbor.server.unarmedpuppy.com/v2/{{ $json.repository }}/manifests/{{ $json.tag }}`
- Method: HEAD
- Headers: `Accept: application/vnd.docker.distribution.manifest.v2+json`
- Response: Extract `Docker-Content-Digest` header

**6. Compare and Filter (Code + Filter)**
```javascript
const localDigest = $('Get Local Digest').first().json.stdout?.trim();
const remoteDigest = $('Get Remote Digest').first().json.headers['docker-content-digest'];

return [{
  json: {
    ...$json,
    local_digest: localDigest,
    remote_digest: remoteDigest,
    needs_update: localDigest !== remoteDigest
  }
}];
```

**7. Deploy Container (SSH)**
```bash
cd ~/server/apps/{{ $json.app_name }} && \
docker pull {{ $json.image }} && \
docker compose up -d {{ $json.service_name }}
```

**8. Mattermost Notification**
Use Mattermost node or HTTP Request to webhook URL.

### Phase 2: Test Workflow

1. Import workflow into n8n
2. Test with manual trigger first
3. Verify:
   - Containers are detected correctly
   - Digests are compared correctly
   - Deploy only triggers when needed
   - Mattermost notifications work

### Phase 3: Disable Systemd Service

```bash
# On server
sudo systemctl stop harbor-deployer
sudo systemctl disable harbor-deployer

# Optionally keep service file for rollback
sudo mv /etc/systemd/system/harbor-deployer.service /etc/systemd/system/harbor-deployer.service.backup
```

### Phase 4: Enable n8n Workflow

1. Activate the workflow in n8n UI
2. Monitor first few runs in execution history
3. Verify deploys work as expected

### Phase 5: Cleanup (After Verification)

```bash
# Remove old systemd service file
sudo rm /etc/systemd/system/harbor-deployer.service.backup
sudo systemctl daemon-reload

# Optionally archive the Python script
mv scripts/harbor-deployer.py scripts/archive/harbor-deployer.py.deprecated
```

## Implementation Plan (Option B - Webhook)

If you prefer webhook-based (instant deploys):

### Harbor Configuration

1. Go to Harbor UI → Projects → `library` → Webhooks
2. Add new webhook:
   - Event: `Artifact pushed`
   - Endpoint: `https://n8n.server.unarmedpuppy.com/webhook/harbor-deploy`
   - Auth Header: (optional, for security)

### n8n Workflow Changes

Replace Schedule Trigger with:

```json
{
  "type": "n8n-nodes-base.webhook",
  "parameters": {
    "path": "harbor-deploy",
    "httpMethod": "POST"
  }
}
```

Parse the Harbor webhook payload:
```javascript
// Harbor webhook payload contains:
// - event_type: "PUSH_ARTIFACT"
// - repository: { name: "library/pokedex", ... }
// - artifact: { tag: "latest", digest: "sha256:...", ... }

const payload = $input.first().json.body;
const repoName = payload.event_data?.repository?.name;
const tag = payload.event_data?.artifact?.tag || 'latest';
const digest = payload.event_data?.artifact?.digest;

// Map repo to container name
// ...
```

## Rollback Plan

If n8n workflow has issues:

```bash
# Re-enable systemd service
sudo mv /etc/systemd/system/harbor-deployer.service.backup /etc/systemd/system/harbor-deployer.service
sudo systemctl daemon-reload
sudo systemctl enable harbor-deployer
sudo systemctl start harbor-deployer

# Disable n8n workflow in UI
```

## Testing Checklist

- [ ] Workflow imports without errors
- [ ] Manual trigger executes successfully
- [ ] Watched containers are detected
- [ ] Local digest is retrieved correctly
- [ ] Remote digest is retrieved correctly (check Harbor auth)
- [ ] Digest comparison works (no false positives)
- [ ] Deploy only triggers when digest differs
- [ ] Docker compose restart works
- [ ] Mattermost notification is sent
- [ ] Workflow handles errors gracefully (container not found, Harbor unavailable, etc.)

## Benefits After Migration

1. **Observability**: View all execution history in n8n UI
2. **Debugging**: Click through each node to see inputs/outputs
3. **Retry**: One-click retry of failed executions
4. **Notifications**: Easy to add/modify notification channels
5. **No custom daemon**: One less systemd service to manage
6. **Consistency**: Matches other n8n automation patterns

## Files to Create/Modify

| Action | File |
|--------|------|
| Create | `apps/n8n/workflows/harbor-auto-deploy.json` |
| Archive | `scripts/harbor-deployer.py` → `scripts/archive/` |
| Delete | `/etc/systemd/system/harbor-deployer.service` (on server) |
| Update | `AGENTS.md` - update Harbor Deployer documentation |

## Notes

- The n8n `server-ssh` credential is already configured for SSH access
- Existing workflow `docker-container-auto-restart.json` shows the SSH pattern
- Poll interval of 2 minutes is reasonable (current is 60s, but n8n overhead makes 2min practical)
- Harbor token auth may be needed - current script handles this, workflow should too
