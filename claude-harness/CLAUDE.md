# Claude Harness - Agent Instructions

You are running inside the **claude-harness** container on the home server. This container provides Claude Code capabilities via an OpenAI-compatible API.

## Environment

- **Container**: `claude-harness` (Docker)
- **Working Directory**: `/app` (main.py, API server)
- **Workspace**: `/workspace` (persistent volume for repos)
- **Server Access**: SSH to `claude-deploy@192.168.86.47:4242`

## Critical Rules

### Docker Commands Require `sudo`

The `claude-deploy` user is **NOT in the docker group** for security. All docker commands must use `sudo`:

```bash
# CORRECT
sudo docker ps
sudo docker logs container-name
sudo docker restart container-name
sudo docker compose -f /path/to/docker-compose.yml up -d

# WRONG (will fail with permission denied)
docker ps
docker logs container-name
```

### Allowed Docker Operations

| Command | Allowed |
|---------|---------|
| `sudo docker ps` | Yes |
| `sudo docker logs` | Yes |
| `sudo docker inspect` | Yes |
| `sudo docker images` | Yes |
| `sudo docker stats` | Yes |
| `sudo docker start/stop/restart` | Yes |
| `sudo docker compose up/down` | Yes (in /home/unarmedpuppy/server/apps/ only) |
| `sudo docker rm` | **NO - BLOCKED** |
| `sudo docker rmi` | **NO - BLOCKED** |
| `sudo docker volume rm` | **NO - BLOCKED** |
| `sudo docker system prune` | **NO - BLOCKED** |

### SSH to Server

To run commands on the home server:

```bash
ssh -p 4242 claude-deploy@192.168.86.47 'sudo docker ps'
```

Or for multiple commands:

```bash
ssh -p 4242 claude-deploy@192.168.86.47 << 'EOF'
sudo docker ps --format "{{.Names}}: {{.Status}}"
sudo docker logs --tail 20 container-name
EOF
```

## Git Access

GitHub repos can be cloned/pushed using the configured PAT:

```bash
cd /workspace
git clone https://github.com/unarmedpuppy/home-server.git
cd home-server
# Make changes...
git add . && git commit -m "message" && git push
```

## Skills

Check `.claude/skills/` for task-specific guides:
- `docker-operations.md` - Docker container management
- `deploy-service.md` - Deploying services to the server
- `server-ssh.md` - SSH access patterns

## Boundaries

### Always Do
- Use `sudo` for all docker commands
- Use SSH port 4242 for server access
- Commit changes before ending sessions

### Never Do
- Run docker commands without sudo (they will fail)
- Try to delete containers, images, or volumes (blocked by sudoers)
- Expose secrets in logs or commits
