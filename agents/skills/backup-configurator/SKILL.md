---
name: backup-configurator
description: Interactive surgical backup selection tool for jenquist-cloud
when_to_use: When you need to selectively backup directories from jenquist-cloud to reduce B2 storage costs
script: scripts/backup-configurator.py
---

# Backup Configurator

Interactive TUI tool for creating surgical backup selections from jenquist-cloud to Backblaze B2.

## When to Use

Use this tool when:
- You want to reduce backup costs by selecting specific directories
- Current backup backs up entire `/jenquist-cloud` (~21TB) 
- You need to exclude certain directories or file types
- You want to create multiple backup profiles (personal vs media vs system)

## What It Does

1. **Scans Directory Structure**: Shows `/jenquist-cloud` with sizes
2. **Interactive Selection**: Browse and select directories to backup
3. **Exclude Patterns**: Configure file/folder exclusions
4. **Generate rclone Commands**: Creates optimized rclone commands
5. **Save Configurations**: Store backup profiles for reuse

## Usage

### Basic Usage
```bash
# Run interactively
python3 scripts/backup-configurator.py

# Specify custom base path
python3 scripts/backup-configurator.py --base-path /mnt/data

# Use different rclone remote
python3 scripts/backup-configurator.py --remote my-b2-remote:
```

### Interactive Workflow
1. **Directory Browser**: Shows jenquist-cloud structure with sizes
2. **Manual Path Entry**: Add specific paths relative to base
3. **Selection Management**: Add/remove selected paths
4. **Exclude Configuration**: Set patterns like `*.tmp`, `.DS_Store`
5. **Profile Saving**: Save configurations with custom names
6. **Command Generation**: Creates rclone commands with include files

### Generated Output
- **Include files**: `~/.rclone-include-{profile}.txt` with path patterns
- **rclone commands**: Optimized commands with proper flags
- **Dry-run support**: Test commands before execution
- **Cost estimates**: See selected paths and estimated sizes

## Features

### Directory Selection
- Browse `/jenquist-cloud` structure interactively
- View directory sizes using `du` command
- Select/deselect individual directories
- Multi-select support for batch operations

### rclone Integration
- Uses existing `b2-encrypted:` remote configuration
- Generates include/exclude file patterns
- Maintains current performance settings (`--transfers 4`, `--checkers 8`)
- Supports `--dry-run` for testing

### Configuration Management
- Save multiple backup profiles
- Store as JSON in `~/.backup-configs.json`
- Load existing configurations on startup
- Priority levels (high/medium/low) for future scheduling

### Exclude Patterns
Default excludes:
- `*.tmp`, `*.temp` - Temporary files
- `.DS_Store`, `Thumbs.db` - System files  
- `.cache/`, `tmp/`, `temp/` - Cache directories
- `.Trash/` - Trash directories

## Examples

### Personal Media Only Backup
```bash
python3 scripts/backup-configurator.py
# Select: archive/personal-media
# Save as: "personal-media-backup"
```

### Exclude Large Media Files
```bash
# Configure excludes: *.mkv, *.iso, downloads/
# Backup documents and photos but not large video files
```

### Multiple Backup Profiles
```bash
# Profile 1: Personal media (high priority)
# Profile 2: Entertainment media (medium priority)  
# Profile 3: System configs (low priority)
```

## Generated rclone Commands

The tool generates commands like:
```bash
rclone sync /jenquist-cloud b2-encrypted: \
    --include-from ~/.rclone-include-backup.txt \
    --exclude "*.tmp" \
    --exclude "*.temp" \
    --exclude ".DS_Store" \
    --transfers 4 \
    --checkers 8 \
    --progress \
    --stats 1m \
    --stats-one-line
```

## Cost Savings

Typical savings with selective backup:
- **Full backup**: ~21TB (entire jenquist-cloud)
- **Personal media only**: ~2TB (photos, documents)
- **System configs only**: ~50GB (configs, scripts)
- **Cost reduction**: 90%+ savings with selective backup

## Files Created

- **Configuration**: `~/.backup-configs.json` - Saved backup profiles
- **Include files**: `~/.rclone-include-{profile}.txt` - rclone path patterns
- **Logs**: Generated rclone commands and dry-run output

## Integration

The tool integrates with existing:
- **rclone configuration**: Uses your existing `b2-encrypted:` remote
- **backup-to-b2.sh**: Can be called from generated commands
- **encryption**: Maintains existing AES-256 encryption setup

## Tips

1. **Start Small**: Select critical directories first, test backup
2. **Use Dry-Run**: Always test with `--dry-run` before full backup
3. **Monitor Costs**: Check B2 dashboard after backup to verify savings
4. **Profile Organization**: Use descriptive names like "personal-photos-2024"
5. **Regular Reviews**: Periodically review and update backup selections

## Troubleshooting

### Permission Issues
- Run with `sudo` if directory access denied
- Check file permissions on target directories
- Use `chmod` if needed for script execution

### rclone Issues
- Verify `rclone config show b2-encrypted:` works
- Test remote connectivity: `rclone lsd b2-encrypted:`
- Check B2 credentials in 1Password if auth fails

### Python Dependencies
```bash
# For enhanced UI (optional)
pip install rich

# Basic requirements only
python3 - standard library only
```

## Related Tools

- **manage-b2-backup**: Monitor and manage B2 backups
- **backup-to-b2.sh**: Current full backup script
- **check-backup-health**: Validate backup integrity