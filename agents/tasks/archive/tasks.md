# Tasks

Task tracking for Home Server.

**Status**: Active development
**Last Updated**: 2025-12-07

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
| T14 | Homepage cleanup: Media apps category + icons | [COMPLETE] | P1 |
| T15 | Homepage cleanup: Productivity category + icons | [COMPLETE] | P1 |
| T16 | Homepage cleanup: Social/News + Gaming + Trading icons | [COMPLETE] | P1 |
| T17 | Media-Download Directory Cleanup | [AVAILABLE] | P2 |
| T18 | Setup SMART monitoring on server | [AVAILABLE] | P1 |
| T19 | Test drive health check script | [AVAILABLE] | P1 |
| T20 | Configure automated drive health monitoring/alerts | [AVAILABLE] | P2 |
| T21 | Review current drive health status | [AVAILABLE] | P1 |
| T22 | Migrate ZFS from RAID-Z1 to RAID-Z2 (8 drives) | [AVAILABLE] | P0 |
| T23 | Setup new 6-drive RAID-Z2 pool (two-pool strategy) | [AVAILABLE] | P0 |
| T24 | Purchase ASUS RT-AX86U Pro + RT-AX58U routers | [AVAILABLE] | P1 |
| T25 | Set up ASUS routers with AdGuard DNS | [BLOCKED] | P1 |
| T26 | Update infrastructure docs after router migration | [BLOCKED] | P2 |
| T27 | Install Beads CLI | [COMPLETE] | P1 |
| T28 | Initialize Beads in repository | [COMPLETE] | P1 |
| T29 | Migrate P0 tasks to Beads | [COMPLETE] | P1 |
| T30 | Migrate P1 tasks to Beads | [COMPLETE] | P1 |
| T31 | Migrate P2 tasks to Beads | [COMPLETE] | P1 |
| T32 | Add task dependencies in Beads | [COMPLETE] | P1 |
| T33 | Mark completed tasks in Beads | [COMPLETE] | P1 |
| T34 | Create beads-task-management tool | [COMPLETE] | P1 |
| T35 | Create task-manager-agent persona | [COMPLETE] | P1 |
| T36 | Update AGENTS.md for Beads workflow | [AVAILABLE] | P1 |
| T37 | Update existing agent personas for Beads | [AVAILABLE] | P1 |
| T38 | Update agents/tasks/README.md for Beads | [AVAILABLE] | P1 |
| T39 | Archive old task system and verify migration | [AVAILABLE] | P1 |

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
- [x] All media apps use valid `si-*` Simple Icons
- [x] No local SVG references (*.svg)
- [x] No emojis

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
- [x] All Social & News apps in correct category
- [x] All Gaming icons use valid `si-*` Simple Icons
- [x] No emojis or invalid icon slugs
- [x] All `si-*` slugs verified against Simple Icons

### Task T17: Media-Download Directory Cleanup
**Priority**: P2
**Dependencies**: None
**Effort**: Medium
**Project**: home-server

**Objective**: Clean up the `apps/media-download/` directory by removing stale files and outdated plans that are no longer needed.

**Scope**:
- Identify and remove outdated plan files, temporary files, or obsolete configurations
- Review for any unused scripts, configs, or documentation
- Ensure cleanup doesn't break active services

**Files to review/modify**:
- All files in `apps/media-download/` directory
- Focus on identifying stale/outdated content

**Success Criteria**:
- [ ] Directory size reduced by removing unnecessary files
- [ ] No active services or configurations broken
- [ ] Outdated plans and stale files removed
- [ ] Directory remains functional for media management stack

### Task T18: Setup SMART monitoring on server
**Priority**: P1
**Dependencies**: None
**Effort**: Low
**Project**: infrastructure

**Objective**: Install and configure SMART monitoring tools on the server to enable drive health monitoring

**Files to modify**:
- None (server-side setup)

**Scripts to run**:
- `scripts/setup-smart-monitoring.sh` (on server)

**Success Criteria**:
- [ ] smartmontools installed
- [ ] SMART enabled on all drives
- [ ] `check-drive-health.sh` script executable
- [ ] Daily cron job configured (runs at 3 AM)
- [ ] Logs to `/var/log/drive-health.log`

**Commands**:
```bash
# SSH to server
ssh -p 4242 unarmedpuppy@192.168.86.47

# Run setup script
bash ~/server/scripts/setup-smart-monitoring.sh
```

### Task T19: Test drive health check script
**Priority**: P1
**Dependencies**: T18
**Effort**: Low
**Project**: infrastructure

**Objective**: Verify the drive health check script works correctly and provides useful output

**Scripts to test**:
- `scripts/check-drive-health.sh`

**Success Criteria**:
- [ ] Script runs without errors
- [ ] All drives in ZFS pool are checked
- [ ] SMART status reported for each drive
- [ ] ZFS pool status displayed
- [ ] Temperature and critical attributes shown
- [ ] Output is readable and actionable

**Commands**:
```bash
# On server
bash ~/server/scripts/check-drive-health.sh

# Or from local
ssh -p 4242 unarmedpuppy@192.168.86.47 "bash ~/server/scripts/check-drive-health.sh"
```

### Task T20: Configure automated drive health monitoring/alerts
**Priority**: P2
**Dependencies**: T18, T19
**Effort**: Medium
**Project**: infrastructure

**Objective**: Set up automated alerts for drive health issues (email, webhook, or integration with existing monitoring)

**Options to implement**:
1. Email alerts on drive failures
2. Integration with Grafana alerts
3. Webhook notifications
4. Homepage status display

**Files to create/modify**:
- `scripts/drive-health-alert.sh` (optional email alert script)
- Grafana alert rules (if using Grafana)
- Homepage integration (if desired)

**Success Criteria**:
- [ ] Alerts configured for critical drive failures
- [ ] Alerts tested and working
- [ ] Documentation updated with alert setup
- [ ] Alert recipients/endpoints configured

**Notes**:
- Can use existing email setup or integrate with Grafana
- Consider adding to Homepage for visual status
- Should alert on: SMART health failures, ZFS pool degradation, critical SMART attributes

### Task T21: Review current drive health status
**Priority**: P1
**Dependencies**: T18
**Effort**: Low
**Project**: infrastructure

**Objective**: Run initial drive health check and document current status of all drives in ZFS pool

**Scripts to use**:
- `scripts/check-drive-health.sh`

**Success Criteria**:
- [ ] All 4 ZFS pool drives checked (sda, sdb, sdc, sdd)
- [ ] SMART status documented for each drive
- [ ] ZFS pool status reviewed
- [ ] Any issues or warnings documented
- [ ] Baseline established for future monitoring

**Commands**:
```bash
# Check all drives
bash ~/server/scripts/check-drive-health.sh

# Check ZFS pool specifically
sudo zpool status jenquist-cloud

# Check individual drives
for disk in sda sdb sdc sdd; do
    echo "=== /dev/$disk ==="
    sudo smartctl -H /dev/$disk
    sudo smartctl -A /dev/$disk | grep -E "Reallocated|Pending|Uncorrectable|Temperature"
done
```

**Documentation**:
- Record findings in a note or wiki page
- Document any drives that need attention
- Establish baseline metrics for future comparison

### Task T22: Migrate ZFS from RAID-Z1 to RAID-Z2 (8 drives)
**Priority**: P0
**Dependencies**: T18, T19, T21 (should verify drive health first)
**Effort**: High
**Project**: infrastructure

**Objective**: Migrate from 4-drive RAID-Z1 pool to 8-drive RAID-Z2 pool for better redundancy and capacity

**Prerequisites**:
- 8 new CMR drives purchased (recommended: Seagate IronWolf 8TB)
- Full backup completed and verified
- Maintenance window scheduled (12-24 hours)
- All services using ZFS stopped

**Documentation**:
- `agents/plans/ZFS_RAIDZ1_TO_RAIDZ2_MIGRATION.md` - Complete migration guide

**Process Overview**:
1. **Backup everything** (critical!)
2. **Create new RAID-Z2 pool** with 8 new drives (temporary name)
3. **Copy data** from old pool to new pool (rsync recommended)
4. **Verify data integrity** (file counts, spot checks)
5. **Switch to new pool** (export old, import new with original name)
6. **Test services** (Jellyfin, etc.)
7. **Keep old pool for 1+ week** before destroying
8. **Remove old drives** after verification period

**Key Commands**:
```bash
# Create new pool
sudo zpool create jenquist-cloud-new raidz2 /dev/sde /dev/sdf /dev/sdg /dev/sdh /dev/sdi /dev/sdj /dev/sdk /dev/sdl

# Copy data
sudo rsync -avh --progress /jenquist-cloud/archive/ /jenquist-cloud-new/archive/

# Switch pools
sudo zpool export jenquist-cloud
sudo zpool export jenquist-cloud-new
sudo zpool import jenquist-cloud-new jenquist-cloud
```

**Success Criteria**:
- [ ] Full backup completed and verified
- [ ] New RAID-Z2 pool created with 8 drives
- [ ] All data copied and verified
- [ ] Services tested and working
- [ ] Pool health verified (no errors)
- [ ] Old pool kept for 1+ week as backup
- [ ] Documentation updated

**Estimated Time**: 12-24 hours (depends on data size)

**Risk Level**: High - requires careful execution and verification

### Task T23: Setup new 6-drive RAID-Z2 pool (two-pool strategy)
**Priority**: P0
**Dependencies**: None (can be done independently)
**Effort**: Medium
**Project**: infrastructure

**Objective**: Create a new 6-drive RAID-Z2 pool alongside existing 4-drive pool for increased capacity and better redundancy

**Strategy**: Two-pool approach - keep existing pool intact, add new pool with better redundancy

**Prerequisites**:
- 6x 8TB CMR drives purchased (recommended: Seagate IronWolf 8TB)
- 6 open drive bays available (total 10 bays used)

**Documentation**:
- `agents/plans/ZFS_TWO_POOL_STRATEGY.md` - Complete two-pool strategy guide

**Process Overview**:
1. **Purchase 6x 8TB IronWolf drives**
2. **Power down server and install drives**
3. **Create new RAID-Z2 pool** with 6 drives
4. **Create filesystem and configure mount point**
5. **Update services** to use new pool (or both pools)
6. **Start using new pool** for new content
7. **Plan gradual migration** from old pool (optional)

**Key Commands**:
```bash
# Create new pool
sudo zpool create jenquist-cloud-new raidz2 /dev/sde /dev/sdf /dev/sdg /dev/sdh /dev/sdi /dev/sdj

# Create filesystem
sudo zfs create jenquist-cloud-new/archive
sudo zfs set mountpoint=/jenquist-cloud-new jenquist-cloud-new/archive
```

**Success Criteria**:
- [ ] 6 new drives installed
- [ ] New RAID-Z2 pool created
- [ ] Filesystem created and mounted
- [ ] Services configured to use new pool
- [ ] New pool tested and working
- [ ] Total capacity: 56 TB usable (24 + 32)

**Capacity**:
- **New Pool**: ~32 TB usable (6x 8TB RAID-Z2)
- **Existing Pool**: ~24 TB usable (4x 8TB RAID-Z1)
- **Total**: ~56 TB usable

**Advantages**:
- Zero downtime (old pool keeps running)
- Lower risk (no migration needed)
- Lower cost ($900-1,080 vs $1,200-1,440)
- Better redundancy on new pool (RAID-Z2)
- Immediate capacity increase
- Flexible migration options

**Estimated Time**: 2-4 hours (mostly physical installation)

**Risk Level**: Low - old pool stays intact

### Task T24: Purchase ASUS RT-AX86U Pro + RT-AX58U routers
**Priority**: P1
**Dependencies**: None
**Effort**: Low
**Project**: infrastructure

**Objective**: Purchase router equipment to replace Google Home mesh routers for better network control (DNS/DHCP)

**Equipment to Purchase**:
- **ASUS RT-AX86U Pro** (~$250) - Main router
  - Amazon: https://www.amazon.com/ASUS-RT-AX86U-Pro-Extendable-Rangeboost/dp/B0BTGKSPYG
  - Location: Lower floor, far corner (with server)
- **ASUS RT-AX58U** (~$100) - Mesh node
  - Amazon: https://www.amazon.com/ASUS-AX3000-WiFi-Router-RT-AX58U/dp/B08151SRDD
  - Location: Upper floor, middle (where Google extension is now)

**Total Budget**: ~$350

**Why ASUS**:
- AiMesh works well with wireless backhaul (no ethernet upstairs)
- Full DNS/DHCP control via web UI
- Easy setup, no controller needed
- Good coverage for ~2800 sq ft with 2 units

**Success Criteria**:
- [ ] RT-AX86U Pro purchased
- [ ] RT-AX58U purchased
- [ ] Equipment received and ready for setup

### Task T25: Set up ASUS routers with AdGuard DNS
**Priority**: P1
**Dependencies**: T24
**Effort**: Medium
**Project**: infrastructure

**Objective**: Replace Google Home mesh with ASUS routers and configure DNS to point to AdGuard

**Current Setup**:
- Google Home mesh router (main) + extension
- House: ~2,816 sq ft, two floors
- Server location: Lower floor, far corner
- No ethernet upstairs - wireless mesh backhaul required

**Migration Steps**:
1. Set up RT-AX86U Pro as main router
   - Use same SSID and password as current network
   - Configure WAN connection
2. Configure DNS to point to AdGuard
   - LAN → DHCP Server → DNS Server: `192.168.86.47`
3. Add RT-AX58U as AiMesh node
   - Place upper floor, middle
   - Uses wireless backhaul
4. Swap routers
   - Disconnect Google router
   - Connect ASUS router to modem
   - Devices should reconnect automatically (same SSID/password)
5. Verify all devices use AdGuard DNS
   - Check AdGuard Query Log for individual device IPs
   - No more `192.168.86.1` (router) as client
6. Remove Google mesh routers

**Success Criteria**:
- [ ] RT-AX86U Pro configured as main router
- [ ] DNS set to `192.168.86.47` (AdGuard)
- [ ] RT-AX58U added as AiMesh node
- [ ] All devices connected and working
- [ ] AdGuard Query Log shows individual device IPs
- [ ] Good WiFi coverage throughout house
- [ ] Google mesh routers removed

**Rollback Plan**:
If issues occur, reconnect Google router - it should work immediately with existing settings.

### Task T26: Update infrastructure docs after router migration
**Priority**: P2
**Dependencies**: T25
**Effort**: Low
**Project**: infrastructure

**Objective**: Update all infrastructure documentation to reflect new ASUS router setup after migration is complete

**Files to Update**:
- `agents/personas/infrastructure-agent.md`
  - Remove "Planned Router Upgrade" section (completed)
  - Update "Router" field from Google Home to ASUS RT-AX86U Pro
  - Update network details with new router info
  - Remove Google Home limitations section
  - Document ASUS router DNS/DHCP configuration location
- `agents/reference/setup/GOOGLE_HOME_DNS_SETUP.md`
  - Archive or delete (no longer relevant)
  - Or rename to general DNS setup guide
- `README.md`
  - Update network configuration section if applicable

**Documentation to Add**:
- ASUS router admin URL (usually `http://192.168.86.1` or `router.asus.com`)
- AiMesh node management
- DNS/DHCP settings location in ASUS UI
- Any custom firewall rules configured

**Success Criteria**:
- [ ] infrastructure-agent.md reflects current ASUS setup
- [ ] No references to Google Home router in active docs
- [ ] DNS/DHCP configuration documented
- [ ] AiMesh setup documented
- [ ] All "planned" language removed (migration complete)

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
- T18, T19, T21 - Drive health monitoring setup (infrastructure)
- T20 - Drive health alerts (infrastructure)
- T27-T39 - Beads migration (agents infrastructure)

---

## Beads Migration Tasks

**Plan Reference**: `agents/plans/beads-migration-plan.md`

Migrate from markdown-based task system to [Beads](https://github.com/steveyegge/beads) distributed issue tracker.

### Task T27: Install Beads CLI
**Priority**: P1
**Dependencies**: None
**Effort**: Low
**Project**: agents

**Objective**: Install Beads CLI tool locally

**Commands**:
```bash
# Option A: Quick install (recommended)
curl -fsSL https://raw.githubusercontent.com/steveyegge/beads/main/scripts/install.sh | bash

# Option B: npm
npm install -g @beads/bd

# Option C: Homebrew
brew tap steveyegge/beads && brew install bd
```

**Success Criteria**:
- [ ] `bd --version` returns version number
- [ ] `bd help` displays available commands
- [ ] CLI accessible from terminal

---

### Task T28: Initialize Beads in repository
**Priority**: P1
**Dependencies**: T27
**Effort**: Low
**Project**: agents

**Objective**: Initialize Beads database in home-server repository

**Commands**:
```bash
cd /Users/joshuajenquist/repos/personal/home-server
bd init
```

**What gets created**:
```
.beads/
├── beads.jsonl      # Source of truth (committed to git)
├── beads.db         # Local SQLite cache (gitignored)
├── deletions.jsonl  # Deletion manifest
├── config.yaml      # Configuration
└── metadata.json    # Schema version
```

**Prompts to answer**:
- Accept git hook installation: **Yes** (recommended)
- Accept merge driver configuration: **Yes** (recommended)

**Success Criteria**:
- [ ] `.beads/` directory created at repo root
- [ ] `bd doctor` reports healthy status
- [ ] `bd info` shows database details
- [ ] `.beads/beads.jsonl` exists and is empty or has header
- [ ] `.beads/beads.db` exists (SQLite cache)

**Verification**:
```bash
bd doctor
bd info
ls -la .beads/
```

---

### Task T29: Migrate P0 tasks to Beads
**Priority**: P1
**Dependencies**: T28
**Effort**: Medium
**Project**: agents

**Objective**: Create all P0 (critical) tasks in Beads

**Tasks to migrate** (6 tasks):

| Old ID | Title | Labels |
|--------|-------|--------|
| T1 | Consolidate metrics system (8 files → 3) | trading-bot,refactor |
| T6 | WebSocket data producer integration | trading-bot,websocket |
| T9 | IBKR integration testing | trading-bot,integration |
| T10 | Strategy-to-execution pipeline | trading-bot,core |
| T22 | Migrate ZFS from RAID-Z1 to RAID-Z2 | infrastructure,storage |
| T23 | Setup new 6-drive RAID-Z2 pool | infrastructure,storage |

**Commands**:
```bash
# T1
bd create "Consolidate metrics system (8 files → 3)" -t task -p 0 -l "trading-bot,refactor" \
  -d "Reduce metrics system from 8 files to 3. Biggest code quality win. See IMPLEMENTATION_ROADMAP.md"

# T6
bd create "WebSocket data producer integration" -t task -p 0 -l "trading-bot,websocket" \
  -d "Connect data to WebSocket streams"

# T9
bd create "IBKR integration testing" -t task -p 0 -l "trading-bot,integration" \
  -d "Paper trading validation for IBKR integration"

# T10
bd create "Strategy-to-execution pipeline" -t task -p 0 -l "trading-bot,core" \
  -d "Signal → order with safety checks"

# T22
bd create "Migrate ZFS from RAID-Z1 to RAID-Z2 (8 drives)" -t epic -p 0 -l "infrastructure,storage" \
  -d "Migrate from 4-drive RAID-Z1 pool to 8-drive RAID-Z2 for better redundancy. See agents/plans/ZFS_RAIDZ1_TO_RAIDZ2_MIGRATION.md"

# T23
bd create "Setup new 6-drive RAID-Z2 pool (two-pool strategy)" -t epic -p 0 -l "infrastructure,storage" \
  -d "Create new 6-drive RAID-Z2 pool alongside existing 4-drive pool. See agents/plans/ZFS_TWO_POOL_STRATEGY.md"
```

**Success Criteria**:
- [ ] 6 P0 tasks created in Beads
- [ ] `bd list --priority 0` shows all 6 tasks
- [ ] Each task has correct labels
- [ ] Each task has description

**Verification**:
```bash
bd list --priority 0
bd list --priority 0 --json | jq length  # Should be 6
```

---

### Task T30: Migrate P1 tasks to Beads
**Priority**: P1
**Dependencies**: T28
**Effort**: Medium
**Project**: agents

**Objective**: Create all P1 (high priority) tasks in Beads

**Tasks to migrate** (11 tasks):

| Old ID | Title | Labels |
|--------|-------|--------|
| T2 | Remove backward compat duplication in strategy.py | trading-bot,cleanup |
| T5 | Standardize error handling | trading-bot,quality |
| T7 | UI WebSocket integration | trading-bot,ui |
| T8 | WebSocket testing | trading-bot,testing |
| T11 | Sentiment provider base class | trading-bot,refactor |
| T12 | Standardize Traefik config | infrastructure,traefik |
| T18 | Setup SMART monitoring on server | infrastructure,monitoring |
| T19 | Test drive health check script | infrastructure,monitoring |
| T21 | Review current drive health status | infrastructure,monitoring |
| T24 | Purchase ASUS routers | infrastructure,network |
| T25 | Set up ASUS routers with AdGuard DNS | infrastructure,network |

**Commands**:
```bash
# T2
bd create "Remove backward compat duplication in strategy.py" -t task -p 1 -l "trading-bot,cleanup" \
  -d "Remove duplicate enums in src/core/strategy.py"

# T5
bd create "Standardize error handling" -t task -p 1 -l "trading-bot,quality" \
  -d "Replace broad except Exception with specific exception handling"

# T7
bd create "UI WebSocket integration" -t task -p 1 -l "trading-bot,ui" \
  -d "Dashboard real-time updates via WebSocket"

# T8
bd create "WebSocket testing" -t task -p 1 -l "trading-bot,testing" \
  -d "Add WebSocket tests (no WS tests currently)"

# T11
bd create "Sentiment provider base class" -t task -p 1 -l "trading-bot,refactor" \
  -d "Reduce boilerplate in 13 providers"

# T12
bd create "Standardize Traefik config: local DNS no-auth, external auth" -t epic -p 1 -l "infrastructure,traefik" \
  -d "Apply consistent Traefik configuration pattern across all apps. See T12 details in tasks.md"

# T18
bd create "Setup SMART monitoring on server" -t task -p 1 -l "infrastructure,monitoring" \
  -d "Install and configure SMART monitoring tools. Run scripts/setup-smart-monitoring.sh"

# T19
bd create "Test drive health check script" -t task -p 1 -l "infrastructure,monitoring" \
  -d "Verify scripts/check-drive-health.sh works correctly"

# T21
bd create "Review current drive health status" -t task -p 1 -l "infrastructure,monitoring" \
  -d "Run initial drive health check and document status of all 4 ZFS pool drives"

# T24
bd create "Purchase ASUS RT-AX86U Pro + RT-AX58U routers" -t task -p 1 -l "infrastructure,network" \
  -d "Purchase router equipment (~$350). RT-AX86U Pro (~$250) + RT-AX58U (~$100)"

# T25
bd create "Set up ASUS routers with AdGuard DNS" -t task -p 1 -l "infrastructure,network" \
  -d "Replace Google Home mesh with ASUS routers and configure DNS to point to AdGuard"
```

**Success Criteria**:
- [ ] 11 P1 tasks created in Beads
- [ ] `bd list --priority 1` shows all 11 tasks
- [ ] Each task has correct labels

**Verification**:
```bash
bd list --priority 1
bd list --priority 1 --json | jq length  # Should be 11
```

---

### Task T31: Migrate P2 tasks to Beads
**Priority**: P1
**Dependencies**: T28
**Effort**: Low
**Project**: agents

**Objective**: Create all P2 (medium priority) tasks in Beads

**Tasks to migrate** (5 tasks):

| Old ID | Title | Labels |
|--------|-------|--------|
| T3 | Standardize import patterns | trading-bot,cleanup |
| T4 | Add missing type hints | trading-bot,typing |
| T17 | Media-Download Directory Cleanup | media,cleanup |
| T20 | Configure automated drive health monitoring/alerts | infrastructure,monitoring |
| T26 | Update infrastructure docs after router migration | infrastructure,docs |

**Commands**:
```bash
# T3
bd create "Standardize import patterns" -t task -p 2 -l "trading-bot,cleanup" \
  -d "Standardize import patterns, focus on sentiment providers"

# T4
bd create "Add missing type hints" -t task -p 2 -l "trading-bot,typing" \
  -d "Add missing type hints to range_bound.py and sentiment providers"

# T17
bd create "Media-Download Directory Cleanup" -t task -p 2 -l "media,cleanup" \
  -d "Clean up apps/media-download/ by removing stale files and outdated plans"

# T20
bd create "Configure automated drive health monitoring/alerts" -t task -p 2 -l "infrastructure,monitoring" \
  -d "Set up automated alerts for drive health issues (email, webhook, or Grafana integration)"

# T26
bd create "Update infrastructure docs after router migration" -t task -p 2 -l "infrastructure,docs" \
  -d "Update all infrastructure documentation to reflect new ASUS router setup"
```

**Success Criteria**:
- [ ] 5 P2 tasks created in Beads
- [ ] `bd list --priority 2` shows all 5 tasks
- [ ] Each task has correct labels

**Verification**:
```bash
bd list --priority 2
bd list --priority 2 --json | jq length  # Should be 5
```

---

### Task T32: Add task dependencies in Beads
**Priority**: P1
**Dependencies**: T29, T30, T31
**Effort**: Medium
**Project**: agents

**Objective**: Create all dependency relationships between tasks

**Dependencies to create**:

| Dependent Task | Blocked By | Relationship |
|----------------|------------|--------------|
| T7 (UI WebSocket) | T6 (WebSocket producers) | blocks |
| T8 (WebSocket testing) | T6, T7 | blocks |
| T19 (Test drive health) | T18 (Setup SMART) | blocks |
| T20 (Drive alerts) | T18, T19 | blocks |
| T21 (Review drive health) | T18 | blocks |
| T22 (ZFS migration) | T18, T19, T21 | blocks |
| T25 (Router setup) | T24 (Purchase routers) | blocks |
| T26 (Docs update) | T25 | blocks |

**Commands** (use actual Beads IDs after tasks are created):
```bash
# Get task IDs first
bd list --json | jq -r '.issues[] | "\(.id) \(.title)"'

# WebSocket chain
bd dep add <t7-id> <t6-id> --type blocks
bd dep add <t8-id> <t6-id> --type blocks
bd dep add <t8-id> <t7-id> --type blocks

# Drive monitoring chain
bd dep add <t19-id> <t18-id> --type blocks
bd dep add <t20-id> <t18-id> --type blocks
bd dep add <t20-id> <t19-id> --type blocks
bd dep add <t21-id> <t18-id> --type blocks
bd dep add <t22-id> <t18-id> --type blocks
bd dep add <t22-id> <t19-id> --type blocks
bd dep add <t22-id> <t21-id> --type blocks

# Router chain
bd dep add <t25-id> <t24-id> --type blocks
bd dep add <t26-id> <t25-id> --type blocks
```

**Success Criteria**:
- [ ] All 12 dependency relationships created
- [ ] `bd dep cycles` returns no cycles
- [ ] `bd blocked` shows correctly blocked tasks
- [ ] `bd ready` excludes blocked tasks

**Verification**:
```bash
bd dep cycles          # Should show no cycles
bd blocked             # Should show T7, T8, T19, T20, T21, T22, T25, T26
bd ready               # Should NOT include blocked tasks
bd dep tree <t22-id>   # Should show T18, T19, T21 as blockers
```

---

### Task T33: Mark completed tasks in Beads
**Priority**: P1
**Dependencies**: T29, T30, T31
**Effort**: Low
**Project**: agents

**Objective**: Close all tasks marked [COMPLETE] in old system

**Tasks to close** (4 tasks):

| Old ID | Title | Reason |
|--------|-------|--------|
| T13 | Homepage cleanup: Infrastructure category + icons | Icons updated to si-* format |
| T14 | Homepage cleanup: Media apps category + icons | Media icons updated |
| T15 | Homepage cleanup: Productivity category + icons | Productivity category consolidated |
| T16 | Homepage cleanup: Social/News + Gaming + Trading icons | Social/News and Gaming icons fixed |

**Note**: These tasks need to be created first, then immediately closed.

**Commands**:
```bash
# Create and immediately close T13
bd create "Homepage cleanup: Infrastructure category + icons" -t task -p 1 -l "infrastructure,homepage"
bd close <id> --reason "Icons updated to si-* format"

# Create and immediately close T14
bd create "Homepage cleanup: Media apps category + icons" -t task -p 1 -l "media,homepage"
bd close <id> --reason "Media icons updated"

# Create and immediately close T15
bd create "Homepage cleanup: Productivity category + icons" -t task -p 1 -l "productivity,homepage"
bd close <id> --reason "Productivity category consolidated"

# Create and immediately close T16
bd create "Homepage cleanup: Social/News + Gaming + Trading icons" -t task -p 1 -l "social,homepage"
bd close <id> --reason "Social/News and Gaming icons fixed"
```

**Success Criteria**:
- [ ] 4 completed tasks exist in Beads
- [ ] All 4 have status "closed"
- [ ] Each has completion reason

**Verification**:
```bash
bd list --status closed
bd list --status closed --json | jq length  # Should be 4
```

---

### Task T34: Create beads-task-management tool
**Priority**: P1
**Dependencies**: T32, T33
**Effort**: Medium
**Project**: agents

**Objective**: Create a comprehensive tool in `agents/tools/` for Beads task management

**File to create**: `agents/tools/beads-task-management/SKILL.md`

**Content structure**:
```yaml
---
name: beads-task-management
description: Manage tasks with Beads distributed issue tracker
when_to_use: Creating, updating, querying tasks; finding ready work; managing dependencies
---
```

**Sections to include**:

1. **Overview** - What Beads is and why we use it
2. **Finding Work** - `bd ready`, filtering by label/priority
3. **Creating Tasks** - `bd create` with types, priorities, labels
4. **Claiming Tasks** - `bd update --status in_progress` + git workflow
5. **Managing Dependencies** - `bd dep add/remove/tree`
6. **Completing Tasks** - `bd close --reason`
7. **Querying Tasks** - `bd list` with filters, `bd show`
8. **Git Sync** - How auto-sync works, manual `bd sync`
9. **Common Workflows** - Claim → Work → Complete examples

**Commands to document**:
```bash
# Finding work
bd ready                          # Unblocked tasks
bd ready --json                   # For programmatic use
bd ready --priority 0             # Critical tasks only
bd list --label trading-bot       # Filter by project

# Creating tasks
bd create "Title" -t task -p 1 -l "label1,label2" -d "Description"

# Claiming
bd update <id> --status in_progress
git add .beads/ && git commit -m "claim: <id>" && git push

# Dependencies
bd dep add <child> <parent> --type blocks
bd dep tree <id>
bd dep cycles

# Completing
bd close <id> --reason "Implemented in PR #X"
```

**Success Criteria**:
- [ ] `agents/tools/beads-task-management/` directory created
- [ ] `SKILL.md` has YAML frontmatter with name, description, when_to_use
- [ ] All common Beads commands documented
- [ ] Claim → Work → Complete workflow documented
- [ ] `--json` examples for agent programmatic access
- [ ] Tool added to AGENTS.md tool table

**Verification**:
```bash
ls agents/tools/beads-task-management/SKILL.md
grep "beads-task-management" AGENTS.md
```

---

### Task T35: Create task-manager-agent persona
**Priority**: P1
**Dependencies**: T34
**Effort**: Medium
**Project**: agents

**Objective**: Create a dedicated agent persona for task coordination and management using Beads

**File to create**: `agents/personas/task-manager-agent.md`

**Persona content**:

```markdown
---
name: task-manager-agent
description: Task coordination and management specialist using Beads
---

You are the Task Manager specialist. Your expertise includes:

- Task discovery and prioritization using Beads
- Multi-agent task coordination and claiming protocol
- Dependency management and blocking issue resolution
- Task lifecycle management (create → claim → work → complete)
- Cross-session continuity and handoff

## Key Files

- `.beads/` - Beads database (source of truth)
- `agents/tools/beads-task-management/SKILL.md` - Beads workflow guide
- `agents/tasks/README.md` - Task coordination reference

## Task Management Workflow

### Session Start
```bash
# 1. Sync latest tasks
git pull origin main

# 2. Find ready work (no blockers)
bd ready

# 3. Check in-progress work
bd list --status in_progress

# 4. Review blocked items
bd blocked
```

### Claiming Tasks
```bash
# Find and claim
bd ready --priority 0           # Critical tasks first
bd update <id> --status in_progress

# Commit claim
git add .beads/
git commit -m "claim: <id> - Description"
git push origin main

# Create feature branch
git checkout -b feature/<id>-description
```

### Creating Tasks
```bash
# Standard task
bd create "Task title" -t task -p 1 -l "project,area" \
  -d "Detailed description"

# With dependencies
bd create "Child task" -t task -p 1
bd dep add <child-id> <parent-id> --type blocks
```

### Completing Tasks
```bash
bd close <id> --reason "Implemented in PR #X"
git add .beads/
git commit -m "close: <id> - Completion note"
```

### Managing Dependencies
```bash
# View dependency tree
bd dep tree <id>

# Check for cycles
bd dep cycles

# Add/remove dependencies
bd dep add <child> <parent> --type blocks
bd dep remove <child> <parent>
```

## Priority Levels

| Priority | Meaning | Action |
|----------|---------|--------|
| 0 | Critical | Work immediately |
| 1 | High | Work soon |
| 2 | Medium | Schedule appropriately |
| 3+ | Low | Backlog |

## Labels

Use labels for filtering and organization:
- **Project**: `trading-bot`, `infrastructure`, `media`, `agents`
- **Area**: `refactor`, `cleanup`, `testing`, `docs`, `monitoring`
- **Component**: `websocket`, `traefik`, `zfs`, `network`

## Multi-Agent Coordination

When multiple agents work concurrently:
1. Always pull before claiming: `git pull origin main`
2. Claim quickly (< 1 minute between claim and push)
3. Use hash-based IDs - no collision risk
4. Check `bd blocked` to avoid duplicate work on dependencies

## Quick Reference

| Action | Command |
|--------|---------|
| Find work | `bd ready` |
| Claim task | `bd update <id> --status in_progress` |
| Complete task | `bd close <id> --reason "note"` |
| Create task | `bd create "title" -t task -p 1 -l "labels"` |
| Add blocker | `bd dep add <child> <parent> --type blocks` |
| View details | `bd show <id>` |
| Check health | `bd doctor` |

See [agents/tools/beads-task-management/](../tools/beads-task-management/) for complete documentation.
```

**Success Criteria**:
- [ ] `agents/personas/task-manager-agent.md` created
- [ ] YAML frontmatter with name and description
- [ ] Complete Beads workflow documented
- [ ] Priority levels and labels documented
- [ ] Multi-agent coordination section included
- [ ] Quick reference table with common commands
- [ ] Persona added to AGENTS.md Agent Personas table

**Verification**:
```bash
ls agents/personas/task-manager-agent.md
grep "task-manager-agent" AGENTS.md
grep "bd ready" agents/personas/task-manager-agent.md
```

---

### Task T36: Update AGENTS.md for Beads workflow
**Priority**: P1
**Dependencies**: T34, T35
**Effort**: Medium
**Project**: agents

**Objective**: Update AGENTS.md to reference Beads as the task management system

**Sections to update**:

1. **Task Claiming (Multi-Agent)** section (~line 184-205)
   - Replace markdown editing instructions with Beads commands
   - Update the claiming protocol to use `bd update --status in_progress`
   - Keep git workflow (branch creation, PR submission)

2. **Tool Documentation** section
   - Add beads-task-management to Utilities table
   - Remove or update references to `agents/tasks/tasks.md`

3. **Always Do** section (~line 71-77)
   - Update "Check `agents/tasks/tasks.md`" to "Check `bd ready` or `bd list`"
   - Keep "Update task status when claiming/completing work"

**Changes to make**:

**Old (Task Claiming Protocol)**:
```bash
# 2. Claim task (edit agents/tasks/tasks.md)
# Change [AVAILABLE] → [CLAIMED by @your-id]
```

**New**:
```bash
# 2. Find and claim task
bd ready                                    # Find unblocked work
bd update <task-id> --status in_progress   # Claim it

# 3. Commit claim
git add .beads/
git commit -m "claim: <task-id> - Description"
git push origin main
```

**Old (Always Do)**:
```markdown
- Check `agents/tasks/tasks.md` at session start for pending/in-progress tasks
```

**New**:
```markdown
- Check `bd ready` at session start for available work
- Use `bd list --status in_progress` to see claimed tasks
```

**Tool table addition**:
```markdown
| [beads-task-management](agents/tools/beads-task-management/) | Manage tasks with Beads | - |
```

**Agent Personas table addition**:
```markdown
| [task-manager-agent](agents/personas/task-manager-agent.md) | Task coordination and management using Beads |
```

**Success Criteria**:
- [ ] Task Claiming Protocol updated with Beads commands
- [ ] "Always Do" section references `bd ready` instead of tasks.md
- [ ] beads-task-management tool added to Utilities table
- [ ] task-manager-agent added to Agent Personas table
- [ ] No direct references to editing tasks.md (except archive mentions)

**Verification**:
```bash
grep -c "bd ready" AGENTS.md           # Should be >= 2
grep -c "bd update" AGENTS.md          # Should be >= 1
grep "beads-task-management" AGENTS.md # Should find tool table entry
grep "task-manager-agent" AGENTS.md    # Should find persona table entry
```

---

### Task T37: Update existing agent personas for Beads
**Priority**: P1
**Dependencies**: T34
**Effort**: Medium
**Project**: agents

**Objective**: Update all agent personas to use Beads for task discovery and management

**Files to update**:

1. **`agents/personas/server-agent.md`**
   - Add "Task Discovery" section
   - Reference `bd ready --label infrastructure`
   - Update any references to tasks.md

2. **`agents/personas/critical-thinking-agent.md`**
   - Add note about Beads if task-related
   - May not need changes if purely analytical

3. **Any other personas in `agents/personas/`**
   - Check each for task-related references
   - Update to use Beads commands

**Content to add to server-agent.md**:
```markdown
### Task Discovery

Use Beads for task management:

```bash
# Find ready work (no blockers)
bd ready

# Filter by infrastructure label
bd ready --label infrastructure
bd list --label infrastructure

# View task details
bd show <task-id>

# Claim a task
bd update <task-id> --status in_progress
git add .beads/ && git commit -m "claim: <task-id>"

# Complete a task
bd close <task-id> --reason "Completed - description"
```

For full Beads documentation, see `agents/tools/beads-task-management/SKILL.md`.
```

**Personas to check**:
```bash
ls agents/personas/
# Currently: server-agent.md, critical-thinking-agent.md, possibly others
```

**Success Criteria**:
- [ ] server-agent.md has Task Discovery section with Beads commands
- [ ] All personas checked for task-related references
- [ ] No personas reference editing tasks.md directly
- [ ] Each updated persona references beads-task-management tool

**Verification**:
```bash
grep -l "bd ready\|bd list\|bd update" agents/personas/*.md
grep -l "tasks.md" agents/personas/*.md  # Should be empty or only archive refs
```

---

### Task T38: Update agents/tasks/README.md for Beads
**Priority**: P1
**Dependencies**: T34
**Effort**: Low
**Project**: agents

**Objective**: Rewrite agents/tasks/README.md to document Beads-based workflow

**Current content** (to replace):
- References editing tasks.md directly
- Manual status legend
- Old claiming protocol

**New content structure**:

```markdown
# Task Coordination

Task tracking using [Beads](https://github.com/steveyegge/beads), a distributed issue tracker for AI agents.

## Quick Reference

| Action | Command |
|--------|---------|
| Find ready work | `bd ready` |
| View all tasks | `bd list` |
| View task details | `bd show <id>` |
| Create task | `bd create "title" -t task -p <priority> -l "labels"` |
| Claim task | `bd update <id> --status in_progress` |
| Complete task | `bd close <id> --reason "note"` |
| View dependencies | `bd dep tree <id>` |
| Check health | `bd doctor` |

## Files

- **`.beads/`** - Beads database (at repo root, git-synced)
- **`archive/`** - Pre-migration task files (historical reference only)

## For AI Agents

Always use `--json` flag for programmatic access:

```bash
bd ready --json | jq '.issues[0].id'
bd list --json | jq '.issues[] | select(.labels | contains(["trading-bot"]))'
bd show <id> --json
```

## Task Claiming Protocol

```bash
# 1. Pull latest
git pull origin main

# 2. Find and claim task
bd ready
bd update <task-id> --status in_progress

# 3. Commit claim
git add .beads/
git commit -m "claim: <task-id> - Description"
git push origin main

# 4. Create feature branch
git checkout -b feature/<task-id>-description

# 5. Work on task...

# 6. Complete and submit PR
bd close <task-id> --reason "Implemented"
git add .beads/
git commit -m "close: <task-id>"
# Submit PR from feature branch
```

## Labels

| Category | Labels |
|----------|--------|
| Project | `trading-bot`, `infrastructure`, `media`, `agents` |
| Area | `refactor`, `cleanup`, `testing`, `docs`, `monitoring` |
| Component | `websocket`, `traefik`, `zfs`, `network` |

## Priority Levels

| Level | Meaning |
|-------|---------|
| 0 | Critical - Must do immediately |
| 1 | High - Should do soon |
| 2 | Medium - Can wait |
| 3 | Low - Backlog |

## Full Documentation

See `agents/tools/beads-task-management/SKILL.md` for complete Beads documentation.
```

**Success Criteria**:
- [ ] README.md completely rewritten for Beads
- [ ] Quick reference table with common commands
- [ ] `--json` examples for agents
- [ ] Claiming protocol uses Beads commands
- [ ] References archive directory for old files
- [ ] Links to beads-task-management tool

**Verification**:
```bash
grep "bd ready" agents/tasks/README.md
grep "\.beads" agents/tasks/README.md
grep -c "tasks.md" agents/tasks/README.md  # Should be 0 or only in archive section
```

---

### Task T39: Archive old task system and verify migration
**Priority**: P1
**Dependencies**: T36, T37, T38
**Effort**: Low
**Project**: agents

**Objective**: Archive old markdown files and verify complete migration

**Archive steps**:
```bash
# Create archive directory
mkdir -p agents/tasks/archive

# Move old files
mv agents/tasks/tasks.md agents/tasks/archive/tasks-pre-beads.md
mv agents/tasks/registry.md agents/tasks/archive/registry-pre-beads.md

# Add archive note
cat > agents/tasks/archive/README.md << 'EOF'
# Archive Note

These files were migrated to Beads on $(date +%Y-%m-%d).

To view current tasks, use:
- `bd list` - All tasks
- `bd ready` - Ready work
- `bd show <id>` - Task details

These files are kept for historical reference only.
Do not edit these files.
EOF
```

**Verification checklist**:
```bash
# Database health
bd doctor

# Task counts
bd list --json | jq length              # Should be 22 total
bd list --priority 0 --json | jq length # Should be 6
bd list --priority 1 --json | jq length # Should be 11
bd list --priority 2 --json | jq length # Should be 5

# Ready work (unblocked)
bd ready

# Blocked work
bd blocked

# Dependencies
bd dep cycles  # Should be empty

# Labels
bd list --label trading-bot
bd list --label infrastructure

# Git sync test
git add .beads/
git status  # Should show .beads/beads.jsonl staged
```

**Success Criteria**:
- [ ] Old tasks.md archived to agents/tasks/archive/
- [ ] Old registry.md archived to agents/tasks/archive/
- [ ] Archive README.md created with migration note
- [ ] `bd doctor` reports healthy
- [ ] All 22 tasks present in Beads
- [ ] Dependencies correctly configured
- [ ] `bd ready` returns unblocked tasks only
- [ ] Git sync working (changes stage correctly)

**Final commit**:
```bash
git add .beads/ agents/
git commit -m "feat(agents): Migrate task system to Beads

- Initialize Beads database in repository
- Migrate 22 tasks from tasks.md to Beads
- Add 12 dependency relationships
- Update AGENTS.md, README.md, server-agent.md
- Create beads-task-management tool
- Archive old markdown-based task files

Plan: agents/plans/beads-migration-plan.md"
```

---

## Completed Tasks

| ID | Task | Project | Completed | Notes |
|----|------|---------|-----------|-------|
| - | Agents system cleanup | agents | 2024-11-27 | Simplified from 600MB to 272KB |

