# Docker Credential Issues Over SSH (Windows/WSL)

When running Docker commands via SSH to a Windows machine (landing in WSL), you may encounter credential store errors:

```
error getting credentials - err: exit status 1, out: `A specified logon session does not exist. It may already have been terminated.`
```

## Cause

Windows credential manager (`credsStore: desktop`) requires an interactive Windows desktop session. SSH connections don't have access to the Windows credential manager token.

## Solution

Bypass the Windows credential store by using a clean Docker config:

```bash
# Create clean docker config in WSL home (no credential store)
mkdir -p ~/.docker
echo '{"auths": {}}' > ~/.docker/config.json

# Use this config explicitly for docker commands
DOCKER_CONFIG=~/.docker docker build -t myimage:latest ./path
DOCKER_CONFIG=~/.docker docker pull nginx:latest
DOCKER_CONFIG=~/.docker docker compose up -d
```

## For Public Images

Public images (like `nvidia/cuda`, `nginx`, `python`) don't require authentication. The issue is that Docker still tries to use the broken credential helper even for public images.

## Permanent Fix (Optional)

If you primarily use Docker over SSH, you can set this in your WSL shell profile:

```bash
# Add to ~/.bashrc or ~/.zshrc
export DOCKER_CONFIG=~/.docker
```

## Things That Don't Work Over SSH

- Restarting Docker Desktop (doesn't fix the credential issue)
- `docker login` (fails to store tokens)
- Modifying Windows Docker config at `/mnt/c/Users/<user>/.docker/config.json`

## Related

- Gaming PC connection: `scripts/connect-gaming-pc.sh`
- TTS server build: `local-ai/build-tts-server.sh`
