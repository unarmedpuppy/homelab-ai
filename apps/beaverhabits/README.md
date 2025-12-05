# Beaver Habits

A self-hosted habit tracking app without "Goals" - inspired by Loop Habit Tracker.

## Description

Beaver Habits is a simple, goal-free habit tracking application that focuses on tracking daily habits without the pressure of goals or targets. It provides a clean interface for marking habits as done each day.

## Features

- Simple habit tracking without goals
- Daily habit marking
- Streak tracking
- Self-hosted and privacy-focused
- iOS standalone app support
- Clean, minimal interface

## Access

- **Local**: `http://192.168.86.47:8096`
- **HTTPS**: `https://beaverhabits.server.unarmedpuppy.com`

## Configuration

### Environment Variables

- `HABITS_STORAGE=USER_DISK` - Stores habits in local JSON files (alternative: `DATABASE` for SQLite)
- `TRUSTED_LOCAL_EMAIL` - (Optional) Skip authentication for this email
- `INDEX_HABIT_DATE_COLUMNS=5` - Number of date columns shown on index page
- `ENABLE_IOS_STANDALONE=true` - Enable iOS standalone app mode

### Volumes

- `./data:/app/.user/` - Stores habit data and configuration

## Setup

1. Create data directory:
   ```bash
   mkdir -p data
   ```

2. Start the service:
   ```bash
   docker compose up -d
   ```

3. Access at `http://192.168.86.47:8096` or via Traefik at `https://beaverhabits.server.unarmedpuppy.com`

## Notes

- The container runs as user `1000:1000` for proper file permissions
- Data is stored in `./data` directory
- For authentication bypass, set `TRUSTED_LOCAL_EMAIL` in an `.env` file (not committed to git)

## References

- [GitHub Repository](https://github.com/daya0576/beaverhabits)
- [Demo](https://beaverhabits.com/demo)

