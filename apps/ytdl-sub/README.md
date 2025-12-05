# ytdl-sub

Automated media downloading and metadata generation with yt-dlp. Downloads YouTube channels, playlists, SoundCloud discographies, and more, then formats them for your media server (Plex, Jellyfin, Kodi, Emby).

**GitHub**: https://github.com/jmbannon/ytdl-sub

## Features

- **YouTube Channels as TV Shows**: Organize YouTube content into TV show format
- **Music Videos & Concerts**: Download and format for music video libraries
- **SoundCloud & Bandcamp Discographies**: Full discography downloads with proper tags
- **Automatic Metadata**: Generates NFO files, thumbnails, and proper file organization
- **Web-GUI**: Code-server interface for easy configuration and management

## Access

- **CLI**: Access via SSH and run `docker exec -it ytdl-sub ytdl-sub <command>`
- **Homepage**: Listed under "Media & Entertainment" (links to documentation)
- **Note**: This setup uses the headless image. For Web-GUI, see [Docker Installation Docs](https://ytdl-sub.readthedocs.io/en/latest/guides/install/docker.html)

## Configuration

### Initial Setup

1. **Create Subscriptions File**: Create `subscriptions.yaml` in the `subscriptions/` directory
2. **Configure Presets**: Use prebuilt presets or create custom configs
3. **Run Downloads**: Execute via SSH or schedule with cron

### Directory Structure

```
ytdl-sub/
├── config/              # ytdl-sub configuration files
│   └── config.yaml      # Main config (auto-created)
├── subscriptions/       # Subscription YAML files
│   └── subscriptions.yaml
└── output/              # Downloaded media (mapped to media path)
```

### Example Subscription File

Create `subscriptions/subscriptions.yaml`:

```yaml
# subscriptions.yaml
__preset__:
  overrides:
    # Root folder of all ytdl-sub TV Shows
    tv_show_directory: "/output/tv_shows"
    
    # Root folder of all ytdl-sub Music
    music_directory: "/output/music"
    
    # Root folder of all ytdl-sub Music Videos
    music_video_directory: "/output/music_videos"
    
    # Only keep recent videos
    only_recent_date_range: "2months"
    only_recent_max_files: 30

# TV Show Presets
Plex TV Show by Date:
  = Documentaries:
    "NOVA PBS": "https://www.youtube.com/@novapbs"
    "National Geographic": "https://www.youtube.com/@NatGeo"

  = Kids | = TV-Y:
    "Jake Trains": "https://www.youtube.com/@JakeTrains"

# Music Presets
YouTube Releases:
  = Jazz:
    "Thelonious Monk": "https://www.youtube.com/@theloniousmonk3870/releases"

SoundCloud Discography:
  = Chill Hop:
    "UKNOWY": "https://soundcloud.com/uknowymunich"
```

### Running Downloads

Via SSH or docker exec:

```bash
# Run all subscriptions
docker exec -it ytdl-sub ytdl-sub sub subscriptions/subscriptions.yaml

# Dry run (test without downloading)
docker exec -it ytdl-sub ytdl-sub sub subscriptions/subscriptions.yaml --dry-run

# Download specific subscription
docker exec -it ytdl-sub ytdl-sub sub subscriptions/subscriptions.yaml --match "NOVA PBS"
```

### Automation (Cron)

To automate downloads, add a cron job on the host or use the container's scheduling:

```bash
# Add to host crontab (runs daily at 2 AM)
0 2 * * * docker exec ytdl-sub ytdl-sub sub /subscriptions/subscriptions.yaml
```

## Integration with Media Servers

### Plex
- TV Shows: Automatically organized into seasons by date
- Music: Properly tagged with metadata
- Music Videos: Organized by artist

### Jellyfin
- Same structure as Plex
- NFO files automatically recognized

### Kodi
- Compatible with Kodi's TV show and music video formats

## Presets

ytdl-sub comes with many prebuilt presets:
- `Plex TV Show by Date` - Organize YouTube channels as TV shows
- `Plex Music Videos` - Music video library format
- `YouTube Releases` - Music releases
- `SoundCloud Discography` - Full SoundCloud artist downloads
- `Bandcamp` - Bandcamp album downloads

See [ytdl-sub documentation](https://ytdl-sub.readthedocs.io/) for all available presets and customization options.

## Volumes

- `./config` - Configuration files (auto-created on first run)
- `./subscriptions` - Subscription YAML files
- `/output` - Downloaded media (mapped to server media path: `/jenquist-cloud/archive/entertainment-media`)

## Environment Variables

- `TZ` - Timezone (America/New_York)
- `PUID` - User ID (1000)
- `PGID` - Group ID (1000)

## Troubleshooting

### Downloads Not Starting
- Check subscription YAML syntax
- Verify URLs are accessible
- Check disk space in output directory

### Metadata Not Generating
- Ensure proper preset is selected
- Check config.yaml for metadata settings
- Verify output directory permissions

### Container Issues
- Check container logs: `docker logs ytdl-sub`
- Verify container is running: `docker ps | grep ytdl-sub`
- Check volume permissions: Ensure PUID/PGID match your user

## Documentation

- **Official Docs**: https://ytdl-sub.readthedocs.io/
- **GitHub**: https://github.com/jmbannon/ytdl-sub
- **Example Configs**: https://github.com/jmbannon/ytdl-sub/tree/master/examples

## Notes

- Downloads are stored in the server's media path (`/jenquist-cloud/archive/entertainment-media`)
- Subscriptions can be updated and re-run to sync new content
- Use `--dry-run` to test configurations before downloading
- For Web-GUI version, see the [official Docker installation guide](https://ytdl-sub.readthedocs.io/en/latest/guides/install/docker.html)
- All commands must be run via `docker exec` or SSH into the server

