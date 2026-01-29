# Build stage
FROM harbor.server.unarmedpuppy.com/docker-hub/library/node:20-alpine AS builder

WORKDIR /app

# Copy package files
COPY package*.json ./

# Install dependencies
RUN npm ci

# Copy source code
COPY . .

# Build the application
RUN npm run build

# Production stage
FROM harbor.server.unarmedpuppy.com/docker-hub/library/nginx:alpine

# Copy built assets from builder
COPY --from=builder /app/dist /usr/share/nginx/html

# Copy nginx configuration template
COPY nginx.conf.template /etc/nginx/templates/default.conf.template

EXPOSE 80

# nginx:alpine automatically runs envsubst on /etc/nginx/templates/*.template
# and outputs to /etc/nginx/conf.d/ at startup
CMD ["nginx", "-g", "daemon off;"]
