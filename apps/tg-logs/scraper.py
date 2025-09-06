import os, sqlite3, mimetypes, logging, asyncio
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv
from telethon import TelegramClient
from telethon.tl.types import MessageMediaPhoto, MessageMediaDocument
from telethon.errors import SessionPasswordNeededError, FloodWaitError

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

load_dotenv()

# Validate required environment variables
required_vars = ["API_ID", "API_HASH", "CHANNELS"]
for var in required_vars:
    if not os.environ.get(var):
        logger.error(f"Missing required environment variable: {var}")
        exit(1)

API_ID = int(os.environ["API_ID"])
API_HASH = os.environ["API_HASH"]
SESSION_NAME = os.environ.get("SESSION_NAME", "scraper")

# Parse channels from environment variable
CHANNELS_STR = os.environ.get("CHANNELS", "")
if not CHANNELS_STR:
    logger.error("Missing required environment variable: CHANNELS")
    exit(1)

# Parse channels (comma-separated)
CHANNELS = [ch.strip() for ch in CHANNELS_STR.split(",") if ch.strip()]
if not CHANNELS:
    logger.error("No channels specified in CHANNELS environment variable")
    exit(1)

logger.info(f"Configured to scrape {len(CHANNELS)} channels: {CHANNELS}")

DATA_DIR = Path("data")
MEDIA_DIR = DATA_DIR / "media"
MEDIA_DIR.mkdir(parents=True, exist_ok=True)

# store Telethon session in the mounted volume
SESSION_PATH = DATA_DIR / f"{SESSION_NAME}.session"

DB = DATA_DIR / "messages.sqlite"
conn = sqlite3.connect(DB)
cur = conn.cursor()
cur.execute("""
CREATE TABLE IF NOT EXISTS channels(
  id TEXT PRIMARY KEY,
  name TEXT,
  username TEXT,
  title TEXT,
  description TEXT,
  created_at TEXT
);
""")
cur.execute("""
CREATE TABLE IF NOT EXISTS messages(
  id INTEGER,
  channel_id TEXT,
  date TEXT,
  sender_id TEXT,
  text TEXT,
  reply_to INTEGER,
  views INTEGER,
  forwards INTEGER,
  PRIMARY KEY (id, channel_id),
  FOREIGN KEY (channel_id) REFERENCES channels(id)
);
""")
cur.execute("""
CREATE TABLE IF NOT EXISTS media(
  message_id INTEGER,
  channel_id TEXT,
  file_path TEXT,
  mime_type TEXT,
  kind TEXT,
  PRIMARY KEY (message_id, channel_id),
  FOREIGN KEY (message_id, channel_id) REFERENCES messages(id, channel_id)
);
""")
conn.commit()

def save_channel(entity):
    """Save or update channel information"""
    try:
        channel_id = str(entity.id)
        username = getattr(entity, 'username', None)
        title = getattr(entity, 'title', 'Unknown Channel')
        description = getattr(entity, 'about', '')
        
        cur.execute("""INSERT OR REPLACE INTO channels
          (id, name, username, title, description, created_at)
          VALUES (?, ?, ?, ?, ?, ?)""",
          (channel_id, username or channel_id, username, title, description, 
           datetime.now().isoformat()))
        conn.commit()
        logger.debug(f"Saved channel: {title} ({channel_id})")
        return channel_id
    except Exception as e:
        logger.error(f"Error saving channel {entity.id}: {e}")
        conn.rollback()
        return None

def save_message(msg, channel_id):
    try:
        cur.execute("""INSERT OR IGNORE INTO messages
          (id, channel_id, date, sender_id, text, reply_to, views, forwards)
          VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
          (msg.id, channel_id,
           msg.date.isoformat() if msg.date else None,
           str(msg.sender_id) if getattr(msg, 'sender_id', None) else None,
           msg.message or "",
           msg.reply_to_msg_id if msg.reply_to_msg_id else None,
           msg.views if hasattr(msg, 'views') else None,
           msg.forwards if hasattr(msg, 'forwards') else None))
        conn.commit()
        logger.debug(f"Saved message {msg.id} from channel {channel_id}")
    except Exception as e:
        logger.error(f"Error saving message {msg.id} from channel {channel_id}: {e}")
        conn.rollback()

def is_image_document(doc):
    if not getattr(doc, 'mime_type', None):
        return False
    return doc.mime_type.startswith("image/")

async def scrape_channel(client, channel_identifier):
    """Scrape a single channel"""
    try:
        logger.info(f"Starting to scrape channel: {channel_identifier}")
        
        # Get channel entity
        entity = await client.get_entity(channel_identifier)
        channel_id = save_channel(entity)
        if not channel_id:
            logger.error(f"Failed to save channel info for {channel_identifier}")
            return 0, 0
            
        logger.info(f"Found channel: {entity.title if hasattr(entity, 'title') else channel_identifier}")

        # Get last scraped message ID for this channel
        cur.execute("SELECT MAX(id) FROM messages WHERE channel_id = ?", (channel_id,))
        row = cur.fetchone()
        max_id = row[0] if row and row[0] else 0
        logger.info(f"Starting from message ID: {max_id}")

        message_count = 0
        media_count = 0

        async for msg in client.iter_messages(entity, limit=None, min_id=max_id):
            try:
                save_message(msg, channel_id)
                message_count += 1

                fp = None
                mime = None
                kind = None

                if isinstance(msg.media, MessageMediaPhoto) or msg.photo:
                    kind = "photo"
                    try:
                        fp = await msg.download_media(file=MEDIA_DIR / f"{channel_id}_{msg.id}")
                        mime = mimetypes.guess_type(fp)[0] if fp else "image/jpeg"
                        logger.debug(f"Downloaded photo for message {msg.id}")
                    except Exception as e:
                        logger.error(f"Error downloading photo for message {msg.id}: {e}")

                elif isinstance(msg.media, MessageMediaDocument) and msg.document and is_image_document(msg.document):
                    kind = "document"
                    try:
                        fp = await msg.download_media(file=MEDIA_DIR / f"{channel_id}_{msg.id}")
                        mime = msg.document.mime_type if msg.document.mime_type else (mimetypes.guess_type(fp)[0] if fp else None)
                        logger.debug(f"Downloaded document for message {msg.id}")
                    except Exception as e:
                        logger.error(f"Error downloading document for message {msg.id}: {e}")

                if fp:
                    try:
                        cur.execute("""INSERT OR REPLACE INTO media (message_id, channel_id, file_path, mime_type, kind)
                                       VALUES (?, ?, ?, ?, ?)""", (msg.id, channel_id, str(fp), mime, kind))
                        conn.commit()
                        media_count += 1
                    except Exception as e:
                        logger.error(f"Error saving media info for message {msg.id}: {e}")
                        conn.rollback()

                if message_count % 100 == 0:
                    logger.info(f"Channel {channel_identifier}: Processed {message_count} messages, downloaded {media_count} media files")

            except FloodWaitError as e:
                logger.warning(f"Rate limited, waiting {e.seconds} seconds...")
                await asyncio.sleep(e.seconds)
            except Exception as e:
                logger.error(f"Error processing message {msg.id}: {e}")
                continue

        logger.info(f"Channel {channel_identifier} completed: {message_count} messages, {media_count} media files")
        return message_count, media_count

    except Exception as e:
        logger.error(f"Error scraping channel {channel_identifier}: {e}")
        return 0, 0

async def run():
    try:
        logger.info(f"Starting Telegram scraper for {len(CHANNELS)} channels: {CHANNELS}")
        
        async with TelegramClient(str(SESSION_PATH), API_ID, API_HASH) as client:
            logger.info("Connected to Telegram")
            
            total_messages = 0
            total_media = 0
            
            for channel in CHANNELS:
                try:
                    msg_count, media_count = await scrape_channel(client, channel)
                    total_messages += msg_count
                    total_media += media_count
                except Exception as e:
                    logger.error(f"Failed to scrape channel {channel}: {e}")
                    continue

            logger.info(f"Scraping completed. Total: {total_messages} messages, {total_media} media files")

    except SessionPasswordNeededError:
        logger.error("Two-factor authentication is enabled. Please provide the password.")
    except Exception as e:
        logger.error(f"Fatal error: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    asyncio.run(run())
