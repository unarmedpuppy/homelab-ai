# Monica

**Personal Relationship Management (PRM)**

Monica is an open-source web application that enables you to document your life, organize, and log your interactions with your family and friends. Think of it as a CRM for your personal relationships.

## Features

- **Contact Management**: Add and manage contacts with detailed information
- **Relationships**: Define relationships between contacts
- **Reminders**: Automatic reminders for birthdays and important dates
- **Activities**: Record and manage activities with contacts
- **Tasks**: Personal task management
- **Diary**: Keep track of what's happening in your life
- **Documents & Photos**: Upload and organize documents and photos
- **Custom Fields**: Define custom contact field types
- **Labels**: Organize contacts with labels
- **Multiple Vaults**: Support for multiple users and vaults
- **27 Languages**: Translated in 27 languages

## Quick Start

### 1. Setup Environment

```bash
cd apps/monica
cp env.template .env
```

### 2. Generate Database Passwords

```bash
# Generate database root password
echo "DATABASE_ROOT_PASSWORD=$(openssl rand -hex 32)" >> .env

# Generate database user password
echo "DATABASE_PASSWORD=$(openssl rand -hex 32)" >> .env
```

### 3. Generate Application Key

```bash
# Generate app key
echo "APP_KEY=$(openssl rand -base64 32)" >> .env
```

Or after starting the container:
```bash
docker exec monica php artisan key:generate --show
```

### 4. Configure Application URL

Edit `.env` and set:
- `APP_URL`: Your Monica site URL (use local IP for testing, domain for production)
- `MONICA_DOMAIN`: Your domain name for Traefik routing

### 5. Start the Application

```bash
docker compose up -d
```

### 6. Run Database Migrations

```bash
docker exec monica php artisan migrate --force
```

### 7. Access Monica

- **Local**: http://192.168.86.47:8098
- **HTTPS**: https://monica.server.unarmedpuppy.com (after DNS setup)
- **Homepage**: Listed under "Productivity & Organization" group

### 8. Create Your Account

1. Open your browser and navigate to your Monica URL
2. Click "Register" to create your first account
3. Complete the registration form
4. Start adding contacts and managing your relationships!

## Configuration

### Environment Variables

See `env.template` for all available configuration options.

**Required:**
- `DATABASE_ROOT_PASSWORD` - MySQL root password
- `DATABASE_PASSWORD` - MySQL user password
- `APP_KEY` - Laravel application key
- `APP_URL` - Your Monica site URL
- `MONICA_DOMAIN` - Domain name for Traefik

**Optional:**
- `MAIL_*` - Email configuration for notifications and reminders

### Database

Monica uses MySQL 8.0. The database is persisted in `./data/mysql/`.

### Storage

Monica data (uploads, photos, documents) is stored in `./data/storage/`.

## Features Overview

### Contact Management
- Add contacts with detailed information
- Track birthdays, anniversaries, and important dates
- Record how you met someone
- Add notes and reminders
- Manage addresses and contact methods

### Relationship Tracking
- Define relationships between contacts
- Track interactions and activities
- Record conversations and meetings
- Manage gifts and significant events

### Personal Organization
- Task management
- Daily diary entries
- Document and photo storage
- Custom activity types
- Multiple currencies support

## Updating Monica

To update to the latest version:

```bash
cd apps/monica
docker compose pull
docker compose up -d
docker exec monica php artisan migrate --force
```

## Troubleshooting

### Port Already in Use

If port 8098 conflicts, change it in `docker-compose.yml`:
```yaml
ports:
  - "8099:80"  # Change 8098 to your preferred port
```

### Database Connection Issues

Check database health:
```bash
docker compose logs monica-db
docker compose ps monica-db
```

### Application Key Issues

If you see encryption errors, regenerate the app key:
```bash
docker exec monica php artisan key:generate --force
```

### Migration Issues

If migrations fail, check logs:
```bash
docker compose logs monica | grep -i migration
```

Run migrations manually:
```bash
docker exec monica php artisan migrate --force
```

### First-Time Setup Issues

If you can't access the registration page:
1. Check container logs: `docker compose logs monica`
2. Verify database is healthy: `docker compose ps`
3. Ensure `APP_URL` matches your access URL
4. Run migrations: `docker exec monica php artisan migrate --force`

## Resources

- **GitHub**: https://github.com/monicahq/monica
- **Website**: https://www.monicahq.com
- **Documentation**: See repository README
- **License**: AGPL-3.0

## Privacy & Philosophy

Monica is designed with privacy in mind:
- **Not a social network**: It's for your eyes only
- **Your data, your server**: You're in complete control
- **No tracking**: Users are not tracked
- **Open source**: Transparent and auditable

## License

AGPL-3.0

