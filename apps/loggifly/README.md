# LoggiFly

A lightweight tool that monitors Docker container logs for predefined keywords or regex patterns and sends notifications.

## Description

LoggiFly monitors your Docker container logs in real-time, detecting security breaches, system errors, or custom patterns, and sends instant alerts through your favorite notification channels (Ntfy, Apprise, Slack, Discord, Telegram, etc.).

## Features

- 🔍 **Plain Text, Regex & Multi-Line Log Detection**: Catch simple keywords or complex patterns in log entries
- 🚨 **Ntfy/Apprise Alerts**: Send notifications to 100+ different services
- 🔁 **Trigger Stop/Restart**: Automatically restart or stop containers on critical keywords
- 📁 **Log Attachments**: Automatically include log context in notifications
- ⚡ **Automatic Reload**: Automatically reloads config when `config.yaml` changes
- 📝 **Configurable Alerts**: Filter log lines and use templates for messages
- 🌐 **Remote Hosts**: Connect to multiple remote Docker hosts
- 🐳 **Multi-Platform**: Runs on Docker, Docker Swarm, and Podman

## Use Cases

- ✅ Catching security breaches (e.g., failed logins in Vaultwarden)
- ✅ Debugging crashes with attached log context
- ✅ Restarting containers on specific errors
- ✅ Stopping containers to avoid restart loops
- ✅ Monitoring custom app behaviors

## Setup

1. Create the config directory:
   ```bash
   mkdir -p config
   ```

2. Create `config/config.yaml` with your monitoring rules. Example:
   ```yaml
   containers:
     - name: vaultwarden
       patterns:
         - keyword: "Invalid master password"
           notify: true
           title: "Vaultwarden Security Alert"
           message: "Failed login attempt detected"
     - name: plex
       patterns:
         - regex: "ERROR|FATAL"
           notify: true
           restart: false
   ```

3. Start the service:
   ```bash
   docker compose up -d
   ```

## Configuration

LoggiFly uses a `config.yaml` file in the `./config` directory. See the [official documentation](https://clemcer.github.io/LoggiFly/guide/config-structure.html) for complete configuration options.

### Key Configuration Options

- **Containers**: List of containers to monitor
- **Patterns**: Keywords or regex patterns to detect
- **Notifications**: Configure Ntfy, Apprise, or custom endpoints
- **Actions**: Restart or stop containers on specific patterns
- **Templates**: Customize notification messages

## Notification Services

LoggiFly supports notifications via:
- **Ntfy**: Simple push notifications
- **Apprise**: 100+ notification services including:
  - Slack
  - Discord
  - Telegram
  - Email
  - Custom webhooks
  - And many more...

## Notes

- Requires access to Docker socket (`/var/run/docker.sock`)
- All processing happens in the container
- Config file is automatically reloaded when changed
- Perfect for monitoring security events and system errors

## References

- [GitHub Repository](https://github.com/clemcer/LoggiFly)
- [Documentation](https://clemcer.github.io/LoggiFly/)
- [Configuration Guide](https://clemcer.github.io/LoggiFly/guide/config-structure.html)

