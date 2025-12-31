FROM harbor.server.unarmedpuppy.com/docker-hub/library/docker:cli AS docker-cli

FROM harbor.server.unarmedpuppy.com/docker-hub/n8nio/n8n:latest

USER root
COPY --from=docker-cli /usr/local/bin/docker /usr/local/bin/docker
RUN addgroup -g 994 docker && adduser node docker
USER node
