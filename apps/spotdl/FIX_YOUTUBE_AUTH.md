# Fix YouTube Authentication for SpotDL

SpotDL uses yt-dlp to download audio from YouTube. YouTube now requires authentication
to prevent bot detection. This guide explains how to fix it.

## The Problem

```
ERROR: Sign in to confirm you're not a bot. Use --cookies-from-browser or --cookies 
for the authentication.
```

## Solution: Export YouTube Cookies

### Step 1: Install Browser Extension

Install one of these extensions in Chrome/Firefox:
- **Chrome**: [Get cookies.txt LOCALLY](https://chrome.google.com/webstore/detail/get-cookiestxt-locally/cclelndahbckbenkjhflpdbgdldlbecc)
- **Firefox**: [cookies.txt](https://addons.mozilla.org/en-US/firefox/addon/cookies-txt/)

### Step 2: Export Cookies

1. Open YouTube in your browser
2. **Make sure you're logged in** to a Google account
3. Click the extension icon
4. Click "Export" or "Get cookies.txt"
5. Save the file as `cookies.txt`

### Step 3: Copy to Server

Copy the cookies file to the server:

```bash
# From your local machine
scp -P 4242 cookies.txt unarmedpuppy@192.168.86.47:~/server/apps/spotifydl/yt-dlp-config/cookies.txt
```

### Step 4: Update yt-dlp Config

The config file is at `~/server/apps/spotifydl/yt-dlp-config/config`. It should include:

```
--cookies
/root/.config/yt-dlp/cookies.txt
```

This is already configured - you just need to add the cookies.txt file.

### Step 5: Restart SpotDL

```bash
cd ~/server/apps/spotifydl
docker compose restart spotdl
```

### Step 6: Test

```bash
# Test yt-dlp directly
docker exec spotdl yt-dlp --cookies /root/.config/yt-dlp/cookies.txt \
    -f bestaudio 'https://www.youtube.com/watch?v=dQw4w9WgXcQ' --print title

# Test spotdl
docker exec spotdl uv run --project /app spotdl download \
    'https://open.spotify.com/track/4PTG3Z6ehGkBFwjybzWkR8' \
    --output '/music/test.mp3'
```

## Alternative: Use OAuth

Some users report success with YouTube OAuth instead of cookies:

```bash
docker exec -it spotdl yt-dlp --username oauth2 --password '' \
    'https://www.youtube.com/watch?v=dQw4w9WgXcQ'
```

This will open a browser-based OAuth flow.

## Troubleshooting

### Cookies expire quickly
YouTube cookies can expire. If downloads stop working:
1. Re-export fresh cookies from browser
2. Replace the cookies.txt file
3. Restart the container

### Still getting bot detection
Try:
1. Use a different Google account
2. Watch a few videos manually first
3. Don't run too many downloads too quickly (rate limiting)

### Use YouTube Music instead
SpotDL can use YouTube Music which sometimes has better luck:

```bash
docker exec spotdl uv run --project /app spotdl download URL --audio youtube-music
```

## References

- [yt-dlp FAQ: Cookies](https://github.com/yt-dlp/yt-dlp/wiki/FAQ#how-do-i-pass-cookies-to-yt-dlp)
- [yt-dlp: Exporting YouTube Cookies](https://github.com/yt-dlp/yt-dlp/wiki/Extractors#exporting-youtube-cookies)
