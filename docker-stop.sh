#!/bin/bash
docker-compose -f ~/server/apps/adguard-home/docker-compose.yml down
docker-compose -f ~/server/apps/bedrock-viz/docker-compose.yml down
docker-compose -f ~/server/apps/cloudflare-ddns/docker-compose.yml down
#docker-compose -f ~/server/apps/grafana/docker-compose.yml down
docker-compose -f ~/server/apps/homeassistant/docker-compose.yml down
docker-compose -f ~/server/apps/homepage/docker-compose.yml down
#docker-compose -f ~/server/apps/immich/docker-compose.yml down
docker-compose -f ~/server/apps/libreddit/docker-compose.yml down
docker-compose -f ~/server/apps/minecraft/docker-compose.yml down
#docker-compose -f ~/server/apps/nextcloud/docker-compose.yml down
#docker-compose -f ~/server/apps/obsidian-remote/docker-compose.yml down
docker-compose -f ~/server/apps/plex/docker-compose.yml down
docker-compose -f ~/server/apps/rust/docker-compose.yml down
docker-compose -f ~/server/apps/traefik/docker-compose.yml down