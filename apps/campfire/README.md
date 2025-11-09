# Campfire

**Web-based Chat Application**

Campfire is a web-based chat application by Basecamp. It supports many of the features you'd expect, including:

- Multiple rooms, with access controls
- Direct messages
- File attachments with previews
- Search
- Notifications (via Web Push)
- @mentions
- API, with support for bot integrations

## Quick Start

### 1. Clone the Repository

```bash
cd apps/campfire
git clone https://github.com/basecamp/once-campfire.git campfire-repo
```

### 2. Setup Environment

```bash
cp env.template .env
```

### 3. Generate Secret Key Base

```bash
# Generate secret key and add to .env
echo "SECRET_KEY_BASE=$(openssl rand -hex 64)" >> .env
```

Or manually edit `.env` and add:
```
SECRET_KEY_BASE=<generated-key>
```

### 4. Generate VAPID Keys (Optional)

After the container is built, you can generate VAPID keys for Web Push notifications:

```bash
docker exec campfire /script/admin/create-vapid-key
```

Then add the output to your `.env` file:
```
VAPID_PUBLIC_KEY=<public-key>
VAPID_PRIVATE_KEY=<private-key>
```

### 5. Start the Application

```bash
docker compose up -d --build
```

### 6. Access Campfire

- **Local**: http://192.168.86.47:8096
- **HTTPS**: https://campfire.server.unarmedpuppy.com
- **Homepage**: Listed under "Communication" group

### 7. Create Admin Account

When you first access Campfire, you'll be guided through creating an admin account. The email address of this admin account will be shown on the login page so that people who forget their password know who to contact for help.

## Configuration

### Environment Variables

See `env.template` for all available configuration options.

**Required:**
- `SECRET_KEY_BASE` - Secret key for Rails (generate with `openssl rand -hex 64`)

**Optional:**
- `VAPID_PUBLIC_KEY` / `VAPID_PRIVATE_KEY` - Keypair for Web Push notifications
- `SSL_DOMAIN` - Enable automatic SSL via Let's Encrypt for the given domain
- `DISABLE_SSL` - Set to `true` to serve over plain HTTP (default: `false`)
- `SENTRY_DSN` - Sentry DSN for error reporting in production

### SSL Configuration

Campfire supports automatic SSL via Let's Encrypt. To enable:

1. Set `SSL_DOMAIN` in `.env`:
   ```
   SSL_DOMAIN=campfire.server.unarmedpuppy.com
   ```

2. Ensure port 443 is accessible and DNS points to your server

Alternatively, use Traefik (already configured) for SSL termination.

### Web Push Notifications

To enable Web Push notifications:

1. Generate VAPID keys:
   ```bash
   docker exec campfire /script/admin/create-vapid-key
   ```

2. Add the keys to your `.env` file

3. Restart the container:
   ```bash
   docker compose restart campfire
   ```

## Data Persistence

Data is stored in:
- `./data/` - Database and file attachments

## Features

- **Multiple Rooms**: Create rooms with access controls
- **Direct Messages**: Private one-on-one conversations
- **File Attachments**: Share files with previews
- **Search**: Find messages across all rooms
- **Notifications**: Web Push notifications for new messages
- **@Mentions**: Mention users in messages
- **API**: RESTful API for bot integrations

## Architecture

Campfire is a single-tenant application:
- Any rooms designated "public" will be accessible by all users in the system
- To support entirely distinct groups of customers, deploy multiple instances

## Updating Campfire

To update to the latest version:

```bash
cd apps/campfire
cd campfire-repo
git pull origin main
cd ..
docker compose up -d --build
```

## Troubleshooting

### Port Already in Use

If port 8096 is already in use, change it in `docker-compose.yml`:
```yaml
ports:
  - "8097:80"  # Change 8096 to your preferred port
```

### Database Issues

The database is stored in `./data/`. Ensure the directory is writable:
```bash
chmod 755 data
```

### First-Time Setup

On first access, you'll be prompted to create an admin account. This account's email will be shown on the login page for password recovery.

## Resources

- **GitHub**: https://github.com/basecamp/once-campfire
- **License**: MIT

