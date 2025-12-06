# Firefly III

Personal finance manager for tracking expenses, income, budgets, and financial goals.

## Access

- **URL**: https://firefly.server.unarmedpuppy.com
- **Port**: 8082 (direct access, optional)
- **Status**: ✅ ACTIVE

## Configuration

Firefly III requires an APP_KEY to be set. On first run, generate it using:

```bash
docker exec -it firefly-iii php artisan key:generate --show
```

Then update the `APP_KEY` environment variable in `docker-compose.yml` and restart:

```bash
cd apps/firefly-iii
docker compose down
docker compose up -d
```

## Initial Setup

1. Access the web interface at https://firefly.server.unarmedpuppy.com
2. Complete the initial setup wizard
3. Create your first account and start tracking finances

## Features

- Double-entry bookkeeping
- Budget management
- Recurring transactions
- Rule-based transaction handling
- Piggy banks (savings goals)
- Income and expense reports
- Multi-currency support
- REST API

## References

- [Official Documentation](https://docs.firefly-iii.org/)
- [GitHub Repository](https://github.com/firefly-iii/firefly-iii)
- [Docker Hub](https://hub.docker.com/r/fireflyiii/core)

