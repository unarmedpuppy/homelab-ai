FROM harbor.server.unarmedpuppy.com/docker-hub/library/node:20-alpine AS builder
WORKDIR /app
COPY package*.json ./
RUN npm ci
COPY . .
RUN npm run build

FROM harbor.server.unarmedpuppy.com/lscr/linuxserver/nginx:latest
COPY --from=builder /app/dist /config/www
COPY nginx.conf /config/nginx/site-confs/default.conf
EXPOSE 80
