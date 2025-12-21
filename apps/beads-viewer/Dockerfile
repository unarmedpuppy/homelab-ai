# Beads UI Dockerfile
# Web interface for the bd CLI tool (beads issue tracker)

# Use Debian-based image (not Alpine) because bd binary requires glibc
FROM node:22-slim

# Install curl for downloading bd binary
RUN apt-get update && apt-get install -y --no-install-recommends curl ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Install the actual bd Go binary (not the npm wrapper)
# The install script places bd in /usr/local/bin when it has write access
RUN curl -fsSL https://raw.githubusercontent.com/steveyegge/beads/main/scripts/install.sh | bash

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
