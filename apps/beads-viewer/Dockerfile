# Beads UI Dockerfile
# Web interface for the bd CLI tool (beads issue tracker)

# Use Debian-based image (not Alpine) because bd binary requires glibc
FROM node:22-slim

# Install curl for downloading bd binary
# Note: flock is part of util-linux which is included in base image
RUN apt-get update && apt-get install -y --no-install-recommends curl ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Install the actual bd Go binary (not the npm wrapper)
# The install script places bd in /usr/local/bin when it has write access
RUN curl -fsSL https://raw.githubusercontent.com/steveyegge/beads/main/scripts/install.sh | bash

# Create a wrapper script that serializes bd calls using flock
# This prevents concurrent migration conflicts
RUN mv /usr/local/bin/bd /usr/local/bin/bd-real && \
    echo '#!/bin/bash\nexec flock /tmp/bd.lock /usr/local/bin/bd-real "$@"' > /usr/local/bin/bd && \
    chmod +x /usr/local/bin/bd

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
