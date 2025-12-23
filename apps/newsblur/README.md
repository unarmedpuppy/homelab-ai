# NewsBlur

Personal news reader with intelligence - RSS feed reader and social news network.

## Access

- **URL**: https://newsblur.server.unarmedpuppy.com
- **Port**: 8001 (direct access, optional)
- **Status**: ✅ ACTIVE

## Setup

NewsBlur requires building from source. Follow these steps:

### 1. Clone NewsBlur Repository

```bash
cd /path/to/home-server
git clone https://github.com/samuelclay/NewsBlur.git ../NewsBlur
```

### 2. Update docker-compose.yml

Edit `apps/newsblur/docker-compose.yml` and:
- Comment out the `image: newsblur/newsblur:latest` line
- Uncomment the `build:` section

### 3. Build and Start

```bash
cd apps/newsblur
docker compose build
docker compose up -d
```

### 4. Initialize Database

```bash
docker compose exec newsblur-web python manage.py migrate
docker compose exec newsblur-web python manage.py create_superuser
```

## Configuration

NewsBlur is configured via environment variables in `docker-compose.yml`:

- `NEWSBLUR_URL` - Your domain (https://newsblur.server.unarmedpuppy.com)
- `SESSION_COOKIE_DOMAIN` - Cookie domain
- `AUTO_PREMIUM` - Give new users premium features (True)
- `AUTO_ENABLE_NEW_USERS` - Auto-activate new accounts (True)
- `ENFORCE_SIGNUP_CAPTCHA` - Require captcha on signup (False)

For additional configuration, create `newsblur_web/local_settings.py` to override settings.

## Services

- **newsblur-web** - Django web application (port 8000)
- **postgres** - PostgreSQL database for relational data
- **mongodb** - MongoDB for stories and read states
- **redis** - Redis for story assembly and caching

## References

- [Official Documentation](https://github.com/samuelclay/NewsBlur)
- [GitHub Repository](https://github.com/samuelclay/NewsBlur)
- [Self-Hosted Guide](https://github.com/samuelclay/NewsBlur#self-hosted-installation)


