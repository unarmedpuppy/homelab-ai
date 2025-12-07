# Tasks

Task tracking for Home Server.

**Status**: Active development
**Last Updated**: 2025-12-06

## Task Claiming Protocol

```bash
# 1. Pull latest
git pull origin main

# 2. Check task status - only claim [AVAILABLE] tasks

# 3. Edit this file: change [AVAILABLE] → [CLAIMED by @your-id]

# 4. Commit and push within 1 minute (creates "lock")
git add agents/tasks/tasks.md
git commit -m "claim: Task X - Description"
git push origin main

# 5. Create feature branch
git checkout -b feature/task-x-description
```

## Task Status Legend

- `[AVAILABLE]` - Ready to claim
- `[CLAIMED by @id]` - Locked by an agent
- `[IN PROGRESS - X%]` - Work underway
- `[COMPLETE]` - Finished
- `[BLOCKED]` - Waiting on dependency

---

## Current Tasks

| Task | Description | Status | Priority |
|------|-------------|--------|----------|
| T1 | Consolidate metrics system (8 files → 3) | [AVAILABLE] | P0 |
| T2 | Remove backward compat duplication in strategy.py | [AVAILABLE] | P1 |
| T3 | Standardize import patterns | [AVAILABLE] | P2 |
| T4 | Add missing type hints | [AVAILABLE] | P2 |
| T5 | Standardize error handling | [AVAILABLE] | P1 |
| T6 | WebSocket data producer integration | [AVAILABLE] | P0 |
| T7 | UI WebSocket integration | [AVAILABLE] | P1 |
| T8 | WebSocket testing | [AVAILABLE] | P1 |
| T9 | IBKR integration testing | [AVAILABLE] | P0 |
| T10 | Strategy-to-execution pipeline | [AVAILABLE] | P0 |
| T11 | Sentiment provider base class | [AVAILABLE] | P1 |
| T12 | Standardize Traefik config: local DNS no-auth, external auth | [CLAIMED by @auto] | P1 |
| T13 | Homepage cleanup: Infrastructure category + icons | [COMPLETE] | P1 |
| T14 | Homepage cleanup: Media apps category + icons | [CLAIMED by @auto] | P1 |
| T15 | Homepage cleanup: Productivity category + icons | [COMPLETE] | P1 |
| T16 | Homepage cleanup: Social/News + Gaming + Trading icons | [CLAIMED by @auto] | P1 |

### Task T1: Consolidate metrics system (8 files → 3)
**Priority**: P0
**Dependencies**: None
**Effort**: High
**Project**: trading-bot

**Objective**: Reduce metrics system from 8 files to 3 for better code quality. Biggest code quality win. See IMPLEMENTATION_ROADMAP.md

**Files to modify**:
- Metrics-related files in trading-bot

**Success Criteria**:
- [ ] Metrics system consolidated to 3 files
- [ ] All functionality preserved
- [ ] Tests pass

### Task T2: Remove backward compat duplication in strategy.py
**Priority**: P1
**Dependencies**: None
**Effort**: Medium
**Project**: trading-bot

**Objective**: Remove duplicate enums in src/core/strategy.py

**Files to modify**:
- `apps/trading-bot/src/core/strategy.py`

**Success Criteria**:
- [ ] Duplicate enums removed
- [ ] Backward compatibility maintained if needed
- [ ] Tests pass

### Task T3: Standardize import patterns
**Priority**: P2
**Dependencies**: None
**Effort**: Low
**Project**: trading-bot

**Objective**: Standardize import patterns, focus on sentiment providers

**Files to modify**:
- Sentiment provider files

**Success Criteria**:
- [ ] Consistent import patterns
- [ ] Code style guide followed

### Task T4: Add missing type hints
**Priority**: P2
**Dependencies**: None
**Effort**: Low
**Project**: trading-bot

**Objective**: Add missing type hints to range_bound.py and sentiment providers

**Files to modify**:
- `apps/trading-bot/src/.../range_bound.py`
- Sentiment provider files

**Success Criteria**:
- [ ] All type hints added
- [ ] Type checking passes

### Task T5: Standardize error handling
**Priority**: P1
**Dependencies**: None
**Effort**: Medium
**Project**: trading-bot

**Objective**: Replace broad `except Exception` with specific exception handling

**Files to modify**:
- Files with broad exception handling

**Success Criteria**:
- [ ] Specific exception types used
- [ ] Error handling consistent
- [ ] Tests pass

### Task T6: WebSocket data producer integration
**Priority**: P0
**Dependencies**: None
**Effort**: High
**Project**: trading-bot

**Objective**: Connect data to WebSocket streams

**Files to modify**:
- WebSocket producer files

**Success Criteria**:
- [ ] Data flows through WebSocket
- [ ] Integration tested

### Task T7: UI WebSocket integration
**Priority**: P1
**Dependencies**: T6
**Effort**: Medium
**Project**: trading-bot

**Objective**: Dashboard real-time updates via WebSocket

**Files to modify**:
- UI/frontend files

**Success Criteria**:
- [ ] Real-time updates working
- [ ] UI responsive

### Task T8: WebSocket testing
**Priority**: P1
**Dependencies**: T6, T7
**Effort**: Medium
**Project**: trading-bot

**Objective**: Add WebSocket tests (no WS tests currently)

**Files to modify**:
- Test files

**Success Criteria**:
- [ ] WebSocket tests added
- [ ] Test coverage adequate

### Task T9: IBKR integration testing
**Priority**: P0
**Dependencies**: None
**Effort**: High
**Project**: trading-bot

**Objective**: Paper trading validation for IBKR integration

**Files to modify**:
- IBKR integration files

**Success Criteria**:
- [ ] Paper trading validated
- [ ] Integration tested

### Task T10: Strategy-to-execution pipeline
**Priority**: P0
**Dependencies**: None
**Effort**: High
**Project**: trading-bot

**Objective**: Signal → order with safety checks

**Files to modify**:
- Strategy and execution files

**Success Criteria**:
- [ ] Pipeline working end-to-end
- [ ] Safety checks in place
- [ ] Tests pass

### Task T11: Sentiment provider base class
**Priority**: P1
**Dependencies**: None
**Effort**: Medium
**Project**: trading-bot

**Objective**: Reduce boilerplate in 13 providers

**Files to modify**:
- Sentiment provider files

**Success Criteria**:
- [ ] Base class created
- [ ] Providers refactored
- [ ] Boilerplate reduced

### Task T12: Standardize Traefik config: local DNS no-auth, external auth
**Priority**: P1
**Dependencies**: None
**Effort**: High
**Project**: home-server

**Objective**: Apply consistent Traefik configuration pattern across all apps:
- Local network (192.168.86.0/24) access without authentication
- External access requires authentication (except x-external: true services)
- Update homepage.href from IP:port to subdomain URLs
- Add HTTPS redirect middleware (Plex pattern)
- Add loadbalancer.server.port where missing

**Scope**:
- **Exclude**: `apps/media-download/*` directory
- **Exclude**: Services with `x-external: true` (maptapdat, plex, minecraft)
- **Target**: ~24 services with `traefik.enable=true`
- **Update**: ~20 services with `homepage.href` using IP:port

**Reference Patterns**:
- **Homepage**: Local network auth bypass pattern (priority 100, ClientIP 192.168.86.0/24)
- **Plex**: HTTPS redirect + loadbalancer.server.port pattern

**Services to Update** (with Traefik config):
1. `apps/bedrock-viz/docker-compose.yml`
2. `apps/open-archiver/docker-compose.yml`
3. `apps/monica/docker-compose.yml`
4. `apps/homepage/docker-compose.yml` ✅ (already done)
5. `apps/homeassistant/docker-compose.yml`
6. `apps/open-health/docker-compose.yml`
7. `apps/immich/docker-compose.yml`
8. `apps/beaverhabits/docker-compose.yml`
9. `apps/rust/docker-compose.yml`
10. `apps/grafana/docker-compose.yml`
11. `apps/wiki/docker-compose.yml`
12. `apps/ghost/docker-compose.yml`
13. `apps/mazanoke/docker-compose.yml`
14. `apps/n8n/docker-compose.yml`
15. `apps/campfire/docker-compose.yml`
16. `apps/soulsync/docker-compose.yml`
17. `apps/vaultwarden/docker-compose.yml`
18. `apps/libreddit/docker-compose.yml`
19. `apps/mealie/docker-compose.yml`
20. `apps/adguard-home/docker-compose.yml`
21. `apps/paperless-ngx/docker-compose.yml`
22. `apps/traefik/docker-compose.yml`
23. `apps/local-ai-app/docker-compose.yml`

**Services to Skip** (x-external: true):
- `apps/maptapdat/docker-compose.yml`
- `apps/plex/docker-compose.yml`
- `apps/minecraft/docker-compose.yml`

**Files to modify**:
- All docker-compose.yml files listed above (except skipped services)

**Success Criteria**:
- [ ] All services with Traefik config have local network auth bypass (priority 100)
- [ ] All services have external auth requirement (priority 1) unless x-external: true
- [ ] All homepage.href labels use subdomain format (https://subdomain.server.unarmedpuppy.com)
- [ ] HTTPS redirect middleware added where appropriate (Plex pattern)
- [ ] loadbalancer.server.port specified for all services
- [ ] All changes tested and deployed
- [ ] No services in media-download directory modified
- [ ] x-external: true services left unchanged

**Implementation Steps**:
1. For each service with `traefik.enable=true`:
   - Add local network router (priority 100, ClientIP 192.168.86.0/24, no auth)
   - Add/update external router (priority 1, with auth middleware)
   - Add HTTPS redirect middleware if missing
   - Add loadbalancer.server.port if missing
2. For each service with `homepage.href`:
   - Extract subdomain from existing Traefik Host rule
   - Update homepage.href to `https://subdomain.server.unarmedpuppy.com`
3. Test each service:
   - Local access works without auth
   - External access requires auth (unless x-external: true)
   - HTTPS redirect works
   - Subdomain resolves correctly

**Notes**:
- Use homepage pattern for auth bypass
- Use Plex pattern for HTTPS redirect and loadbalancer
- External IP exception (76.156.139.101) only applies to homepage
- All other services: local network = no auth, everything else = auth required

### Task T13: Homepage cleanup: Infrastructure category + icons
**Priority**: P1
**Dependencies**: None
**Effort**: Low
**Project**: home-server

**Objective**: Update Infrastructure apps with correct icons and move monitoring tools from Trading to Infrastructure.

**Plan Reference**: `agents/plans-local/homepage-category-consolidation.md`

**Files to modify**:
- `apps/vaultwarden/docker-compose.yml` - icon: `si-1password` → `si-vaultwarden`
- `apps/tailscale/docker-compose.yml` - icon: `si-wireguard` → `si-tailscale`
- `apps/loggifly/docker-compose.yml` - icon: `📊` → `si-logstash`
- `apps/wiki/docker-compose.yml` - icon: `postgresql` → `si-postgresql` (db service)
- `apps/trading-bot/docker-compose.yml` - Move Prometheus, Grafana, Alertmanager to group `Infrastructure`; icon for Alertmanager: `si-bell` → `si-prometheus`
- `apps/n8n/ai-agent-webhook/docker-compose.yml` - group: `Automation` → `Infrastructure`

**Success Criteria**:
- [x] All Infrastructure icons use valid `si-*` Simple Icons
- [x] Monitoring tools (Prometheus, Grafana, Alertmanager) in Infrastructure category
- [x] AI Agent Webhook in Infrastructure category
- [x] No emojis or invalid icon slugs

### Task T14: Homepage cleanup: Media apps category + icons
**Priority**: P1
**Dependencies**: None
**Effort**: Medium
**Project**: home-server

**Objective**: Update all media apps to use `si-*` icons and consolidate into Media Servers / Media Management categories.

**Plan Reference**: `agents/plans-local/homepage-category-consolidation.md`

**Files to modify**:
- `apps/jellyfin/docker-compose.yml` - icon: `si-redhat` → `si-jellyfin`
- `apps/immich/docker-compose.yml` - icon: `si-googlephotos` → `si-immich`
- `apps/soulsync/docker-compose.yml` - icon: `🎵` → `si-navidrome`
- `apps/media-download/docker-compose.yml` - Update all icons:
  - NZBHydra2: `nzbhydra2.svg` → `si-nzbhydra2`
  - Jackett: `jackett.svg` → `si-jackett`
  - Prowlarr: `prowlarr.svg` → `si-prowlarr`
  - Sonarr: `sonarr.svg` → `si-sonarr`
  - Radarr: `radarr.svg` → `si-radarr`
  - Lidarr: `lidarr.svg` → `si-lidarr`
  - Bazarr: `bazarr.svg` → `si-bazarr`
  - Overseerr: `overseerr.svg` → `si-overseerr`
  - LazyLibrarian: `readarr.svg` → `si-readarr`
  - Calibre: `calibre.svg` → `si-calibre`
  - Calibre-Web: `calibre.svg` → `si-calibre`
  - SABnzbd: `sabnzbd.svg` → `si-sabnzbd`

**Success Criteria**:
- [ ] All media apps use valid `si-*` Simple Icons
- [ ] No local SVG references (*.svg)
- [ ] No emojis

### Task T15: Homepage cleanup: Productivity category + icons
**Priority**: P1
**Dependencies**: None
**Effort**: Low
**Project**: home-server

**Objective**: Consolidate all productivity apps under single "Productivity" category and fix icons.

**Plan Reference**: `agents/plans-local/homepage-category-consolidation.md`

**Files to modify**:
- `apps/planka/docker-compose.yml` - icon: `si-todoist` → `si-planka`; group stays `Productivity & Organization` → `Productivity`
- `apps/mealie/docker-compose.yml` - icon: `si-aldinord` → `si-mealie`; group: → `Productivity`
- `apps/firefly-iii/docker-compose.yml` - icon: `si-firefly` → `si-fireflyiii`; group: → `Productivity`
- `apps/lubelog/docker-compose.yml` - icon: `si-car` → `si-lubelog`; group: → `Productivity`
- `apps/beaverhabits/docker-compose.yml` - icon: `🐻` → `si-habitica`; group: `Productivity` (already correct)
- `apps/open-archiver/docker-compose.yml` - icon: `si-archive` → `si-internetarchive`; group: → `Productivity`
- `apps/wiki/docker-compose.yml` - icon: `si-wikijs` → `si-wikidotjs` (wiki service); group: → `Productivity`
- `apps/mazanoke/docker-compose.yml` - icon: `🖼️` → `si-unsplash`; group: `Tools & Utilities` → `Productivity`
- `apps/paperless-ngx/docker-compose.yml` - group: → `Productivity`
- `apps/excalidraw/docker-compose.yml` - group: → `Productivity`
- `apps/monica/docker-compose.yml` - group: → `Productivity`
- `apps/habitica/docker-compose.yml` - group: → `Productivity`

**Success Criteria**:
- [x] All Productivity apps use valid `si-*` Simple Icons
- [x] All apps in single "Productivity" category (not "Productivity & Organization")
- [x] No emojis or invalid icon slugs

### Task T16: Homepage cleanup: Social/News + Gaming + Trading icons
**Priority**: P1
**Dependencies**: None
**Effort**: Low
**Project**: home-server

**Objective**: Update Social & News category and fix remaining icons in Gaming/Trading.

**Plan Reference**: `agents/plans-local/homepage-category-consolidation.md`

**Files to modify**:
- `apps/campfire/docker-compose.yml` - icon: `si-campfire` → `si-basecamp`; group: `Communication & Social` → `Social & News`
- `apps/freshRSS/docker-compose.yml` - icon: `si-rss` → `si-freshrss`; group: → `Social & News`
- `apps/newsblur/docker-compose.yml` - group: `Communication & Social` → `Social & News`
- `apps/ghost/docker-compose.yml` - group: → `Social & News`
- `apps/libreddit/docker-compose.yml` - group: → `Social & News`
- `apps/mattermost/docker-compose.yml` - group: `Productivity & Organization` → `Social & News`
- `apps/maptapdat/docker-compose.yml` - icon: `🗺️` → `si-openstreetmap`
- `apps/ollama-docker/docker-compose.yml` - icon: `si-openai` → `si-ollama`
- `apps/open-health/docker-compose.yml` - icon: `si-heart` → `si-openai`

**Success Criteria**:
- [ ] All Social & News apps in correct category
- [ ] All Gaming icons use valid `si-*` Simple Icons
- [ ] No emojis or invalid icon slugs
- [ ] All `si-*` slugs verified against Simple Icons

---

## Priority Order

**Immediate (This Session):**
1. T1 - Metrics consolidation
2. T2 - Strategy.py cleanup

**Next Session:**
3. T6 - WebSocket producers
4. T9 - IBKR testing
5. T10 - Execution pipeline

**Later:**
- T3, T4, T5 - Style cleanup
- T7, T8 - UI and tests
- T11 - Provider refactor
- T12 - Traefik config standardization (home-server infrastructure)
- T13, T14, T15, T16 - Homepage cleanup (categories + icons)

---

## Completed Tasks

| ID | Task | Project | Completed | Notes |
|----|------|---------|-----------|-------|
| - | Agents system cleanup | agents | 2024-11-27 | Simplified from 600MB to 272KB |

