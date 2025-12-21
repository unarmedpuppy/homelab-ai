# Beads UI Dockerfile
# Web interface for the bd CLI tool (beads issue tracker)

FROM node:22-alpine

# Install beads CLI (bd) and beads-ui globally
RUN npm install -g @beads/bd beads-ui

WORKDIR /app

# Default port for beads-ui
ENV PORT=3000
ENV HOST=0.0.0.0

# Expose the web UI port
EXPOSE 3000

# Run the server directly in foreground mode (not as daemon)
# The server is at /usr/local/lib/node_modules/beads-ui/server/index.js
CMD ["node", "/usr/local/lib/node_modules/beads-ui/server/index.js"]
