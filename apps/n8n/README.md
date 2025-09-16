# n8n - Workflow Automation Platform

n8n is a powerful workflow automation tool that allows you to connect different services and automate tasks without coding.

## Configuration

### Environment Variables

All configuration is managed through the `.env` file. This file contains:

- **Timezone settings**: `TZ` and `GENERIC_TIMEZONE`
- **n8n server settings**: `N8N_HOST`, `N8N_PORT`, `N8N_PROTOCOL`
- **Authentication**: `N8N_BASIC_AUTH_*` variables
- **Database**: `DB_TYPE` and `DB_SQLITE_DATABASE`
- **Security**: `N8N_ENCRYPTION_KEY` (change this!)
- **Server info**: `SERVER_IP` and `DOMAIN` for Traefik/Homepage integration

### Initial Setup

1. **Copy the environment template**:
   ```bash
   cp env.template .env
   ```

2. **Edit the environment file**:
   ```bash
   nano .env
   ```

3. **Change sensitive values**:
   - Update `N8N_BASIC_AUTH_PASSWORD` with a strong password
   - Update `N8N_ENCRYPTION_KEY` with a secure 32-character key
   - Update `SERVER_IP` if your server IP changes
   - Update `DOMAIN` if you change your domain

4. **Start the service**:
   ```bash
   docker-compose up -d
   ```

### Default Credentials
- **Username**: `admin`
- **Password**: `changeme123`

**⚠️ IMPORTANT**: Change these credentials immediately after first login by editing the `.env` file!

## Access

### Local Access
- **URL**: http://${SERVER_IP}:${N8N_PORT} (configured in .env)
- **Port**: 5678 (configurable via N8N_PORT in .env)

### External Access (via Traefik)
- **URL**: https://n8n.${DOMAIN} (configured in .env)
- **SSL**: Automatically handled by Traefik with Let's Encrypt

## Usage

1. **Initial setup** (first time only):
   ```bash
   cd /Users/joshuajenquist/repos/personal/home-server/apps/n8n
   cp env.template .env
   nano .env  # Edit configuration as needed
   ```

2. **Start the service**:
   ```bash
   docker-compose up -d
   ```

3. **Access the web interface**:
   - Open http://192.168.86.47:5678 in your browser
   - Login with the default credentials (admin/changeme123)
   - Change the password immediately!

4. **Create your first workflow**:
   - Click "New workflow" to start building
   - Use the node palette to add triggers and actions
   - Connect different services and APIs

## Security Notes

1. **Change default credentials** immediately after first login by editing `.env`
2. **Update the encryption key** in the `.env` file
3. **Keep the `.env` file secure** - it contains sensitive information
4. **Regular backups** of the n8n_data volume are recommended

## Backup

The n8n data is stored in a Docker volume named `n8n_data`. To backup:

```bash
# Create backup
docker run --rm -v n8n_data:/data -v $(pwd):/backup alpine tar czf /backup/n8n_backup_$(date +%Y%m%d_%H%M%S).tar.gz -C /data .

# Restore backup
docker run --rm -v n8n_data:/data -v $(pwd):/backup alpine tar xzf /backup/n8n_backup_YYYYMMDD_HHMMSS.tar.gz -C /data
```

## Integration with Homepage

This service is configured to appear in your Homepage dashboard under the "Automation" group.

## Troubleshooting

- Check logs: `docker-compose logs -f n8n`
- Restart service: `docker-compose restart n8n`
- Check if port 5678 is available: `netstat -tulpn | grep 5678`
