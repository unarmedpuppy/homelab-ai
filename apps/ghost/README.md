# Ghost

**Professional Publishing Platform**

Ghost is a powerful, open-source publishing platform designed for journalists, writers, and content creators. It's fast, secure, and optimized for SEO.

## Features

- **Modern Publishing**: Beautiful, distraction-free writing experience
- **Memberships**: Built-in membership and subscription features
- **Newsletters**: Send newsletters directly from Ghost
- **SEO Optimized**: Built-in SEO features and sitemaps
- **Themes**: Customizable themes and templates
- **API**: Full REST API for integrations
- **ActivityPub**: Social Web (ActivityPub) support (optional)
- **Analytics**: Web analytics with Tinybird (optional)

## Quick Start

### 1. Clone the Repository (Optional)

If you want to use Ghost's official Docker setup with Caddy, you can clone their repo:

```bash
cd apps/ghost
git clone https://github.com/TryGhost/ghost-docker.git ghost-docker-repo
```

However, this setup uses Traefik instead of Caddy for better integration with your existing infrastructure.

### 2. Setup Environment

```bash
cp env.template .env
```

### 3. Generate Database Passwords

```bash
# Generate database root password
echo "DATABASE_ROOT_PASSWORD=$(openssl rand -hex 32)" >> .env

# Generate database user password
echo "DATABASE_PASSWORD=$(openssl rand -hex 32)" >> .env
```

### 4. Configure Ghost URL

Edit `.env` and set:
- `GHOST_URL`: Your Ghost site URL (use local IP for testing, domain for production)
- `GHOST_DOMAIN`: Your domain name for Traefik routing

### 5. Configure SMTP Email (REQUIRED)

Ghost requires SMTP configuration for transactional emails (password reset, etc.). Edit `.env`:

```
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=your-app-password
SMTP_FROM=noreply@yourdomain.com
```

**Gmail Setup:**
1. Enable 2-factor authentication
2. Generate an App Password: https://myaccount.google.com/apppasswords
3. Use the app password (not your regular password) in `SMTP_PASSWORD`

**Other SMTP Providers:**
- SendGrid: `smtp.sendgrid.net:587`
- Mailgun: `smtp.mailgun.org:587`
- AWS SES: See AWS SES documentation

### 6. Start the Application

```bash
docker compose up -d
```

### 7. Access Ghost

- **Local**: http://192.168.86.47:8097
- **HTTPS**: https://blog.server.unarmedpuppy.com (after DNS setup)
- **Admin**: Navigate to `/ghost` to complete setup
- **Homepage**: Listed under "Content & Publishing" group

### 8. Complete Setup

1. Open your browser and navigate to your Ghost URL
2. Click "Create your account" to set up your admin account
3. Follow the setup wizard to configure your site

## Configuration

### Environment Variables

See `env.template` for all available configuration options.

**Required:**
- `DATABASE_ROOT_PASSWORD` - MySQL root password
- `DATABASE_PASSWORD` - MySQL user password
- `GHOST_URL` - Your Ghost site URL
- `GHOST_DOMAIN` - Domain name for Traefik
- `SMTP_*` - SMTP email configuration

**Optional:**
- ActivityPub (Social Web) configuration
- Tinybird Analytics configuration

### Database

Ghost uses MySQL 8.0. The database is persisted in `./data/mysql/`.

### Content Storage

Ghost content (themes, images, etc.) is stored in `./data/ghost/`.

## Advanced Features

### ActivityPub (Social Web)

To enable self-hosted ActivityPub:

1. Add to `.env`:
   ```
   ACTIVITYPUB_TARGET=activitypub:8080
   ```

2. Follow the official Ghost Docker documentation for ActivityPub setup

### Web Analytics (Tinybird)

To enable analytics:

1. Create a Tinybird account
2. Follow the official Ghost Docker documentation for Tinybird setup
3. Add Tinybird configuration to `.env`

## Updating Ghost

To update to the latest version:

```bash
cd apps/ghost
docker compose pull
docker compose up -d
```

## Troubleshooting

### Port Already in Use

If port 8097 conflicts, change it in `docker-compose.yml`:
```yaml
ports:
  - "8098:2368"  # Change 8097 to your preferred port
```

### Database Connection Issues

Check database health:
```bash
docker compose logs ghost-db
docker compose ps ghost-db
```

### Email Not Sending

Verify SMTP configuration:
```bash
docker compose logs ghost | grep -i mail
```

Check your SMTP credentials and ensure:
- App passwords are used for Gmail (not regular passwords)
- SMTP port is correct (587 for TLS, 465 for SSL)
- Firewall allows outbound SMTP connections

### First-Time Setup Issues

If you can't access the setup page:
1. Check container logs: `docker compose logs ghost`
2. Verify database is healthy: `docker compose ps`
3. Ensure `GHOST_URL` matches your access URL

## Resources

- **Official Docs**: https://docs.ghost.org/
- **Docker Setup**: https://docs.ghost.org/install/docker
- **GitHub**: https://github.com/TryGhost/Ghost
- **Themes**: https://ghost.org/themes/
- **Forum**: https://forum.ghost.org/

## License

MIT

