# Build stage
FROM node:20-alpine AS builder

WORKDIR /app

# Copy package files
COPY package*.json ./

# Install dependencies
RUN npm install

# Copy source code
COPY . .

# Build the application with environment variables
# Note: VITE_API_URL is now detected at runtime, so we don't need it at build time
ARG VITE_API_KEY
ARG VITE_APP_NAME
ENV VITE_API_KEY=$VITE_API_KEY
ENV VITE_APP_NAME=$VITE_APP_NAME

RUN npm run build

# Production stage
FROM nginx:alpine

# Copy built files from builder
COPY --from=builder /app/dist /usr/share/nginx/html

# Copy nginx configuration
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Expose port 80
EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]

