# Home Server Apps Cleanup Plan

**Date**: 2025-01-04
**Status**: Completed (pending server deployment)

## Overview

Audit and cleanup of home-server apps directory. Removing unused apps, fixing naming inconsistencies, and ensuring docker maintenance is automated.

## Tasks

### 1. Docker Maintenance Script
- [x] Check existing crontab - found backup and plex cleanup only
- [x] README mentions weekly prune but NOT in crontab
- [x] Created `scripts/docker-maintenance.sh` with container/image/network prune
- [ ] TODO: Add to crontab on server: `0 5 * * 1 ~/server/scripts/docker-maintenance.sh`

### 2. Migration Candidates (verify CI/CD)
All repos have CI/CD publishing to Harbor:
- [x] `trading-bot` → `library/trading-bot` - CI configured
- [x] `trading-journal` → `library/trading-journal-backend/frontend` - CI configured  
- [x] `maptapdat` → `library/maptapdat` - CI configured
- [x] `polyjuiced` → `library/polymarket-bot` - CI configured (keeps old image name)

**Note**: These are already using Harbor images. No changes needed to compose files.

### 3. Delete Unused Apps
- [x] `tradenote` - Not running, simple web app
- [x] `tradingagents` - Not running, old experiment
- [x] `discord-reaction-bot` - Disabled, project ended
- [x] `grist` - No docker-compose, empty persist dir
- [x] `ollama-docker` - Not used (ollama runs differently)

### 4. Triage Problematic Apps
- [x] `media-download-slskd` - inotify limit (128) too low → created sysctl.d/99-inotify.conf
- [x] `agent-gateway` - Python import error (broken image) → disabled
- [x] `frigate` - No cameras configured → disabled until cameras added
- [x] `paperless` - Actually working fine! Logs show normal operation
- [x] `libreddit` - Running fine, health check may be slow
- [x] `trading-bot-ib-gateway` - 2FA timeout (expected, needs manual VNC login)

### 5. Fix Naming Inconsistencies
- [x] Rename `freshRSS` → `freshrss`
- [x] Rename `spotifydl` → `spotdl`
- [x] Rename `minecraft` → `minecraft-bedrock`

### 6. Server Cleanup (after git push)
- [ ] `git pull` on server
- [ ] Stop and remove containers for deleted apps
- [ ] Copy sysctl config: `sudo cp scripts/sysctl.d/99-inotify.conf /etc/sysctl.d/ && sudo sysctl -p /etc/sysctl.d/99-inotify.conf`
- [ ] Add docker-maintenance.sh to crontab
- [ ] Prune orphaned containers/images
- [ ] Restart slskd after inotify fix

## Execution Log

### 2025-01-04 22:XX - Started cleanup
- Created this plan document
- Verified CI/CD for migration candidates (all 4 repos have CI/CD to Harbor)
- Crontab check: weekly docker prune mentioned in README but not actually in crontab

### 2025-01-04 22:XX - Completed local changes
- Deleted 5 unused apps: tradenote, tradingagents, discord-reaction-bot, grist, ollama-docker
- Renamed 3 directories: freshRSS→freshrss, spotifydl→spotdl, minecraft→minecraft-bedrock
- Disabled agent-gateway (Python import error in image)
- Disabled frigate (no cameras configured)
- Created docker-maintenance.sh script
- Created sysctl.d/99-inotify.conf for slskd inotify limit fix
- Verified paperless and libreddit are actually working (health check cosmetic issues only)
- Confirmed ib-gateway needs manual 2FA via VNC (expected behavior)

