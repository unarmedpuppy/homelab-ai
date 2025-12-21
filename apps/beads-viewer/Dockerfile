# Beads UI Dockerfile
# Web interface for the bd CLI tool (beads issue tracker)

FROM node:20-alpine

# Install beads CLI (bd) and beads-ui globally
RUN npm install -g @beads/bd beads-ui

WORKDIR /app

# Default port for beads-ui
ENV PORT=3000
ENV HOST=0.0.0.0

# Expose the web UI port
EXPOSE 3000

# Start beads-ui - it will look for .beads in the working directory
CMD ["bdui", "start"]
