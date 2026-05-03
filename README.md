# Homelab AI Dashboard

A centralized dashboard for monitoring and managing AI-related infrastructure and cron jobs in the homelab.

## Overview

This dashboard provides:
- **Cron Job Monitoring**: Track all scheduled tasks, their status, and execution history
- **System Status**: Monitor AI services, databases, and other infrastructure
- **Documentation**: Quick access to runbooks and configuration guides
- **Alerts**: Real-time notifications for critical events

## Components

### Cron Jobs
View and monitor all active cron jobs across the homelab:
- Job status (running, paused, failed)
- Last execution time
- Next scheduled run
- Execution logs
- Documentation links

## Infrastructure

- **Server**: `server.unarmedpuppy.com`
- **Dashboard URL**: `https://dashboard.unarmedpuppy.com` (TODO: configure)
- **Git Repository**: `ssh://gitea.server.unarmedpuppy.com:2223/homelab/homelab-ai.git`

## Getting Started

1. Clone the repository:
   ```bash
   git clone ssh://gitea.server.unarmedpuppy.com:2223/homelab/homelab-ai.git
   ```

2. Deploy the dashboard:
   ```bash
   cd homelab-ai
   ./deploy/deploy.sh
   ```

3. Access the dashboard at `http://localhost:3000` (or configured URL)

## Quick Links

- [Cron Jobs Documentation](docs/cron-jobs/)
- [System Configuration](docs/configuration/)
- [Runbooks](docs/runbooks/)

## Contributing

See the [CONTRIBUTING](CONTRIBUTING.md) guide.

## License

MIT License - See [LICENSE](LICENSE) for details.
