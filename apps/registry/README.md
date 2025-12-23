# Private Docker Registry

Private Docker registry for home server custom applications.

## Setup

### 1. Create auth directory and htpasswd file

On the server, run:

```bash
cd ~/server/apps/registry
mkdir -p auth data

# Create htpasswd file (you'll be prompted for password)
docker run --rm --entrypoint htpasswd httpd:2 -Bbn YOUR_USERNAME YOUR_PASSWORD > auth/htpasswd

# Or interactively:
docker run -it --rm --entrypoint htpasswd httpd:2 -Bn YOUR_USERNAME >> auth/htpasswd
```

### 2. Start the registry

```bash
docker compose up -d
```

### 3. Configure Docker clients

On any machine that needs to push/pull:

```bash
docker login registry.server.unarmedpuppy.com
# Enter username and password
```

## Usage

### Push an image

```bash
# Tag the image
docker tag my-app:latest registry.server.unarmedpuppy.com/my-app:v1.0.0

# Push
docker push registry.server.unarmedpuppy.com/my-app:v1.0.0
```

### Pull an image

```bash
docker pull registry.server.unarmedpuppy.com/my-app:v1.0.0
```

### List images (via API)

```bash
curl -u username:password https://registry.server.unarmedpuppy.com/v2/_catalog
```

## Web UI

Access the registry UI at: https://registry-ui.server.unarmedpuppy.com

## Storage

Registry data is stored in `./data/`. Include this in your backup strategy.

## Cleanup

To delete old/unused images and reclaim space:

```bash
# Delete via UI or API, then run garbage collection
docker exec registry bin/registry garbage-collect /etc/docker/registry/config.yml
```
