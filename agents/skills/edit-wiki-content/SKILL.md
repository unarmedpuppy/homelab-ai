---
name: edit-wiki-content
description: Programmatically create and update Wiki.js pages using the API tool
when_to_use: Adding documentation to the wiki, updating existing wiki pages, bulk content updates, automating wiki maintenance, creating structured documentation
---

# Edit Wiki.js Content

Programmatically create and update Wiki.js pages using the API tool.

## When to Use

- Adding documentation to the wiki
- Updating existing wiki pages
- Bulk content updates
- Automating wiki maintenance
- Creating structured documentation

## Prerequisites

- Wiki.js API key configured in `apps/wiki/.env`
- Python 3 with `requests` and `python-dotenv` installed
- Access to the Wiki.js instance (http://192.168.86.47:3001)

## Steps

### 1. Verify API Key

The API key is stored in `apps/wiki/.env`:

```bash
cd apps/wiki
cat .env | grep WIKI_API_KEY
```

**Note**: The API key expires December 4, 2028. Generate a new one in Wiki.js admin panel if needed.

### 2. Prepare Content

Create or edit your markdown content file:

```bash
# Edit existing content
vim apps/wiki/homepage-content.md

# Or create new content
cat > apps/wiki/new-page.md << EOF
# New Page Title

Your markdown content here...
EOF
```

### 3. Use the API Tool

The tool is located at `apps/wiki/edit-wiki.py`:

```bash
cd apps/wiki
```

#### Create a New Page

```bash
python3 edit-wiki.py create \
  --path "/page-path" \
  --title "Page Title" \
  --content "content-file.md" \
  --description "Page description"
```

#### Update Existing Page

```bash
python3 edit-wiki.py update \
  --path "/page-path" \
  --content "updated-content.md"
```

#### Get Page Content

```bash
python3 edit-wiki.py get --path "/page-path"
```

#### Trigger Page Rendering

```bash
python3 edit-wiki.py render --path "/page-path"
```

### 4. Examples

#### Create Homepage

```bash
cd apps/wiki
python3 edit-wiki.py create \
  --path "/home" \
  --title "Home Server Overview" \
  --content "homepage-content.md" \
  --description "Overview of the home server infrastructure"
```

#### Update Documentation Page

```bash
python3 edit-wiki.py update \
  --path "/documentation/server-setup" \
  --content "server-setup.md" \
  --title "Server Setup Guide"
```

#### Create Nested Page

```bash
python3 edit-wiki.py create \
  --path "/documentation/apps/plex" \
  --title "Plex Configuration" \
  --content "plex-config.md"
```

## Tool Reference

**Location**: `apps/wiki/edit-wiki.py`

**Environment Variables** (from `.env`):
- `WIKI_API_KEY` - API authentication token
- `WIKI_URL` - Wiki.js URL (default: http://192.168.86.47:3001)
- `WIKI_HTTPS_URL` - HTTPS URL (default: https://wiki.server.unarmedpuppy.com)

**Available Actions**:
- `create` - Create a new page
- `update` - Update existing page
- `get` - Retrieve page content
- `render` - Trigger page rendering

## Common Issues

### API Authentication Error

**Problem**: `401 Unauthorized` or authentication failures

**Solution**:
1. Verify API key in `apps/wiki/.env`
2. Check key hasn't expired (current expires: Dec 4, 2028)
3. Regenerate key in Wiki.js admin: Administration → System → API Access

### Page Not Found

**Problem**: `Page not found at path: /path`

**Solution**:
- Use `get` action to verify page exists
- Check path format (must start with `/`)
- Ensure locale matches (default: `en`)

### GraphQL Errors

**Problem**: `400 Bad Request` or GraphQL validation errors

**Solution**:
- Verify Wiki.js API format hasn't changed
- Check Wiki.js version compatibility
- Review GraphQL mutation syntax in script

### Content Not Rendering

**Problem**: Page created but shows "no rendered version"

**Solution**:
```bash
# Trigger rendering manually
python3 edit-wiki.py render --path "/page-path"
```

## Manual Alternative

If the API tool isn't working, you can manually edit:

1. Log in to Wiki.js: http://192.168.86.47:3001/login
2. Navigate to the page
3. Click "Edit"
4. Paste content from markdown file
5. Save

**Login Credentials**:
- Email: `admin@unarmedpuppy.com`
- Password: Check server documentation or reset if needed

## Related Files

- **Script**: `apps/wiki/edit-wiki.py`
- **Config**: `apps/wiki/.env` (contains API key)
- **Content**: `apps/wiki/homepage-content.md` (example content)
- **Docs**: `apps/wiki/README.md` (full documentation)

## Notes

- API key is stored in `.env` and excluded from git (via `.gitignore`)
- All paths must start with `/`
- Content files should be UTF-8 encoded
- Markdown syntax is supported
- Pages are created in English locale by default (use `--locale` to change)

