# Alembic Database Migrations

This directory contains database migration scripts managed by [Alembic](https://alembic.sqlalchemy.org/).

## Running Migrations

The migrations will be automatically applied when the Docker container starts (see `docker-compose.yml` or startup script).

### Manual Migration Commands

```bash
# Check current version
alembic current

# Upgrade to latest version
alembic upgrade head

# Upgrade by one version
alembic upgrade +1

# Downgrade by one version
alembic downgrade -1

# Show migration history
alembic history

# Show SQL that would be executed (don't actually run)
alembic upgrade head --sql
```

## Creating New Migrations

```bash
# Create a new migration with auto-generated changes
alembic revision --autogenerate -m "Description of changes"

# Create a blank migration
alembic revision -m "Description of changes"
```

## Migration Files

- `001_add_conversation_metadata.py` - Adds username, source, and display_name columns to conversations table
- `002_add_api_keys_table.py` - Creates api_keys table for managing provider API keys

## Configuration

- `alembic.ini` - Main configuration file
- `env.py` - Environment configuration (loads database path from environment)
- `script.py.mako` - Template for new migration files

## Database Location

The database path is configured via the `DATABASE_PATH` environment variable (default: `/data/local-ai-router.db`).
