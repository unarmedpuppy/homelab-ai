# Beads Viewer Dockerfile
# Builds the web interface for visualizing Beads projects

FROM oven/bun:1.1-alpine AS builder

# Install git and build dependencies for native modules (better-sqlite3)
RUN apk add --no-cache git python3 make g++ linux-headers

WORKDIR /build

# Clone the beads-viewer repository
RUN git clone --depth 1 https://github.com/mgalpert/beads-viewer.git .

# Install dependencies
RUN bun install

# Build the frontend
RUN bun run build

# Production stage
FROM oven/bun:1.1-alpine

# Install beads CLI (bd) and required tools
RUN apk add --no-cache nodejs npm git curl bash \
    && npm install -g @beads/bd

WORKDIR /app

# Copy built application from builder
COPY --from=builder /build/dist ./dist
COPY --from=builder /build/server ./server
COPY --from=builder /build/package.json ./
COPY --from=builder /build/bun.lockb ./
COPY --from=builder /build/node_modules ./node_modules

# Copy our production server wrapper
COPY server-prod.ts ./server-prod.ts

# The backend server port
ENV PORT=3001

# Expose ports
EXPOSE 3001

# Working directory is /app where .beads will be mounted
WORKDIR /app

# Start the production server
CMD ["bun", "run", "server-prod.ts"]
