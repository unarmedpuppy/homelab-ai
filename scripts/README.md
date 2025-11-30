# Docker Startup Scripts

## docker-start.sh

Automatically starts all Docker Compose applications on server boot.

### Features

- **Label-based control**: Uses `x-enabled` label in docker-compose.yml files
- **Backward compatible**: Apps without the label will start by default
- **Easy management**: Just set `x-enabled: false` to disable an app

### Usage

The script runs automatically on boot. To run manually:

```bash
~/server/scripts/docker-start.sh
```

### Configuration

Add `x-enabled: true` or `x-enabled: false` to your docker-compose.yml:

```yaml
version: "3.8"

x-enabled: true  # or false to disable

services:
  my-app:
    # ... your config
```

### Examples

**Enable an app (default):**
```yaml
x-enabled: true
```

**Disable an app:**
```yaml
x-enabled: false
```

**No label (backward compatible):**
If you don't specify `x-enabled`, the app will start by default.

## docker-start-example.sh

Test script to see which apps would start without actually starting them.

### Usage

```bash
~/server/scripts/docker-start-example.sh
```

This will show you:
- ✅ Apps that are enabled (will start)
- ❌ Apps that are disabled (will be skipped)
- Apps without the label (default: enabled)

## See Also

- [Docker Compose Enabled Label Documentation](../docs/DOCKER_COMPOSE_ENABLED_LABEL.md)

