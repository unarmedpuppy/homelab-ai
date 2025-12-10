# NewsBlur local settings
# Override default settings for self-hosted deployment

# Tell Django we're behind a reverse proxy that terminates SSL
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')

# Trust X-Forwarded-* headers from Traefik
USE_X_FORWARDED_HOST = True

# Site URL (must match django_site table)
NEWSBLUR_URL = "https://newsblur.server.unarmedpuppy.com"

# Note: "newsblur" subdomain was added to ALLOWED_SUBDOMAINS in
# /home/unarmedpuppy/NewsBlur/apps/reader/views.py on the server
