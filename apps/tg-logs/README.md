# Telegram Logs Scraper

A Docker-based Telegram channel scraper with web viewer interface.

## Features

- **Multi-Channel Support**: Scrape multiple Telegram channels simultaneously
- **Channel Management**: Web interface with channel listing and filtering
- **Telegram Scraping**: Uses Telethon to fetch messages and media from Telegram channels
- **Database Storage**: SQLite database for messages, media metadata, and channel information
- **Web Viewer**: FastAPI-based web interface with search, pagination, and media display
- **Tabbed Interface**: Switch between channels with a clean tabbed UI
- **Docker Support**: Containerized setup for easy deployment
- **Error Handling**: Robust error handling with logging and rate limit management

## Setup

### 1. Get Telegram API Credentials

1. Go to https://my.telegram.org/apps
2. Create a new application
3. Note down your `API_ID` and `API_HASH`

### 2. Configure Environment

1. Copy the environment template:
   ```bash
   cp env.template .env
   ```

2. Edit `.env` with your credentials:
   ```bash
   API_ID=your_api_id_here
   API_HASH=your_api_hash_here
   CHANNELS=@channel1,@channel2,-1001234567890
   SESSION_NAME=scraper
   ```

### 3. Find Your Channel Name/ID

#### Option A: Use the Helper Script (Recommended)
```bash
# First, set your API credentials in .env
# Then run the channel finder
python find_channel.py
```

This will show all channels and groups you have access to with their usernames or IDs.

#### Option B: Manual Methods

**For Public Channels:**
- Use the username: `@channel_name`
- Example: `@durov`, `@telegram`

**For Private Channels:**
- Open the channel in Telegram
- Look at the URL: `t.me/c/1234567890/123`
- Use the ID with `-100` prefix: `-1001234567890`

**For Multiple Channels:**
- Separate with commas: `@channel1,@channel2,-1001234567890`

#### Option C: Test Channel Access
```bash
# Test if your channel configuration works
python test_channel.py
```

### 4. Run with Docker Compose

```bash
# Start both scraper and viewer
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

### 5. Access the Web Interface

Open your browser to `http://localhost:8050` to view the scraped messages.

- **Channel Overview**: Visit `/channels` to see all scraped channels
- **Message Browser**: Visit `/messages` to browse messages with channel filtering
- **Channel Filtering**: Use the dropdown to filter messages by specific channels

## Usage

### First Run

On first run, you'll need to authenticate with Telegram:
1. The scraper will prompt for your phone number
2. Enter the verification code sent to your phone
3. If 2FA is enabled, enter your password

### Scraping

The scraper will:
- Start from the last scraped message (incremental updates)
- Download photos and image documents
- Store message metadata in SQLite
- Handle rate limits automatically

### Web Viewer

The web interface provides:
- **Channel Management**: View all scraped channels with statistics
- **Channel Filtering**: Filter messages by specific channels
- **Search**: Full-text search across messages
- **Media Filtering**: Show only messages with media
- **Pagination**: Navigate through large message sets
- **Sorting**: Newest or oldest first
- **Media Display**: View downloaded images

## File Structure

```
tg-logs/
├── scraper.py              # Main scraper script (multi-channel)
├── find_channel.py         # Helper script to find channels
├── test_channel.py         # Helper script to test channel access
├── docker-compose.yml      # Docker services configuration
├── Dockerfile             # Scraper container
├── requirements.txt       # Python dependencies
├── env.template          # Environment variables template
├── viewer/               # Web viewer application
│   ├── app/
│   │   ├── main.py       # FastAPI application (multi-channel)
│   │   └── templates/
│   │       ├── index.html    # Messages interface
│   │       └── channels.html # Channel overview
│   ├── Dockerfile        # Viewer container
│   └── requirements.txt  # Viewer dependencies
└── data/                 # Persistent data (created at runtime)
    ├── messages.sqlite   # Database (with channel support)
    ├── media/           # Downloaded media files (channel_id_message_id)
    └── scraper.session  # Telegram session file
```

## Troubleshooting

### Authentication Issues
- Ensure your API credentials are correct
- Check that the channel is accessible to your account
- For private channels, make sure you're a member

### Rate Limiting
- The scraper handles Telegram rate limits automatically
- Large channels may take time to scrape completely

### Media Download Issues
- Check available disk space
- Ensure proper permissions on the data directory

### Database Issues
- The database is created automatically
- Check Docker volume mounts if data isn't persisting

## Development

### Running Locally

```bash
# Install dependencies
pip install -r requirements.txt

# Run scraper
python scraper.py

# Run viewer (in another terminal)
cd viewer
pip install -r requirements.txt
uvicorn app.main:app --host 0.0.0.0 --port 8080
```

### Adding Features

- **New Media Types**: Extend the media detection in `scraper.py`
- **Additional Filters**: Add new query parameters in `viewer/app/main.py`
- **UI Improvements**: Modify `viewer/app/templates/index.html`
