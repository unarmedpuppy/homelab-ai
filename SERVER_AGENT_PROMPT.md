# Server Agent Prompt

## Overview

This document provides essential context for AI agents working on the home server infrastructure. It covers connection methods, project structure, deployment workflows, and key learnings from previous work.

## Server Connection

### Connection Method

The server is accessed via SSH using the `connect-server.sh` script:

```bash
# From the local repository root
cd /Users/joshuajenquist/repos/personal/home-server
bash scripts/connect-server.sh "command to run on server"
```

**Example:**
```bash
bash scripts/connect-server.sh "cd ~/server && docker ps"
```

### Server Details

- **Server Path**: `~/server` (home directory of `unarmedpuppy` user)
- **Local Repository**: `/Users/joshuajenquist/repos/personal/home-server`
- **Git Remote**: `origin/main` (GitHub: `unarmedpuppy/home-server`)
- **Network**: `my-network` (Docker external network)
- **Local IP**: `192.168.86.47`

## Project Structure

### Directory Layout

```
home-server/
├── apps/                    # All Docker Compose applications
│   ├── trading-bot/         # Trading bot with sentiment analysis
│   ├── monica/              # Personal relationship management
│   ├── open-health/         # Health tracking application
│   ├── campfire/            # Basecamp Campfire chat
│   ├── ghost/               # Ghost blogging platform
│   ├── open-archiver/       # Email archiving platform
│   ├── grafana/             # Metrics visualization
│   ├── traefik/             # Reverse proxy & HTTPS
│   ├── homepage/            # Service dashboard
│   └── [other apps]/        # Additional services
├── scripts/                 # Utility scripts
│   └── connect-server.sh    # SSH connection helper
└── README.md                # Main project documentation
```

### Key Applications

#### Trading Bot (`apps/trading-bot/`)
- **Purpose**: Automated trading bot with sentiment analysis
- **Tech Stack**: FastAPI, PostgreSQL, Redis, IBKR integration
- **Features**: Real-time sentiment aggregation, position sync, scheduler dashboard
- **Port**: 8000
- **Docs**: `apps/trading-bot/README.md`, `apps/trading-bot/docs/`

#### Monica (`apps/monica/`)
- **Purpose**: Personal relationship management
- **Tech Stack**: Laravel, MySQL
- **Port**: 8098
- **Note**: Requires patched `RouteServiceProvider.php` for HTTP access (see `apps/monica/patches/`)

#### OpenArchiver (`apps/open-archiver/`)
- **Purpose**: Email archiving platform
- **Tech Stack**: SvelteKit, Node.js, PostgreSQL, Meilisearch, Valkey
- **Port**: 8099
- **Note**: Uses pre-built image `logiclabshq/open-archiver:latest`

#### Other Services
- **Grafana**: Metrics visualization (port 3000)
- **Traefik**: Reverse proxy with automatic HTTPS
- **Homepage**: Service dashboard aggregator

## Deployment Workflow

### Standard Deployment Process

**CRITICAL**: Always follow this workflow when making changes:

1. **Make changes locally** in `/Users/joshuajenquist/repos/personal/home-server`

2. **Commit and push to Git**:
   ```bash
   git add .
   git commit -m "Description of changes"
   git push origin main
   ```

3. **Pull on server**:
   ```bash
   bash scripts/connect-server.sh "cd ~/server && git pull origin main"
   ```

4. **Restart affected services**:
   ```bash
   bash scripts/connect-server.sh "cd ~/server/apps/[app-name] && docker compose restart [service-name]"
   ```

5. **Or rebuild if needed**:
   ```bash
   bash scripts/connect-server.sh "cd ~/server/apps/[app-name] && docker compose up -d --build"
   ```

### Docker Compose Commands

All Docker Compose commands should be run on the server:

```bash
# Start services
bash scripts/connect-server.sh "cd ~/server/apps/[app] && docker compose up -d"

# Stop services
bash scripts/connect-server.sh "cd ~/server/apps/[app] && docker compose down"

# View logs
bash scripts/connect-server.sh "cd ~/server/apps/[app] && docker compose logs -f [service]"

# Check status
bash scripts/connect-server.sh "docker ps --filter name=[service]"

# Restart service
bash scripts/connect-server.sh "cd ~/server/apps/[app] && docker compose restart [service]"
```

## Key Learnings & Patterns

### Docker Compose Best Practices

1. **Always use external network**: `my-network` (defined in Traefik)
   ```yaml
   networks:
     my-network:
       external: true
   ```

2. **Homepage labels**: Always add homepage labels for services with UI:
   ```yaml
   labels:
     - "homepage.group=Category Name"
     - "homepage.name=Service Name"
     - "homepage.icon=si-icon-name"
     - "homepage.href=http://192.168.86.47:PORT"
     - "homepage.description=Service description"
   ```

3. **Traefik labels**: For HTTPS routing (when domain is configured):
   ```yaml
   labels:
     - "traefik.enable=true"
     - "traefik.http.routers.[service].rule=Host(`DOMAIN`)"
     - "traefik.http.routers.[service].entrypoints=websecure"
     - "traefik.http.routers.[service].tls.certresolver=myresolver"
     - "traefik.http.services.[service].loadbalancer.server.port=PORT"
   ```

4. **Health checks**: Always include health checks for dependent services:
   ```yaml
   healthcheck:
     test: ["CMD", "health-check-command"]
     interval: 10s
     timeout: 5s
     retries: 5
   ```

5. **Environment files**: 
   - Always create `env.template` with all required variables
   - Document required vs optional variables
   - Include password generation commands
   - Never commit `.env` files (use `.gitignore`)

### Common Issues & Solutions

#### Port Conflicts
- Check existing ports: `grep -r "8098\|8099\|8100" apps/`
- Use unique ports for each service
- Don't expose ports that are only accessed via Traefik

#### Database Authentication
- **MySQL 8.0**: May need `--default-authentication-plugin=mysql_native_password` for older clients
- **PostgreSQL**: Standard connection strings work
- Always use strong passwords (generate with `openssl rand -hex 32`)

#### HTTPS/HTTP Issues
- Services accessed via local IP should use HTTP (`http://192.168.86.47:PORT`)
- HTTPS is handled by Traefik when using domain names
- Some apps (like Monica) force HTTPS - may need patches

#### Environment Variables
- Use `env_file: - .env` in docker-compose for bulk loading
- Override specific vars in `environment:` section
- Critical vars should be in both `.env` and `environment:` for reliability

#### Container Builds
- Some apps use pre-built images (check official docs)
- Others require building from source (clone repo, build in docker-compose)
- Always check official repository for recommended setup

### File Structure Patterns

Each app should have:
```
apps/[app-name]/
├── docker-compose.yml       # Service definitions
├── env.template             # Environment variable template
├── README.md                # Setup and usage instructions
├── .gitignore              # Ignore .env, data/, etc.
└── data/                    # Persistent data (gitignored)
    ├── [database]/          # Database volumes
    ├── storage/             # Application storage
    └── [other]/             # Other persistent data
```

## Environment Variables

### Common Variables

- **APP_URL**: Application public URL (use local IP for testing)
- **DOMAIN**: Domain name for Traefik routing
- **Database passwords**: Generate with `openssl rand -hex 32`
- **Secret keys**: Generate with `openssl rand -base64 32` or `openssl rand -hex 32`

### Database Connection Strings

- **PostgreSQL**: `postgresql://user:password@host:5432/database`
- **MySQL**: `mysql://user:password@host:3306/database`
- **Redis/Valkey**: `redis://:password@host:6379`

## Testing & Validation

### After Deployment

1. **Check container status**:
   ```bash
   bash scripts/connect-server.sh "docker ps --filter name=[service]"
   ```

2. **Check logs**:
   ```bash
   bash scripts/connect-server.sh "docker logs [service] --tail 50"
   ```

3. **Test HTTP response**:
   ```bash
   bash scripts/connect-server.sh "curl -s -o /dev/null -w '%{http_code}' http://localhost:PORT"
   ```

4. **Verify homepage entry**: Check that service appears in homepage dashboard

## Documentation

### Main Documentation

- **README.md**: Root-level project overview and quick start
- **apps/[app]/README.md**: App-specific setup and usage
- **apps/[app]/docs/**: Detailed documentation (if exists)

### Key Documentation Files

- `apps/trading-bot/docs/`: Extensive trading bot documentation
- `apps/trading-bot/PROJECT_TODO.md`: Project task tracking
- `apps/trading-bot/AGENT_START_PROMPT.md`: Agent coordination guide

## Important Notes

### Security

- Never commit `.env` files
- Always use strong, randomly generated passwords
- Store secrets in `.env` files (gitignored)
- Use environment variables, not hardcoded values

### Data Persistence

- All persistent data should be in `./data/` directories
- Database volumes: `./data/[database-name]/`
- Application storage: `./data/storage/`
- Always backup before major changes

### Network Configuration

- All services use `my-network` (external network)
- Services communicate via service names (e.g., `postgres`, `redis`)
- Ports are exposed for local IP access
- Traefik handles HTTPS routing for domains

### Service Dependencies

- Always use `depends_on` with health checks
- Wait for dependencies to be healthy before starting
- Check logs if services fail to start

## Quick Reference Commands

```bash
# Connect and run command
bash scripts/connect-server.sh "command"

# Deploy changes
git add . && git commit -m "message" && git push origin main
bash scripts/connect-server.sh "cd ~/server && git pull origin main"

# Restart service
bash scripts/connect-server.sh "cd ~/server/apps/[app] && docker compose restart [service]"

# View logs
bash scripts/connect-server.sh "docker logs [service] --tail 50 -f"

# Check all services
bash scripts/connect-server.sh "docker ps --format 'table {{.Names}}\t{{.Status}}\t{{.Ports}}'"
```

## Agent Workflow Checklist

When working on a new task:

1. ✅ Read this prompt and relevant README files
2. ✅ Understand the deployment workflow
3. ✅ Make changes locally
4. ✅ Test locally if possible
5. ✅ Commit and push to Git
6. ✅ Pull on server
7. ✅ Deploy/restart services
8. ✅ Verify deployment (logs, HTTP response, homepage)
9. ✅ Document any new patterns or issues encountered

## Questions to Ask

If unsure about something:

1. Check the app's `README.md` first
2. Check the main `README.md` for project-wide info
3. Review similar apps for patterns
4. Check Docker Compose files for examples
5. Review logs for error messages

## Remember

- **Always deploy via Git**: Never edit files directly on the server
- **Test after deployment**: Verify services are running and accessible
- **Document changes**: Update README files when adding new features
- **Follow patterns**: Use existing apps as templates for new ones
- **Homepage labels**: Always add them for services with UI
- **Health checks**: Include them for database and critical services

---

**Last Updated**: Based on work completed through OpenArchiver setup (November 2025)
**Maintained By**: AI Agents working on home-server infrastructure

