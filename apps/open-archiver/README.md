# OpenArchiver

**Secure Email Archiving Platform**

OpenArchiver is a secure, sovereign, and open-source platform for email archiving. It provides a robust, self-hosted solution for archiving, storing, indexing, and searching emails from major platforms.

## Features

- **Universal Ingestion**: Connect to any email provider
  - IMAP connection
  - Google Workspace
  - Microsoft 365
  - PST files
  - Zipped .eml files
  - Mbox files
- **Secure Storage**: Emails stored in `.eml` format with deduplication and compression
- **Encryption**: All files encrypted at rest
- **Powerful Search**: Full-text search across emails and attachments (PDF, DOCX, etc.)
- **Thread Discovery**: Automatically discover email threads and conversations
- **Compliance & Retention**: Granular retention policies and legal holds
- **File Integrity**: Hash verification ensures tamper-proof archives
- **Comprehensive Auditing**: Immutable audit trail of all system activities

## Quick Start

### 1. Clone the Repository

```bash
cd apps/open-archiver
git clone https://github.com/LogicLabs-OU/OpenArchiver.git open-archiver-repo
```

### 2. Setup Environment

```bash
cp env.template .env
```

### 3. Generate Secrets

```bash
# Generate database password
echo "POSTGRES_PASSWORD=$(openssl rand -hex 32)" >> .env

# Generate Meilisearch master key
echo "MEILI_MASTER_KEY=$(openssl rand -hex 32)" >> .env

# Generate JWT secret
echo "JWT_SECRET=$(openssl rand -hex 32)" >> .env

# Generate encryption key
echo "ENCRYPTION_KEY=$(openssl rand -hex 32)" >> .env
```

### 4. Configure Application URL

Edit `.env` and set:
- `APP_URL`: Your OpenArchiver site URL (use local IP for testing, domain for production)
- `OPEN_ARCHIVER_DOMAIN`: Your domain name for Traefik routing

### 5. Start the Application

```bash
docker compose up -d --build
```

### 6. Access OpenArchiver

- **Local**: http://192.168.86.47:8099
- **HTTPS**: https://archive.server.unarmedpuppy.com (after DNS setup)
- **Homepage**: Listed under "Productivity & Organization" group

### 7. Initial Setup

1. Open your browser and navigate to your OpenArchiver URL
2. Create your admin account
3. Configure email ingestion sources (Google Workspace, Microsoft 365, IMAP, etc.)
4. Start archiving emails!

## Configuration

### Environment Variables

See `env.template` for all available configuration options.

**Required:**
- `POSTGRES_PASSWORD` - PostgreSQL database password
- `MEILI_MASTER_KEY` - Meilisearch master key
- `JWT_SECRET` - JWT token secret
- `ENCRYPTION_KEY` - Encryption key for data at rest
- `APP_URL` - Your OpenArchiver site URL
- `OPEN_ARCHIVER_DOMAIN` - Domain name for Traefik

**Optional:**
- `STORAGE_TYPE` - Storage backend (local or s3)
- `S3_*` - S3-compatible storage configuration
- `SMTP_*` - Email notification configuration

### Services

OpenArchiver consists of:
- **Frontend**: SvelteKit application (port 3000)
- **Backend**: Node.js/Express API
- **PostgreSQL**: Metadata and audit logs
- **Meilisearch**: Full-text search engine
- **Redis/Valkey**: Job queue for async processing

### Data Persistence

Data is stored in:
- `./data/postgres/` - PostgreSQL database
- `./data/redis/` - Redis/Valkey data
- `./data/meilisearch/` - Meilisearch index data
- `./data/storage/` - Archived email files

## Email Ingestion

After deployment, configure one or more ingestion sources:

- **Google Workspace**: OAuth-based connection
- **Microsoft 365**: OAuth-based connection
- **IMAP**: Generic IMAP server connection
- **PST Files**: Upload and import PST files
- **EML Files**: Upload zipped .eml files
- **Mbox Files**: Import Mbox format archives

## Updating OpenArchiver

To update to the latest version:

```bash
cd apps/open-archiver
cd open-archiver-repo
git pull origin main
cd ..
docker compose up -d --build
```

## Troubleshooting

### Port Already in Use

If port 8099 conflicts, change it in `docker-compose.yml`:
```yaml
ports:
  - "8100:3000"  # Change 8099 to your preferred port
```

### Database Connection Issues

Check database health:
```bash
docker compose logs open-archiver-db
docker compose ps open-archiver-db
```

### Search Not Working

Check Meilisearch health:
```bash
docker compose logs open-archiver-meilisearch
docker compose ps open-archiver-meilisearch
```

### Build Issues

If the build fails, ensure you have cloned the repository:
```bash
cd apps/open-archiver
git clone https://github.com/LogicLabs-OU/OpenArchiver.git open-archiver-repo
```

## Resources

- **GitHub**: https://github.com/LogicLabs-OU/OpenArchiver
- **Website**: https://openarchiver.com
- **Live Demo**: https://demo.openarchiver.com
- **License**: AGPL-3.0

## License

AGPL-3.0

