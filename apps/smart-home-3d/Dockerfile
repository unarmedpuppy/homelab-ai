# Multi-stage Dockerfile for Smart Home 3D

# =============================================================================
# Stage 1: Build Frontend
# =============================================================================
FROM node:20-alpine AS frontend-builder

WORKDIR /app/frontend

# Copy frontend package files
COPY frontend/package*.json ./

# Install dependencies
RUN npm ci

# Copy frontend source
COPY frontend/ ./

# Build frontend
RUN npm run build

# =============================================================================
# Stage 2: Build Backend
# =============================================================================
FROM node:20-alpine AS backend-builder

WORKDIR /app/backend

# Copy backend package files
COPY backend/package*.json ./

# Install dependencies (including dev for build)
RUN npm ci

# Copy Prisma schema
COPY backend/prisma ./prisma

# Generate Prisma client
RUN npx prisma generate

# Copy backend source
COPY backend/ ./

# Build backend
RUN npm run build

# =============================================================================
# Stage 3: Production Image
# =============================================================================
FROM node:20-alpine AS production

WORKDIR /app

# Install only production dependencies for backend
COPY backend/package*.json ./backend/
WORKDIR /app/backend
RUN npm ci --only=production

# Copy Prisma schema and generated client
COPY backend/prisma ./prisma
RUN npx prisma generate

# Copy built backend
COPY --from=backend-builder /app/backend/dist ./dist

# Copy built frontend to serve statically
COPY --from=frontend-builder /app/frontend/dist /app/frontend/dist

WORKDIR /app

# Create a simple static file server script
RUN echo 'import express from "express"; \
import path from "path"; \
import { fileURLToPath } from "url"; \
const __dirname = path.dirname(fileURLToPath(import.meta.url)); \
const app = express(); \
app.use(express.static(path.join(__dirname, "frontend/dist"))); \
app.get("*", (req, res) => { \
  if (!req.path.startsWith("/api") && !req.path.startsWith("/socket.io")) { \
    res.sendFile(path.join(__dirname, "frontend/dist/index.html")); \
  } \
}); \
export { app };' > static.js

# Modify server to include static file serving
RUN echo 'import "./backend/dist/server.js";' > start.js

# Expose port
EXPOSE 3000

# Environment variables
ENV NODE_ENV=production
ENV PORT=3000

# Start server
CMD ["node", "--experimental-specifier-resolution=node", "backend/dist/server.js"]
