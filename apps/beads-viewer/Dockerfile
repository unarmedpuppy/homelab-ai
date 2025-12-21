# Beads UI Dockerfile
# Web interface for the bd CLI tool (beads issue tracker)

FROM node:22-alpine

# Install curl for downloading bd binary
RUN apk add --no-cache curl bash

# Install the actual bd Go binary (not the npm wrapper)
RUN curl -fsSL https://raw.githubusercontent.com/steveyegge/beads/main/scripts/install.sh | bash \
    && mv /root/.local/bin/bd /usr/local/bin/bd \
    && chmod +x /usr/local/bin/bd

# Install beads-ui globally
RUN npm install -g beads-ui

WORKDIR /app

# Default port for beads-ui
ENV PORT=3000
ENV HOST=0.0.0.0

# Expose the web UI port
EXPOSE 3000

# Run the server directly in foreground mode (not as daemon)
CMD ["node", "/usr/local/lib/node_modules/beads-ui/server/index.js"]
