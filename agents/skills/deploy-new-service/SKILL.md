---
name: deploy-new-service
description: Set up a new Docker service on the home server
when_to_use: Adding a new application, setting up a new containerized service
---

# Deploy New Service

Set up a new Docker service on the home server.

## When to Use

- Adding a new application
- Setting up a new containerized service

## Steps

### 1. Check Port Availability

```bash
# Check if port is in use
lsof -i :PORT
netstat -an | grep PORT
```

### 2. Create Directory Structure

```bash
mkdir -p apps/SERVICE_NAME
cd apps/SERVICE_NAME
```

### 3. Create docker-compose.yml

```yaml
services:
  SERVICE_NAME:
    image: IMAGE:TAG
    container_name: SERVICE_NAME
    restart: unless-stopped
    ports:
      - "PORT:PORT"
    volumes:
      - ./data:/data
    environment:
      - TZ=America/Chicago
    labels:
      - "homepage.group=Category"
      - "homepage.name=Service Name"
      - "homepage.icon=icon.png"
      - "homepage.href=http://IP:PORT"
```

### 4. Create .env File (if needed)

```bash
cat > .env << EOF
API_KEY=your_key
DATABASE_URL=postgres://...
EOF
```

### 5. Validate Configuration

```bash
docker compose config
```

### 6. Start Service

```bash
docker compose up -d
```

### 7. Verify

```bash
docker ps | grep SERVICE_NAME
docker logs SERVICE_NAME --tail 20
curl http://localhost:PORT/health  # if applicable
```

### 8. Deploy to Server

```bash
git add .
git commit -m "Add SERVICE_NAME service"
git push
ssh homeserver "cd /home/shua/home-server && git pull && cd apps/SERVICE_NAME && docker compose up -d"
```

## Template docker-compose.yml

```yaml
services:
  app:
    image:
    container_name:
    restart: unless-stopped
    ports:
      - ":"
    volumes:
      - ./config:/config
      - ./data:/data
    environment:
      - TZ=America/Chicago
      - PUID=1000
      - PGID=1000
```

