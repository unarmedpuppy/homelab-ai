# Habitica

Gamified habit tracker and task manager that treats your goals like a Role Playing Game.

## Access

- **URL**: https://habitica.server.unarmedpuppy.com
- **Port**: 3007 (direct access, optional)
- **Status**: ✅ ACTIVE

## Setup

1. Copy the example config file:
   ```bash
   cp config.json.example config.json
   ```

2. Edit `config.json` if needed (defaults should work)

3. Build and start the containers:
   ```bash
   docker compose up -d --build
   ```

## Initial Setup

1. Access the web interface at https://habitica.server.unarmedpuppy.com
2. Create your first account
3. Start tracking habits and completing tasks!

## Features

- Gamified task management (RPG-style)
- Habit tracking with rewards
- Daily tasks and to-dos
- Character progression (level up, earn gold)
- Social features (parties, guilds)
- Mobile app support (may require configuration for self-hosted)

## Configuration

The application uses `config.json` for configuration. Key settings:

- `host.url`: Base URL for the application
- `database.url`: MongoDB connection string
- `mail.enabled`: Email notifications (set to `true` and configure SMTP if needed)
- `inviteOnly`: Whether registration requires an invite

## References

- [Official Repository](https://github.com/HabitRPG/habitica)
- [Habitica Wiki](https://habitica.fandom.com/wiki/Habitica_Wiki)
- [Setting up Habitica Locally](https://habitica.fandom.com/wiki/Setting_up_Habitica_Locally)

## Notes

- The first build may take several minutes as it clones the repository and builds the application
- MongoDB replica set is automatically initialized
- Mobile apps may require additional configuration to connect to self-hosted instances

