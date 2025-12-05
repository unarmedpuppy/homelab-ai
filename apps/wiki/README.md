# Wiki.js

A modern, powerful, and extensible wiki software built on Node.js. Perfect for documentation, knowledge bases, and team wikis.

**GitHub**: https://github.com/Requarks/wiki  
**Documentation**: https://docs.requarks.io/

## Features

- **Markdown Support**: Full Markdown editing with live preview
- **Git Integration**: Version control with Git backend
- **Rich Media**: Support for images, videos, and embedded content
- **Search**: Full-text search across all pages
- **Access Control**: User roles and permissions
- **Themes**: Customizable themes and styling
- **Extensions**: Extensible with modules and themes
- **Multi-language**: Internationalization support

## Access

- **Local**: http://192.168.86.47:3001
- **HTTPS**: https://wiki.server.unarmedpuppy.com
- **Homepage**: Listed under "Productivity & Organization"

## Initial Setup

1. **Access Wiki.js**: Navigate to http://192.168.86.47:3001 or https://wiki.server.unarmedpuppy.com
2. **Complete Setup Wizard**: 
   - Create admin account
   - Configure site settings
   - Set up storage (Git or Local)
3. **Start Creating**: Begin adding pages and organizing your wiki

## Configuration

### Environment Variables

Create a `.env` file from `env.template`:

```bash
cp env.template .env
# Edit .env and set WIKI_DB_PASSWORD
```

### Volumes

- `db-data` - PostgreSQL database data
- `content` - Wiki content files
- `uploads` - User-uploaded files (images, attachments)

### Database

Wiki.js uses PostgreSQL for data storage. The database is automatically configured via environment variables.

**Default Database Settings:**
- Database: `wiki`
- User: `wikijs`
- Password: Set via `WIKI_DB_PASSWORD` environment variable (default: `wikijsrocks`)

**⚠️ Important**: Change the default database password in production!

## Storage Backends

Wiki.js supports multiple storage backends:

### Local Storage (Default)
- Files stored in Docker volumes
- Simple setup, no additional configuration

### Git Storage
- Store wiki content in a Git repository
- Enables version control and backup via Git
- Configure in Wiki.js admin panel: Administration → Storage

## Usage

### Creating Pages

1. Click "Create Page" in the navigation
2. Use Markdown syntax for formatting
3. Add tags and organize in folders
4. Save and publish

### Managing Users

1. Go to Administration → Users
2. Create new users or invite via email
3. Assign roles (Admin, Editor, Viewer, etc.)

### Customization

- **Themes**: Change appearance in Administration → Rendering → Theme
- **Navigation**: Customize menu structure in Administration → Navigation
- **Modules**: Enable/disable features in Administration → Modules

## Backup

### Database Backup

```bash
# Backup PostgreSQL database
docker exec wiki-db pg_dump -U wikijs wiki > wiki_backup.sql

# Restore from backup
docker exec -i wiki-db psql -U wikijs wiki < wiki_backup.sql
```

### Content Backup

If using local storage, backup the volumes:

```bash
# Backup content volume
docker run --rm -v wiki_content:/data -v $(pwd):/backup alpine tar czf /backup/wiki-content-backup.tar.gz /data
```

### Git Storage Backup

If using Git storage, your content is already version-controlled. Simply push to your remote repository regularly.

## Troubleshooting

### Container Won't Start
- Check database connection: Ensure `db` service is running
- Verify environment variables are set correctly
- Check logs: `docker logs wiki`

### Database Connection Errors
- Verify `WIKI_DB_PASSWORD` matches in both services
- Ensure database container is healthy: `docker ps | grep wiki-db`
- Check network connectivity: Both services must be on `my-network`

### Permission Issues
- Ensure volumes have correct permissions
- Check container logs for file system errors

### Performance Issues
- Consider using Git storage for better performance with large wikis
- Monitor database size and optimize if needed
- Enable caching in Wiki.js settings

## Updating

```bash
# Pull latest images
docker compose pull

# Restart services
docker compose up -d

# Run migrations (automatic on startup)
```

## Documentation

- **Official Docs**: https://docs.requarks.io/
- **GitHub**: https://github.com/Requarks/wiki
- **Community**: https://community.requarks.io/

## Notes

- Default admin account is created during first-time setup
- Wiki content is stored in Docker volumes (persistent)
- For production, change default database password
- Consider setting up Git storage for version control and backup
- Wiki.js supports LDAP/OAuth authentication (configure in admin panel)

