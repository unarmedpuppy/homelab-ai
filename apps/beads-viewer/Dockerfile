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
ENV BEADS_NO_DAEMON=1

# Expose the web UI port
EXPOSE 3000

# Create startup script that builds database from JSONL before starting server
RUN echo '#!/bin/bash\n\
cd /app\n\
# Build fresh database from JSONL source of truth\n\
if [ -f .beads/issues.jsonl ]; then\n\
  echo "Building beads database from JSONL..."\n\
  # Remove any stale database to force fresh import\n\
  rm -f .beads/beads.db .beads/beads.db-shm .beads/beads.db-wal\n\
  # Initialize and import\n\
  bd import -i .beads/issues.jsonl 2>&1 || echo "Import completed with warnings"\n\
  echo "Database ready"\n\
fi\n\
# Start the server\n\
exec node /usr/local/lib/node_modules/beads-ui/server/index.js\n\
' > /start.sh && chmod +x /start.sh

CMD ["/start.sh"]
