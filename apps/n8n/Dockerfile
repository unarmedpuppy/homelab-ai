FROM harbor.server.unarmedpuppy.com/docker-hub/n8nio/n8n:latest

USER root
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    docker.io \
    && rm -rf /var/lib/apt/lists/*
USER node
