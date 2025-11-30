# Docker Compose Auto-Start Configuration

## Overview

The `docker-start.sh` script now supports enabling/disabling apps from auto-starting using the `x-enabled` label in docker-compose files.

## How It Works

The script checks each `docker-compose.yml` file for a top-level `x-enabled` field:
- If `x-enabled: true` → App will start automatically
- If `x-enabled: false` → App will be skipped
- If `x-enabled` is not specified → App will start (backward compatible)

## Adding the Label

Add the `x-enabled` field at the top level of your `docker-compose.yml` file:

```yaml
version: "3.8"

x-enabled: true  # Set to false to disable auto-start

services:
  my-service:
    image: my-image:latest
    # ... rest of your config
```

## Examples

### Enable an app (default behavior)
```yaml
version: "3.8"

x-enabled: true

services:
  app:
    image: myapp:latest
```

### Disable an app from auto-starting
```yaml
version: "3.8"

x-enabled: false

services:
  app:
    image: myapp:latest
```

### No label (backward compatible)
If you don't add `x-enabled`, the app will start by default (backward compatible with existing setup).

## Benefits

1. **No hardcoded exceptions**: No need to modify the script for each app
2. **Self-documenting**: Each compose file declares if it should auto-start
3. **Easy to manage**: Just set `x-enabled: false` to disable an app
4. **Backward compatible**: Existing compose files without the label will still work

## Migration

To disable an app from auto-starting:
1. Open the app's `docker-compose.yml` file
2. Add `x-enabled: false` at the top level (after `version:`)
3. Save the file

The script will automatically skip it on the next boot.

## Notes

- The `x-enabled` field uses Docker Compose's standard `x-` extension syntax for custom metadata
- This field is ignored by Docker Compose itself - it's only used by our startup script
- You can still manually start disabled apps with `docker-compose up -d`

