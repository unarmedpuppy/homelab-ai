---
name: update-homepage-groups
description: Update homepage service groups in docker-compose.yml files
when_to_use: After adding new services, reorganizing homepage categories, updating service metadata
script: scripts/update-homepage-groups.py
---

# Update Homepage Groups

Updates homepage service groups in docker-compose.yml files.

## When to Use

- After adding new services
- Reorganizing homepage categories
- Updating service metadata
- Maintaining homepage organization

## Usage

```bash
# On server or local
python3 scripts/update-homepage-groups.py
```

## What It Does

The script:
1. Scans all `apps/*/docker-compose.yml` files
2. Reads existing homepage labels
3. Updates service groups based on configuration
4. Maintains consistent homepage organization

## Homepage Groups

Services are organized into categories:
- **Infrastructure** - Core system services
- **Media & Entertainment** - Media servers and tools
- **Productivity & Organization** - Task management, notes
- **Development & Tools** - Development tools
- **Games** - Game servers

## Related Documentation

- `agents/reference/setup/HOMEPAGE_GROUPS.md` - Homepage organization guide
- `apps/homepage/` - Homepage configuration

## Related Tools

- `standard-deployment` - Deploy changes after updating

