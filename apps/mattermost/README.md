# Mattermost

Team collaboration and chat platform - open-source alternative to Slack.

## Access

- **URL**: https://mattermost.server.unarmedpuppy.com
- **Port**: 8065 (direct access, optional)
- **Status**: ✅ ACTIVE

## Description

Mattermost is an open-source, self-hosted team collaboration platform that provides secure messaging, file sharing, and team communication. It's a powerful alternative to Slack with features like channels, direct messages, file sharing, and integrations.

## Features

- 💬 Team messaging and channels
- 📁 File sharing and attachments
- 🔍 Search functionality
- 🔌 Integrations and webhooks
- 📱 Mobile and desktop apps
- 🔒 End-to-end encryption options
- 👥 User management and permissions
- 🎨 Customizable themes and branding
- 📊 Analytics and reporting
- 🔐 LDAP/AD integration
- 🔑 SSO support (SAML, OAuth, OpenID Connect)

## Architecture

This deployment includes:
- **Mattermost Server**: Main application (port 8065)
- **PostgreSQL**: Database for storing messages, users, and data
- **Redis**: Session cache and performance optimization

## Configuration

### Initial Setup

1. Access the web interface at `https://mattermost.server.unarmedpuppy.com`
2. Create the first admin account
3. Configure system settings as needed

### Environment Variables

Key configuration options (set in docker-compose.yml):
- `MM_SERVICESETTINGS_SITEURL`: Public URL of your Mattermost instance
- `MM_SQLSETTINGS_DATASOURCE`: PostgreSQL connection string
- `MM_SERVICESETTINGS_SESSIONCACHEREDISURL`: Redis connection for session cache

### Data Persistence

All data is stored in Docker volumes:
- `mattermost-db-data`: PostgreSQL database
- `mattermost-redis-data`: Redis cache data
- `./data`: Mattermost application data
- `./config`: Configuration files
- `./logs`: Log files
- `./plugins`: Custom plugins
- `./bleve-indexes`: Search indexes

## Notes

- **Database**: Uses PostgreSQL 14 (internal, not exposed)
- **Redis**: Used for session caching and performance (internal, not exposed)
- **Port**: Default Mattermost port 8065
- **Collaboration**: Real-time messaging with WebSocket support
- **Mobile Apps**: Available for iOS and Android
- **Desktop Apps**: Available for Windows, macOS, and Linux

## References

- [GitHub Repository](https://github.com/mattermost/mattermost)
- [Official Website](https://mattermost.com)
- [Documentation](https://docs.mattermost.com)
- [Deployment Guide](https://docs.mattermost.com/deployment-guide/deployment-guide-index.html)


